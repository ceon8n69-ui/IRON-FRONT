// Polytopia-style match board: hex terrain, territory, cities, improvements and units with fog.
import { useEffect, useRef, useState } from "react";
import { Application, Assets, Container, Graphics, Sprite, Text, Texture } from "pixi.js";
import { preloadWorld, rasterEnvironment, worldObject } from "./WorldArt";

export type MTile = { q: number; r: number; t: string; res: string | null; imp: string | null; owner: number | null; city: string | null; fog: boolean };
export type MCity = { id: string; name: string; q: number; r: number; owner: number | null; level: number; pop: number; spec: string | null; capital: boolean; radius: number; walls: boolean; reward: number | null; income: number; units: number; cap: number };
export type MUnit = { id: string; role: string; q: number; r: number; owner: number; hp: number; max_hp: number; moved: boolean; attacked: boolean; kills: number; branch: string | null;
  atk: number; def: number; mv: number; rng: number; promote: boolean; moves?: string[]; targets?: { id: string; forecast: [number, number] }[]; can_capture?: boolean };
export type Board = { size: number; turn: number; current: number; winner: number | null; tiles: MTile[]; cities: MCity[]; units: MUnit[];
  players: { seat: number; faction: string; eliminated: boolean; cities: number; stars?: number; techs?: string[] }[];
  income?: number; tech_costs?: Record<string, number>; build?: Record<string, string[]>; train?: Record<string, string[]> };

export const SEAT_COLORS = [0x4c9ce5, 0xd95a52, 0xe5b65a, 0x64b87b];
export const SEAT_CSS = ["#4c9ce5", "#d95a52", "#e5b65a", "#64b87b"];
const GROUND: Record<string, number> = { field: 0x6fae4c, forest: 0x4f9440, mountain: 0x8f948c, water: 0x3d86c6 };
const SIDE: Record<string, number> = { field: 0x5a3f2a, forest: 0x4b3624, mountain: 0x5d5a52, water: 0x1f5d8f };
const BIOME: Record<string, string> = { field: "plain", forest: "forest", mountain: "mountain" };
const IMP_ART: Record<string, string> = { farm: "/art/buildings/farm.png", mine: "/art/buildings/quarry.png", lumber: "/art/buildings/warehouse.png" };
const RES_ICON: Record<string, string> = { crop: "🌾", fruit: "🍎", ore: "⛏" };
const W = 54 * Math.sqrt(3), H = 54 * 0.975;
export const pos = (q: number, r: number) => [W * (q + r / 2), H * r];

function hex(g: Graphics, x: number, y: number, size: number, color: number, alpha = 1) {
  const pts: number[] = [];
  for (let i = 0; i < 6; i++) { const a = ((i * 60 + 30) * Math.PI) / 180; pts.push(x + Math.cos(a) * size, y + Math.sin(a) * size * 0.65); }
  g.poly(pts).fill({ color, alpha });
  return pts;
}

type Props = {
  board: Board; mySeat: number | null; unitArt: (seat: number, role: string) => string;
  selected: { q: number; r: number } | null; focus: { q: number; r: number } | null; onTap: (q: number, r: number) => void;
};

