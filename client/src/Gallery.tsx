import { useEffect, useState } from "react";
import { request } from "./store";
import { Roster } from "./Roster";

type Faction = { name: string; accent: string; units: { key: string; name: string; art: string; role: string; trait?: string }[] };

/** Read-only art review page: every commander's five units. Open with ?gallery. */
export function Gallery() {
  const [cfg, setCfg] = useState<{ factions: Record<string, Faction>; heroes: Record<string, { name: string; role: string }>; traits: Record<string, string> } | null>(null);
  useEffect(() => { request("/config").then(setCfg).catch(() => {}); }, []);
  if (!cfg) return <main className="content"><p>Загрузка…</p></main>;
  return <main className="gallery">
    <h1>Отряды командиров</h1>
    {Object.entries(cfg.factions).map(([hero, f]) => <section key={hero} className="gallery-faction" style={{ borderColor: f.accent }}>
      <small>{cfg.heroes[hero].name} · {cfg.heroes[hero].role}</small>
      <h2 style={{ color: f.accent }}>{f.name}</h2>
      <Roster units={f.units} faction={hero} height={104} scale={1.05} />
      <div className="gallery-names">{f.units.map((u) => <span key={u.key}><b>{u.name}</b>{u.trait && <em>{cfg.traits[u.trait].split(":")[0]}</em>}</span>)}</div>
    </section>)}
  </main>;
}
