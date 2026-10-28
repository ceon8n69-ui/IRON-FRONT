import concurrent.futures
from sqlalchemy import select, func
from app import game
from app.models import Army, ArmyOrder, ArmyUnit, TileOwnership, Resource, Player
from conftest import login, post
from test_integration import advance


def commander(c, monkeypatch, uid=123):
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


def home(c,h):
    base=c.get('/api/v1/player/me',headers=h).json()['base']
    return base['q'],base['r']


def create(c,h,unit):
    r=post(c,'/army/create',{'unit_id':unit},h,'create-army-once')
    assert r.status_code==200,r.text
    return r.json()['state']['armies'][0]


def order(c,h,army,q,r,action='capture',key=None):
    return post(c,'/army/orders',{'army_id':army['id'],'q':q,'r':r,'action':action},h,key)


def player_id(c,uid):
    with c.factory() as db:
        return db.scalar(select(Player.id).where(Player.telegram_id==uid))


def test_march_capture_restart_income_and_idempotency(client,monkeypatch):
    c=client;h,unit=commander(c,monkeypatch);army=create(c,h,unit);Q,R=home(c,h)
    assert (army['q'],army['r'])==(Q,R)
    assert post(c,'/army/create',{'unit_id':unit},h,'create-army-once').status_code==200
    assert post(c,'/army/create',{'unit_id':unit},h).status_code==409
    r=order(c,h,army,Q+1,R,key='same-march-key');assert r.status_code==200
    assert r.json()['state']['resources']['fuel']==199
    assert order(c,h,army,Q+1,R,key='same-march-key').json()==r.json()
    assert order(c,h,army,Q,R+1).status_code==409
    assert not r.json()['state']['territories']
    advance(c,monkeypatch,9)
    assert not c.get('/api/v1/player/me',headers=h).json()['territories']
    advance(c,monkeypatch,2)
    c.factory.kw['bind'].dispose()
    s=c.get('/api/v1/player/me',headers=login(c)).json()
    assert s['armies'][0]['q']==Q+1 and s['armies'][0]['status']=='idle'
    assert len(s['territories'])==1 and s['base']=={'q':Q,'r':R}
    before=s['resources']['food'];advance(c,monkeypatch,180)
    first=c.get('/api/v1/player/me',headers=h).json()
    second=c.get('/api/v1/player/me',headers=h).json()
    assert first['resources']==second['resources'] and first['resources']['food']>before
    assert len(first['territories'])==1
    assert order(c,h,army,Q,R,'move').status_code==200
    advance(c,monkeypatch,31)
    assert c.get('/api/v1/player/me',headers=h).json()['armies'][0]['q']==Q
    with c.factory() as db:
        assert db.scalar(select(func.count()).select_from(ArmyUnit))==1
        assert db.scalar(select(func.count()).select_from(ArmyOrder))==2


def test_access_coordinates_limit_and_no_early_reward(client,monkeypatch):
    monkeypatch.setitem(game.EXPEDITIONS,"control_limit",3)
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u);Q,R=home(c,h)
    other=login(c,456);post(c,'/heroes/choose',{'kind':'ghost'},other)
    assert post(c,'/army/create',{'unit_id':u},other).status_code==409
    assert order(c,h,a,Q+4,R+4).status_code==409
    assert order(c,h,a,128,64).status_code==422
    assert order(c,h,a,Q+1,R,key='payload-bound').status_code==200
    assert order(c,h,a,Q,R+1,key='payload-bound').status_code==409
    advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    for q in (Q+2,Q+3):
        assert order(c,h,a,q,R).status_code==200
        advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    assert order(c,h,a,Q+4,R).status_code==409
    assert len(c.get('/api/v1/player/me',headers=h).json()['territories'])==3
    assert c.get('/api/v1/player/me',headers=other).json()['armies']==[]


