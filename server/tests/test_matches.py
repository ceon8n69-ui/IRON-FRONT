"""Match rooms over HTTP: lobby, AI seats, instant turn hand-off, limits, notices."""
from sqlalchemy import select
from app import main
from app.models import MatchNotice
from conftest import login


def call(c, method, path, h, body=None):
    return getattr(c, method)(f'/api/v1{path}', headers=h, **({'json': body} if body is not None else {}))


def act(c, h, m, **action):
    return call(c, 'post', f"/matches/{m['id']}/action", h, {'version': m['version'], **action})


def set_now(monkeypatch, t):
    monkeypatch.setattr(main, 'now', lambda: t)


def test_vs_ai_room_starts_and_the_turn_comes_straight_back(client, monkeypatch):
    c = client; h = login(c, 501)
    r = call(c, 'post', '/matches', h, {'name': 'Тест', 'size': 'small', 'seats': 2, 'vs_ai': True})
    assert r.status_code == 200, r.text
    m = r.json()
    assert m['status'] == 'active' and m['your_turn'] and m['my_seat'] == 0
    assert [s['ai'] for s in m['seats']] == [False, True]
    board = m['board']
    assert board['players'][0]['stars'] == 5 and any(u['owner'] == 0 for u in board['units'])
    r = act(c, h, m, type='end_turn')
    assert r.status_code == 200, r.text
    m = r.json()['match']
    assert m['your_turn'] and m['turn'] == 2                      # the AI moved instantly
    assert act(c, h, {**m, 'version': m['version'] - 1}, type='end_turn').status_code == 409   # stale version


def test_illegal_actions_are_refused_with_a_reason(client):
    c = client; h = login(c, 502)
    m = call(c, 'post', '/matches', h, {'vs_ai': True}).json()
    r = act(c, h, m, type='research', tech='armor')
    assert r.status_code == 409 and 'Моторы' in r.json()['detail']


def test_two_players_by_code_turns_hand_over_and_notify(client, monkeypatch):
    c = client; a = login(c, 503); b = login(c, 504)
    room = call(c, 'post', '/matches', a, {'name': 'Дуэль', 'seats': 2, 'private': True}).json()
    assert room['status'] == 'lobby' and room['code']
    assert room['id'] not in [x['id'] for x in call(c, 'get', '/matches', b).json()['open']]   # private
    assert call(c, 'post', f"/matches/{room['id']}/join", b).status_code == 409                  # needs the code
    joined = call(c, 'post', '/matches/join', b, {'code': room['code'].lower()}).json()
    assert joined['status'] == 'active' and joined['my_seat'] == 1 and not joined['your_turn']
    assert act(c, b, joined, type='end_turn').status_code == 409                                  # not his turn
    m = call(c, 'get', f"/matches/{room['id']}", a).json()
    assert m['your_turn']
    m = act(c, a, m, type='end_turn').json()['match']
    assert not m['your_turn']
    assert call(c, 'get', f"/matches/{room['id']}", b).json()['your_turn']
    with c.factory() as db:
        texts = [n.text for n in db.scalars(select(MatchNotice).order_by(MatchNotice.id))]
    assert any('Ваш ход' in t and 'Дуэль' in t for t in texts) and len(texts) >= 2


def test_overdue_turn_is_skipped(client, monkeypatch):
    c = client; a = login(c, 505); b = login(c, 506)
    room = call(c, 'post', '/matches', a, {'seats': 2, 'turn_limit': 300}).json()
    assert room['id'] in [x['id'] for x in call(c, 'get', '/matches', b).json()['open']]
    call(c, 'post', f"/matches/{room['id']}/join", b)
    m = call(c, 'get', f"/matches/{room['id']}", b).json()
    set_now(monkeypatch, m['deadline'] + 1)
    m = call(c, 'get', f"/matches/{room['id']}", b).json()
    assert m['your_turn'] and m['current'] == 1


def test_host_starts_with_ai_fill_and_resign_ends_the_match(client):
    c = client; a = login(c, 507); b = login(c, 508)
    room = call(c, 'post', '/matches', a, {'seats': 3}).json()
    assert call(c, 'post', f"/matches/{room['id']}/start", b, {'fill_ai': True}).status_code == 409   # only the host
    call(c, 'post', f"/matches/{room['id']}/join", b)
    m = call(c, 'post', f"/matches/{room['id']}/start", a, {'fill_ai': True}).json()
    assert m['status'] == 'active' and [s['ai'] for s in m['seats']] == [False, False, True]
    assert call(c, 'post', f"/matches/{room['id']}/leave", b).status_code == 200                     # resign out of turn
    m = call(c, 'get', f"/matches/{room['id']}", a).json()
    assert m['status'] == 'active'
    assert next(p for p in m['board']['players'] if p['seat'] == 1)['eliminated']


def test_room_limit_and_notice_delivery(client):
    c = client; h = login(c, 509)
    for _ in range(5):
        assert call(c, 'post', '/matches', h, {'seats': 2}).status_code == 200
    assert call(c, 'post', '/matches', h, {'seats': 2}).status_code == 409
    from app import worker
    with c.factory.begin() as db:
        pid = db.scalar(select(main.Player.id).where(main.Player.telegram_id == 509))
        room = db.scalar(select(main.Match.id).limit(1))
        db.add(MatchNotice(player_id=pid, match_id=room, text='⚔ Ваш ход', created_at=main.now()))
    sent = []
    monkey_session = worker.SessionLocal
    worker.SessionLocal = c.factory
    try:
        worker.send_notices(main.now(), post=sent.append)
    finally:
        worker.SessionLocal = monkey_session
    assert sent and sent[0]['chat_id'] == 509 and sent[0]['text'] == '⚔ Ваш ход'
