import { useEffect, useState } from "react";
import { MapView } from "./Map";
import { request, command, type State, type WorldTile, type ExpeditionRules, type RoutePreview, type TargetPreview, type PvpReport } from "./store";
const biomeNames:Record<string,string>={plain:"Равнина",forest:"Лес",hills:"Холмы",desert:"Пустыня",beach:"Побережье",mountain:"Горы",river:"Река",lake:"Озеро",sea:"Море",unknown:"Неизвестная территория"};
const resources:Record<string,string>={food:"провизии",metal:"металла",oil:"нефти",fuel:"топлива",electronics:"электроники"};
const objectTitle=(o:NonNullable<WorldTile["object"]>)=>o.kind==="pile"?`Ресурсы: ${o.amount} ${resources[o.resource!]}`:o.kind==="chest"?"Сундук":o.kind==="ruin"?"Руины":o.kind==="camp"?`Лагерь наёмников · ${o.name} ${o.count}`:`Шахта · ${o.rate} ${resources[o.resource!]}/мин`;
const objectText=(o:NonNullable<WorldTile["object"]>)=>o.kind==="ruin"?"Что внутри — неизвестно: тайник, архив, артефакт, уцелевшие бойцы или старые карты. Достанется первому.":o.kind==="camp"?(o.available?`Приведите соединение и наймите отряд: ${Object.entries(o.cost??{}).map(([k,v])=>`${v} ${resources[k]}`).join(", ")}. Один отряд в игровую неделю.`:"На этой неделе отряд уже наняли. Новые наёмники придут через игровую неделю."):o.kind==="pile"?"Заберите ресурсы, приведя сюда соединение. Достанется первому.":o.kind==="chest"?`На выбор: ${"250 металла + 60 электроники"} или ${120} опыта командиру.`:o.owner==="self"?"Ваша шахта приносит доход каждую минуту.":o.owner==="other"?"Шахта другого командира. Её можно отбить атакой.":"Приведите соединение, чтобы поднять флаг и получать доход каждую минуту.";
const mmss=(n:number)=>n>=3600?`${Math.floor(n/3600)} ч ${Math.floor(n%3600/60)} мин`:n>=60?`${Math.floor(n/60)} мин`:`${n} сек`;
const targetNames:Record<string,string>={base:"базу",territory:"территорию",mine:"шахту"};
const hours=(n:number)=>n>=3600?`${Math.ceil(n/3600)} ч`:mmss(Math.max(0,n));
const lootLine=(l:Record<string,number>)=>Object.entries(l).map(([k,v])=>`${v} ${resources[k]}`).join(", ");
export const reportLine=(r:PvpReport)=>r.role==="attacker"
  ?`${r.outcome==="victory"?"Победа":"Поражение"}: атака на ${targetNames[r.target]} командира ${r.enemy}${Object.keys(r.loot).length?` · добыча ${lootLine(r.loot)}`:""}`
  :`${r.enemy} атаковал вашу ${targetNames[r.target]} · ${r.outcome==="victory"?"оборона выстояла":Object.keys(r.loot).length?`потеряно ${lootLine(r.loot)}`:"владение потеряно"}`;
