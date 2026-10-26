import { useState } from "react";
import type { State } from "./store";
export type HeroDefinition = { name: string; role: string; bio: string; effect: string };
const heroIds = new Set(["raven", "valkyrie", "titan", "phoenix", "ghost", "storm"]);
export function Portrait({id, name, eager = false}: {id: string; name: string; eager?: boolean}) {
  return heroIds.has(id) ? <img className="commander-image" src={`/art/commanders/${id}-v1.webp`} alt={name} width="640" height="960" loading={eager ? "eager" : "lazy"} decoding="async"/> : <span>Портрет недоступен</span>;
}
export function Commander({state, definition, busy, equip}: {
  state: State; definition: HeroDefinition; busy: boolean; equip: (id: string, equipped: boolean) => void;
}) {
  const [filter, setFilter] = useState("all");
  const [details, setDetails] = useState<string | null>(null);
  const hero = state.hero!;
  const active = state.inventory.find(i => i.equipped);
  const items = state.inventory.filter(i => filter === "all" || i.equipped);
  const progress = hero.xp % 100;
  return <div className="commander-screen">
    <article className="commander-card">
      <div className="commander-art"><Portrait id={hero.kind} name={definition.name} eager/>
        <span className="commander-rank">УРОВЕНЬ {1+Math.floor(hero.xp/100)}</span>
      </div>
      <div className="commander-profile">
        <small className="gold-text">{definition.role}</small><h2>{definition.name}</h2>
        <p>{definition.bio}</p>
        <div className="xp-heading"><b>{hero.xp} XP</b><span>{100-progress} XP до следующего уровня</span></div>
        <progress max={100} value={progress} aria-label="Опыт до следующего уровня"/>
        <div className="bonus-block"><small>СПЕЦИАЛИЗАЦИЯ</small><b>{definition.effect}</b></div>
        <div className="bonus-block"><small>ЭКИПИРОВКА</small><b>{active ? "Полевой модуль · +3% к урону" : "Тактический слот свободен"}</b></div>
        <p className="commander-note">Опыт первой операции: +100 XP. Уровень показывает прогресс; бонус специализации фиксирован.</p>
      </div>
    </article>
    <div className="inventory-heading"><div><small>ТАКТИЧЕСКИЙ СЛОТ</small><h2>Снаряжение <span>{state.inventory.length}</span></h2></div>
      <div className="inventory-filters" role="group" aria-label="Фильтр инвентаря">
        <button aria-pressed={filter === "all"} onClick={()=>setFilter("all")}>Все</button>
        <button aria-pressed={filter === "equipped"} onClick={()=>setFilter("equipped")}>Снаряжено</button>
      </div>
    </div>
    {!state.inventory.length && <div className="equipment-empty"><img src="/art/equipment/field-module-v1.webp" alt="Полевой модуль — награда за первую победу" width="96" height="96"/><div><b>Первый трофей ждёт вас</b><p>Победите патруль NPC, чтобы получить уникальный полевой модуль.</p></div></div>}
    {!!state.inventory.length && !items.length && <p className="notice">Сейчас ничего не снаряжено. Откройте «Все» и выберите предмет.</p>}
    {items.map(item=><article className={"equipment-card"+(item.equipped ? " equipped" : "")} key={item.id}>
      <button className="equipment-preview" aria-label="Карточка полевого модуля" onClick={()=>setDetails(details === item.id ? null : item.id)} aria-expanded={details === item.id}><img src="/art/equipment/field-module-v1.webp" alt="Полевой модуль" width="96" height="96" loading="lazy"/></button>
      <div className="equipment-info"><small className="rarity-uncommon">НЕОБЫЧНЫЙ · {item.equipped ? "СНАРЯЖЕНО" : "ИНВЕНТАРЬ"}</small><h3>Полевой модуль</h3><p>+3% к урону · Тактический слот</p><small>#{item.id.slice(0,8)} · Победа над NPC</small></div>
      <button className={item.equipped ? "" : "primary"} disabled={busy || state.battles.some(b=>b.status === "active")} onClick={()=>equip(item.id,!item.equipped)}>{item.equipped ? "Снять" : "Снарядить"}</button>
      {details === item.id && <div className="equipment-details"><img src="/art/equipment/field-module-v1.webp" alt="Полевой модуль крупным планом" width="240" height="240"/><dl><dt>Уникальный ID</dt><dd>{item.id}</dd><dt>Владелец</dt><dd>{state.player.name}</dd><dt>Источник</dt><dd>Первая победа над патрулём NPC</dd><dt>Состояние</dt><dd>{item.equipped ? "Бонус активен" : "Хранится в инвентаре"}</dd></dl><p>Можно снарядить один модуль. Во время боя смена экипировки недоступна.</p></div>}
    </article>)}
    <p className="commander-note">Дополнительные слоты, улучшения и комплекты появятся на следующем этапе RPG.</p>
  </div>;
}