export function MatchBoard({ board, mySeat, unitArt, selected, focus, onTap }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const app = useRef<Application | null>(null);
  const scene = useRef(new Container());
  const camera = useRef({ x: 0, y: 0, scale: 1.05 });
  const latest = useRef({ onTap });
  latest.current = { onTap };
  const [ready, setReady] = useState(false);
  const [textures, setTextures] = useState(0);
  const loading = useRef(new Set<string>());

  useEffect(() => {
    let alive = true, cleanup = () => {};
    const a = new Application();
    (async () => {
      await a.init({ resizeTo: host.current!, background: 0x15232b, antialias: true, resolution: Math.min(devicePixelRatio, 2), autoDensity: true, preference: "webgl" });
      if (!alive) { a.destroy(true, { children: true }); return; }
      app.current = a;
      host.current!.appendChild(a.canvas);
      scene.current = new Container();
      a.stage.addChild(scene.current);
      a.ticker.maxFPS = 30;
      const apply = () => {
        scene.current.position.set(a.screen.width / 2 + camera.current.x, a.screen.height / 2 + camera.current.y);
        scene.current.scale.set(camera.current.scale);
      };
      (a as unknown as { applyCamera: () => void }).applyCamera = apply;
      const pointers = new Map<number, { x: number; y: number }>();
      let traveled = 0, pinch = 0;
      const down = (e: PointerEvent) => { a.canvas.setPointerCapture(e.pointerId); pointers.set(e.pointerId, { x: e.clientX, y: e.clientY }); traveled = 0;
        if (pointers.size === 2) { const [p, q] = [...pointers.values()]; pinch = Math.hypot(p.x - q.x, p.y - q.y); } };
      const move = (e: PointerEvent) => {
        const prev = pointers.get(e.pointerId); if (!prev) return;
        const dx = e.clientX - prev.x, dy = e.clientY - prev.y;
        pointers.set(e.pointerId, { x: e.clientX, y: e.clientY }); traveled += Math.abs(dx) + Math.abs(dy);
        if (pointers.size === 2) { const [p, q] = [...pointers.values()]; const d = Math.hypot(p.x - q.x, p.y - q.y);
          if (pinch) camera.current.scale = Math.max(0.3, Math.min(1.8, camera.current.scale * d / pinch)); pinch = d; }
        else { camera.current.x += dx; camera.current.y += dy; }
        apply();
      };
      const up = (e: PointerEvent) => {
        if (traveled < 8 && pointers.size === 1) {
          const rect = a.canvas.getBoundingClientRect();
          const x = (e.clientX - rect.left - a.screen.width / 2 - camera.current.x) / camera.current.scale;
          const y = (e.clientY - rect.top - a.screen.height / 2 - camera.current.y) / camera.current.scale;
          const rawR = y / H, rawQ = x / W - rawR / 2;
          let best = [0, 0], dist = Infinity;
          for (let q = Math.floor(rawQ) - 1; q <= Math.ceil(rawQ) + 1; q++)
            for (let r = Math.floor(rawR) - 1; r <= Math.ceil(rawR) + 1; r++) {
              const [px, py] = pos(q, r); const d = (px - x) ** 2 + ((py - y) / 0.65) ** 2;
              if (d < dist) { best = [q, r]; dist = d; }
            }
          latest.current.onTap(best[0], best[1]);
        }
        pointers.delete(e.pointerId); pinch = 0;
      };
      const wheel = (e: WheelEvent) => { e.preventDefault(); camera.current.scale = Math.max(0.3, Math.min(1.8, camera.current.scale * Math.exp(-e.deltaY * 0.001))); apply(); };
      const hold = (e: TouchEvent) => e.preventDefault();
      a.canvas.addEventListener("pointerdown", down); a.canvas.addEventListener("pointermove", move);
      a.canvas.addEventListener("pointerup", up); a.canvas.addEventListener("pointercancel", (e) => pointers.delete(e.pointerId));
      a.canvas.addEventListener("wheel", wheel, { passive: false });
      a.canvas.addEventListener("touchmove", hold, { passive: false }); a.canvas.addEventListener("touchstart", hold, { passive: false });
      const resize = new ResizeObserver(apply); resize.observe(host.current!);
      apply();
      setReady(true);
      cleanup = () => { resize.disconnect(); a.destroy(true, { children: true }); };
    })();
    return () => { alive = false; cleanup(); app.current = null; };
  }, []);

  useEffect(() => preloadWorld(() => setTextures((n) => n + 1)), []);

  // Centre the camera on a requested hex (my capital on open, or a unit).
  useEffect(() => {
    if (!focus || !app.current) return;
    const [x, y] = pos(focus.q, focus.r);
    camera.current.x = -x * camera.current.scale; camera.current.y = -y * camera.current.scale;
    (app.current as unknown as { applyCamera?: () => void }).applyCamera?.();
  }, [focus?.q, focus?.r, ready]);

  const tex = (url: string) => {
    if (Assets.cache.has(url)) return Assets.cache.get(url) as Texture;
    if (!loading.current.has(url)) { loading.current.add(url); Assets.load(url).then(() => setTextures((n) => n + 1)).catch(() => {}); }
    return null;
  };

  useEffect(() => {
    if (!ready || !app.current) return;
    const s = scene.current;
    s.removeChildren().forEach((c) => c.destroy({ children: true }));
    const ground = new Container(), props = new Container(), marks = new Container(), labels = new Container();
    s.addChild(ground, marks, props, labels);
    const tiles = [...board.tiles].sort((a, b) => a.r - b.r || a.q - b.q);
    const me = board.units.find((u) => u.owner === mySeat && selected && u.q === selected.q && u.r === selected.r);
    const reach = new Set(me?.moves ?? []);
    const targets = new Set((me?.targets ?? []).map((t) => t.id));
    const cityAt = new Map(board.cities.map((c) => [`${c.q},${c.r}`, c]));
    for (const t of tiles) {
      const [x, y] = pos(t.q, t.r);
      const g = new Graphics();
      hex(g, x, t.t === "water" ? y + 4 : y + 9, 52, SIDE[t.t] ?? 0x263a36);
      const rim = hex(g, x, y, 52, GROUND[t.t] ?? 0x555555);
      g.poly(rim).stroke({ color: 0x1b201e, width: 1.4, alpha: .55 });
      if (t.t !== "water") hex(g, x, y - 1, 44, (GROUND[t.t] ?? 0) + 0x0a0a06);
      else for (let i = 0; i < 3; i++) g.moveTo(x - 16 + i * 12, y - 6 + i * 6).quadraticCurveTo(x - 12 + i * 12, y - 9 + i * 6, x - 8 + i * 12, y - 6 + i * 6).stroke({ color: 0xd6efff, width: 1.3, alpha: .7 });
      ground.addChild(g);
      if (t.owner !== null) {
        const b = new Graphics(); const pts = hex(b, x, y, 48, SEAT_COLORS[t.owner] ?? 0xffffff, .22);
        b.poly(pts).stroke({ color: SEAT_COLORS[t.owner] ?? 0xffffff, width: 2, alpha: .7 }); marks.addChild(b);
      }
      const city = cityAt.get(`${t.q},${t.r}`);
      if (city) {
        const kind = city.owner === null ? "camp" : city.capital ? "capital" : "base";
        const occupied = board.units.some((u) => u.q === t.q && u.r === t.r);
        const art = worldObject(kind, x, y, (city.owner === null ? 72 : 80 + city.level * 4) * (occupied ? .8 : 1), city.owner === null ? null : SEAT_COLORS[city.owner]);
        if (art) { if (occupied) art.alpha = .75; props.addChild(art); }
        else { const c = new Graphics(); c.roundRect(x - 22, y - 34, 44, 34, 6).fill(city.owner === null ? 0xb59a6a : SEAT_COLORS[city.owner]).stroke({ color: 0x1b201e, width: 2 }); props.addChild(c); }
        const name = new Text({ text: `${city.name}${city.owner !== null ? ` · ${city.level}` : ""}`, style: { fontSize: 12, fill: 0xffffff, fontFamily: "sans-serif", fontWeight: "bold" } });
        name.anchor.set(.5);
        const w = name.width + 12;
        labels.addChild(new Graphics().roundRect(x - w / 2, y + 16, w, 18, 9).fill({ color: city.owner === null ? 0x2a2f33 : SEAT_COLORS[city.owner], alpha: .92 }).stroke({ color: 0x1b201e, width: 1 }));
        name.position.set(x, y + 25); labels.addChild(name);
      } else if (t.imp && IMP_ART[t.imp]) {
        const tx = tex(IMP_ART[t.imp]);
        if (tx) { const sp = new Sprite(tx); sp.anchor.set(.5, .8); sp.scale.set(70 / tx.width); sp.position.set(x, y + 8); props.addChild(sp); }
      } else {
        const env = BIOME[t.t] ? rasterEnvironment(x, y, BIOME[t.t], t.q, t.r) : null;
        if (env) props.addChild(env);
        if (t.res && RES_ICON[t.res]) {
          const icon = new Text({ text: RES_ICON[t.res], style: { fontSize: 18 } }); icon.anchor.set(.5); icon.position.set(x + 24, y + 6); labels.addChild(icon);
        }
      }
      if (t.fog) { const f = new Graphics(); hex(f, x, y, 53, 0x0d1418, .45); labels.addChild(f); }
      if (reach.has(`${t.q},${t.r}`)) { const m = new Graphics(); const pts = hex(m, x, y, 40, 0xffffff, .28); m.poly(pts).stroke({ color: 0xffffff, width: 2, alpha: .8 }); labels.addChild(m); }
      if (board.build?.[`${t.q},${t.r}`] && selected && selected.q === t.q && selected.r === t.r) {
        const m = new Graphics(); m.poly(hex(m, x, y, 44, 0xe5b65a, .15)).stroke({ color: 0xe5b65a, width: 2 }); labels.addChild(m);
      }
    }
    const units = [...board.units].sort((a, b) => a.r - b.r);
    for (const u of units) {
      const [x, y] = pos(u.q, u.r);
      const node = new Container();
      const onCity = cityAt.has(`${u.q},${u.r}`);
      if (onCity) node.addChild(new Graphics().ellipse(0, 4, 30, 11).fill({ color: SEAT_COLORS[u.owner] ?? 0xffffff, alpha: .35 }));
      const shadow = new Graphics().ellipse(0, 4, 26, 9).fill({ color: 0x000000, alpha: .28 }); node.addChild(shadow);
      const ring = new Graphics().ellipse(0, 4, 28, 10).stroke({ color: SEAT_COLORS[u.owner] ?? 0xffffff, width: 3 }); node.addChild(ring);
      const tx = tex(unitArt(u.owner, u.role));
      if (tx) {
        const sp = new Sprite(tx); sp.anchor.set(.5, .88); const sc = 64 / Math.max(tx.width, tx.height) * 1.25;
        sp.scale.set(u.owner % 2 ? -sc : sc, sc); node.addChild(sp);
      } else node.addChild(new Graphics().circle(0, -18, 14).fill(SEAT_COLORS[u.owner]).stroke({ color: 0x1b201e, width: 2 }));
      const done = u.owner === mySeat && board.current === mySeat && u.moved && u.attacked;
      if (done) node.alpha = .6;
      const bar = new Graphics();
      bar.roundRect(-20, 10, 40, 6, 3).fill(0x1b201e);
      bar.roundRect(-19, 11, 38 * Math.max(0, u.hp) / u.max_hp, 4, 2).fill(u.hp / u.max_hp > .5 ? 0x7ccf6a : u.hp / u.max_hp > .25 ? 0xe5b65a : 0xd95a52);
      node.addChild(bar);
      const hpText = new Text({ text: String(u.hp), style: { fontSize: 11, fill: 0xffffff, fontFamily: "sans-serif", fontWeight: "bold", stroke: { color: 0x1b201e, width: 3 } } });
      hpText.anchor.set(.5); hpText.position.set(24, 12); node.addChild(hpText);
      if (u.branch || u.promote) {
        const star = new Text({ text: u.branch ? "★" : "⇧", style: { fontSize: 14, fill: 0xffd77a, fontFamily: "sans-serif", stroke: { color: 0x1b201e, width: 3 } } });
        star.anchor.set(.5); star.position.set(-24, 10); node.addChild(star);
      }
      if (targets.has(u.id)) {
        const t = new Graphics().ellipse(0, 4, 32, 12).stroke({ color: 0xff5a4a, width: 3 }); node.addChild(t);
        const f = me?.targets?.find((x) => x.id === u.id)?.forecast;
        if (f) { const ft = new Text({ text: `−${f[0]}`, style: { fontSize: 13, fill: 0xffb4a0, fontFamily: "sans-serif", fontWeight: "bold", stroke: { color: 0x1b201e, width: 3 } } }); ft.anchor.set(.5); ft.position.set(0, -58); node.addChild(ft); }
      }
      node.position.set(x, y + (onCity ? 10 : 4));
      labels.addChild(node);
    }
    if (selected) {
      const [x, y] = pos(selected.q, selected.r);
      const sel = new Graphics(); sel.poly(hex(new Graphics(), x, y, 50, 0, 0)).stroke({ color: 0xffd77a, width: 3 }); labels.addChild(sel);
    }
  }, [ready, board, selected, mySeat, textures]);

  return <div className="match-stage" ref={host} />;
}
