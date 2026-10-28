import { useState } from "react";
import { command, type AllianceView } from "./store";

/** Create, join, share and manage an alliance of up to five commanders. */
export function Alliance({ alliance, busy, run }: { alliance: AllianceView | null | undefined; busy: boolean; run: (f: () => Promise<unknown>) => void }) {
  const [name, setName] = useState("");
  const [tag, setTag] = useState("");
  const [code, setCode] = useState("");
  const [copied, setCopied] = useState(false);
  if (!alliance) return <article className="alliance-card">
    <h3>Альянс</h3>
    <p>До 5 командиров. Союзники не нападают друг на друга, проходят через земли друг друга и соревнуются в общем рейтинге альянсов.</p>
    <form onSubmit={(e) => { e.preventDefault(); run(() => command("/alliance/create", { name, tag })); }}>
      <input aria-label="Название альянса" placeholder="Название" value={name} maxLength={24} onChange={(e) => setName(e.target.value)} />
      <input aria-label="Тег альянса" placeholder="Тег" value={tag} maxLength={5} onChange={(e) => setTag(e.target.value.toUpperCase())} style={{ maxWidth: 90 }} />
      <button className="primary" disabled={busy || name.trim().length < 3 || tag.trim().length < 2}>Создать</button>
    </form>
    <form onSubmit={(e) => { e.preventDefault(); run(() => command("/alliance/join", { code })); }}>
      <input aria-label="Код приглашения" placeholder="Код приглашения" value={code} maxLength={12} onChange={(e) => setCode(e.target.value.toUpperCase())} />
      <button disabled={busy || code.trim().length < 4}>Вступить</button>
    </form>
  </article>;
  const share = async () => {
    const text = `Вступай в мой альянс «${alliance.name}» [${alliance.tag}] в IRON FRONT. Код: ${alliance.code}`;
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* clipboard may be blocked */ }
  };
  return <article className="alliance-card">
    <h3>[{alliance.tag}] {alliance.name}</h3>
    <p>Очки альянса: <b>{alliance.vp}</b> · {alliance.members.length}/{alliance.max} командиров</p>
    <div className="row"><span>Код приглашения:</span><span className="code">{alliance.code}</span><button onClick={share}>{copied ? "Скопировано" : "Скопировать приглашение"}</button></div>
    <ul>{alliance.members.map((m) => <li key={m.id}>
      <span>{m.owner ? "★ " : ""}{m.name}{m.me ? " (вы)" : ""}</span><span>{m.vp} очк.</span>
      {alliance.owner && !m.me && <button disabled={busy} onClick={() => run(() => command("/alliance/kick", { player_id: m.id }))}>Исключить</button>}
    </li>)}</ul>
    <button disabled={busy} onClick={() => run(() => command("/alliance/leave", {}))}>Покинуть альянс</button>
  </article>;
}