const distance=(a:number[],b:number[])=>Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]),Math.abs(a[0]+a[1]-b[0]-b[1]));
export function World({state,clock,rules,goArmy}:{state:State;clock:number;rules:ExpeditionRules;goArmy:()=>void}) {
 const home=state.base?[state.base.q,state.base.r]:rules.staging;
 const [center,setCenter]=useState(home);
 const [focusVersion,setFocusVersion]=useState(0);
 const [selected,setSelected]=useState<number[]|null>(null);
 const [tiles,setTiles]=useState<WorldTile[]>([]);
 const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 const [route,setRoute]=useState<RoutePreview|null>(null);const [routeError,setRouteError]=useState("");
 const [target,setTarget]=useState<TargetPreview|null>(null);
 const [armyId,setArmyId]=useState<string|null>(null);
 const armies=state.armies??[];
 const army=armies.find(a=>a.id===armyId)??armies.find(a=>a.commander)??armies[0];
 const order=army?.orders.find(o=>o.status==="moving");
 const armyName=(a:typeof army)=>a?`${a.commander?"★ ":""}${a.number}-е соединение${a.commander?" · командир":""}`:"";
 useEffect(()=>{
   let alive=true;let pending=false;
   const refresh=async()=>{if(pending)return;pending=true;try{const d=await request(`/world/tiles?q=${center[0]}&r=${center[1]}&radius=6`);if(alive){setTiles(d.tiles);setError("");}}catch(e){if(alive)setError((e as Error).message);}finally{pending=false;}};
   refresh();const id=setInterval(refresh,5000);return()=>{alive=false;clearInterval(id);};
 },[center[0],center[1],state.revision]);
 const tile=tiles.find(t=>selected&&t.q===selected[0]&&t.r===selected[1]);
 const armyKey=army?`${army.id}:${army.q}:${army.r}:${army.status}:${army.movement}`:"";
 useEffect(()=>{
   setRoute(null);setRouteError("");
   if(!army||order||!selected||(selected[0]===army.q&&selected[1]===army.r))return;
   let alive=true;
   request(`/army/route?q=${selected[0]}&r=${selected[1]}&army_id=${army.id}`).then(d=>{if(alive)setRoute(d);}).catch(e=>{if(alive)setRouteError((e as Error).message);});
   return()=>{alive=false;};
 },[selected?.[0],selected?.[1],armyKey,!!order]);
 const hostile=!!tile&&tile.visibility==="visible"&&(tile.base==="other"||tile.control==="other"||(tile.object?.kind==="mine"&&tile.object.owner==="other"));
 useEffect(()=>{
   setTarget(null);
   if(!hostile||!tile)return;
   let alive=true;
   request(`/world/target?q=${tile.q}&r=${tile.r}`).then(d=>{if(alive)setTarget(d);}).catch(()=>{});
   return()=>{alive=false;};
 },[hostile,tile?.q,tile?.r,state.revision]);
 const pvp=state.pvp;const shield=pvp?Math.max(0,pvp.shield_until-clock):0;
 const nextPoint=army?.movement_next_at?Math.max(0,army.movement_next_at-clock):0;
 const baseReason=!state.first_victory?"Сначала победите учебный патруль":!army?"Сформируйте соединение в разделе «Армия»":army.in_battle?"Соединение в бою":order?"Соединение уже в походе":!tile?"Выберите гекс на карте":tile.visibility==="unknown"?"Гекс скрыт туманом войны":routeError?routeError:!route?"Строим маршрут…":!route.affordable?`Нужно ${route.cost} очков хода, доступно ${army.movement}`:state.resources.fuel<(route?.fuel??rules.fuel)?"Недостаточно топлива":"";
 const connected=!!tile&&(distance(home,[tile.q,tile.r])===1||state.territories.some(t=>t.supplied!==false&&distance([t.q,t.r],[tile.q,tile.r])===1));
 const attackReason=baseReason||(!target?"Разведка…":target.reason||"");
 const captureReason=baseReason|| (tile?.base?"Базу нельзя захватить":tile?.control==="self"?"Уже под вашим контролем":state.territories.length>=(state.control_limit??rules.control_limit)?"Достигнут лимит контроля":"");
 const chestPending=state.pending_chests?.[0];
 const openChest=async(choice:"resources"|"xp")=>{if(!chestPending)return;setBusy(true);setError("");try{await command('/world/chest',{q:chestPending.q,r:chestPending.r,choice});}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const hire=async()=>{if(!army)return;setBusy(true);setError("");try{await command('/world/hire',{army_id:army.id});}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const send=async(action:string)=>{if(!army||!selected)return;setBusy(true);setError("");try{await command('/army/orders',{army_id:army.id,q:selected[0],r:selected[1],action});}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const focus=(q:number,r:number)=>{setCenter([q,r]);setFocusVersion(n=>n+1);setSelected(null);};
 return <div className="world-stage">
   <div className="world-tools"><button onClick={()=>focus(home[0],home[1])}>Моя база</button><button disabled={!army} onClick={()=>army&&focus(army.q,army.r)}>К соединению</button></div>
   {armies.length>0&&<div className="army-switch" role="group" aria-label="Соединения">
     {armies.map(a=><button key={a.id} aria-pressed={a.id===army?.id} aria-label={armyName(a)} onClick={()=>{setArmyId(a.id);focus(a.q,a.r);}}>
       <b>{a.commander?"★":a.number}</b><small>{a.in_battle?"⚔":a.status==="moving"?"→":`${a.movement}`}</small></button>)}
     {armies.length<(state.armies_max??1)&&<button className="add" aria-label="Новое соединение" onClick={goArmy}>+</button>}
   </div>}
   <MapView key={center.join(':')+':'+focusVersion} buildings={[]} world={tiles} center={center} armies={armies.map(a=>({army:a,active:a.id===army?.id,kinds:a.unit_ids.map(id=>state.units.find(u=>u.id===id)?.kind).filter((k):k is string=>!!k)}))} route={route?.path} now={clock} selected={selected} onSelect={(q,r)=>{if(q<0||q>=128||r<0||r>=128)return;const mine=armies.find(a=>a.q===q&&a.r===r&&a.id!==army?.id&&a.status!=="moving");if(mine){setArmyId(mine.id);setSelected(null);return;}setSelected([q,r]);}}/>
   <div className="world-control-count">Под контролем {state.territories.length}/{state.control_limit??rules.control_limit}{shield>0&&<span className="shield-chip" title={pvp?.newbie?"Защита новичка":"Защита после налёта"}> · 🛡 {hours(shield)}</span>}</div>
   {!!pvp?.incoming.length&&<button className="incoming-alert" onClick={()=>focus(pvp.incoming[0].q,pvp.incoming[0].r)}>⚠ {pvp.incoming[0].attacker} идёт на вашу {targetNames[pvp.incoming[0].target]} · {mmss(Math.max(0,pvp.incoming[0].arrive_at-clock))}</button>}
   {state.calendar&&<div className="calendar-chip" title={state.calendar.event.about}><b>Неделя {state.calendar.week} · день {state.calendar.day}</b><small>{state.calendar.event.name}</small></div>}
   {army&&<div className="movement-meter" aria-label={`Очки хода ${army.movement} из ${army.movement_max}`}>
     <b>Ход {army.movement}/{army.movement_max}</b>
     <span className="pips">{Array.from({length:army.movement_max},(_,i)=><i key={i} className={i<army.movement?"on":""}/>)}</span>
     <small>{state.calendar?`Рассвет через ${mmss(Math.max(0,state.calendar.next_day_at-clock))}`:army.movement>=army.movement_max?"Запас полон":`+1 через ${mmss(nextPoint)}`}</small>
   </div>}
   <section className="world-orders" aria-label="Приказы на карте">
     {chestPending&&<article className="world-tile chest-choice"><small>СУНДУК · {chestPending.q} : {chestPending.r}</small><h2>Выберите награду</h2><p>Можно взять только одно.</p>
       <div className="actions"><button disabled={busy} onClick={()=>openChest("resources")}>{Object.entries(chestPending.options.resources).map(([k,v])=>`${v} ${resources[k]}`).join(" + ")}</button><button className="primary" disabled={busy} onClick={()=>openChest("xp")}>{chestPending.options.xp} опыта</button></div></article>}
     {!army&&<button className="primary" onClick={goArmy}>Сформировать соединение</button>}
     {army&&!tile&&<article className="card"><div><h3>{armyName(army)} · {army.q} : {army.r}</h3><p>{order?`Поход в ${order.q} : ${order.r} · ${Math.max(0,order.ready_at-clock)} сек.`:"Готово к приказу"}</p>{order&&<small>Прибытие и захват подтверждает сервер.</small>}{!order&&army.orders[0]&&<small role="status">{army.orders[0].result}</small>}</div></article>}
     {tile&&<article className="world-tile"><button className="world-close" aria-label="Закрыть карточку гекса" onClick={()=>setSelected(null)}>×</button><small>ГЕКС {tile.q} : {tile.r}</small><h2>{tile.home?"Ваша база":tile.base==="other"?"База другого командира":tile.base==="staging"?"Общий пункт сбора":biomeNames[tile.biome]}</h2><p>{tile.visibility==="unknown"?"Сведения об участке скрыты туманом войны.":tile.visibility==="explored"?"Ранее исследовано. Актуальные владения скрыты.":tile.control==="self"?(tile.supplied===false?"⛓ Отрезано от базы: доход не идёт, оборона ослаблена. Восстановите цепочку своих гексов до базы.":"Под вашим контролем"):tile.control==="other"?"Под контролем другого игрока":"Нейтральная территория"}</p>
       {tile.visibility==="visible"&&!tile.base&&tile.control!=="self"&&!connected&&<p className="action-reason">Этот гекс не примыкает к вашим снабжаемым землям: после захвата он будет отрезан и не даст дохода, пока цепочка не дотянется.</p>}
       {tile.visibility==="visible"&&!tile.base&&<p>Добыча при контроле: {Object.entries(rules.territory_yield[tile.biome]||{}).map(([k,v])=>`${v} ${resources[k]} / мин`).join(', ')}.</p>}
       {tile.node&&<p className="object-line node-line"><b>★ {tile.node.name}</b><br/>{tile.node.about}. {tile.control==="self"?"":tile.garrison?`Охраняет «${tile.garrison_strength?.name??"Укрепрайон"}».`:"Владение другого командира."}</p>}
       {tile.object&&<p className="object-line"><b>{objectTitle(tile.object)}</b><br/>{objectText(tile.object)}</p>}
       {tile.object?.kind==="camp"&&army&&!order&&army.q===tile.q&&army.r===tile.r&&<div className="actions"><button className="primary" disabled={busy||!tile.object.available} onClick={hire}>Нанять {tile.object.name} · {tile.object.count}</button></div>}
       <p>{tile.garrison?`${tile.garrison_strength?.name??"Гарнизон"} NPC · ${tile.garrison_strength?.hp??55} HP · ${tile.garrison_strength?.xp??50} опыта за победу. Захват только после победы.`:""}</p><p>{order?`Поход · ${Math.max(0,order.ready_at-clock)} сек.`:route?`Маршрут: ${route.path.length} гекс. · ${route.cost} очк. хода · ${mmss(route.seconds)} · ${route.fuel} топлива`:"Равнина и берег 1 · лес и пустыня 2 · холмы и брод через реку 3 · горы непроходимы · по воде только флотом"}</p>
       {hostile&&<div className="target-intel">
         <p><b>Командир {target?.defender??"…"}</b>{target&&target.shield_until>clock?` · 🛡 защита ещё ${hours(target.shield_until-clock)}`:""}</p>
         {target&&<p>Оборона: {target.forces.map(f=>`${f.name} ${f.approx?"~":""}${f.count}${f.militia?" (ополчение)":""}`).join(" · ")}</p>}
         {target&&<p>{target.kind==="base"?"Базу нельзя захватить: победа даёт часть ресурсов сверх защищённого запаса, после налёта база получает защиту на 8 ч.":target.kind==="mine"?"Победа переводит шахту под ваш флаг.":"Победа переводит территорию под ваш контроль."} Атак на этого командира сегодня: осталось {target.attacks_left}.</p>}
         {target?.loses_shield&&<p className="action-reason">Нападение снимет вашу защиту новичка.</p>}
       </div>}
       {hostile?<div className="actions"><button className="primary danger" disabled={busy||!!attackReason} onClick={()=>send('attack')}>Атаковать {target?targetNames[target.kind]:""}</button></div>:
       <div className="actions"><button disabled={busy||!!baseReason||!!tile?.garrison} onClick={()=>send('move')}>{tile.object?.kind==="pile"?"Забрать ресурсы":tile.object?.kind==="chest"?"Открыть сундук":tile.object?.kind==="ruin"?"Исследовать руины":tile.object?.kind==="camp"?"Идти в лагерь":tile.object?.kind==="mine"&&tile.object.owner!=="self"?"Поднять флаг":"Переместить армию"}</button><button className="primary" disabled={busy||!!captureReason} onClick={()=>send('capture')}>{tile.garrison?"Атаковать гарнизон":"Захватить гекс"}</button></div>}
       {(hostile?attackReason&&attackReason!=="Разведка…":baseReason||captureReason)&&<p className="action-reason">{hostile?attackReason:baseReason||captureReason}</p>}
     </article>}
     {!tile&&army&&<p>Выберите соединение вверху или на карте, затем любой разведанный гекс: маршрут и цена в очках хода появятся на карте. На каждом рассвете, раз в 4 часа, соединения получают полный запас хода. Доход идёт только с земель, связанных с базой. Гарнизоны NPC отмечены флагом, узлы — ★.</p>}
     {!tile&&!!pvp?.reports.length&&<div className="pvp-reports"><small>ДОНЕСЕНИЯ</small>{pvp.reports.slice(0,3).map(r=><p key={r.id} className={r.outcome} onClick={()=>focus(r.q,r.r)}>{reportLine(r)}</p>)}</div>}
     {!tile&&state.battles.some(b=>b.state.loot)&&<button className="loot-shortcut" onClick={goArmy}>Трофеи → Армия → Командир</button>}
     {error&&<p className="action-reason" role="alert">{error}</p>}

   </section>
 </div>;
}
