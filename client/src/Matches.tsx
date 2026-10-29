// Rooms (lobby) and the Polytopia-style match screen.
import { useEffect, useMemo, useState } from "react";
import { request } from "./store";
import { MatchBoard, SEAT_CSS, type Board, type MCity, type MUnit } from "./MatchBoard";

type Seat = { seat: number; name: string; ai: boolean; faction: string; me: boolean };
type Room = { id: string; code: string | null; name: string; status: "lobby" | "active" | "finished"; size: string; seats_max: number; turn_limit: number;
  private: boolean; host: boolean; version: number; my_seat: number | null; current: number | null; turn: number; winner: number | null;
  deadline: number | null; your_turn: boolean; seats: Seat[]; board?: Board };
type Rules = {
  roles: Record<string, { name: string; cost: number; hp: number; atk: number; def: number; mv: number; rng: number; tech: string | null; factory?: boolean }>;
  branches: Record<string, { key: string; name: string; bonus: Record<string, number> }[]>;
  techs: Record<string, { name: string; tier: number; requires: string | null; about: string }>;
  improvements: Record<string, { name: string; cost: number; pop: number; tech: string | null }>;
  specs: Record<string, { name: string; about: string }>;
  rewards: Record<string, { key: string; about: string }[]>;
  walls_cost: number;
};
type Listing = { mine: Room[]; open: Room[]; sizes: Record<string, number>; turn_limits: number[]; rules: Rules };
type FactionUnits = Record<string, { name: string; accent: string; units: { key: string; role: string; name: string }[] }>;

const SIZE_NAMES: Record<string, string> = { small: "Малая", medium: "Средняя", large: "Большая" };
const LIMIT_NAMES: Record<number, string> = { 300: "5 мин", 3600: "1 час", 86400: "24 часа" };
const STAT_NAMES: Record<string, string> = { atk: "атака", def: "защита", mv: "ход", rng: "дальность", hp: "здоровье" };
const left = (deadline: number | null, now: number) => {
  if (!deadline) return "";
  const s = Math.max(0, deadline - now);
  return s >= 3600 ? `${Math.floor(s / 3600)} ч ${Math.floor((s % 3600) / 60)} мин` : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
};

