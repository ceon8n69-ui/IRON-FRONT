import { useState } from "react";
import { command, type State, type Army } from "./store";

type UnitDef = { name: string; art?: string; naval?: boolean };
type Props = {
  state: State;
  units: Record<string, UnitDef>;
  stacks: number;
  busy: boolean;
  run: (f: () => Promise<unknown>) => void;
  toMap: () => void;
};

export const armyName = (a: Army) => `${a.commander ? "★ " : ""}${a.number}-е соединение`;
const ICON: Record<string, string> = { metal: "⬡", oil: "◈", fuel: "◉", electronics: "⌘", food: "✦" };
const price = (cost: Record<string, number>) => Object.entries(cost).map(([k, v]) => `${ICON[k] ?? k}${v}`).join(" ");
const mmss = (s: number) => s >= 60 ? `${Math.floor(s / 60)} мин${s % 60 ? ` ${s % 60} с` : ""}` : `${s} с`;
const CHEVRONS = ["", "▲", "▲▲", "★"];

/** Heroes-style army management: several armies, all composed on the base. */
export function Armies({ state, units, stacks, busy, run, toMap }: Props) {
  const armies = state.armies ?? [];
  const max = state.armies_max ?? 1;
  const atBase = (a: Army) => !!state.base && a.status === "idle" && !a.in_battle && a.q === state.base.q && a.r === state.base.r;
  const home = armies.filter(atBase);
  const [targetId, setTargetId] = useState<string | null>(null);
  const target = home.find((a) => a.id === targetId) ?? home[0];
  const owner = (unitId: string) => armies.find((a) => a.unit_ids.includes(unitId));
  const name = (kind: string) => units[kind]?.name ?? kind;
  const status = (a: Army) => a.in_battle ? "В бою" : a.status === "moving" ? "В походе" : atBase(a) ? "На базе" : "Готово к приказу";
  const upkeep = state.upkeep ?? {};
  const hungry = Object.entries(upkeep).some(([k, v]) => v > 0 && (state.resources[k] ?? 0) < v);
  return <>
    {(upkeep.food > 0 || upkeep.fuel > 0) && <p className={`upkeep-line${hungry ? " hungry" : ""}`}>
      Содержание: {upkeep.food ? `✦${upkeep.food}` : ""} {upkeep.fuel ? `◉${upkeep.fuel}` : ""} в час{hungry ? " · ⚠ запасов меньше чем на час" : ""}</p>}
    <div className="section-label">СОЕДИНЕНИЯ · {armies.length}/{max}</div>
    {!armies.length && state.first_victory && <p>Сформируйте соединение из резерва ↓</p>}
    {armies.map((a) => <article className={`card army-card${target?.id === a.id ? " target" : ""}`} key={a.id}>
      <div>
        <h3>{armyName(a)}{a.commander && <small className="lead"> · командир</small>}</h3>
        <p>{status(a)} · {a.q} : {a.r} · ход {a.movement}/{a.movement_max}</p>
        <p className="army-stacks">{a.unit_ids.map((id) => state.units.find((u) => u.id === id)).filter(Boolean)
          .map((u) => `${name(u!.kind)} ${u!.count}`).join(" · ")}</p>
        {atBase(a) && <div className="actions">
          {home.length > 1 && target?.id !== a.id && <button disabled={busy} onClick={() => setTargetId(a.id)}>Пополнять это</button>}
          {!a.commander && <button disabled={busy || !armies.filter((x) => x.commander).every(atBase)} onClick={() => run(() => command("/army/lead", { army_id: a.id }))}>Командир сюда</button>}
          <button disabled={busy || (a.commander && armies.length > 1)} onClick={() => run(() => command("/army/disband", { army_id: a.id }))}>Распустить</button>
        </div>}
      </div>
      <button className="primary" onClick={toMap}>На карту</button>
    </article>)}
    {armies.length > 0 && !home.length && <p className="action-reason">Состав меняется только на базе</p>}
    <div className="section-label">ОТРЯДЫ</div>
    {state.units.map((u) => {
      const a = owner(u.id);
      const here = u.status === "reserve" || (u.status === "army" && !!a && atBase(a));
      const rank = u.rank ?? 0;
      const refilling = state.jobs.some((j) => ((j as { kind?: string }).kind ?? "").startsWith(`refill:${u.id}:`));
      // Merge into the fullest other stack of the same kind that still has room.
      const into = state.first_victory && here ? state.units
        .filter((x) => x.id !== u.id && x.kind === u.kind && x.count < (x.cap ?? x.count) &&
          (x.status === "reserve" || (x.status === "army" && atBase(owner(x.id)!))))
        .sort((x, y) => y.count - x.count)[0] : undefined;
      return <article className="card" key={u.id}>
        <img className="unit-thumb" src={`/art/units/${u.kind}.png`} alt="" width={64} height={56} />
        <div>
          <h3>{name(u.kind)} · {u.count}{u.cap ? <small>/{u.cap}</small> : null}{rank > 0 && <span className={`rank-chip r${rank}`} title={u.rank_name}>{CHEVRONS[rank]}</span>}</h3>
          <p>{u.rank_name ?? "Новобранцы"} · опыт {u.xp ?? 0}{u.next_xp ? `/${u.next_xp}` : ""}{rank >= 3 ? " · способность ×2" : rank ? ` · урон +${rank * 5}%` : ""}</p>
          {u.next_xp ? <div className="xp-bar" aria-hidden><i style={{ width: `${Math.min(100, Math.round(100 * (u.xp ?? 0) / u.next_xp))}%` }} /></div> : null}
          <p>Здоровье {u.hp}/100 · {u.status === "battle" ? "В бою" : a ? `В ${a.number}-м соединении` : "В резерве"}{refilling ? " · ⏳ пополнение" : ""}</p>
        </div>
        <div className="actions column">
          {!state.first_victory && <button className="primary" disabled={busy} onClick={() => run(() => command("/battles", { unit_id: u.id }))}>В бой</button>}
          {state.first_victory && u.status === "reserve" && target && <button disabled={busy || target.unit_ids.length >= stacks} onClick={() => run(() => command("/army/assign", { unit_id: u.id, army_id: target.id }))}>В {target.number}-е</button>}
          {state.first_victory && u.status === "reserve" && armies.length < max && <button className={armies.length ? "" : "primary"} disabled={busy} onClick={() => run(async () => { await command("/army/create", { unit_id: u.id }); if (!armies.length) toMap(); })}>Новое соединение</button>}
          {u.status === "army" && a && atBase(a) && a.unit_ids.length > 1 && <button disabled={busy} onClick={() => run(() => command("/army/release", { unit_id: u.id, army_id: a.id }))}>В резерв</button>}
          {state.first_victory && here && u.refill && !refilling && <button disabled={busy || state.jobs.length > 0 || Object.entries(u.refill.cost).some(([k, v]) => (state.resources[k] ?? 0) < v)}
            title={`Пополнение: +${u.refill.missing} бойцов за ${mmss(u.refill.seconds)}. Новобранцы разбавляют опыт стека.`}
            onClick={() => run(() => command("/units/refill", { unit_id: u.id }))}>Пополнить +{u.refill.missing} · {price(u.refill.cost)}</button>}
          {into && <button disabled={busy} title="Перелить бойцов в другой стек того же типа. Опыт усредняется."
            onClick={() => run(() => command("/units/merge", { unit_id: u.id, into_id: into.id }))}>Слить → {name(into.kind)} {into.count}</button>}
        </div>
      </article>;
    })}
    {!state.units.length && <p>Подготовьте первый отряд в казармах.</p>}
  </>;
}
