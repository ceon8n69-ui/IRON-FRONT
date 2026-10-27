from sqlalchemy import select, func
from app.models import Battle, TileOwnership
from conftest import post
from test_expeditions import commander, create, order
from test_integration import advance


def arrive(c,h,a,monkeypatch):
    assert order(c,h,a,64,65).status_code==200
    advance(c,monkeypatch,31)
    s=c.get('/api/v1/player/me',headers=h).json()
    assert not s['territories']
    b=next(b for b in s['battles'] if b['status']=='active')
    assert b['state']['expedition']['q']==64
    assert order(c,h,a,65,64).status_code==409
    return b


def finish(c,h,b,action='attack'):
    r=post(c,'/battles/commands',{'battle_id':b['id'],'turn':1,'action':'move','q':3,'r':4},h)
    for turn in range(2,51):
        r=post(c,'/battles/commands',{'battle_id':b['id'],'turn':turn,'action':action},h,f"{b['id']}-{turn}")
        assert r.status_code==200,r.text
        if r.json()['result']['outcome']!='active':
            assert post(c,'/battles/commands',{'battle_id':b['id'],'turn':turn,'action':action},h,f"{b['id']}-{turn}").json()==r.json()
            return r.json()
    raise AssertionError('Battle did not finish')


def test_garrison_capture_and_restart(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u);b=arrive(c,h,a,monkeypatch)
    c.factory.kw['bind'].dispose()
    s=c.get('/api/v1/player/me',headers=h).json()
    assert next(x for x in s['battles'] if x['id']==b['id'])['status']=='active'
    result=finish(c,h,b)
    assert result['result']['captured'] is True
    s=result['state'];assert len(s['territories'])==1 and s['armies'][0]['r']==65
    assert s['hero']['xp']==150 and len(s['inventory'])==2
    assert s['units'][0]['status']=='army'
    trophy=next(i for i in s['inventory'] if i['source']=='garrison')
    from app.equipment import loot, damage_bonus
    from app.models import Item, Ownership
    with c.factory() as db:
        saved=db.get(Battle,b['id'])
        assert trophy['definition_id']==loot(saved.seed)[0]
        assert saved.state['loot']['item_id']==trophy['id']
        assert db.scalar(select(func.count()).select_from(Ownership).where(Ownership.item_id==trophy['id']))==1
    equip=post(c,'/equipment/equip',{'item_id':trophy['id'],'equipped':True},h)
    assert equip.status_code==200
    with c.factory() as db:
        assert damage_bonus(db.scalars(select(Item)))==trophy['definition']['damage_bonus']
    reopened=c.get('/api/v1/player/me',headers=h).json()
    assert sum(i['equipped'] for i in reopened['inventory'])==1
    assert len(reopened['inventory'])==2
    assert post(c,'/battles/commands',{'battle_id':b['id'],'turn':50,'action':'attack'},h).status_code==409


def test_garrison_defeat_keeps_origin_and_no_reward(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);a=create(c,h,u);b=arrive(c,h,a,monkeypatch)
    result=finish(c,h,b,'defend');s=result['state']
    assert result['result']['outcome']=='defeat' and not s['territories']
    assert s['armies'][0]['r']==64 and s['hero']['xp']==100
    assert len(s['inventory'])==1
    assert s['units'][0]['hp']>=50 and s['units'][0]['status']=='army'


def test_two_garrison_victories_only_one_owner_and_reward(client,monkeypatch):
    c=client;h,u=commander(c,monkeypatch);h2,u2=commander(c,monkeypatch,456)
    a=create(c,h,u);a2=create(c,h2,u2)
    b=arrive(c,h,a,monkeypatch);b2=arrive(c,h2,a2,monkeypatch)
    assert post(c,'/battles/commands',{'battle_id':b['id'],'turn':1,'action':'defend'},h2).status_code==404
    first=finish(c,h,b);second=finish(c,h2,b2)
    assert first['result']['captured'] and not second['result']['captured']
    assert second['state']['hero']['xp']==100
    assert len(first['state']['inventory'])==2 and len(second['state']['inventory'])==1
    with c.factory() as db:assert db.scalar(select(func.count()).select_from(TileOwnership))==1
