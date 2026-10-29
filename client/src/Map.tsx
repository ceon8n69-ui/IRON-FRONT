import {surface, environment, bunker, squad, pile, chest, mine, node, ruin, camp} from "./Terrain";
import { unitSprite, pirateShip } from "./Units";
import {Icon} from "./Icon";
import { useEffect, useRef, useState } from "react";
import { Application, Assets, Container, Graphics, Sprite, Text, Texture } from "pixi.js";
import { createBuilding, type BuildingVisual } from "./Buildings";
import type { Building, Battle, Army } from "./store";
import { Director, type BattleEvent, type UnitHandle, type UnitInfo } from "./BattleFx";
import { preloadWorld, rasterEnvironment, worldObject, worldReady } from "./WorldArt";
type Tile = { q: number; r: number; biome: string; control?: string | null; visibility?: string; home?: boolean; base?: string | null; garrison?: boolean; garrison_strength?: {name:string;hp:number} | null; object?: {kind:string;resource?:string;amount?:number;owner?:string|null;pending?:boolean} | null; node?: {kind:string;name:string} | null; supplied?: boolean | null };
type Props = {
  buildings: Building[];
  paused?: boolean;
  battle?: Battle;
  world?: Tile[];
  center?: number[];
  armies?: { army: Army; kinds: string[]; active: boolean }[];
  route?: number[][] | null;
  now?: number;
  selected: number[] | null;
  onSelect: (q: number, r: number) => void;
  playback?: { key: number; events: BattleEvent[]; speed: number } | null;
  onPlaybackDone?: () => void;
  unitInfo?: UnitInfo;
};
// Bright diorama palette: lit top, darker soil side, ink rim.
const colors: Record<string, number> = {
  plain: 0x6fae4c,
  forest: 0x4f9440,
  hills: 0x8fa36a,
  desert: 0xd9b46c,
  beach: 0xe8d39a,
  mountain: 0x8f948c,
  river: 0x5aa7d8,
  lake: 0x4a96cf,
  sea: 0x3a7fc0,
  unknown: 0x1e2c37,
};
const sides: Record<string, number> = { plain: 0x6b4a2e, forest: 0x5c3f27, hills: 0x6c5a48, desert: 0x9c7442, beach: 0xb08d55,
  mountain: 0x5d5f5a, river: 0x6b4a2e, lake: 0x2d6aa6, sea: 0x26609e, unknown: 0x141e27 };