def test_foreign_army_and_capture_conflict_concurrent(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);other,v=commander(c,monkeypatch,456)
    a=create(c,h,u);b=create(c,other,v);Q,R=home(c,h)
    assert home(c,other)!=(Q,R)
    # Second commander reaches the same neutral hex from an adjacent holding.
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1,q=Q+2,r=R,player_id=player_id(c,456),acquired_at=game.now()))
        army=db.get(Army,b['id']);army.q,army.r=Q+2,R
    assert order(c,other,a,Q+1,R).status_code==404
    assert order(c,h,a,Q+1,R).status_code==200
    assert order(c,other,b,Q+1,R).status_code==200
    advance(c,monkeypatch,31)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        states=list(pool.map(lambda auth:c.get('/api/v1/player/me',headers=auth).json(),[h,other]))
    gained=[len(s['territories']) for s in states]
    assert gained in ([1,1],[0,2])  # A wins -> 1/1; B wins -> 0/2 (B already held one)
    assert sorted(s['armies'][0]['orders'][0]['status'] for s in states)==['blocked','complete']
    with c.factory() as db:
        assert db.scalar(select(func.count()).select_from(TileOwnership).where(TileOwnership.q==Q+1,TileOwnership.r==R))==1
        winner=db.get(TileOwnership,(1,Q+1,R)).player_id
    for auth,uid in [(h,123),(other,456)]:
        tiles=c.get(f'/api/v1/world/tiles?q={Q+1}&r={R}&radius=1',headers=auth).json()['tiles']
        target=next(t for t in tiles if (t['q'],t['r'])==(Q+1,R))
        assert target['control']==('self' if winner==player_id(c,uid) else 'other')


def test_discovery_persists_without_leaking_hidden_owners(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u);Q,R=home(c,h)
    for q in (Q+1,Q+2,Q+3):
        assert order(c,h,a,q,R,'move').status_code==200
        advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    for q in (Q+2,Q+1,Q):
        assert order(c,h,a,q,R,'move').status_code==200
        advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    with c.factory.begin() as db:
        db.add(TileOwnership(world_id=1,q=Q+5,r=R,player_id=player_id(c,123),acquired_at=game.now()))
    tiles=c.get(f'/api/v1/world/tiles?q={Q+5}&r={R}&radius=1',headers=h).json()['tiles']
    target=next(t for t in tiles if (t['q'],t['r'])==(Q+5,R))
    assert target['visibility']=='explored' and target['biome']=='plain' and target['control'] is None
    unknown=next(t for t in tiles if (t['q'],t['r'])==(Q+6,R+1))
    assert unknown['visibility']=='unknown' and unknown['biome']=='unknown' and unknown['control'] is None


def test_no_fuel_and_sanctuary_capture(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u);Q,R=home(c,h)
    assert order(c,h,a,Q+1,R,'move').status_code==200
    advance(c,monkeypatch,31);c.get('/api/v1/player/me',headers=h)
    assert order(c,h,a,Q,R,'capture').status_code==409
    with c.factory.begin() as db:db.scalar(select(Resource).where(Resource.kind=='fuel')).amount=0
    assert order(c,h,a,Q+2,R,'move').status_code==409
    assert c.get('/api/v1/player/me',headers=h).json()['armies'][0]['status']=='idle'


def test_expanded_limit_allows_fourth_npc_attack_but_blocks_thirteenth(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u);Q,R=home(c,h)
    assert game.EXPEDITIONS['control_limit']==12
    pid=player_id(c,123)
    with c.factory.begin() as db:
        for q,r in [(Q-1,R),(Q,R-1),(Q+1,R-1)]:
            db.add(TileOwnership(world_id=1,q=q,r=r,player_id=pid,acquired_at=game.now()))
    assert order(c,h,a,Q,R+1).status_code==200
    advance(c,monkeypatch,31)
    s=c.get('/api/v1/player/me',headers=h).json()
    assert len(s['territories'])==3
    assert any(b['status']=='active' and b['state'].get('expedition') for b in s['battles'])
    # Check the configured cap independently of a battle-in-progress rejection.
    from app.models import Battle, Unit
    with c.factory.begin() as db:
        db.scalar(select(Battle).where(Battle.status=='active')).status='defeat'
        db.get(Unit,u).status='army'
        for q,r in [(Q-4,r) for r in range(R-4,R+5)]:
            db.add(TileOwnership(world_id=1,q=q,r=r,player_id=pid,acquired_at=game.now()))
    response=order(c,h,a,Q+1,R)
    assert response.status_code==409 and 'лимит' in response.json()['detail'].lower()
