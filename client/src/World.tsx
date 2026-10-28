import { useEffect, useState } from "react";
import { MapView } from "./Map";
import { request, command, type State, type WorldTile, type ExpeditionRules, type RoutePreview } from "./store";
const biomeNames:Record<string,string>={plain:"Равнина",forest:"Лес",hills:"Холмы",desert:"Пустыня",beach:"Побережье",mountain:"Горы",river:"Река",lake:"Озеро",sea:"Море",unknown:"Неизвестная территория"};
const resources:Record<string,string>={food:"провизии",metal:"металла",oil:"нефти",fuel:"топлива",electronics:"электроники"};
const objectTitle=(o:NonNullable<WorldTile["object"]>)=>o.kind==="pile"?`Ресурсы: ${o.amount} ${resources[o.resource!]}`:o.kind==="chest"?"Сундук":`Шахта · ${o.rate} ${resources[o.resource!]}/мин`;
const objectText=(o:NonNullable<WorldTile["object"]>)=>o.kind==="pile"?"Заберите ресурсы, приведя сюда соединение. Достанется первому.":o.kind==="chest"?`На выбор: ${"250 металла + 60 электроники"} или ${120} опыта командиру.`:o.owner==="self"?"Ваша шахта приносит доход каждую минуту.":o.owner==="other"?"Шахта другого командира. PvP пока не включён.":"Приведите соединение, чтобы поднять флаг и получать доход каждую минуту.";
const mmss=(n:number)=>n>=3600?`${Math.floor(n/3600)} ч ${Math.floor(n%3600/60)} мин`:n>=60?`${Math.floor(n/60)} мин`:`${n} сек`;
const distance=(a:number[],b:number[])=>Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]),Math.abs(a[0]+a[1]-b[0]-b[1]));
export function World({state,clock,rules,goArmy}:{state:State;clock:number;rules:ExpeditionRules;goArmy:()=>void}) {
 const home=state.base?[state.base.q,state.base.r]:rules.staging;
 const [center,setCenter]=useState(home);
 const [focusVersion,setFocusVersion]=useState(0);
 const [selected,setSelected]=useState<number[]|null>(null);
 const [tiles,setTiles]=useState<WorldTile[]>([]);
 const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 const [route,setRoute]=useState<RoutePreview|null>(null);const [routeError,setRouteError]=useState("");
 const army=state.armies?.[0];const order=army?.orders.find(o=>o.status==="moving");
 useEffect(()=>{
   let alive=true;let pending=false;
   const refresh=async()=>{if(pending)return;pending=true;try{const d=await request(`/world/tiles?q=${center[0]}&r=${center[1]}&radius=6`);if(alive){setTiles(d.tiles);setError("");}}catch(e){if(alive)setError((e as Error).message);}finally{pending=false;}};
   refresh();const id=setInterval(refresh,5000);return()=>{alive=false;clearInterval(id);};
 },[center[0],center[1],state.revision]);
 const tile=tiles.find(t=>selected&&t.q===selected[0]&&t.r===selected[1]);
 const armyKey=army?`${army.q}:${army.r}:${army.status}:${army.movement}`:"";
 useEffect(()=>{
   setRoute(null);setRouteError("");
   if(!army||order||!selected||(selected[0]===army.q&&selected[1]===army.r))return;
   let alive=true;
   request(`/army/route?q=${selected[0]}&r=${selected[1]}`).then(d=>{if(alive)setRoute(d);}).catch(e=>{if(alive)setRouteError((e as Error).message);});
   return()=>{alive=false;};
 },[selected?.[0],selected?.[1],armyKey,!!order]);
 const nextPoint=army?.movement_next_at?Math.max(0,army.movement_next_at-clock):0;
 const baseReason=!state.first_victory?"Сначала победите учебный патруль":!army?"Сформируйте соединение в разделе «Армия»":order?"Соединение уже в походе":!tile?"Выберите гекс на карте":tile.visibility==="unknown"?"Гекс скрыт туманом войны":routeError?routeError:!route?"Строим маршрут…":!route.affordable?`Нужно ${route.cost} очков хода, доступно ${army.movement}`:tile.base==="other"?"База другого командира: PvP ещё не включён":tile.control==="other"?"Чужая территория: PvP ещё не включён":state.resources.fuel<(route?.fuel??rules.fuel)?"Недостаточно топлива":"";
 const connected=tile&&(distance(home,[tile.q,tile.r])===1||state.territories.some(t=>distance([t.q,t.r],[tile.q,tile.r])===1));
 const captureReason=baseReason|| (tile?.base?"Базу нельзя захватить":tile?.control==="self"?"Уже под вашим контролем":state.territories.length>=rules.control_limit?"Достигнут лимит контроля":!connected?"Нет связи с вашей землёй или базой":"");
 const chestPending=state.pending_chests?.[0];
 const openChest=async(choice:"resources"|"xp")=>{if(!chestPending)return;setBusy(true);setError("");try{await command('/world/chest',{q:chestPending.q,r:chestPending.r,choice});}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const send=async(action:string)=>{if(!army||!selected)return;setBusy(true);setError("");try{await command('/army/orders',{army_id:army.id,q:selected[0],r:selected[1],action});}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const focus=(q:number,r:number)=>{setCenter([q,r]);setFocusVersion(n=>n+1);setSelected(null);};
 return <div className="world-stage">
   <div className="world-tools"><button onClick={()=>focus(home[0],home[1])}>Моя база</button><button disabled={!army} onClick={()=>army&&focus(army.q,army.r)}>К соединению</button></div>
   <MapView key={center.join(':')+':'+focusVersion} buildings={[]} world={tiles} center={center} army={army} route={route?.path} now={clock} selected={selected} onSelect={(q,r)=>{if(q>=0&&q<128&&r>=0&&r<128)setSelected([q,r]);}}/>
   <div className="world-control-count">Под контролем {state.territories.length}/{rules.control_limit}</div>
   {army&&<div className="movement-meter" aria-label={`Очки хода ${army.movement} из ${army.movement_max}`}>
     <b>Ход {army.movement}/{army.movement_max}</b>
     <span className="pips">{Array.from({length:army.movement_max},(_,i)=><i key={i} className={i<army.movement?"on":""}/>)}</span>
     <small>{army.movement>=army.movement_max?"Запас полон":`+1 через ${mmss(nextPoint)}`}</small>
   </div>}
   <section className="world-orders" aria-label="Приказы на карте">
     {chestPending&&<article className="world-tile chest-choice"><small>СУНДУК · {chestPending.q} : {chestPending.r}</small><h2>Выберите награду</h2><p>Можно взять только одно.</p>
       <div className="actions"><button disabled={busy} onClick={()=>openChest("resources")}>{Object.entries(chestPending.options.resources).map(([k,v])=>`${v} ${resources[k]}`).join(" + ")}</button><button className="primary" disabled={busy} onClick={()=>openChest("xp")}>{chestPending.options.xp} опыта</button></div></article>}
     {!army&&<button className="primary" onClick={goArmy}>Сформировать соединение</button>}
     {army&&!tile&&<article className="card"><div><h3>Первое соединение · {army.q} : {army.r}</h3><p>{order?`Поход в ${order.q} : ${order.r} · ${Math.max(0,order.ready_at-clock)} сек.`:"Готово к приказу"}</p>{order&&<small>Прибытие и захват подтверждает сервер.</small>}{!order&&army.orders[0]&&<small role="status">{army.orders[0].result}</small>}</div></article>}
     {tile&&<article className="world-tile"><button className="world-close" aria-label="Закрыть карточку гекса" onClick={()=>setSelected(null)}>×</button><small>ГЕКС {tile.q} : {tile.r}</small><h2>{tile.home?"Ваша база":tile.base==="other"?"База другого командира":tile.base==="staging"?"Общий пункт сбора":biomeNames[tile.biome]}</h2><p>{tile.visibility==="unknown"?"Сведения об участке скрыты туманом войны.":tile.visibility==="explored"?"Ранее исследовано. Актуальные владения скрыты.":tile.control==="self"?"Под вашим контролем":tile.control==="other"?"Под контролем другого игрока":"Нейтральная территория"}</p>
       {tile.visibility==="visible"&&!tile.base&&<p>Добыча при контроле: {Object.entries(rules.territory_yield[tile.biome]||{}).map(([k,v])=>`${v} ${resources[k]} / мин`).join(', ')}.</p>}
       {tile.object&&<p className="object-line"><b>{objectTitle(tile.object)}</b><br/>{objectText(tile.object)}</p>}
       <p>{tile.garrison?`${tile.garrison_strength?.name??"Гарнизон"} NPC · ${tile.garrison_strength?.hp??55} HP · ${tile.garrison_strength?.xp??50} опыта за победу. Захват только после победы.`:""}</p><p>{order?`Поход · ${Math.max(0,order.ready_at-clock)} сек.`:route?`Маршрут: ${route.path.length} гекс. · ${route.cost} очк. хода · ${mmss(route.seconds)} · ${route.fuel} топлива`:"Равнина и берег 1 · лес и пустыня 2 · холмы и брод через реку 3 · горы непроходимы · по воде только флотом"}</p>
       <div className="actions"><button disabled={busy||!!baseReason||!!tile?.garrison} onClick={()=>send('move')}>{tile.object?.kind==="pile"?"Забрать ресурсы":tile.object?.kind==="chest"?"Открыть сундук":tile.object?.kind==="mine"&&tile.object.owner!=="self"?"Поднять флаг":"Переместить армию"}</button><button className="primary" disabled={busy||!!captureReason} onClick={()=>send('capture')}>{tile.garrison?"Атаковать гарнизон":"Захватить гекс"}</button></div>
       {(baseReason||captureReason)&&<p className="action-reason">{baseReason||captureReason}</p>}
     </article>}
     {!tile&&army&&<p>Выберите любой разведанный гекс: маршрут и цена в очках хода появятся на карте. Очки восстанавливаются сами, полный запас за 8 часов. Гарнизоны NPC отмечены флагом.</p>}
     {!tile&&state.battles.some(b=>b.state.loot)&&<button className="loot-shortcut" onClick={goArmy}>Трофеи → Армия → Командир</button>}
     {error&&<p className="action-reason" role="alert">{error}</p>}

   </section>
 </div>;
}
