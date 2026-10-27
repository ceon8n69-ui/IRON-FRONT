import { useEffect, useState } from "react";
import { MapView } from "./Map";
import { request, command, type State, type WorldTile, type ExpeditionRules } from "./store";
const biomeNames:Record<string,string>={plain:"Равнина",forest:"Лес",hills:"Холмы",desert:"Пустыня",unknown:"Неизвестная территория"};
const resources:Record<string,string>={food:"провизии",metal:"металла",oil:"нефти"};
const distance=(a:number[],b:number[])=>Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1]),Math.abs(a[0]+a[1]-b[0]-b[1]));
export function World({state,clock,rules,goArmy}:{state:State;clock:number;rules:ExpeditionRules;goArmy:()=>void}) {
 const [center,setCenter]=useState(rules.home);
 const [focusVersion,setFocusVersion]=useState(0);
 const [selected,setSelected]=useState<number[]|null>(null);
 const [tiles,setTiles]=useState<WorldTile[]>([]);
 const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 const army=state.armies?.[0];const order=army?.orders.find(o=>o.status==="moving");
 useEffect(()=>{
   let alive=true;let pending=false;
   const refresh=async()=>{if(pending)return;pending=true;try{const d=await request(`/world/tiles?q=${center[0]}&r=${center[1]}&radius=6`);if(alive){setTiles(d.tiles);setError("");}}catch(e){if(alive)setError((e as Error).message);}finally{pending=false;}};
   refresh();const id=setInterval(refresh,5000);return()=>{alive=false;clearInterval(id);};
 },[center[0],center[1],state.revision]);
 const tile=tiles.find(t=>selected&&t.q===selected[0]&&t.r===selected[1]);
 const baseReason=!state.first_victory?"Сначала победите учебный патруль":!army?"Сформируйте соединение в разделе «Армия»":order?"Соединение уже в походе":!tile?"Выберите гекс на карте":tile.visibility!=="visible"?"Гекс вне текущего обзора":distance([army.q,army.r],[tile.q,tile.r])!==1?"Можно идти только на соседний гекс":tile.control==="other"?"Чужая территория: PvP ещё не включён":state.resources.fuel<rules.fuel?"Недостаточно топлива":"";
 const connected=tile&&(distance(rules.home,[tile.q,tile.r])===1||state.territories.some(t=>distance([t.q,t.r],[tile.q,tile.r])===1));
 const captureReason=baseReason|| (tile?.home?"Стартовый пункт нельзя захватить":tile?.control==="self"?"Уже под вашим контролем":state.territories.length>=rules.control_limit?"Достигнут лимит контроля":!connected?"Нет связи с вашей землёй или стартовым пунктом":"");
 const send=async(action:string)=>{if(!army||!selected)return;setBusy(true);setError("");try{await command('/army/orders',{army_id:army.id,q:selected[0],r:selected[1],action});}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const focus=(q:number,r:number)=>{setCenter([q,r]);setFocusVersion(n=>n+1);setSelected(null);};
 return <div className="world-stage">
   <div className="world-tools"><button onClick={()=>focus(...rules.home as [number,number])}>Стартовый пункт</button><button disabled={!army} onClick={()=>army&&focus(army.q,army.r)}>К соединению</button></div>
   <MapView key={center.join(':')+':'+focusVersion} buildings={[]} world={tiles} center={center} army={army} now={clock} selected={selected} onSelect={(q,r)=>{if(q>=0&&q<128&&r>=0&&r<128)setSelected([q,r]);}}/>
   <div className="world-control-count">Под контролем {state.territories.length}/{rules.control_limit}</div>
   <section className="world-orders" aria-label="Приказы на карте">
     {!army&&<button className="primary" onClick={goArmy}>Сформировать соединение</button>}
     {army&&!tile&&<article className="card"><div><h3>Первое соединение · {army.q} : {army.r}</h3><p>{order?`Поход в ${order.q} : ${order.r} · ${Math.max(0,order.ready_at-clock)} сек.`:"Готово к приказу"}</p>{order&&<small>Прибытие и захват подтверждает сервер.</small>}{!order&&army.orders[0]&&<small role="status">{army.orders[0].result}</small>}</div></article>}
     {tile&&<article className="world-tile"><button className="world-close" aria-label="Закрыть карточку гекса" onClick={()=>setSelected(null)}>×</button><small>ГЕКС {tile.q} : {tile.r}</small><h2>{tile.home?"Стартовый пункт":biomeNames[tile.biome]}</h2><p>{tile.visibility==="unknown"?"Сведения об участке скрыты туманом войны.":tile.visibility==="explored"?"Ранее исследовано. Актуальные владения скрыты.":tile.control==="self"?"Под вашим контролем":tile.control==="other"?"Под контролем другого игрока":"Нейтральная территория"}</p>
       {tile.visibility==="visible"&&!tile.home&&<p>Добыча при контроле: {Object.entries(rules.territory_yield[tile.biome]||{}).map(([k,v])=>`${v} ${resources[k]} / мин`).join(', ')}.</p>}
       <p>{tile.garrison?"Гарнизон NPC · 55 HP. Захват только после победы.":""}</p><p>{order?`Поход · ${Math.max(0,order.ready_at-clock)} сек.`:`${rules.seconds} сек. · ${rules.fuel} топлива за поход`}</p>
       <div className="actions"><button disabled={busy||!!baseReason||!!tile?.garrison} onClick={()=>send('move')}>Переместить армию</button><button className="primary" disabled={busy||!!captureReason} onClick={()=>send('capture')}>{tile.garrison?"Атаковать гарнизон":"Захватить гекс"}</button></div>
       {(baseReason||captureReason)&&<p className="action-reason">{baseReason||captureReason}</p>}
     </article>}
     {!tile&&army&&<p>Выберите соседний гекс для движения или захвата. Гарнизоны NPC отмечены флагом: для захвата потребуется бой.</p>}
     {!tile&&state.battles.some(b=>b.state.loot)&&<button className="loot-shortcut" onClick={goArmy}>Трофеи → Армия → Командир</button>}
     {error&&<p className="action-reason" role="alert">{error}</p>}

   </section>
 </div>;
}