const WATER = new Set(["sea", "lake"]);
export const BATTLE_SCALE = 0.72, BATTLE_SHIFT = -70;
// Raster unit sprites: 256x224 px (2x of the 128x112 render frame), feet at 82% height.
// Displayed at the same size as the code-drawn figure, which is scaled 1.45 in that frame.
const RASTER_FEET = 92 / 112, RASTER_SCALE = 0.5 / 1.45;
const failed = new Set<string>();
const loading = new Set<string>();
// Raster base buildings (art/buildings/<kind>.png): displayed width and the anchor that puts the hex patch on the tile centre.
const BUILDING_WIDTH = 116, BUILDING_ANCHOR = 0.8;
const NAVAL_KINDS = new Set(["transport", "gunboat", "ironclad"]);
function hex(g: Graphics, x: number, y: number, size: number, color: number) {
  const p: number[] = [];
  for (let i = 0; i < 6; i++) {
    const a = ((i * 60 + 30) * Math.PI) / 180;
    p.push(x + Math.cos(a) * size, y + Math.sin(a) * size * 0.65);
  }
  g.poly(p).fill(color).stroke({ color: 0xa6bbab, alpha: 0.14, width: 1 });
}
function tower(
  g: Graphics,
  x: number,
  y: number,
  h: number,
  w: number,
  color: number,
) {
  g.poly([x - w, y, x, y + w * 0.45, x + w, y, x, y - w * 0.45]).fill(0x18232b);
  g.poly([x - w, y, x, y + w * 0.45, x, y + w * 0.45 - h, x - w, y - h]).fill(
    color,
  );
  g.poly([x, y + w * 0.45, x + w, y, x + w, y - h, x, y + w * 0.45 - h]).fill(
    0x35444a,
  );
  g.poly([
    x - w,
    y - h,
    x,
    y + w * 0.45 - h,
    x + w,
    y - h,
    x,
    y - w * 0.45 - h,
  ]).fill(0x8f9d93);
  g.rect(x - w + 4, y - h + 7, 6, 3).fill(0xe5b65a);
}
export function MapView(props: Props) {
  const host = useRef<HTMLDivElement>(null);
  const app = useRef<Application | null>(null);
  const scene = useRef(new Container());
  const latest = useRef(props);
  latest.current = props;
  const selection = useRef(new Graphics());
  const animations = useRef<BuildingVisual[]>([]);
  const units = useRef(new globalThis.Map<string, UnitHandle>());
  const fxLayer = useRef(new Container());
  const director = useRef<Director | null>(null);
  const played = useRef<number | null>(null);
  const [ready, setReady] = useState(false);
  const [textures, setTextures] = useState(0);
  const [error, setError] = useState("");
  // Tactical field starts zoomed out so all 9 columns fit a phone above the command panel.
  const home = props.battle ? { scale: BATTLE_SCALE, x: 0, y: BATTLE_SHIFT } : props.world ? { scale: 1, x: 0, y: 0 } : { scale: 1.22, x: 0, y: 0 };
  const camera = useRef({ ...home });
  useEffect(() => {
    let alive = true;
    let cleanup = () => {};
    const a = new Application();
    (async () => {
      await a.init({
        resizeTo: host.current!,
        background: 0x15232b,
        antialias: true,
        resolution: Math.min(devicePixelRatio, 2),
        autoDensity: true,
        preference: "webgl",
      });
      if (!alive) {
        a.destroy(true, { children: true });
        return;
      }
      app.current = a;
      host.current!.appendChild(a.canvas);
      scene.current = new Container();
      a.stage.addChild(scene.current);
      selection.current = new Graphics();
      const motion = matchMedia("(prefers-reduced-motion: reduce)");
      let elapsed = 0;
      a.ticker.maxFPS = 30;
      a.ticker.add((ticker) => {
        if (document.hidden) return;
        director.current?.tick(ticker.deltaMS);
        elapsed += ticker.deltaMS / 1000;
        const scale = camera.current.scale;
        for (const visual of animations.current) {
          if (visual.node.label === "march" && !motion.matches && !latest.current.paused) visual.animate(elapsed);
          const x = visual.node.x * scale + a.screen.width / 2 + camera.current.x;
          const y = visual.node.y * scale + a.screen.height * .5 + camera.current.y;
          const visible = x > -100 && x < a.screen.width + 100 && y > -30 && y < a.screen.height + 100;
          visual.node.visible = visible;
          if (visible && scale > .6 && !latest.current.paused && !motion.matches) visual.animate(elapsed);
        }
      });
      setReady(true);
      const pointers = new globalThis.Map<number, { x: number; y: number }>();
      let start = { x: 0, y: 0 };
      let traveled = 0;
      let pinch = 0;
      const apply = () => {
        scene.current.position.set(
          a.screen.width / 2 + camera.current.x,
          a.screen.height * 0.5 + camera.current.y,
        );
        scene.current.scale.set(camera.current.scale);
      };
      const down = (e: PointerEvent) => {
        a.canvas.setPointerCapture(e.pointerId);
        pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
        start = { x: e.clientX, y: e.clientY };
        traveled = 0;
        if (pointers.size === 2) {
          const [p, q] = [...pointers.values()];
          pinch = Math.hypot(p.x - q.x, p.y - q.y);
        }
      };
      const move = (e: PointerEvent) => {
        const prev = pointers.get(e.pointerId);
        if (!prev) return;
        const dx = e.clientX - prev.x,
          dy = e.clientY - prev.y;
        pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
        traveled += Math.abs(dx) + Math.abs(dy);
        if (pointers.size === 2) {
          const [p, q] = [...pointers.values()];
          const d = Math.hypot(p.x - q.x, p.y - q.y);
          if (pinch)
            camera.current.scale = Math.max(
              0.45,
              Math.min(2.5, (camera.current.scale * d) / pinch),
            );
          pinch = d;
        } else {
          camera.current.x += dx;
          camera.current.y += dy;
        }
        apply();
      };
      const up = (e: PointerEvent) => {
        if (traveled < 8 && pointers.size === 1) {
          const rect = a.canvas.getBoundingClientRect();
          const x =
            (e.clientX - rect.left - a.screen.width / 2 - camera.current.x) /
            camera.current.scale;
          const y =
            (e.clientY - rect.top - a.screen.height * 0.5 - camera.current.y) /
            camera.current.scale;
          const rawR = y / (54 * 0.975);
          const rawQ = x / (54 * Math.sqrt(3)) - rawR / 2;
          let best = [0, 0],
            dist = Infinity;
          for (let q = Math.floor(rawQ) - 1; q <= Math.ceil(rawQ) + 1; q++)
            for (let r = Math.floor(rawR) - 1; r <= Math.ceil(rawR) + 1; r++) {
              const d =
                (q - rawQ) ** 2 + (r - rawR) ** 2 + (q + r - rawQ - rawR) ** 2;
              if (d < dist) {
                best = [q, r];
                dist = d;
              }
            }
          if (latest.current.battle) best = [best[0] + 4, best[1] + 4];
          if (latest.current.world) best = [best[0] + (latest.current.center?.[0] ?? 64), best[1] + (latest.current.center?.[1] ?? 64)];
          latest.current.onSelect(best[0], best[1]);
        }
        pointers.delete(e.pointerId);
        pinch = 0;
      };
      const wheel = (e: WheelEvent) => {
        e.preventDefault();
        camera.current.scale = Math.max(
          0.45,
          Math.min(2.5, camera.current.scale * Math.exp(-e.deltaY * 0.001)),
        );
        apply();
      };
      a.canvas.addEventListener("pointerdown", down);
      a.canvas.addEventListener("pointermove", move);
      a.canvas.addEventListener("pointerup", up);
      a.canvas.addEventListener("pointercancel", (e) =>
        pointers.delete(e.pointerId),
      );
      a.canvas.addEventListener("wheel", wheel, { passive: false });
      // Older Telegram/iOS ignore touch-action: stop the page and the app sheet
      // from moving while a finger drags the map.
      const hold = (e: TouchEvent) => e.preventDefault();
      a.canvas.addEventListener("touchmove", hold, { passive: false });
      a.canvas.addEventListener("touchstart", hold, { passive: false });
      const resize = new ResizeObserver(apply);
      resize.observe(host.current!);
      apply();
      const visible = () => (document.hidden ? a.stop() : a.start());
      document.addEventListener("visibilitychange", visible);
      cleanup = () => {
        resize.disconnect();
        document.removeEventListener("visibilitychange", visible);
        a.destroy(true, { children: true });
      };
    })().catch((e) => setError("Не удалось открыть WebGL: " + e.message));
    return () => {
      alive = false;
      cleanup();
      app.current = null;
    };
  }, []);
  // Snapshots arrive frequently; rebuild geometry only when renderable state changes.
  const geometryKey = JSON.stringify([props.buildings, props.battle, props.world, props.armies, props.center, props.route, textures]);
  useEffect(() => (props.world ? preloadWorld(() => setTextures((n) => n + 1)) : undefined), [props.world ? 1 : 0]);
  useEffect(() => {
    if (!ready || !app.current) return;
    const s = scene.current;
    if (selection.current.parent) selection.current.removeFromParent();
    if (director.current) { director.current.skip(); director.current = null; }
    s.removeChildren().forEach((c) => c.destroy({ children: true }));
    animations.current = [];
    units.current = new globalThis.Map();
    const ground = new Container();
    const labels = new Container();
    s.addChild(ground);
    const tiles: Tile[] = props.world
      ? props.world.map((t) => ({ ...t, q: t.q - (props.center?.[0] ?? 64), r: t.r - (props.center?.[1] ?? 64) }))
      : [];
    if (!props.world)
      for (let q = -4; q <= 4; q++)
        for (let r = -4; r <= 4; r++)
          if (
            props.battle ||
            Math.max(Math.abs(q), Math.abs(r), Math.abs(q + r)) <= 4
          )
            tiles.push({
              q,
              r,
              biome: props.battle?.state.terrain === "sea" ? "sea" : (q * 7 + r * 3) % 7 === 0 ? "forest" : "plain",
            });
    tiles.sort((a, b) => a.r - b.r || a.q - b.q);
    for (const t of tiles) {
      const x = 54 * Math.sqrt(3) * (t.q + t.r / 2),
        y = 54 * 0.975 * t.r;
      const g = new Graphics();
      hex(g, x, WATER.has(t.biome) ? y + 4 : y + 9, 52, sides[t.biome] ?? 0x263a36);
      hex(g, x, y, 52, colors[t.biome]);
      if (t.biome !== "unknown") {
        const rim: number[] = [];
        for (let i = 0; i < 6; i++) { const a = ((i * 60 + 30) * Math.PI) / 180; rim.push(x + Math.cos(a) * 52, y + Math.sin(a) * 52 * 0.65); }
        g.poly(rim).stroke({ color: 0x1b201e, width: 1.4, alpha: 0.55 });
        hex(g, x, y - 1, 44, colors[t.biome] + 0x0a0a06);
      }
      if (t.visibility === "explored") g.alpha = .55;
      ground.addChild(g);
      if(t.visibility!=="unknown")ground.addChild(surface(x,y,t.biome,t.q+(props.center?.[0]??0),t.r+(props.center?.[1]??0)));
      if (t.control === "self" || t.control === "other" || t.control === "ally" || t.home || t.base) {
        const border = new Graphics();
        hex(border,x,y,48,t.home ? 0xe5b65a : t.base === "ally" || t.control === "ally" ? 0x64b87b : t.base === "other" ? 0xd95a52 : t.base === "staging" ? 0xa7aeb5 : t.control === "self" ? 0x4c9ce5 : 0xd95a52);
        border.alpha=.3;ground.addChild(border);
        if (t.control === "self" && t.supplied === false) {
          // Cut off from the base: red rim and a broken-chain mark.
          const cut = new Graphics(); hex(cut,x,y,46,0xd95a52); cut.alpha=.22; ground.addChild(cut);
          const mark = new Text({text:"⛓",style:{fontSize:15,fill:0xffb4a0,fontFamily:"sans-serif"}});
          mark.anchor.set(.5); mark.position.set(x+26,y-22); labels.addChild(mark);
        }
      }
      const owner = t.control === "self" ? 0x4c9ce5 : t.control === "ally" ? 0x64b87b : t.control === "other" ? 0xd95a52 : null;
      if (t.base && props.world && t.visibility !== "unknown") {
        const fort = worldObject("base", x, y, 88, t.home ? 0xe5b65a : t.base === "ally" ? 0x64b87b : 0xd95a52);
        if (fort) s.addChild(fort);
      }
      if (t.node && t.visibility !== "unknown") {
        s.addChild(worldObject(t.node.kind, x, y, t.node.kind === "capital" ? 100 : 84, owner) ?? node(x, y - 6, t.node.kind, owner));
      }
      if (t.garrison) {
        if (t.biome === "sea") {
          const art = worldObject("pirates", x, y);
          if (art) s.addChild(art); else { const p = pirateShip(); p.position.set(x, y + 6); s.addChild(p); }
        }
        else if (!t.node) s.addChild(worldObject("bunker", x, y, 76) ?? bunker(x,y-7));
        const tag = t.garrison_strength ? `⚑ ${t.garrison_strength.hp}` : "⚑";
        const badge = new Text({text:tag,style:{fontSize:13,fill:0xffb4a0,fontFamily:"sans-serif",fontWeight:"bold"}});
        badge.anchor.set(.5);badge.position.set(x,y+20);
        const w = Math.max(60, badge.width + 14);
        labels.addChild(new Graphics().roundRect(x-w/2,y+8,w,24,5).fill(0x382126));labels.addChild(badge);
      }
      if (t.object) {
        const o = t.object;
        const mineFlag = o.owner === "self" ? 0x4c9ce5 : o.owner === "other" ? 0xd95a52 : null;
        const art = worldObject(o.kind, x, y, o.kind === "chest" ? 56 : o.kind === "pile" ? 64 : 76, o.kind === "mine" ? mineFlag : null);
        if (art) s.addChild(art);
        else if (o.kind === "pile") s.addChild(pile(x,y-6,o.resource ?? ""));
        else if (o.kind === "chest") s.addChild(chest(x,y-8));
        else if (o.kind === "mine") s.addChild(mine(x,y-6,o.resource ?? "",mineFlag));
        else if (o.kind === "ruin") s.addChild(ruin(x,y-6));
        else if (o.kind === "camp") s.addChild(camp(x,y-6,(o as {available?:boolean}).available !== false));
      }
      const b = props.buildings.find((b) => b.q === t.q && b.r === t.r);
      if (b && !props.battle && !props.world) {
        // Raster diorama art once loaded (scaffolding stays code-drawn while under construction).
        const url = `/art/buildings/${b.kind}.png`;
        const tex = b.status !== "building" && Assets.cache.has(url) ? (Assets.cache.get(url) as Texture) : null;
        if (tex) {
          const node = new Container();
          const img = new Sprite(tex);
          img.anchor.set(0.5, BUILDING_ANCHOR);
          img.scale.set(BUILDING_WIDTH / tex.width);
          node.addChild(img);
          node.position.set(x, y);
          s.addChild(node);
          // A slow, subtle breathing so the base feels alive.
          const phase = (t.q * 1.3 + t.r * 2.1) % 6.28;
          animations.current.push({ node, animate: (sec) => { img.scale.y = (BUILDING_WIDTH / tex.width) * (1 + Math.sin(sec * 1.4 + phase) * 0.006); } });
        } else {
          const visual = createBuilding(b);
          visual.node.position.set(x, y);
          s.addChild(visual.node);
          animations.current.push(visual);
          if (!failed.has(url) && !Assets.cache.has(url) && !loading.has(url)) {
            loading.add(url);   // load once; a cached texture must never re-trigger a rebuild
            Assets.load(url).then(() => setTextures((n) => n + 1)).catch(() => failed.add(url));
          }
        }
        // Compact level chip instead of a text label; the building sheet names it.
        const lvl = b.level + (b.upgrade_ready_at ? 0 : 0);
        const chip = new Text({ text: b.status === "building" ? "⏳" : b.upgrade_ready_at ? `${lvl}↑` : String(lvl),
          style: { fontSize: 11, fill: 0xf0f3f5, fontFamily: "sans-serif", fontWeight: "bold" } });
        chip.anchor.set(0.5);
        chip.position.set(x + 30, y + 14);
        labels.addChild(new Graphics().roundRect(x + 30 - Math.max(9, chip.width / 2 + 4), y + 6, Math.max(18, chip.width + 8), 16, 8)
          .fill({ color: 0x101923, alpha: .88 }).stroke({ color: 0xe5b65a, width: 1, alpha: .8 }));
        labels.addChild(chip);
      } else if (!props.battle && !t.garrison && !t.node && !(t as {object?:unknown}).object && t.biome!=="unknown" && !(props.world && t.base && worldReady())) {
        const wq=t.q+(props.center?.[0]??0), wr=t.r+(props.center?.[1]??0);
        const detail=(props.world && !t.base ? rasterEnvironment(x,y,t.biome,wq,wr) : null) ?? environment(x,y,t.biome,wq,wr);
        if(t.visibility==="explored")detail.alpha=.55;
        s.addChild(detail);
      }
      if (
        props.battle &&
        props.battle.state.cover.some(
          (c) => c[0] === t.q + 4 && c[1] === t.r + 4,
        )
      ) {
        const cover = new Graphics();
        tower(cover, x, y, 13, 22, 0x687665);
        s.addChild(cover);
      }
    }
    if (props.battle) {
      const per: Record<string, number> = {rifles:10,scouts:8,assault:14,artillery:12,armor:40};
      const legacyArt: Record<string, string> = {rifles:"rifleman",scouts:"scout",assault:"stormtrooper",artillery:"mortar",armor:"exosuit_drill"};
      for (const st of props.battle.state.stacks ?? []) {
        if (st.hp <= 0) continue;
        const q = st.pos[0] - 4, r = st.pos[1] - 4;
        const x = 54 * Math.sqrt(3) * (q + r / 2), y = 54 * 0.975 * r;
        const each = st.each ?? per[st.kind] ?? 10;
        if (st.id === props.battle.state.active) {
          const ring = new Graphics(); hex(ring,x,y,46,0xe5b65a); ring.alpha=.4; ground.addChild(ring);
        }
        // Raster sprite from /art/units/<kind>.png when loaded (owner art drops in here); code art otherwise.
        const url = `/art/units/${st.kind}.png`;
        const ratio = st.hp / (st.start * each);
        const sprite = unitSprite(st.art ?? legacyArt[st.kind], st.faction ?? undefined, st.side, ratio);
        const tex = Assets.cache.has(url) ? (Assets.cache.get(url) as Texture) : null;
        if (tex) {
          sprite.removeChildren(0, sprite.children.length - 1);   // keep only the health bar
          const img = new Sprite(tex);
          img.anchor.set(0.5, RASTER_FEET);
          img.scale.set(RASTER_SCALE * (st.side === "npc" ? -1 : 1), RASTER_SCALE);
          sprite.addChildAt(img, 0);
        } else if (!failed.has(url) && !loading.has(url)) {
          loading.add(url);
          Assets.load(url).then(() => setTextures((n) => n + 1)).catch(() => failed.add(url));
        }
        // One container per stack so playback can move, shake and fade it with its badge.
        const unit = new Container();
        unit.position.set(x, y + 8);
        sprite.scale.set(1.35);
        unit.addChild(sprite);
        const alive = Math.ceil(st.hp / each);
        const badge = new Text({text:String(alive),style:{fontSize:13,fill:0xf0f3f5,fontFamily:"sans-serif",fontWeight:"bold"}});
        badge.anchor.set(.5); badge.position.set(24,-28);
        unit.addChild(new Graphics().roundRect(12,-38,24,20,6).fill(st.side === "player" ? 0x1d4f7a : 0x6b2a27));
        unit.addChild(badge);
        s.addChild(unit);
        units.current.set(st.id, { node: unit, pos: [...st.pos], badge, count: alive, side: st.side, kind: st.kind, art: st.art });
        // Idle life: a gentle breathing bob, phase-shifted per stack.
        const phase = (st.pos[0] * 1.7 + st.pos[1] * 2.3) % 6.28;
        animations.current.push({ node: unit, animate: (t) => { sprite.y = Math.sin(t * 2.2 + phase) * 1.6; sprite.scale.y = 1.35 * (1 + Math.sin(t * 2.2 + phase) * 0.012); } });
      }
    }
    if (props.armies?.length && props.world) {
      const project = (q:number,r:number) => [54*Math.sqrt(3)*(q-(props.center?.[0]??64)+(r-(props.center?.[1]??64))/2),54*.975*(r-(props.center?.[1]??64))];
      // Inactive armies first so the active one is drawn on top.
      for (const {army, kinds, active} of [...props.armies].sort((a, b) => Number(a.active) - Number(b.active))) {
      const order = army.orders.find(o=>o.status === "moving");
      const [x,y]=project(army.q,army.r);
      const marker = new Container();marker.label="march";marker.position.set(x,y);
      const afloat = (props.world ?? []).some((t) => t.q === army.q && t.r === army.r && (t.biome === "sea" || t.biome === "lake"));
      // Lead stack's raster sprite (ship afloat, land unit ashore); code art until it loads.
      const lead = afloat ? kinds.find((k) => NAVAL_KINDS.has(k)) ?? "transport" : kinds.find((k) => !NAVAL_KINDS.has(k));
      const url = lead ? `/art/units/${lead}.png` : "";
      const tex = url && Assets.cache.has(url) ? (Assets.cache.get(url) as Texture) : null;
      const shadow = new Graphics().ellipse(0, 4, 30, 10).fill({ color: active ? 0xe5b65a : 0x4c9ce5, alpha: active ? .6 : .4 });
      if (active) shadow.stroke({ color: 0xffe2a0, width: 2, alpha: .9 });
      marker.addChild(shadow);
      if (tex) {
        const img = new Sprite(tex); img.anchor.set(0.5, RASTER_FEET); img.scale.set(RASTER_SCALE * 1.15);
        img.position.set(0, 6);
        marker.addChild(img);
      } else {
        marker.addChild(afloat ? unitSprite("boat_transport", undefined, "player", 1) : squad(0,0,0x4c9ce5));
        if (url && !failed.has(url) && !loading.has(url)) { loading.add(url); Assets.load(url).then(() => setTextures((n) => n + 1)).catch(() => failed.add(url)); }
      }
      // Number badge (gold with a star for the commander's army).
      const badge = new Container(); badge.position.set(22, -34);
      badge.addChild(new Graphics().circle(0, 0, 11).fill(army.commander ? 0xe5b65a : 0x1d4f7a).stroke({ color: 0x101923, width: 2 }));
      const num = new Text({ text: army.commander ? "★" : String(army.number), style: { fontSize: 12, fill: army.commander ? 0x101923 : 0xf0f3f5, fontFamily: "sans-serif", fontWeight: "bold" } });
      num.anchor.set(.5); badge.addChild(num); marker.addChild(badge);
      s.addChild(marker);
      if (order) {
        // Walk the server path hex by hex: [[q, r, arrive_at], ...] after the start hex.
        const steps = order.path?.length ? order.path : [[order.q, order.r, order.ready_at]];
        const points = [[order.from_q, order.from_r, order.started_at], ...steps].map(([q,r,t]) => [...project(q,r), t]);
        const line = new Graphics().moveTo(points[0][0],points[0][1]);
        points.slice(1).forEach(([px,py]) => line.lineTo(px,py));
        line.stroke({color:0xe5b65a,width:3,alpha:active ? .8 : .45}); ground.addChild(line);
        for (const [px,py] of points.slice(1)) ground.addChild(new Graphics().circle(px,py,5).fill({color:0xe5b65a,alpha:active ? .85 : .45}));
        animations.current.push({node:marker,animate:(t)=>{
          const now = latest.current.now ?? order.started_at;
          let i = 1; while (i < points.length - 1 && points[i][2] <= now) i++;
          const [ax,ay,at] = points[i-1], [bx,by,bt] = points[i];
          const k = Math.max(0, Math.min(1, (now - at) / Math.max(1, bt - at)));
          // Marching step: a small hop while the column is on the move.
          marker.position.set(ax+(bx-ax)*k, ay+(by-ay)*k - Math.abs(Math.sin(t*7))*3);
        }});
      }
      if (active && props.route?.length && !order) {
        const points = [[army.q, army.r], ...props.route].map(([q,r]) => project(q,r));
        const preview = new Graphics().moveTo(points[0][0], points[0][1]);
        points.slice(1).forEach(([px,py]) => preview.lineTo(px,py));
        preview.stroke({color:0x64b87b,width:3,alpha:.8}); ground.addChild(preview);
        let spent = 0;
        props.route.forEach(([,, cost], i) => {
          spent += cost;
          const [px,py] = points[i+1];
          ground.addChild(new Graphics().circle(px,py,11).fill({color:0x101923,alpha:.85}).stroke({color:0x64b87b,width:2}));
          const t = new Text({text:String(spent),style:{fontSize:12,fill:0xf0f3f5,fontFamily:"sans-serif",fontWeight:"bold"}});
          t.anchor.set(.5); t.position.set(px,py); labels.addChild(t);
        });
      }
      }
    }
    s.addChild(labels);
    fxLayer.current = new Container();
    s.addChild(fxLayer.current);
    s.addChild(selection.current);
  }, [ready, geometryKey]);
  // Battle playback: animate the server's events on top of the pre-command scene.
  useEffect(() => {
    const pb = props.playback;
    if (!ready || !pb || !props.battle || played.current === pb.key) return;
    played.current = pb.key;
    const d = new Director(fxLayer.current, units.current, props.unitInfo ?? {}, pb.speed);
    director.current = d;
    d.play(pb.events, () => { if (director.current === d) director.current = null; latest.current.onPlaybackDone?.(); });
  }, [ready, props.playback?.key, geometryKey]);
  useEffect(() => {
    const ring = selection.current;
    ring.clear();
    if (!ready || !props.selected) return;
    const offset = props.battle ? 4 : props.world ? 64 : 0;
    const q = props.selected[0] - (props.world ? (props.center?.[0] ?? 64) : offset), r = props.selected[1] - (props.world ? (props.center?.[1] ?? 64) : offset);
    const x = 54 * Math.sqrt(3) * (q+r/2), y = 54*.975*r;
    const points: number[]=[];
    for(let i=0;i<6;i++){const a=(i*60+30)*Math.PI/180;points.push(x+Math.cos(a)*49,y+Math.sin(a)*49*.65);}
    ring.poly(points).stroke({color:0xe5b65a,width:2});
  }, [ready, props.selected, !!props.battle, !!props.world, geometryKey]);
  return (
    <div className="map" ref={host}>
      {error && <p role="alert">{error}</p>}
      <div className="map-controls">
        <button
          aria-label="Центрировать карту"
          onClick={() => {
            camera.current = { ...home };
            if (app.current) {
              scene.current.position.set(
                app.current.screen.width / 2 + home.x,
                app.current.screen.height * 0.5 + home.y,
              );
              scene.current.scale.set(1);
            }
          }}
        >
          <Icon name="target"/>
        </button>
      </div>
      <div className="map-hint">ПЕРЕТАЩИТЕ КАРТУ · ДВА ПАЛЬЦА ДЛЯ МАСШТАБА</div>
    </div>
  );
}
