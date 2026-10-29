import { command, type State } from "./store";

const RES: Record<string, string> = { metal: "металл", electronics: "электроника", fuel: "топливо", oil: "нефть", food: "провизия" };
const mins = (s: number) => s >= 3600 ? `${Math.round(s / 3600)} ч` : `${Math.round(s / 60)} мин`;

/** Polytopia-style doctrine tree: three branches, one of two picks per tier. */
export function Doctrines({ state, clock, busy, run }: { state: State; clock: number; busy: boolean; run: (f: () => Promise<unknown>) => void }) {
  const tree = state.doctrines;
  if (!tree) return null;
  const researching = tree.doctrines.find((d) => d.state === "research");
  const done = new Set(tree.doctrines.filter((d) => d.state === "done").map((d) => d.key));
  const taken = new Set(tree.doctrines.filter((d) => d.state !== "available").map((d) => d.key));
  return <section className="doctrines" aria-label="Доктрины">
    <div className="section-label">ДОКТРИНЫ</div>
    <p className="commander-note">Один выбор из двух на ярус{researching && <> · ⏳ <b>{researching.name}</b> {mins(Math.max(0, (researching.ready_at ?? 0) - clock))}</>}</p>
    {Object.entries(tree.branches).map(([branch, title]) => <div className="doctrine-branch" key={branch}>
      <h3>{title}</h3>
      {[1, 2, 3].map((tier) => {
        const pair = tree.doctrines.filter((d) => d.branch === branch && d.tier === tier);
        const chosen = pair.find((d) => taken.has(d.key));
        const unlocked = tier === 1 || tree.doctrines.some((d) => d.branch === branch && d.tier === tier - 1 && done.has(d.key));
        return <div className="doctrine-tier" key={tier}>
          <small>ЯРУС {tier}</small>
          <div className="doctrine-pair">{pair.map((d) => {
            const afford = Object.entries(d.cost).every(([k, v]) => (state.resources[k] ?? 0) >= v);
            const reason = chosen && chosen.key !== d.key ? "Закрыто выбором" : !unlocked ? "Нужен предыдущий ярус" :
              researching && researching.key !== d.key ? "Идёт другое исследование" : !afford ? "Не хватает ресурсов" : "";
            return <button key={d.key} className={`doctrine ${d.state}`} disabled={busy || d.state !== "available" || !!reason}
              onClick={() => run(() => command("/doctrines/research", { key: d.key }))}>
              <b>{d.name}</b><span>{d.about}</span>
              <small>{d.state === "done" ? "✔ Изучено" : d.state === "research" ? `⏳ ${mins(Math.max(0, (d.ready_at ?? 0) - clock))}`
                : reason || `${Object.entries(d.cost).map(([k, v]) => `${v} ${RES[k] ?? k}`).join(", ")} · ${mins(d.seconds)}`}</small>
            </button>;
          })}</div>
        </div>;
      })}
    </div>)}
  </section>;
}