export function Matches({ factions, onError }: { factions: FactionUnits; onError: (m: string) => void }) {
  const [listing, setListing] = useState<Listing | null>(null);
  const [openId, setOpenId] = useState<string | null>(() => { try { return sessionStorage.getItem("iron-match"); } catch { return null; } });
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ name: "", size: "small", seats: 2, turn_limit: 3600, private: false });
  const [code, setCode] = useState("");
  const load = () => request("/matches").then(setListing).catch((e) => onError((e as Error).message));
  useEffect(() => { load(); const id = setInterval(load, 8000); return () => clearInterval(id); }, []);
  const open = (id: string | null) => { setOpenId(id); try { id ? sessionStorage.setItem("iron-match", id) : sessionStorage.removeItem("iron-match"); } catch { /* storage may be blocked */ } if (!id) load(); };
  const run = async (f: () => Promise<Room>) => { setBusy(true); try { const room = await f(); open(room.id); } catch (e) { onError((e as Error).message); } finally { setBusy(false); } };

  if (openId && listing) return <MatchRoom id={openId} rules={listing.rules} factions={factions} onClose={() => open(null)} onError={onError} />;
  if (!listing) return <section className="content matches"><p>Загрузка партий…</p></section>;
  const create = (vs_ai: boolean) => run(() => request("/matches", { ...form, vs_ai }));
  return <section className="content matches">
    <div className="section-label">МОИ ПАРТИИ</div>
    {!listing.mine.length && <p className="muted">Пока нет партий. Создайте комнату или сыграйте с ИИ.</p>}
    {listing.mine.map((m) => <button key={m.id} className={`card room-card${m.your_turn ? " your-turn" : ""}`} onClick={() => open(m.id)}>
      <div>
        <h3>{m.name}</h3>
        <p>{m.status === "lobby" ? `Ожидание игроков ${m.seats.length}/${m.seats_max}` : m.status === "finished" ? (m.winner === m.my_seat ? "🏆 Победа" : "Партия окончена") : `Ход ${m.turn} · ${m.your_turn ? "ваш ход" : "ход соперника"}`}</p>
        <p className="seats-line">{m.seats.map((s) => <span key={s.seat} style={{ color: SEAT_CSS[s.seat] }}>{s.ai ? "🤖" : "●"} {s.name}{s.me ? " (вы)" : ""}</span>)}</p>
      </div>
      {m.your_turn && <span className="turn-badge">Ваш ход</span>}
    </button>)}
    <div className="section-label">НОВАЯ ПАРТИЯ</div>
    <article className="card create-room">
      <input aria-label="Название" placeholder="Название комнаты" value={form.name} maxLength={40} onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <div className="choice-row" role="group" aria-label="Размер карты">{Object.entries(listing.sizes).map(([k, n]) => <button key={k} aria-pressed={form.size === k} onClick={() => setForm({ ...form, size: k })}>{SIZE_NAMES[k]} {n}×{n}</button>)}</div>
      <div className="choice-row" role="group" aria-label="Игроков">{[2, 3, 4].map((n) => <button key={n} aria-pressed={form.seats === n} onClick={() => setForm({ ...form, seats: n })}>{n} игрока</button>)}</div>
      <div className="choice-row" role="group" aria-label="Время на ход">{listing.turn_limits.map((t) => <button key={t} aria-pressed={form.turn_limit === t} onClick={() => setForm({ ...form, turn_limit: t })}>⏱ {LIMIT_NAMES[t]}</button>)}</div>
      <label className="check"><input type="checkbox" checked={form.private} onChange={(e) => setForm({ ...form, private: e.target.checked })} /> Закрытая (вход по коду)</label>
      <div className="actions">
        <button className="primary" disabled={busy} onClick={() => create(true)}>Играть с ИИ</button>
        <button disabled={busy} onClick={() => create(false)}>Создать комнату</button>
      </div>
    </article>
    <form className="join-code" onSubmit={(e) => { e.preventDefault(); run(() => request("/matches/join", { code })); }}>
      <input aria-label="Код комнаты" placeholder="Код комнаты" value={code} maxLength={8} onChange={(e) => setCode(e.target.value.toUpperCase())} />
      <button disabled={busy || code.length < 4}>Войти</button>
    </form>
    <div className="section-label">ОТКРЫТЫЕ КОМНАТЫ</div>
    {!listing.open.length && <p className="muted">Свободных комнат нет — создайте свою.</p>}
    {listing.open.map((m) => <article key={m.id} className="card room-card">
      <div><h3>{m.name}</h3><p>{SIZE_NAMES[m.size]} карта · {m.seats.length}/{m.seats_max} · ⏱ {LIMIT_NAMES[m.turn_limit]}</p></div>
      <button className="primary" disabled={busy} onClick={() => run(() => request(`/matches/${m.id}/join`, {}))}>Войти</button>
    </article>)}
  </section>;
}

