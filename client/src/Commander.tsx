import type React from "react";
import { useState } from "react";
import type { State } from "./store";
export type HeroDefinition = { name: string; role: string; bio: string; effect: string };
const rarityNames:Record<string,string>={uncommon:"НЕОБЫЧНЫЙ",rare:"РЕДКИЙ",epic:"ЭПИЧЕСКИЙ"};
const PERK_LABELS:Record<string,[string,boolean]>={attack:["урон",true],defense:["защита",true],ranged:["урон стрелков",true],initiative:["инициатива",false],morale:["боевой дух",true],luck:["удача",true],movement:["очки хода",false],vision:["обзор",false],first_aid:["полевая медицина",true],plunder:["трофеи",true],supply:["производство",true],engineering:["скорость стройки",true]};
export const perkText=(perks:Record<string,number>)=>Object.entries(perks).map(([k,v])=>{const [n,pct]=PERK_LABELS[k]??[k,false];return `${n} +${pct?Math.round(v*100)+"%":v}`;}).join(" · ");
const SLOT_ORDER:[string,string][]=[["weapon","Оружие"],["armor","Броня"],["badge","Знак"],["gear","Модуль"],["optics","Снаряжение"]];
const itemImage=(e:React.SyntheticEvent<HTMLImageElement>)=>{const img=e.currentTarget;if(!img.src.endsWith("field-module-v1.webp"))img.src="/art/equipment/field-module-v1.webp";};
const heroIds = new Set(["raven", "valkyrie", "titan", "phoenix", "ghost", "storm"]);
export function Portrait({id, name, eager = false}: {id: string; name: string; eager?: boolean}) {
  return heroIds.has(id) ? <img className="commander-image" src={`/art/commanders/${id}-v2.webp`} onError={(e) => { const img = e.currentTarget; if (!img.src.endsWith("-v1.webp")) img.src = `/art/commanders/${id}-v1.webp`; }} alt={name} width="640" height="960" loading={eager ? "eager" : "lazy"} decoding="async"/> : <span>Портрет недоступен</span>;
}
export function Commander({state, definition, busy, equip, pick}: {
  state: State; definition: HeroDefinition; busy: boolean; equip: (id: string, equipped: boolean) => void; pick: (key: string) => void;
}) {
  const [filter, setFilter] = useState("all");
  const [details, setDetails] = useState<string | null>(null);
  const hero = state.hero!;
  const cmd = state.commander;
  const items = state.inventory.filter(i => filter === "all" || (filter === "equipped" ? i.equipped : i.definition.rarity===filter));
  const level = cmd?.level ?? 1, floor = cmd?.level_xp ?? 0, next = cmd?.next_xp ?? null;
  const span = next ? next - floor : 1, progress = next ? hero.xp - floor : 1;
  const inBattle = state.battles.some(b=>b.status === "active");
  return <div className="commander-screen">
    <article className="commander-card">
      <div className="commander-art"><Portrait id={hero.kind} name={definition.name} eager/>
        <span className="commander-rank">УРОВЕНЬ {level}</span>
      </div>
      <div className="commander-profile">
        <small className="gold-text">{definition.role}</small><h2>{definition.name}</h2>
        <p>{definition.bio}</p>
        <div className="xp-heading"><b>{hero.xp} XP</b><span>{next ? `${next - hero.xp} XP до ${level + 1} уровня` : "Максимальный уровень"}</span></div>
        <progress max={span} value={progress} aria-label="Опыт до следующего уровня"/>
        <div className="bonus-block"><small>СПЕЦИАЛИЗАЦИЯ</small><b>{definition.effect}</b></div>
        {cmd && Object.keys(cmd.perks).length > 0 && <div className="bonus-block"><small>БОНУСЫ КОМАНДИРА</small><b>{perkText(cmd.perks)}</b></div>}
        <p className="commander-note">Бонусы работают в соединении командира ★</p>
      </div>
    </article>
    {cmd && cmd.pending > 0 && <section className="skill-choice" aria-label="Выбор навыка">
      <small>НОВЫЙ УРОВЕНЬ{cmd.pending > 1 ? ` · ОЧКОВ: ${cmd.pending}` : ""}</small><h2>Выберите навык</h2>
      <div className="skill-offers">{cmd.offers.map(o=><button key={o.key} disabled={busy} onClick={()=>pick(o.key)}>
        <span className="skill-icon">{o.icon}</span><b>{o.name} {"I".repeat(o.rank)}</b><small>{o.about}</small></button>)}</div>
    </section>}
    {cmd && <section className="skill-list" aria-label="Навыки">
      <small>НАВЫКИ · {cmd.skills.length}/{cmd.max_skills}</small>
      {cmd.skills.length ? <div>{cmd.skills.map(sk=><span key={sk.key} className="skill-chip" title={sk.about}>{sk.icon} {sk.name} {"I".repeat(sk.rank)}<small>{sk.about}</small></span>)}</div>
        : <p className="commander-note">Навык — с каждым новым уровнем</p>}
    </section>}
    <section className="slot-row" aria-label="Слоты экипировки">{SLOT_ORDER.map(([slot,name])=>{const it=state.inventory.find(i=>i.equipped&&(i.definition.slot??"gear")===slot);
      return <div key={slot} className={"slot"+(it?" filled rarity-"+it.definition.rarity:"")}>{it?<img src={it.definition.image} onError={itemImage} alt={it.definition.name}/>:<span>+</span>}<small>{name}</small></div>;})}</section>
    <div className="inventory-heading"><div><small>ТАКТИЧЕСКИЙ СЛОТ</small><h2>Снаряжение <span>{state.inventory.length}</span></h2></div>
      <div className="inventory-filters" role="group" aria-label="Фильтр инвентаря">
        <button aria-pressed={filter === "all"} onClick={()=>setFilter("all")}>Все</button>
        <button aria-pressed={filter === "equipped"} onClick={()=>setFilter("equipped")}>Снаряжено</button>
        <button aria-pressed={filter === "rare"} onClick={()=>setFilter("rare")}>Редкие</button><button aria-pressed={filter === "epic"} onClick={()=>setFilter("epic")}>Эпические</button>
      </div>
    </div>
    {!state.inventory.length && <div className="equipment-empty"><img src="/art/equipment/field-module-v1.webp" alt="Полевой модуль — награда за первую победу" width="96" height="96"/><div><b>Первый трофей ждёт вас</b><p>Победите патруль NPC, чтобы получить уникальный полевой модуль.</p></div></div>}
    {!!state.inventory.length && !items.length && <p className="notice">Сейчас ничего не снаряжено. Откройте «Все» и выберите предмет.</p>}
    {items.map(item=><article className={"equipment-card rarity-"+item.definition.rarity+(item.equipped ? " equipped" : "")} key={item.id}>
      <button className="equipment-preview" aria-label={item.definition_id==="field-module"?"Карточка полевого модуля":`Карточка: ${item.definition.name}`} onClick={()=>setDetails(details === item.id ? null : item.id)} aria-expanded={details === item.id}><img src={item.definition.image} onError={itemImage} alt={item.definition.name} width="96" height="96" loading="lazy"/></button>
      <div className="equipment-info"><small className="rarity-uncommon">{rarityNames[item.definition.rarity]} · {item.equipped ? "СНАРЯЖЕНО" : "ИНВЕНТАРЬ"}</small><h3>{item.definition.name}</h3><p>{item.definition.perks ? perkText(item.definition.perks) : `урон +${Math.round(item.definition.damage_bonus*100)}%`} · {item.definition.slot_name ?? "Модуль"}</p></div>
      <button className={item.equipped ? "" : "primary"} disabled={busy || inBattle} onClick={()=>equip(item.id,!item.equipped)}>{item.equipped ? "Снять" : "Снарядить"}</button>
      {details === item.id && <div className="equipment-details"><img src={item.definition.image} onError={itemImage} alt={item.definition.name} width="240" height="240"/><dl><dt>Уникальный ID</dt><dd>{item.id}</dd><dt>Владелец</dt><dd>{state.player.name}</dd><dt>Источник</dt><dd>{item.source==="garrison"?"Победа над гарнизоном на карте":"Первая победа над патрулём NPC"}</dd><dt>Состояние</dt><dd>{item.equipped ? "Бонус активен" : "Хранится в инвентаре"}</dd></dl><p>В каждом слоте один предмет: новый заменит старый. Во время боя смена экипировки недоступна.</p></div>}
    </article>)}

  </div>;
}
