import {surface, environment, bunker, squad, pile, chest, mine} from "./Terrain";
import {Icon} from "./Icon";
import { useEffect, useRef, useState } from "react";
import { Application, Container, Graphics, Text } from "pixi.js";
import { createBuilding, type BuildingVisual } from "./Buildings";
import type { Building, Battle, Army } from "./store";
type Tile = { q: number; r: number; biome: string; control?: string | null; visibility?: string; home?: boolean; base?: string | null; garrison?: boolean; garrison_strength?: {name:string;hp:number} | null; object?: {kind:string;resource?:string;amount?:number;owner?:string|null;pending?:boolean} | null };
type Props = {
  buildings: Building[];
  paused?: boolean;
  battle?: Battle;
  world?: Tile[];
  center?: number[];
  army?: Army;
  route?: number[][] | null;
  now?: number;
  selected: number[] | null;
  onSelect: (q: number, r: number) => void;
};
const colors: Record<string, number> = {
  plain: 0x465c4a,
  forest: 0x304f43,
  hills: 0x6b7165,
  desert: 0x8a7c55,
  unknown: 0x1e2c37,
};
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
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const camera = useRef({ scale: 1, x: 0, y: 0 });
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
  const geometryKey = JSON.stringify([props.buildings, props.battle, props.world, props.army, props.center, props.route]);
  useEffect(() => {
    if (!ready || !app.current) return;
    const s = scene.current;
    if (selection.current.parent) selection.current.removeFromParent();
    s.removeChildren().forEach((c) => c.destroy({ children: true }));
    animations.current = [];
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
              biome: (q * 7 + r * 3) % 7 === 0 ? "forest" : "plain",
            });
    tiles.sort((a, b) => a.r - b.r || a.q - b.q);
    for (const t of tiles) {
      const x = 54 * Math.sqrt(3) * (t.q + t.r / 2),
        y = 54 * 0.975 * t.r;
      const g = new Graphics();
      hex(g, x, y + 7, 53, 0x263a36);
      hex(g, x, y, 52, colors[t.biome]);
      if (t.visibility === "explored") g.alpha = .55;
      ground.addChild(g);
      if(t.visibility!=="unknown")ground.addChild(surface(x,y,t.biome,t.q+(props.center?.[0]??0),t.r+(props.center?.[1]??0)));
      if (t.control === "self" || t.control === "other" || t.home || t.base) {
        const border = new Graphics();
        hex(border,x,y,48,t.home ? 0xe5b65a : t.base === "other" ? 0xd95a52 : t.base === "staging" ? 0xa7aeb5 : t.control === "self" ? 0x4c9ce5 : 0xd95a52);
        border.alpha=.3;ground.addChild(border);
      }
      if (t.garrison) {
        s.addChild(bunker(x,y-7));
        const tag = t.garrison_strength ? `⚑ ${t.garrison_strength.name} ${t.garrison_strength.hp}` : "⚑ NPC";
        const badge = new Text({text:tag,style:{fontSize:13,fill:0xffb4a0,fontFamily:"sans-serif",fontWeight:"bold"}});
        badge.anchor.set(.5);badge.position.set(x,y+20);
        const w = Math.max(60, badge.width + 14);
        labels.addChild(new Graphics().roundRect(x-w/2,y+8,w,24,5).fill(0x382126));labels.addChild(badge);
      }
      if (t.object) {
        const o = t.object;
        if (o.kind === "pile") s.addChild(pile(x,y-6,o.resource ?? ""));
        else if (o.kind === "chest") s.addChild(chest(x,y-8));
        else if (o.kind === "mine") s.addChild(mine(x,y-6,o.resource ?? "",o.owner === "self" ? 0x4c9ce5 : o.owner === "other" ? 0xd95a52 : null));
      }
      const b = props.buildings.find((b) => b.q === t.q && b.r === t.r);
      if (b && !props.battle && !props.world) {
        const visual = createBuilding(b);
        visual.node.position.set(x,y);
        s.addChild(visual.node);
        animations.current.push(visual);
        const label = new Text({
          text: (
            {
              hq: "ШТАБ",
              power: "ЭНЕРГИЯ",
              quarry: "КАРЬЕР",
              barracks: "КАЗАРМЫ",
              refinery: "НПЗ",
              oil_well: "НЕФТЬ",
              farm: "АГРО",
              warehouse: "СКЛАД",
              watchtower: "БАШНЯ",
              electronics: "ЭЛЕКТРОНИКА",
              repair: "РЕМОНТ",
            } as Record<string, string>
          )[b.kind],
          style: {
            fontSize: 11,
            fill: 0xe7efea,
            fontFamily: "sans-serif",
            letterSpacing: .5,
          },
        });
        label.anchor.set(0.5);
        label.position.set(x, y + 29);
        const plate = new Graphics().roundRect(x-label.width/2-6,y+21,label.width+12,17,3).fill({color:0x101923,alpha:.9});
        labels.addChild(plate);
        labels.addChild(label);
      } else if (!props.battle && !t.garrison && t.biome!=="unknown") {
        const detail=environment(x,y,t.biome,t.q+(props.center?.[0]??0),t.r+(props.center?.[1]??0));
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
      for (const [key, color] of [
        ["player", 0x4c9ce5],
        ["npc", 0xd95a52],
      ] as const) {
        const unit = props.battle.state[key];
        const q = unit.pos[0] - 4,
          r = unit.pos[1] - 4,
          x = 54 * Math.sqrt(3) * (q + r / 2),
          y = 54 * 0.975 * r;
        s.addChild(squad(x,y,color,unit.hp));
      }
    }
    if (props.army && props.world) {
      const army = props.army;
      const order = army.orders.find(o=>o.status === "moving");
      const project = (q:number,r:number) => [54*Math.sqrt(3)*(q-(props.center?.[0]??64)+(r-(props.center?.[1]??64))/2),54*.975*(r-(props.center?.[1]??64))];
      const [x,y]=project(army.q,army.r);
      const marker = new Container();marker.label="march";marker.position.set(x,y);
      const flag = squad(0,0,0x4c9ce5);
      marker.addChild(flag);s.addChild(marker);
      if (order) {
        // Walk the server path hex by hex: [[q, r, arrive_at], ...] after the start hex.
        const steps = order.path?.length ? order.path : [[order.q, order.r, order.ready_at]];
        const points = [[order.from_q, order.from_r, order.started_at], ...steps].map(([q,r,t]) => [...project(q,r), t]);
        const line = new Graphics().moveTo(points[0][0],points[0][1]);
        points.slice(1).forEach(([px,py]) => line.lineTo(px,py));
        line.stroke({color:0xe5b65a,width:3,alpha:.75}); ground.addChild(line);
        for (const [px,py] of points.slice(1)) ground.addChild(new Graphics().circle(px,py,5).fill({color:0xe5b65a,alpha:.85}));
        animations.current.push({node:marker,animate:()=>{
          const now = latest.current.now ?? order.started_at;
          let i = 1; while (i < points.length - 1 && points[i][2] <= now) i++;
          const [ax,ay,at] = points[i-1], [bx,by,bt] = points[i];
          const k = Math.max(0, Math.min(1, (now - at) / Math.max(1, bt - at)));
          marker.position.set(ax+(bx-ax)*k, ay+(by-ay)*k);
        }});
      }
      if (props.route?.length && !order) {
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
    s.addChild(labels);
    s.addChild(selection.current);
  }, [ready, geometryKey]);
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
            camera.current = { scale: 1, x: 0, y: 0 };
            if (app.current) {
              scene.current.position.set(
                app.current.screen.width / 2,
                app.current.screen.height * 0.5,
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