function MatchRoom({ id, rules, factions, onClose, onError }: { id: string; rules: Rules; factions: FactionUnits; onClose: () => void; onError: (m: string) => void }) {
  const [room, setRoom] = useState<Room | null>(null);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<{ q: number; r: number } | null>(null);
  const [focus, setFocus] = useState<{ q: number; r: number } | null>(null);
  const [techs, setTechs] = useState(false);
  const [now, setNow] = useState(() => Math.floor(Date.now() / 1000));
  const [copied, setCopied] = useState(false);
  const load = () => request(`/matches/${id}`).then((r: Room) => setRoom((old) => (old && old.version === r.version && old.status === r.status ? old : r)))
    .catch((e) => { onError((e as Error).message); if (/не найдена/.test((e as Error).message)) onClose(); });
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    const poll = setInterval(load, room?.your_turn ? 10000 : 2500);
    const tick = setInterval(() => setNow(Math.floor(Date.now() / 1000)), 1000);
    return () => { clearInterval(poll); clearInterval(tick); };
  }, [id, room?.your_turn, room?.status]);
  const board = room?.board;
  const me = room?.my_seat ?? null;
  useEffect(() => {   // centre on my capital (or first city) when the board first appears
    if (!board || focus) return;
    const c = board.cities.find((x) => x.owner === me && x.capital) ?? board.cities.find((x) => x.owner === me);
    if (c) setFocus({ q: c.q, r: c.r });
  }, [board, me]);
  const act = async (action: Record<string, unknown>) => {
    if (!room || busy) return;
    setBusy(true);
    try {
      const res = await request(`/matches/${id}/action`, { version: room.version, ...action });
      setRoom(res.match);
    } catch (e) { onError((e as Error).message); load(); } finally { setBusy(false); }
  };
  const unitArt = useMemo(() => (seat: number, role: string) => {
    const faction = room?.seats.find((s) => s.seat === seat)?.faction ?? "raven";
    const key = factions[faction]?.units.find((u) => u.role === role)?.key ?? role;
    return `/art/units/${key}.png`;
  }, [room?.seats, factions]);

  if (!room) return <section className="content"><p>Загрузка…</p></section>;
  if (room.status === "lobby") {
    const invite = `Сыграем в IRON FRONT? Комната «${room.name}», код: ${room.code}`;
    return <section className="content matches">
      <button className="back" onClick={onClose}>← Партии</button>
      <h2>{room.name}</h2>
      <p>{SIZE_NAMES[room.size]} карта · ⏱ {LIMIT_NAMES[room.turn_limit]} на ход · {room.private ? "закрытая" : "открытая"}</p>
      <div className="section-label">ИГРОКИ {room.seats.length}/{room.seats_max}</div>
      {room.seats.map((s) => <p key={s.seat} style={{ color: SEAT_CSS[s.seat] }}>● {s.name}{s.me ? " (вы)" : ""} · {factions[s.faction]?.name ?? s.faction}</p>)}
      {Array.from({ length: room.seats_max - room.seats.length }, (_, i) => <p key={i} className="muted">○ свободно</p>)}
      {room.code && <div className="row invite"><span>Код: <b className="code">{room.code}</b></span>
        <button onClick={async () => { try { await navigator.clipboard.writeText(invite); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* blocked */ } }}>{copied ? "Скопировано" : "Пригласить"}</button></div>}
      <div className="actions">
        {room.host && <button className="primary" disabled={busy} onClick={async () => { setBusy(true); try { setRoom(await request(`/matches/${id}/start`, { fill_ai: true })); } catch (e) { onError((e as Error).message); } finally { setBusy(false); } }}>
          {room.seats.length < room.seats_max ? "Начать, свободные места — ИИ" : "Начать"}</button>}
        <button disabled={busy} onClick={async () => { await request(`/matches/${id}/leave`, {}).catch(() => {}); onClose(); }}>{room.host ? "Удалить комнату" : "Выйти"}</button>
      </div>
      <p className="muted">Партия начнётся сама, когда соберутся все игроки.</p>
    </section>;
  }
  if (!board) return <section className="content"><button className="back" onClick={onClose}>← Партии</button><p>Партия окончена.</p></section>;

  const mine = board.players.find((p) => p.seat === me);
  const myTurn = room.status === "active" && board.current === me;
  const at = (q: number, r: number) => ({
    unit: board.units.find((u) => u.q === q && u.r === r),
    city: board.cities.find((c) => c.q === q && c.r === r),
    tile: board.tiles.find((t) => t.q === q && t.r === r),
  });
  const sel = selected ? at(selected.q, selected.r) : null;
  const tap = (q: number, r: number) => {
    const here = at(q, r);
    const active = sel?.unit && sel.unit.owner === me ? sel.unit : null;
    if (myTurn && active && !busy) {
      const target = here.unit && active.targets?.find((t) => t.id === here.unit!.id);
      if (target) { act({ type: "attack", unit: active.id, target: here.unit!.id }); return; }
      if (!here.unit && active.moves?.includes(`${q},${r}`)) { act({ type: "move", unit: active.id, q, r }).then(() => setSelected({ q, r })); return; }
    }
    if (selected && selected.q === q && selected.r === r && here.unit && here.city) { setSelected({ q, r }); return; }
    setSelected(here.tile ? { q, r } : null);
  };
  const seatName = (seat: number) => room.seats.find((s) => s.seat === seat)?.name ?? `Игрок ${seat + 1}`;
  const nextUnit = () => {
    const idle = board.units.filter((u) => u.owner === me && !(u.moved && u.attacked));
    if (!idle.length) return;
    const i = sel?.unit ? (idle.findIndex((u) => u.id === sel.unit!.id) + 1) % idle.length : 0;
    setSelected({ q: idle[i].q, r: idle[i].r }); setFocus({ q: idle[i].q, r: idle[i].r });
  };
  return <section className="match-screen">
    <div className="match-hud">
      <button className="back" onClick={onClose} aria-label="К списку партий">←</button>
      <span className="stars" title="Снабжение">★ {mine?.stars ?? 0}<small> +{board.income ?? 0}</small></span>
      <span className="turn-info">Ход {board.turn} · {board.winner !== null ? (board.winner === me ? "🏆 Победа!" : `Победил ${seatName(board.winner)}`) : myTurn ? "ваш ход" : `ходит ${seatName(board.current)}`}
        {room.deadline && board.winner === null ? <small> · ⏱ {left(room.deadline, now)}</small> : null}</span>
      <span className="hud-actions">
        <button onClick={() => setTechs(true)} disabled={!mine} aria-label="Технологии" title="Технологии">🔬</button>
        {myTurn && <button className="primary" disabled={busy} onClick={() => { setSelected(null); act({ type: "end_turn" }); }}>Конец хода</button>}
      </span>
    </div>
    <div className="seats-strip">{board.players.map((p) => <span key={p.seat} className={p.eliminated ? "out" : p.seat === board.current ? "now" : ""} style={{ color: SEAT_CSS[p.seat] }}>
      {room.seats.find((s) => s.seat === p.seat)?.ai ? "🤖" : "●"} {seatName(p.seat)} · 🏙{p.cities}</span>)}</div>
    <MatchBoard board={board} mySeat={me} unitArt={unitArt} selected={selected} focus={focus} onTap={tap} />
    {myTurn && <button className="next-unit" onClick={nextUnit} aria-label="Следующий отряд">⇥ Отряд</button>}
    <Panel sel={sel} board={board} me={me} myTurn={myTurn} busy={busy} rules={rules} act={act} seatName={seatName} />
    {techs && mine && <TechTree mine={mine} costs={board.tech_costs ?? {}} rules={rules} myTurn={myTurn} busy={busy}
      research={(tech) => act({ type: "research", tech })} close={() => setTechs(false)} />}
  </section>;
}

