import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { useGame, request, command } from "./store";
import { MapView } from "./Map";
import "./style.css";
import {Icon} from "./Icon";
import { Commander, Portrait } from "./Commander";
import { World } from "./World";
import { Armies } from "./Armies";
import { Season } from "./Season";
import { Gallery } from "./Gallery";
import { SpriteStage } from "./SpriteStage";
import { Roster } from "./Roster";
import type { ExpeditionRules } from "./store";
declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        ready: () => void;
        expand: () => void;
        setHeaderColor: (s: string) => void;
        platform?: string;
        isVersionAtLeast?: (v: string) => boolean;
        disableVerticalSwipes?: () => void;
        requestFullscreen?: () => void;
      };
    };
  }
}
type Definitions = {
  expeditions: ExpeditionRules;
  max_level?: number;
  buildings: Record<
    string,
    {
      name: string;
      cost: Record<string, number>;
      seconds: number;
      power: number;
      hq?: number;
      about?: string;
    }
  >;
  heroes: Record<
    string,
    { name: string; role: string; bio: string; effect: string }
  >;
  factions: Record<string, { name: string; accent: string; units: { key: string; name: string; art: string; role: string; trait?: string }[] }>;
  traits: Record<string, string>;
  units: Record<string, { name: string; gen?: string; trait?: string | null; art?: string; ability?: { name: string; effect: string; value: number; about: string }; hp: number; damage: number; defense: number; speed: number; initiative: number; range: number; melee: boolean; count: number; seconds: number; cost: Record<string, number>; requires: Record<string, number> }>;
  abilities: Record<string, { name: string; about: string }>;
  army_stacks: number;
};
const resourceNames: Record<string, string> = {
  metal: "Металл",
  oil: "Нефть",
  fuel: "Топливо",
  electronics: "Электроника",
  food: "Провизия",
};
const resourceSymbols: Record<string, string> = {
  metal: "⬡",
  oil: "◈",
  fuel: "◉",
  electronics: "⌘",
  food: "✦",
};
function App() {
  const { state, token, connected, setState, setToken, setConnected } =
    useGame();
  const [defs, setDefs] = useState<Definitions | null>(null);
  const [tab, setTab] = useState("База");
  const [armyView, setArmyView] = useState("units");
  useEffect(() => { if (state?.first_victory) setArmyView("commander"); }, [state?.first_victory]);
  const [sheet, setSheet] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const [selected, setSelected] = useState<number[] | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [clock, setClock] = useState(0);
  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  useEffect(() => {
    request("/config")
      .then(setDefs)
      .catch((e) => setError(e.message));
    const tg = window.Telegram?.WebApp;
    tg?.ready();
    tg?.expand();
    tg?.setHeaderColor("#101923");
    // A map drag must never collapse or scroll the Mini App (Bot API 7.7+).
    if (tg?.isVersionAtLeast?.("7.7")) tg.disableVerticalSwipes?.();
    // Phones get the whole screen, like a native game (Bot API 8.0+).
    if (tg?.isVersionAtLeast?.("8.0") && ["ios", "android"].includes(tg.platform ?? "")) {
      try { tg.requestFullscreen?.(); } catch { /* older clients keep the expanded view */ }
    }
    if (tg?.initData) {
      request("/auth/telegram", { init_data: tg.initData })
        .then((d) => setToken(d.token))
        .catch((e) => setError(e.message));
    }
  }, []);
  useEffect(() => {
    if (!token) return;
    let stopped = false;
    let ws: WebSocket;
    let retry: number;
    const connect = () => {
      if (stopped) return;
      ws = new WebSocket(
        `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/v1/ws`,
      );
      ws.onopen = () => ws.send(JSON.stringify({ token }));
      ws.onmessage = (e) => {
        const d = JSON.parse(e.data);
        setConnected(true);
        if (d.type === "snapshot") setState(d.state);
      };
      ws.onclose = (e) => {
        setConnected(false);
        if (e.code === 4401) {
          setError("Сессия истекла. Закройте и откройте игру через Telegram.");
          return;
        }
        retry = window.setTimeout(connect, 2500);
      };
      ws.onerror = () => ws.close();
    };
    request("/player/me")
      .then(setState)
      .catch((e) => setError(e.message));
    connect();
    const poll = window.setInterval(() => {
      if (!useGame.getState().connected)
        request("/player/me")
          .then(setState)
          .catch(() => {});
    }, 10000);
    return () => {
      stopped = true;
      clearTimeout(retry);
      clearInterval(poll);
      ws?.close();
    };
  }, [token]);
  useEffect(() => {
    if (!state) return;
    setClock(state.server_time);
    const t = setInterval(() => setClock((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, [state?.server_time]);
  const battle = state?.battles.find((b) => b.status === "active");
  const activeStack = battle?.state.stacks?.find((x) => x.id === battle.state.active);
  const targetStack = battle && selected ? battle.state.stacks?.find((x) => x.side === "npc" && x.hp > 0 && x.pos[0] === selected[0] && x.pos[1] === selected[1]) : undefined;
  const [battleNote, setBattleNote] = useState("");
  const noteFrom = (events: { type: string }[] = []) => {
    const lines = [events.some((e) => e.type === "luck") && "🍀 Удачный удар ×1.5", events.some((e) => e.type === "morale") && "🎺 Боевой дух: стек действует ещё раз"].filter(Boolean);
    setBattleNote(lines.join(" · "));
  };
  const battleCommand = (extra: Record<string, unknown>) => battle && run(async () => {
    const data = await command("/battles/commands", { battle_id: battle.id, turn: battle.state.turn, ...extra });
    noteFrom(data?.result?.events);
    setSelected(null);
  });
  const quickBattle = () => battle && run(async () => {
    await command("/battles/auto", { battle_id: battle.id });
    setBattleNote(""); setSelected(null);
  });
  const hexDistance = (a: number[], b: number[]) => Math.max(Math.abs(a[0] - b[0]), Math.abs(a[1] - b[1]), Math.abs(a[0] + a[1] - b[0] - b[1]));
  const lastBattle = state?.battles.at(-1);
  const step = !state?.hero
    ? 0
    : !state.buildings.some((b) => b.kind === "power" && b.status === "ready")
      ? 1
      : !state.buildings.some(
            (b) => b.kind === "quarry" && b.status === "ready",
          )
        ? 2
        : !state.buildings.some(
              (b) => b.kind === "barracks" && b.status === "ready",
            )
          ? 3
          : !state.units.length
            ? 4
            : !state.first_victory
              ? 5
              : state.inventory.some(i=>i.equipped) ? 7 : 6;
  const objectives = [
    "Выберите своего командира",
    "Постройте электростанцию",
    "Постройте металлургический карьер",
    "Постройте казармы",
    "Подготовьте стрелков",
    "Победите патруль NPC",
    "Снарядите тактический модуль",
    "Первая операция завершена",
  ];
  const targetKind = ["", "power", "quarry", "barracks"][step];
  const pendingBuilding = state?.buildings.find(b => b.kind === targetKind && b.status === "building");
  const tutorialCopy = [
    "Специализация командира даёт постоянный бонус. Выберите подходящий стиль игры.",
    "Электростанция обеспечивает базу энергией. Выберите свободный участок, затем подтвердите строительство.",
    "Карьер приносит металл для строительства и армии. Производство идёт автоматически при наличии энергии.",
    "Казармы открывают подготовку первого отряда. Постройте их на свободном участке.",
    "В разделе «Армия» подготовьте стрелков: 60 металла и 40 провизии. Обучение занимает 45 секунд.",
    "Отправьте стрелков против патруля. Стеки ходят по инициативе; стрелки бьют на 4 гекса, укрытия уменьшают урон.",
    "В разделе «Армия» снарядите полученный полевой модуль. Его бонус применяется сервером в бою.",
    "База снабжает армию, а победы развивают командира. Прогресс сохранён: можно вернуться позже.",
  ];
  const genitive: Record<string, string> = { rifles: "стрелков", scouts: "разведчиков", assault: "штурмовиков", artillery: "артиллерию", armor: "бронетехнику" };
  const unitReason = (kind: string) => {
    const unit = defs?.units[kind]; if (!unit || !state) return "Недоступно";
    const ready = (k: string) => state.buildings.find((b) => b.kind === k && b.status === "ready")?.level ?? 0;
    if (!(unit as { naval?: boolean }).naval && !ready("barracks")) return "Сначала завершите строительство казарм";
    for (const [need, level] of Object.entries(unit.requires)) if (ready(need) < level) return `Нужно: ${defs?.buildings[need]?.name} ${level} уровня`;
    if (state.jobs.length) return "Дождитесь завершения текущей подготовки";
    if (Object.entries(unit.cost).some(([k, v]) => state.resources[k] < v)) return "Недостаточно ресурсов";
    return "";
  };
  const goToObjective = () => {
    setGuideOpen(false);
    if (step >= 4 && step <= 6) { changeTab("Армия"); setArmyView(step === 6 ? "commander" : "units"); return; }
    if (step >= 7) { changeTab("Командование"); return; }
    changeTab("База");
    if (pendingBuilding) { setSelected([pendingBuilding.q,pendingBuilding.r]); setSheet(true); return; }
    // Select an available nearby cell, but never spend resources without confirmation.
    const occupied = new Set(state?.buildings.map(b => `${b.q},${b.r}`));
    for (let radius=1;radius<=4;radius++) {
      for(let r=-radius;r<=radius;r++) for(let q=-radius;q<=radius;q++) {
        if(Math.max(Math.abs(q),Math.abs(r),Math.abs(q+r))<=radius && !occupied.has(`${q},${r}`)) {
          setSelected([q,r]); setSheet(true); return;
        }
      }
    }
  };
  const mapOpen = !!state && (tab === "Карта" || !!battle?.state.expedition);
  useEffect(() => {
    document.documentElement.classList.toggle("locked", mapOpen);
    return () => document.documentElement.classList.remove("locked");
  }, [mapOpen]);
  const changeTab = (t: string) => {
    setTab(t);
    setSheet(false);
    setSelected(null);
  };
  const chooseTile = (q: number, r: number) => {
    if (
      !battle && tab === "База" &&
      Math.max(Math.abs(q), Math.abs(r), Math.abs(q + r)) > 4
    )
      return;
    if (battle && (q < 0 || q > 8 || r < 0 || r > 8)) return;
    setSelected([q, r]);
    if (tab === "База" && !battle) setSheet(true);
  };
  const formatTime = (n: number) => n >= 3600 ? `${Math.floor(n/3600)} ч ${Math.round(n%3600/60)} мин` : n >= 60 ? `${Math.floor(n/60)} мин ${n%60 ? `${n%60} сек` : ""}`.trim() : `${n} сек.`;
  const effectText = (e: { output: Record<string, number>; input: Record<string, number>; power: number; storage: number; vision: number; repair: number }) => [
    ...Object.entries(e.output).map(([k, v]) => `+${v} ${resourceNames[k].toLowerCase()}/мин`),
    ...Object.entries(e.input).map(([k, v]) => `−${v} ${resourceNames[k].toLowerCase()}/мин`),
    e.power ? `${e.power > 0 ? "+" : ""}${e.power} MW` : "",
    e.storage ? `+${e.storage} к складу` : "",
    e.vision ? `+${e.vision} обзор` : "",
    e.repair ? `+${e.repair} HP/мин` : "",
  ].filter(Boolean).join(" · ") || "Открывает механики базы";
  const cost = (c: Record<string, number>) =>
    Object.entries(c)
      .map(([k, v]) => `${v} ${resourceNames[k]}`)
      .join(" · ");
  return (
    <main className={battle?.state.expedition ? "map-screen battle-screen" : state && tab === "Карта" && !battle ? "map-screen" : ""}>
      <header>
        <div className="brand">
          <span className="insignia">IF</span>
          <div>
            <b>IRON FRONT</b>
            <small>WORLD AT WAR</small>
          </div>
        </div>
        <div className="status">
          <i className={connected ? "online" : ""} />
          {state ? state.player.name : "КОМАНДНЫЙ ЦЕНТР"}
        </div>
      </header>
      {!state ? (
        <section className="login">
          <div className="eyebrow">СТРАТЕГИЧЕСКОЕ КОМАНДОВАНИЕ</div>
          <h1>
            Ваш фронт.
            <br />
            Ваша история.
          </h1>
          <p>
            Развивайте базу, подготовьте первый отряд и проведите операцию
            против NPC.
          </p>
          <div className="login-box">
            <b>
              {token ? "Подключение к штабу…" : "Откройте игру через Telegram"}
            </b>
            <p>
              Вход выполняется через кнопку бота IRON FRONT. Игровой прогресс
              хранится на сервере.
            </p>
            {error && <p role="alert">{error}</p>}
          </div>
          <small>ВЕРТИКАЛЬНЫЙ СРЕЗ 0.1 · ТЕСТОВАЯ ВЕРСИЯ</small>
        </section>
      ) : (
        <>
          <div className="resources">
            {Object.entries(state.resources).map(([k, v]) => (
              <div key={k}>
                <span>{resourceSymbols[k]}</span>
                <strong>{v.toLocaleString("ru")}</strong>
                <small>{resourceNames[k]}</small>
              </div>
            ))}
          </div>
          <section className="objective">
            <span className="step">0{Math.min(step + 1, 7)}</span>
            <div>
              <small>ПЕРВАЯ ОПЕРАЦИЯ</small>
              <b>{objectives[step]}</b>
            </div>
            <button className="guide-toggle" aria-expanded={guideOpen} aria-label="План первой операции" onClick={() => setGuideOpen(!guideOpen)}>{Math.min(step,7)}/7 · План</button>
          </section>
          {(step < 7 || guideOpen) && <section className="guide" aria-label="Текущее задание">
            <p>{pendingBuilding ? `Строительство идёт. Осталось ${Math.max(0,pendingBuilding.ready_at-clock)} сек. Завершение подтвердит сервер.` : tutorialCopy[step]}</p>
            {step > 0 && !battle && <button className="guide-action" onClick={goToObjective}>{pendingBuilding ? "К стройке" : step < 4 ? "Выбрать участок" : step < 7 ? "К армии" : "Посмотреть отчёт"} →</button>}
            {guideOpen && <ol className="guide-list">{objectives.slice(0,7).map((text,i)=><li key={text} className={i<step ? "done" : i===step ? "current" : ""}><span>{i<step ? "✓" : i+1}</span>{text}</li>)}</ol>}
          </section>}
          <div className="screen-title">
            <div>
              <small>СЕКТОР {state.base ? `${state.base.q} : ${state.base.r}` : "—"}</small>
              <h1>
                {battle
                  ? "Патруль «Рубеж»"
                  : tab === "База"
                    ? "Передовая база"
                    : tab === "Карта"
                      ? "Театр операций"
                      : tab === "Армия"
                        ? "Вооружённые силы"
                        : tab}
              </h1>
            </div>
            <span className="tag">
              {battle ? `РАУНД ${battle.state.turn}` : "ALPHA 0.4"}
            </span>
          </div>
          {battle ? (
            <>
              <MapView
                buildings={[]}
                battle={battle}
                selected={selected}
                onSelect={chooseTile}
              />
              <div className="combat">
                {battle.state.expedition && <h2>{battle.state.pvp ? `⚔ Атака: ${battle.state.pvp.defender}` : `${battle.state.npc_tier?.name ?? "Гарнизон"} NPC`} · {battle.state.expedition.q}:{battle.state.expedition.r}</h2>}
                <div className="initiative" aria-label="Очередь ходов">
                  {(battle.state.order ?? []).map((id) => {
                    const st = battle.state.stacks?.find((x) => x.id === id);
                    if (!st || st.hp <= 0) return null;
                    return <span key={id} className={`init ${st.side}${id === battle.state.active ? " now" : ""}${st.acted ? " done" : ""}`}>
                      {defs?.units[st.kind]?.name ?? st.kind} · {Math.ceil(st.hp / (defs?.units[st.kind]?.hp ?? 10))}
                    </span>;
                  })}
                </div>
                {activeStack && (() => {
                  const foes = (battle.state.stacks ?? []).filter((x) => x.side === "npc" && x.hp > 0);
                  const aim = targetStack ?? [...foes].sort((a, b) => hexDistance(activeStack.pos, a.pos) - hexDistance(activeStack.pos, b.pos) || a.hp - b.hp)[0];
                  const pv = aim && battle.preview?.[aim.id];
                  if (!pv) return null;
                  const range = (v: number[]) => v[0] === v[1] ? `${v[0]}` : `${v[0]}–${v[1]}`;
                  return <p className="strike-preview">{pv.reach
                    ? <>🎯 {defs?.units[aim.kind]?.name}: урон {range(pv.damage)}, убьёт <b>{range(pv.kills)}</b>{pv.retaliation ? <> · ответ: потеряете <b>{range(pv.retaliation.kills)}</b></> : " · без ответа"}</>
                    : <>🎯 {defs?.units[aim.kind]?.name}: {defs?.units[activeStack.kind]?.melee ? "не дойти за ход" : "вне дальности"} — подойдите ближе</>}</p>;
                })()}
                {battleNote && <p className="battle-note" role="status">{battleNote}</p>}
                {activeStack && <p>
                  Ходит: <b>{defs?.units[activeStack.kind]?.name}</b> ({Math.ceil(activeStack.hp / (defs?.units[activeStack.kind]?.hp ?? 10))} из {activeStack.start}) ·
                  скорость {defs?.units[activeStack.kind]?.speed}{state.hero?.kind === "storm" ? "+1" : ""} · {defs?.units[activeStack.kind]?.melee ? "ближний бой" : `дальность ${defs?.units[activeStack.kind]?.range}`}.
                  {targetStack ? ` Цель: ${defs?.units[targetStack.kind]?.name} противника.` : " Выберите гекс для движения или вражеский стек как цель."}
                </p>}
                <div className="actions">
                  <button disabled={busy || !selected || !!targetStack}
                    onClick={() => battleCommand({ action: "move", q: selected![0], r: selected![1] })}>
                    Переместить
                  </button>
                  <button className="primary" disabled={busy}
                    onClick={() => battleCommand({ action: "attack", ...(targetStack ? { target: targetStack.id } : {}) })}>
                    Атаковать
                  </button>
                  <button disabled={busy} onClick={() => battleCommand({ action: "defend" })}>
                    Защита
                  </button>
                </div>
                {activeStack && defs?.units[activeStack.kind]?.ability && (() => {
                  const ab = defs.units[activeStack.kind].ability!;
                  const used = !!(activeStack as { skill_used?: boolean }).skill_used;
                  const needsHex = ab.effect === "dash";
                  return <div className="unit-skill">
                    <button className="skill" disabled={busy || used || (needsHex && (!selected || !!targetStack))}
                      onClick={() => battleCommand(needsHex ? { action: "skill", q: selected![0], r: selected![1] } : { action: "skill", ...(targetStack ? { target: targetStack.id } : {}) })}>
                      ◆ {ab.name}{used ? " · использовано" : ""}
                    </button>
                    <small>{ab.about}{needsHex ? ". Выберите гекс." : ""}</small>
                  </div>;
                })()}
                <div className="actions">
                  <button disabled={busy} onClick={() => battleCommand({ action: "wait" })}>Ждать</button>
                  <button disabled={busy} title="Сервер доиграет бой за вас: быстро, но без способностей" onClick={quickBattle}>⚡ Быстрый бой</button>
                  {state.hero && defs?.abilities[state.hero.kind] && battle.state.led !== false && <button disabled={busy || !!battle.state.ability_used} title={defs.abilities[state.hero.kind].about}
                    onClick={() => battleCommand({ action: "ability", ...(targetStack ? { target: targetStack.id } : {}) })}>
                    ★ {defs.abilities[state.hero.kind].name}{battle.state.ability_used ? " · использовано" : ""}
                  </button>}
                </div>
                {state.hero && defs?.abilities[state.hero.kind] && battle.state.led !== false && !battle.state.ability_used && <small>{defs.abilities[state.hero.kind].about}. Один раз за бой.</small>}
              </div>
            </>
          ) : tab === "База" ? (
            <>
              <MapView
                buildings={state.buildings}
                paused={sheet || guideOpen}
                selected={selected}
                onSelect={chooseTile}
              />
              <div className="base-toolbar">
                <div>
                  <small>ЭНЕРГОБАЛАНС</small>
                  <b>
                    {state.buildings
                      .filter((b) => b.status === "ready")
                      .reduce(
                        (sum, b) => sum + (b.effects?.current.power ?? defs?.buildings[b.kind].power ?? 0),
                        0,
                      )}{" "}
                    MW
                  </b>
                </div>
                <button
                  className="primary"
                  onClick={() => {
                    setSheet(true);
                    setSelected(null);
                  }}
                >
                  + Строительство
                </button>
              </div>
            </>
          ) : tab === "Карта" ? (
            defs && <World state={state} clock={clock} rules={defs.expeditions} goArmy={()=>{changeTab("Армия");setArmyView("units");}}/>
          ) : tab === "Армия" ? (
            <section className="content">
              <div className="army-tabs" role="group" aria-label="Раздел армии">
                <button aria-pressed={armyView === "units"} onClick={()=>setArmyView("units")}>Подразделения</button>
                <button aria-pressed={armyView === "commander"} onClick={()=>setArmyView("commander")}>Командир</button>
              </div>
              {armyView === "units" ? <>
              {defs && <Armies state={state} units={defs.units} stacks={defs.army_stacks ?? 5} busy={busy} run={run} toMap={()=>changeTab("Карта")}/>}
              {state.jobs.map((j) => (
                <div className="notice" key={j.id}>
                  Подготовка: {defs?.units[(j as {kind?:string}).kind ?? "rifles"]?.name ?? "отряд"} · {Math.max(0, j.ready_at - clock)} сек.
                </div>
              ))}
              <div className="section-label">НАЙМ В КАЗАРМАХ</div>
              {defs && state.hero && defs.factions[state.hero.kind] && <>
                <p className="faction-line" style={{ color: defs.factions[state.hero.kind].accent }}>{defs.factions[state.hero.kind].name}</p>
                <Roster units={defs.factions[state.hero.kind].units} faction={state.hero.kind} height={86} />
                {defs.factions[state.hero.kind].units.map(({ key: kind }) => {
                  const unit = defs.units[kind];
                  const reason = unitReason(kind);
                  return <div key={kind} className="train-option">
                    <button disabled={busy || !!reason} aria-describedby={`train-${kind}`} onClick={() => run(() => command("/army/train", { kind }))}>
                      Подготовить {unit.gen ?? genitive[kind] ?? unit.name} · {unit.count} · {cost(unit.cost)} · {unit.seconds} сек.
                    </button>
                    <small>HP {unit.hp} · урон {unit.damage} · защита {unit.defense} · скорость {unit.speed} · инициатива {unit.initiative} · {unit.melee ? "ближний бой" : `дальность ${unit.range}`}</small>
                    {unit.trait && <small className="trait">★ {defs.traits[unit.trait]}</small>}
                    {unit.ability && <small className="trait">◆ {unit.ability.name}: {unit.ability.about}</small>}
                    {reason && <p id={`train-${kind}`} className="action-reason">{reason}</p>}
                  </div>;
                })}
                <div className="section-label">ВЕРФЬ · ФЛОТ</div>
                <p className="faction-line">С кораблями соединение ходит по морям, озёрам и рекам. В морском бою сражаются только корабли.</p>
                <Roster units={["transport", "gunboat", "ironclad"].map((key) => ({ key, art: defs.units[key]?.art ?? "" }))} faction={state.hero.kind} height={70} />
                {["transport", "gunboat", "ironclad"].filter((k) => defs.units[k]).map((kind) => {
                  const unit = defs.units[kind];
                  const reason = unitReason(kind);
                  return <div key={kind} className="train-option">
                    <button disabled={busy || !!reason} onClick={() => run(() => command("/army/train", { kind }))}>
                      Построить {unit.gen ?? unit.name} · {unit.count} · {cost(unit.cost)} · {unit.seconds} сек.
                    </button>
                    <small>HP {unit.hp} · урон {unit.damage} · защита {unit.defense} · скорость {unit.speed} · {unit.melee ? "таран" : `дальность ${unit.range}`}</small>
                    {unit.ability && <small className="trait">◆ {unit.ability.name}: {unit.ability.about}</small>}
                    {reason && <p className="action-reason">{reason}</p>}
                  </div>;
                })}
              </>}
              </> : state.hero && defs && <Commander state={state} definition={defs.heroes[state.hero.kind]} busy={busy} equip={(item_id,equipped)=>run(()=>command("/equipment/equip",{item_id,equipped}))} pick={(key)=>run(()=>command("/commander/skill",{key}))}/>}
            </section>
          ) : tab === "Сезон" ? (
            <Season clock={clock} revision={state.revision} heroes={defs?.heroes ?? {}} />
          ) : (
            <section className="content">
              <div className="section-label">БОЕВОЙ ОТЧЁТ</div>
              {lastBattle ? (
                <article className="card">
                  <div>
                    <h2>
                      {lastBattle.status === "victory"
                        ? "Победа на рубеже"
                        : lastBattle.status === "defeat"
                          ? "Отряд вернулся на базу"
                          : "Бой продолжается"}
                    </h2>
                    <p>
                      {lastBattle.state.pvp?.result
                        ? `${lastBattle.state.pvp.result}.${lastBattle.status === "victory" ? ` +${lastBattle.state.npc_tier?.xp ?? 60} XP.` : " Каждый стек сохранил минимум половину бойцов."}`
                        : lastBattle.status === "victory"
                        ? lastBattle.state.expedition ? lastBattle.state.loot ? `Территория захвачена. +${lastBattle.state.npc_tier?.xp ?? 50} XP и трофейный модуль в инвентаре командира.` : "Бой завершён. Результат захвата указан в приказе армии." : "Награда: 150 металла, 60 провизии, 100 XP и полевой модуль."
                        : "Потери сохраняются, но после поражения каждый стек сохраняет минимум половину бойцов."}
                    </p>
                    <small>
                      Баланс {lastBattle.balance_version} ·{" "}
                      {lastBattle.state.turn - 1} раундов
                    </small>
                  </div>
                </article>
              ) : (
                <p>Завершите первую операцию, чтобы получить отчёт.</p>
              )}
              <div className="section-label">ЭКОНОМИКА</div>
              <p>
                Производство рассчитывается сервером каждую минуту. Склад: 5 000
                каждого ресурса. Офлайн-начисление: до 24 часов. При дефиците
                энергии производство останавливается.
              </p>
              <div className="section-label">СТАТУС СРЕЗА</div>
              <p>
                Строительство, подготовка войск, PvE, экипировка, походы и нейтральные территории. PvP,
                рынок, Stars и расширенная RPG-система ещё не включены.
              </p>
            </section>
          )}
          {error && (
            <div className="error" role="alert" onClick={() => setError("")}>
              {error} <span>×</span>
            </div>
          )}
          <nav>
            {[
              ["База", "base"],
              ["Армия", "army"],
              ["Карта", "map"],
              ["Сезон", "alliance"],
              ["Командование", "command"],
            ].map(([t, icon]) => (
              <button
                key={t}
                aria-label={t}
                className={tab === t ? "active" : ""}
                onClick={() => changeTab(t)}
              >
                <span><Icon name={icon}/>{t === "Армия" && !!state?.commander?.pending && <i className="nav-badge" aria-label="Доступен новый навык">{state.commander.pending}</i>}</span>
                {t}
              </button>
            ))}
          </nav>
          {sheet && tab === "База" && !battle && (
            <div className="scrim" onClick={() => setSheet(false)}>
              <section className="sheet" onClick={(e) => e.stopPropagation()}>
                <div className="handle" />
                <button className="close" onClick={() => setSheet(false)}>
                  ×
                </button>
                <small>ИНФРАСТРУКТУРА</small>
                <h2>
                  {selected
                    ? `Участок ${selected.join(" : ")}`
                    : "Строительство"}
                </h2>
                {selected &&
                state.buildings.some(
                  (b) => b.q === selected[0] && b.r === selected[1],
                ) ? (
                  state.buildings
                    .filter((b) => b.q === selected[0] && b.r === selected[1])
                    .map((b) => {
                      const upgrading = !!b.upgrade_ready_at;
                      const total = b.upgrade?.seconds || 1;
                      const left = upgrading ? Math.max(0, b.upgrade_ready_at! - clock) : 0;
                      const queueBusy = state.buildings.some((x) => x.status === "building" || x.upgrade_ready_at);
                      const hqLevel = state.buildings.find((x) => x.kind === "hq")?.level ?? 1;
                      const upgradeReason = b.status !== "ready" ? "Дождитесь завершения строительства"
                        : upgrading ? "Улучшение уже идёт"
                        : !b.upgrade ? ((b.level >= (defs?.max_level ?? 10)) ? "Максимальный уровень" : `Сначала улучшите штаб до ${hqLevel + 1} уровня`)
                        : queueBusy ? "Строительная очередь занята"
                        : Object.entries(b.upgrade.cost).some(([r, v]) => state.resources[r] < v) ? "Недостаточно ресурсов" : "";
                      return (
                      <article key={b.id}>
                        <h3>{defs?.buildings[b.kind].name}</h3>
                        <p className="building-purpose">{defs?.buildings[b.kind].about}</p>
                        <div className="level-pips" aria-label={`Уровень ${b.level} из 10`}>{Array.from({length:10},(_,i)=><i key={i} className={i < b.level ? "on" : ""}/>)}</div>
                        <p>
                          Уровень {b.level} ·{" "}
                          {b.status !== "ready"
                            ? `Готовность через ${Math.max(0, b.ready_at - clock)} сек.`
                            : upgrading ? `Улучшение до ${b.level + 1}: ${left} сек.` : "В работе"}
                        </p>
                        {upgrading && <div className="upgrade-progress"><i style={{width:`${Math.min(100, 100 - left / total * 100)}%`}}/></div>}
                        {b.effects && <div className="building-effects">
                          <div><small>Сейчас</small><b>{effectText(b.effects.current)}</b></div>
                          <div><small>Уровень {b.level + 1}</small><b>{b.effects.next ? effectText(b.effects.next) : "—"}</b></div>
                        </div>}
                        {b.upgrade && !upgrading && <button className="primary" disabled={busy || !!upgradeReason}
                          onClick={() => run(() => command("/construction/upgrade", { building_id: b.id }))}>
                          Улучшить · {cost(b.upgrade.cost)} · {formatTime(b.upgrade.seconds)}
                        </button>}
                        {upgradeReason && !upgrading && b.status === "ready" && <p className="action-reason">{upgradeReason}</p>}
                      </article>
                      );
                    })
                ) : (
                  <>
                    <p>
                      {selected
                        ? "Выберите объект для этого участка."
                        : "Сначала выберите свободный гекс на карте."}
                    </p>
                    {defs &&
                      Object.entries(defs.buildings)
                        .filter(([k]) => k !== "hq")
                        .map(([k, b]) => {
                          const existing = state.buildings.find(
                            (x) => x.kind === k,
                          );
                          const hqLevel = state.buildings.find((x) => x.kind === "hq")?.level ?? 1;
                          const reason = existing
                            ? "Уже построено: выберите здание, чтобы улучшить"
                            : (b.hq ?? 1) > hqLevel
                              ? `Нужен штаб ${b.hq} уровня`
                            : state.buildings.some(
                                  (x) => x.status === "building" || x.upgrade_ready_at,
                                )
                              ? "Очередь занята"
                              : k !== "power" &&
                                  !state.buildings.some(
                                    (x) =>
                                      x.kind === "power" &&
                                      x.status === "ready",
                                  )
                                ? "Нужна электростанция"
                                : Object.entries(b.cost).some(
                                      ([r, v]) => state.resources[r] < v,
                                    )
                                  ? "Недостаточно ресурсов"
                                  : !selected
                                    ? "Выберите гекс"
                                    : "";
                          return (
                            <button
                              className={"building-option" + (k === targetKind ? " recommended" : "")}
                              key={k}
                              disabled={busy || !!reason}
                              onClick={() =>
                                run(async () => {
                                  await command("/construction/start", {
                                    kind: k,
                                    q: selected![0],
                                    r: selected![1],
                                  });
                                  setSheet(false);
                                })
                              }
                            >
                              <span>
                                <b>{b.name}</b>
                                {k === targetKind && <small className="recommend-label">ТЕКУЩАЯ ЗАДАЧА</small>}
                                <small>
                                  {cost(b.cost)} · {b.seconds} сек.
                                </small>
                                {reason && <em>{reason}</em>}
                              </span>
                              <span>＋</span>
                            </button>
                          );
                        })}
                  </>
                )}
              </section>
            </div>
          )}
          {!state.hero && defs && (
            <div className="hero-overlay">
              <small>ВАША ПЕРВАЯ КОМАНДА</small>
              <h1>Выберите командира</h1>
              <p>
                Стартовый выбор постоянный. Остальные герои появятся в следующих
                этапах.
              </p>
              <div className="hero-grid">
                {Object.entries(defs.heroes).map(([id, h]) => (
                  <button
                    disabled={busy}
                    key={id}
                    onClick={() =>
                      run(() => command("/heroes/choose", { kind: id }))
                    }
                  >
                    <div className="selection-portrait"><Portrait id={id} name={h.name}/></div>
                    <small>{h.role}</small>
                    <b>{h.name}</b>
                    <p>{h.effect}</p>
                    {defs.factions?.[id] && <>
                      <em className="faction-line" style={{ color: defs.factions[id].accent }}>{defs.factions[id].name}</em>
                      <Roster units={defs.factions[id].units} faction={id} height={58} scale={0.62} />
                    </>}
                  </button>
                ))}
              </div>
              {error && <p role="alert">{error}</p>}
              <small>ШЕСТЬ СПЕЦИАЛИЗАЦИЙ · ОДИН ПЕРВЫЙ КОМАНДИР</small>
            </div>
          )}
        </>
      )}
    </main>
  );
}
const page = new URLSearchParams(location.search);
createRoot(document.getElementById("root")!).render(page.has("sprite") ? <SpriteStage /> : page.has("gallery") ? <Gallery /> : <App />);
