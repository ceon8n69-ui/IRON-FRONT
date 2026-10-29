import { useEffect, useState } from "react";
import { request, type Calendar, type AllianceView } from "./store";
import { Alliance } from "./Alliance";

type Row = { rank: number; name: string; vp: number; hero: string; me?: boolean; title?: string };
type Board = {
  calendar: Calendar | null;
  top: Row[];
  me: { rank: number; vp: number };
  rules: Record<string, number>;
  last: { season: number; top: Row[] } | null;
  medals: { season: number; rank: number; title: string; vp: number }[];
  alliances: { rank: number; name: string; tag: string; vp: number; members: number }[];
};
const left = (s: number) => {
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
  return d ? `${d} д ${h} ч` : h ? `${h} ч ${m} мин` : `${m} мин`;
};
const medal = (rank: number) => rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : `${rank}`;

/** Season standings: time left, the week's event, victory points and the leaderboard. */
export function Season({ clock, revision, heroes, alliance, busy, run }: { clock: number; revision: number; heroes: Record<string, { name: string }>;
  alliance?: AllianceView | null; busy: boolean; run: (f: () => Promise<unknown>) => void }) {
  const [board, setBoard] = useState<Board | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    request("/season").then((d) => { if (alive) setBoard(d); }).catch((e) => { if (alive) setError((e as Error).message); });
    return () => { alive = false; };
  }, [revision]);
  if (!board) return <section className="content"><p>{error || "Загружаем сезон…"}</p></section>;
  const cal = board.calendar;
  return <section className="content season">
    {cal && <article className="season-hero">
      <small>СЕЗОН {cal.season}</small>
      <h2>До конца сезона {left(Math.max(0, cal.ends_at - clock))}</h2>
      <p>Неделя {cal.week}, день {cal.day} · <b>{cal.event.name}</b>: {cal.event.about}</p>
      <div className="season-me"><span>Ваше место</span><b>{medal(board.me.rank)}</b><span>Очки победы</span><b>{board.me.vp}</b></div>
    </article>}
    <Alliance alliance={alliance} busy={busy} run={run} />
    <details className="season-details"><summary>Как набирать очки</summary>
    <ul className="season-rules">
      <li><b>Столица</b> в центре карты: {board.rules.capital_vp_per_hour} очков в час, пока она связана с вашей базой цепочкой своих гексов. Охраняет её «Гвардия Столицы».</li>
      <li><b>Узлы</b> (нефть, электроника, радар): по {board.rules.node_vp_per_hour} очков в час, тоже только со снабжением.</li>
      <li>Победы: гарнизон +{board.rules.garrison}, укрепрайон +{board.rules.fortress}, взятие Столицы +{board.rules.capital}, нападение на игрока +{board.rules.pvp_attack}, отбитая атака +{board.rules.pvp_defence}.</li>
      <li>Через 2 недели — итоги, звания и новая карта. Командир и медали остаются.</li>
    </ul></details>
    <div className="section-label">ТАБЛИЦА СЕЗОНА</div>
    <ol className="season-board">
      {board.top.map((r) => <li key={r.rank} className={r.me ? "me" : ""}>
        <span className="pos">{medal(r.rank)}</span><span className="who">{r.name}<small>{heroes[r.hero]?.name ?? r.hero}</small></span><b>{r.vp}</b>
      </li>)}
      {!board.top.length && <li>Пока никто не набрал очков.</li>}
    </ol>
    {!!board.alliances.length && <>
      <div className="section-label">АЛЬЯНСЫ</div>
      <ol className="season-board">{board.alliances.map((a) => <li key={a.tag} className={alliance?.tag === a.tag ? "me" : ""}>
        <span className="pos">{medal(a.rank)}</span><span className="who">[{a.tag}] {a.name}<small>{a.members} команд.</small></span><b>{a.vp}</b></li>)}</ol>
    </>}
    {board.last && <>
      <div className="section-label">ПОБЕДИТЕЛИ СЕЗОНА {board.last.season}</div>
      <ol className="season-board">{board.last.top.map((r) => <li key={r.rank}><span className="pos">{medal(r.rank)}</span><span className="who">{r.name}<small>{r.title}</small></span><b>{r.vp}</b></li>)}</ol>
    </>}
    {!!board.medals.length && <>
      <div className="section-label">ВАШИ МЕДАЛИ</div>
      <div className="medals">{board.medals.map((m) => <span key={m.season}>🎖 Сезон {m.season}: {m.title} · {m.rank} место · {m.vp} очков</span>)}</div>
    </>}
  </section>;
}