function Panel({ sel, board, me, myTurn, busy, rules, act, seatName }: {
  sel: { unit?: MUnit; city?: MCity; tile?: Board["tiles"][number] } | null; board: Board; me: number | null; myTurn: boolean; busy: boolean; rules: Rules;
  act: (a: Record<string, unknown>) => void; seatName: (s: number) => string;
}) {
  if (!sel || !sel.tile) return <div className="match-panel hint">{myTurn ? "Выберите отряд, город или клетку. Белые клетки — куда можно пойти, красные кольца — цели." : "Ждём ход соперника…"}</div>;
  const { unit, city, tile } = sel;
  const stars = board.players.find((p) => p.seat === me)?.stars ?? 0;
  const techs = board.players.find((p) => p.seat === me)?.techs ?? [];
  const build = board.build?.[`${tile.q},${tile.r}`] ?? [];
  const parts = [];
  if (unit) {
    const role = rules.roles[unit.role];
    const own = unit.owner === me;
    parts.push(<div key="u" className="panel-block">
      <h3 style={{ color: SEAT_CSS[unit.owner] }}>{role?.name ?? unit.role}{unit.branch ? ` ★ ${rules.branches[unit.role]?.find((b) => b.key === unit.branch)?.name}` : ""} {!own && <small>· {seatName(unit.owner)}</small>}</h3>
      <p>❤ {unit.hp}/{unit.max_hp} · ⚔ {unit.atk} · 🛡 {unit.def} · 👣 {unit.mv} · 🎯 {unit.rng} · побед {unit.kills}</p>
      {own && myTurn && <div className="actions">
        {unit.can_capture && <button className="primary" disabled={busy} onClick={() => act({ type: "capture", unit: unit.id })}>Захватить</button>}
        {!unit.moved && !unit.attacked && unit.hp < unit.max_hp && <button disabled={busy} onClick={() => act({ type: "recover", unit: unit.id })}>Восстановить</button>}
        {unit.promote && rules.branches[unit.role]?.map((b) => <button key={b.key} disabled={busy} onClick={() => act({ type: "promote", unit: unit.id, branch: b.key })}>
          ⇧ {b.name}: {Object.entries(b.bonus).map(([k, v]) => `+${v} ${STAT_NAMES[k] ?? k}`).join(", ")}</button>)}
        {unit.moved && unit.attacked && <small className="muted">Отряд уже действовал</small>}
      </div>}
      {own && !unit.promote && !unit.branch && <small className="muted">Повышение после {3} побед: выбор ветки</small>}
    </div>);
  }
  if (city) {
    const own = city.owner === me;
    const free = !board.units.some((u) => u.q === city.q && u.r === city.r);
    parts.push(<div key="c" className="panel-block">
      <h3 style={{ color: city.owner === null ? undefined : SEAT_CSS[city.owner] }}>{city.capital ? "★ " : ""}{city.name}{city.owner === null ? " · нейтральное поселение" : ` · уровень ${city.level}`}</h3>
      {city.owner === null ? <p>Приведите отряд и захватите в начале следующего хода.</p>
        : <p>{own ? `Население ${city.pop}/${city.level + 1} · +${city.income} ★ · отряды ${city.units}/${city.cap}` : seatName(city.owner)}{city.spec && city.spec !== "capital" ? ` · ${rules.specs[city.spec]?.name}` : ""}{city.walls ? " · стены" : ""}</p>}
      {own && myTurn && city.spec === null && <><p className="choice-title">Выберите, чем станет город:</p><div className="option-grid">
        {Object.entries(rules.specs).map(([k, s]) => <button key={k} disabled={busy} onClick={() => act({ type: "spec", city: city.id, spec: k })}><b>{s.name}</b><small>{s.about}</small></button>)}</div></>}
      {own && myTurn && city.reward && <><p className="choice-title">Город вырос! Награда:</p><div className="option-grid">
        {rules.rewards[String(city.reward)]?.map((r) => <button key={r.key} disabled={busy} onClick={() => act({ type: "reward", city: city.id, reward: r.key })}><small>{r.about}</small></button>)}</div></>}
      {own && myTurn && <div className="train-row">
        {(board.train?.[city.id] ?? []).map((role) => { const r = rules.roles[role]; return <button key={role} disabled={busy || !free || stars < r.cost || city.units >= city.cap}
          title={`❤${r.hp} ⚔${r.atk} 🛡${r.def} 👣${r.mv} 🎯${r.rng}`} onClick={() => act({ type: "train", city: city.id, role })}>{r.name}<small>★{r.cost}</small></button>; })}
        {!city.walls && techs.includes("fortify") && <button disabled={busy || stars < rules.walls_cost} onClick={() => act({ type: "walls", city: city.id })}>Стены<small>★{rules.walls_cost}</small></button>}
      </div>}
      {own && myTurn && !free && <small className="muted">Чтобы нанять отряд, освободите клетку города.</small>}
    </div>);
  }
  if (!unit && !city) {
    const names: Record<string, string> = { field: "Поле", forest: "Лес", mountain: "Горы", water: "Вода" };
    const res: Record<string, string> = { crop: "урожай", fruit: "сад", ore: "руда" };
    parts.push(<div key="t" className="panel-block">
      <h3>{names[tile.t] ?? tile.t}{tile.res ? ` · ${res[tile.res]}` : ""}{tile.imp ? ` · ${rules.improvements[tile.imp]?.name}` : ""}</h3>
      {tile.owner !== null && <p style={{ color: SEAT_CSS[tile.owner] }}>Территория: {seatName(tile.owner)}</p>}
    </div>);
  }
  if (myTurn && build.length && !city) parts.push(<div key="b" className="train-row">
    {build.map((k) => { const imp = rules.improvements[k]; return <button key={k} disabled={busy || stars < imp.cost} onClick={() => act({ type: "build", q: tile.q, r: tile.r, improvement: k })}>
      {imp.name}<small>★{imp.cost} · +{imp.pop} жит.</small></button>; })}
  </div>);
  return <div className="match-panel">{parts}</div>;
}

