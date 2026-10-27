import concurrent.futures
from sqlalchemy import select, func
from app import game
from app.models import Army, ArmyOrder, ArmyUnit, Tile, TileOwnership, Resource, Player
from conftest import login, post
from test_integration import advance


def world(c):
    with c.factory.begin() as db:
        if not db.get(Tile,(1,64,64)):
            db.add_all([Tile(world_id=1,q=q,r=r,biome='plain') for q in range(57,74) for r in range(57,74)])


def commander(c, monkeypatch, uid=123):
    world(c)
    h=login(c,uid)
    post(c,'/heroes/choose',{'kind':'raven'},h)
    for kind,q,r,seconds in [('power',1,0,31),('barracks',0,1,61)]:
        assert post(c,'/construction/start',{'kind':kind,'q':q,'r':r},h).status_code==200
        advance(c,monkeypatch,seconds)
    assert post(c,'/army/train',{},h).status_code==200
    advance(c,monkeypatch,46)
    s=c.get('/api/v1/player/me',headers=h).json();unit=s['units'][0]['id']
    b=post(c,'/battles',{'unit_id':unit},h).json()['result']['id']
    assert post(c,'/battles/commands',{'battle_id':b,'turn':1,'action':'move','q':3,'r':4},h).status_code==200
    for turn in range(2,12):
        result=post(c,'/battles/commands',{'battle_id':b,'turn':turn,'action':'attack'},h)
        assert result.status_code==200,result.text
        if result.json()['state']['first_victory']:break
    assert result.json()['state']['first_victory']
    return h,unit


def create(c,h,unit):
    r=post(c,'/army/create',{'unit_id':unit},h,'create-army-once')
    assert r.status_code==200,r.text
    return r.json()['state']['armies'][0]


def order(c,h,army,q,r,action='capture',key=None):
    return post(c,'/army/orders',{'army_id':army['id'],'q':q,'r':r,'action':action},h,key)


def test_march_capture_restart_income_and_idempotency(client,monkeypatch):
    c=client;h,unit=commander(c,monkeypatch);army=create(c,h,unit)
    assert post(c,'/army/create',{'unit_id':unit},h,'create-army-once').status_code==200
    assert post(c,'/army/create',{'unit_id':unit},h).status_code==409
    r=order(c,h,army,65,64,key='same-march-key');assert r.status_code==200
    assert r.json()['state']['resources']['fuel']==198
    assert order(c,h,army,65,64,key='same-march-key').json()==r.json()
    assert order(c,h,army,64,65).status_code==409
    assert not r.json()['state']['territories']
    advance(c,monkeypatch,29)
    assert not c.get('/api/v1/player/me',headers=h).json()['territories']
    advance(c,monkeypatch,2)
    c.factory.kw['bind'].dispose()
    s=c.get('/api/v1/player/me',headers=login(c)).json()
    assert s['armies'][0]['q']==65 and s['armies'][0]['status']=='idle'
    assert len(s['territories'])==1
    before=s['resources']['food'];advance(c,monkeypatch,180)
    first=c.get('/api/v1/player/me',headers=h).json()
    second=c.get('/api/v1/player/me',headers=h).json()
    assert first['resources']==second['resources'] and first['resources']['food']>before
    assert len(first['territories'])==1
    assert order(c,h,army,64,64,'move').status_code==200
    advance(c,monkeypatch,31)
    assert c.get('/api/v1/player/me',headers=h).json()['armies'][0]['q']==64
    with c.factory() as db:
        assert db.scalar(select(func.count()).select_from(ArmyUnit))==1
        assert db.scalar(select(func.count()).select_from(ArmyOrder))==2


def test_access_coordinates_limit_and_no_early_reward(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u)
    other=login(c,456);post(c,'/heroes/choose',{'kind':'ghost'},other)
    assert post(c,'/army/create',{'unit_id':u},other).status_code==409
    assert order(c,h,a,68,68).status_code==409
    assert order(c,h,a,128,64).status_code==422
    assert order(c,h,a,65,64,key='payload-bound').status_code==200
    assert order(c,h,a,64,65,key='payload-bound').status_code==409
    advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    for q in (66,67):
        assert order(c,h,a,q,64).status_code==200
        advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    assert order(c,h,a,68,64).status_code==409
    assert len(c.get('/api/v1/player/me',headers=h).json()['territories'])==3
    assert c.get('/api/v1/player/me',headers=other).json()['armies']==[]


def test_foreign_army_and_capture_conflict_concurrent(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);other,v=commander(c,monkeypatch,456)
    a=create(c,h,u);b=create(c,other,v)
    assert order(c,other,a,65,64).status_code==404
    assert order(c,h,a,65,64).status_code==200
    assert order(c,other,b,65,64).status_code==200
    advance(c,monkeypatch,31)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        states=list(pool.map(lambda auth:c.get('/api/v1/player/me',headers=auth).json(),[h,other]))
    assert sorted(len(s['territories']) for s in states)==[0,1]
    assert sorted(s['armies'][0]['orders'][0]['status'] for s in states)==['blocked','complete']
    loser=next(s for s in states if not s['territories']);assert loser['armies'][0]['q']==64
    with c.factory() as db:
        assert db.scalar(select(func.count()).select_from(TileOwnership))==1
    for auth,s in zip([h,other],states):
        tiles=c.get('/api/v1/world/tiles?q=65&r=64&radius=1',headers=auth).json()['tiles']
        target=next(t for t in tiles if (t['q'],t['r'])==(65,64))
        assert target['control']==('self' if s['territories'] else 'other')


def test_discovery_persists_without_leaking_hidden_owners(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u)
    for q in (65,66,67):
        assert order(c,h,a,q,64,'move').status_code==200
        advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    assert order(c,h,a,68,64,'capture').status_code==409  # isolated territory
    for q in (66,65,64):
        assert order(c,h,a,q,64,'move').status_code==200
        advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    with c.factory.begin() as db:
        owner=db.scalar(select(Player.id))
        db.add(TileOwnership(world_id=1,q=69,r=64,player_id=owner,acquired_at=game.now()))
    tiles=c.get('/api/v1/world/tiles?q=69&r=64&radius=1',headers=h).json()['tiles']
    target=next(t for t in tiles if (t['q'],t['r'])==(69,64))
    assert target['visibility']=='explored' and target['biome']=='plain' and target['control'] is None
    unknown=next(t for t in tiles if (t['q'],t['r'])==(70,65))
    assert unknown['visibility']=='unknown' and unknown['biome']=='unknown' and unknown['control'] is None


def test_no_fuel_and_sanctuary_capture(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u)
    assert order(c,h,a,65,64,'move').status_code==200
    advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    assert order(c,h,a,64,64,'capture').status_code==409
    with c.factory.begin() as db:db.scalar(select(Resource).where(Resource.kind=='fuel')).amount=0
    assert order(c,h,a,66,64,'move').status_code==409
    assert c.get('/api/v1/player/me',headers=h).json()['armies'][0]['status']=='idle'
