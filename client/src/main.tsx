import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { useGame, request, command } from "./store";
import { MapView } from "./Map";
import "./style.css";
import {Icon} from "./Icon";
import { Commander, Portrait } from "./Commander";
import { World } from "./World";
import type { ExpeditionRules } from "./store";
declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        ready: () => void;
        expand: () => void;
        setHeaderColor: (s: string) => void;
      };
    };
  }
}
type Definitions = {
  expeditions: ExpeditionRules;
  buildings: Record<
    string,
    {
      name: string;
      cost: Record<string, number>;
      seconds: number;
      power: number;
    }
  >;
  heroes: Record<
    string,
    { name: string; role: string; bio: string; effect: string }
  >;
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
    "Отправьте стрелков против патруля. Приблизьтесь на дальность 3 гекса и атакуйте; укрытия уменьшают урон.",
    "В разделе «Армия» снарядите полученный полевой модуль. Его бонус применяется сервером в бою.",
    "База снабжает армию, а победы развивают командира. Прогресс сохранён: можно вернуться позже.",
  ];
  const trainReason = !state?.buildings.some(b => b.kind === "barracks" && b.status === "ready")
    ? "Сначала завершите строительство казарм"
    : state.jobs.length ? "Дождитесь завершения текущей подготовки"
    : state.resources.metal < 60 || state.resources.food < 40 ? "Нужно 60 металла и 40 провизии" : "";
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
  const changeTab = (t: string) => {
    setTab(t);
    setSheet(false);
    setSelected(null);
  };
  const chooseTile = (q: number, r: number) => {
    if (
      tab === "База" &&
      Math.max(Math.abs(q), Math.abs(r), Math.abs(q + r)) > 4
    )
      return;
    if (battle && (q < 0 || q > 8 || r < 0 || r > 8)) return;
    setSelected([q, r]);
    if (tab === "База" && !battle) setSheet(true);
  };
  const cost = (c: Record<string, number>) =>
    Object.entries(c)
      .map(([k, v]) => `${v} ${resourceNames[k]}`)
      .join(" · ");
  return (
    <main>
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
              <small>СЕКТОР 64 : 64</small>
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
              {battle ? `РАУНД ${battle.state.turn}` : "ALPHA 0.1"}
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
                <div>
                  <b>Ваш отряд · {battle.state.player.hp} HP</b>
                  <span>NPC · {battle.state.npc.hp} HP</span>
                </div>
                <p>
                  Выберите соседний гекс для движения. Дальность атаки: 3.
                  Укрытие снижает входящий урон.
                </p>
                <div className="actions">
                  <button
                    disabled={busy || !selected}
                    onClick={() =>
                      run(() =>
                        command("/battles/commands", {
                          battle_id: battle.id,
                          turn: battle.state.turn,
                          action: "move",
                          q: selected![0],
                          r: selected![1],
                        }),
                      )
                    }
                  >
                    Переместить
                  </button>
                  <button
                    className="primary"
                    disabled={busy}
                    onClick={() =>
                      run(() =>
                        command("/battles/commands", {
                          battle_id: battle.id,
                          turn: battle.state.turn,
                          action: "attack",
                        }),
                      )
                    }
                  >
                    Атаковать
                  </button>
                  <button
                    disabled={busy}
                    onClick={() =>
                      run(() =>
                        command("/battles/commands", {
                          battle_id: battle.id,
                          turn: battle.state.turn,
                          action: "defend",
                        }),
                      )
                    }
                  >
                    Защита
                  </button>
                </div>
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
                        (sum, b) => sum + (defs?.buildings[b.kind].power || 0),
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
              <div className="section-label">РЕЗЕРВ И ПОДГОТОВКА</div>
              {(state.armies || []).map(a=><article className="card" key={a.id}><div><h3>Первое соединение</h3><p>{a.status === "moving" ? "В походе" : "Готово к приказу"} · {a.q} : {a.r}</p></div><button className="primary" onClick={()=>changeTab("Карта")}>На карту</button></article>)}
              {state.units.map((u) => (
                <article className="card" key={u.id}>
                  <div className="unit-icon"><Icon name="army"/></div>
                  <div>
                    <h3>Стрелковое отделение</h3>
                    <p>Здоровье {u.hp}/100 · {u.status === "army" ? "В составе соединения" : u.status === "battle" ? "В бою" : "В резерве"}</p>
                  </div>
                  {state.first_victory && u.status === "reserve" && !(state.armies || []).length && <button disabled={busy} className="primary" onClick={()=>run(async()=>{await command("/army/create",{unit_id:u.id});changeTab("Карта");})}>Сформировать</button>}
                  {!state.first_victory && (
                    <button
                      className="primary"
                      disabled={busy}
                      onClick={() =>
                        run(() => command("/battles", { unit_id: u.id }))
                      }
                    >
                      В бой
                    </button>
                  )}
                </article>
              ))}
              {!state.units.length && (
                <p>Подготовьте первый отряд в казармах.</p>
              )}
              {state.jobs.map((j) => (
                <div className="notice" key={j.id}>
                  Подготовка стрелков · {Math.max(0, j.ready_at - clock)} сек.
                </div>
              ))}
              <button
                disabled={busy || !!trainReason}
                aria-describedby="train-reason"
                onClick={() => run(() => command("/army/train", {}))}
              >
                Подготовить стрелков · 60 металла + 40 провизии · 45 сек.
              </button>
              {trainReason && <p id="train-reason" className="action-reason">{trainReason}</p>}
              </> : state.hero && defs && <Commander state={state} definition={defs.heroes[state.hero.kind]} busy={busy} equip={(item_id,equipped)=>run(()=>command("/equipment/equip",{item_id,equipped}))}/>}
            </section>
          ) : tab === "Альянс" ? (
            <section className="content">
              <div className="empty-emblem">⚑</div>
              <h2>Союз начинается с командиров</h2>
              <p>
                Альянсы запланированы для многопользовательского этапа. В
                текущем срезе ещё недоступны.
              </p>
            </section>
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
                      {lastBattle.status === "victory"
                        ? "Награда: 150 металла, 60 провизии, 100 XP и полевой модуль."
                        : "После поражения сохраняется минимум 50 HP. Подготовьте новую попытку."}
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
              ["Альянс", "alliance"],
              ["Командование", "command"],
            ].map(([t, icon]) => (
              <button
                key={t}
                aria-label={t}
                className={tab === t ? "active" : ""}
                onClick={() => changeTab(t)}
              >
                <span><Icon name={icon}/></span>
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
                    .map((b) => (
                      <article key={b.id}>
                        <h3>{defs?.buildings[b.kind].name}</h3>
                        <p className="building-purpose">{({hq:"Командный центр вашей базы.",power:"Даёт 20 MW для производственных зданий.",quarry:"Производит металл каждую минуту. Требует 4 MW.",barracks:"Открывает подготовку стрелков в разделе «Армия». Требует 6 MW.",refinery:"Перерабатывает 2 нефти в 3 топлива за минуту. Требует 5 MW."} as Record<string,string>)[b.kind]}</p>
                        <p>
                          Уровень {b.level} ·{" "}
                          {b.status === "ready"
                            ? "В работе"
                            : `Готовность через ${Math.max(0, b.ready_at - clock)} сек.`}
                        </p>
                      </article>
                    ))
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
                          const reason = existing
                            ? "Уже построено или в очереди"
                            : state.buildings.some(
                                  (x) => x.status === "building",
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
createRoot(document.getElementById("root")!).render(<App />);