function TechTree({ mine, costs, rules, myTurn, busy, research, close }: {
  mine: Board["players"][number]; costs: Record<string, number>; rules: Rules; myTurn: boolean; busy: boolean; research: (t: string) => void; close: () => void;
}) {
  const have = new Set(mine.techs ?? []);
  return <div className="modal-backdrop" onClick={close}>
    <div className="modal tech-modal" onClick={(e) => e.stopPropagation()}>
      <div className="modal-head"><h2>Технологии · ★ {mine.stars}</h2><button onClick={close} aria-label="Закрыть">✕</button></div>
      {[1, 2, 3].map((tier) => <div key={tier} className="tech-tier"><small>ЯРУС {tier}</small>
        {Object.entries(rules.techs).filter(([, t]) => t.tier === tier).map(([k, t]) => {
          const locked = t.requires && !have.has(t.requires);
          return <button key={k} className={have.has(k) ? "done" : ""} disabled={busy || have.has(k) || !!locked || !myTurn || (mine.stars ?? 0) < costs[k]}
            onClick={() => research(k)}>
            <b>{t.name}</b><span>{t.about}</span>
            <small>{have.has(k) ? "✔ Изучено" : locked ? `Нужно: ${rules.techs[t.requires!].name}` : `★ ${costs[k]}`}</small>
          </button>;
        })}</div>)}
    </div>
  </div>;
}
