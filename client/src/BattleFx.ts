// Battle playback: turns server battle events into short Pixi animations.
// The scene shows the state *before* the command; the director plays the
// events in order (moves, shots, hits, deaths...), then the caller swaps in
// the new state. Everything here is original procedural art.
import { Container, Graphics, Text } from "pixi.js";

export type BattleEvent = { type: string; actor?: string; target?: string; pos?: number[]; damage?: number; kills?: number;
  amount?: number; name?: string; round?: number };
export type UnitHandle = { node: Container; pos: number[]; badge?: Text; count: number; side: string; kind: string; art?: string | null };
export type UnitInfo = Record<string, { melee?: boolean; art?: string }>;
type Fx = { update: (ms: number) => boolean };   // returns true when finished

const SQ3 = Math.sqrt(3);
export const hexXY = (pos: number[]) => [54 * SQ3 * (pos[0] - 4 + (pos[1] - 4) / 2), 54 * 0.975 * (pos[1] - 4) + 8];
const dist = (a: number[], b: number[]) => Math.max(Math.abs(a[0] - b[0]), Math.abs(a[1] - b[1]), Math.abs(a[0] + a[1] - b[0] - b[1]));
const SHELL = new Set(["mortar", "field_gun", "spg", "walker_tank", "exosuit_cannon", "gunboat", "howitzer"]);
const LIGHTNING = new Set(["tesla"]);
const ease = (t: number) => 1 - Math.pow(1 - t, 3);

export class Director {
  private fx: Fx[] = [];
  private queue: BattleEvent[] = [];
  private wait = 0;
  private done?: () => void;
  constructor(private layer: Container, private units: Map<string, UnitHandle>, private info: UnitInfo, private speed = 1) {}

  play(events: BattleEvent[], done: () => void) {
    this.queue = events.filter((e) => e.type !== "round" || this.speed === 1);
    this.done = done;
    this.wait = 120;
  }

  skip() { this.queue = []; this.fx = []; this.wait = 0; this.finish(); }

  private finish() { const d = this.done; this.done = undefined; d?.(); }

  tick(deltaMS: number) {
    const ms = deltaMS * this.speed;
    this.fx = this.fx.filter((f) => !f.update(ms));
    if (!this.done) return;
    this.wait -= ms;
    if (this.wait > 0) return;
    const next = this.queue.shift();
    if (!next) {
      if (!this.fx.length) this.finish();
      return;
    }
    this.wait = this.step(next);
  }

  private add(f: Fx) { this.fx.push(f); }

  private step(e: BattleEvent): number {
    const actor = e.actor ? this.units.get(e.actor) : undefined;
    const target = e.target ? this.units.get(e.target) : undefined;
    switch (e.type) {
      case "move": {
        if (!actor || !e.pos) return 0;
        const from = hexXY(actor.pos), to = hexXY(e.pos);
        actor.pos = e.pos;
        this.add(tween(actor.node, from, to, 380, 10));
        this.add(dust(this.layer, from[0], from[1] + 6));
        return 400;
      }
      case "attack": case "retaliate": case "splash": {
        if (!actor || !target) return 0;
        return this.strike(actor, target, e);
      }
      case "destroyed": {
        if (!actor) return 0;
        const [x, y] = hexXY(actor.pos);
        this.add(fadeOut(actor.node, 450));
        this.add(smoke(this.layer, x, y - 20, 0x5b5f60, 34));
        return 380;
      }
      case "heal": {
        const who = target ?? actor;
        if (!who) return 0;
        const [x, y] = hexXY(who.pos);
        this.add(sparkles(this.layer, x, y - 30, 0x64d48a));
        this.add(popup(this.layer, `+${e.amount ?? ""}`, x, y - 58, 0x7fe0a0));
        return 520;
      }
      case "defend": {
        if (!actor) return 0;
        const [x, y] = hexXY(actor.pos);
        this.add(shield(this.layer, x, y - 30));
        return 360;
      }
      case "skill": case "ability": {
        if (!actor) return 0;
        const [x, y] = hexXY(actor.pos);
        this.add(banner(this.layer, `${e.type === "ability" ? "★" : "◆"} ${e.name ?? ""}`, x, y - 96, e.type === "ability" ? 0xe5b65a : 0x9fd0ff));
        this.add(glow(actor.node, e.type === "ability" ? 0xe5b65a : 0x5f8fd0));
        return 620;
      }
      case "luck": case "morale": {
        if (!actor) return 0;
        const [x, y] = hexXY(actor.pos);
        this.add(banner(this.layer, e.type === "luck" ? "🍀 Удача!" : "🎺 Боевой дух!", x, y - 96, 0x7fd6a0));
        return 480;
      }
      case "jammed": case "jam": case "suppress": case "mark": {
        const who = target ?? actor;
        if (!who) return 0;
        const [x, y] = hexXY(who.pos);
        const label = { jammed: "⚡ Помехи", jam: "⚡ Глушение", suppress: "⛔ Подавлен", mark: "🎯 Цель" }[e.type] ?? "";
        this.add(banner(this.layer, label, x, y - 90, 0xffb4a0));
        if (e.type !== "jammed" && actor && target) this.add(lightning(this.layer, hexXY(actor.pos), hexXY(target.pos), 0x9fd0ff));
        return 420;
      }
      case "round":
        this.add(banner(this.layer, `Раунд ${e.round}`, 0, -230, 0xf0f3f5, 26));
        return 420;
      case "wait":
        return 120;
      default:
        return 60;
    }
  }

  private strike(a: UnitHandle, t: UnitHandle, e: BattleEvent): number {
    const from = hexXY(a.pos), to = hexXY(t.pos);
    const art = a.art ?? this.info[a.kind]?.art ?? "";
    const melee = !!this.info[a.kind]?.melee && dist(a.pos, t.pos) === 1 && e.type !== "splash";
    let impactAt: number;
    if (e.type === "splash") {
      impactAt = 0;
    } else if (melee) {
      this.add(lunge(a.node, from, to, 260));
      impactAt = 130;
    } else if (SHELL.has(art)) {
      this.add(recoil(a.node, from, to));
      this.add(muzzle(this.layer, from, to, 1.6));
      this.add(shell(this.layer, from, to, 440));
      impactAt = 440;
    } else if (LIGHTNING.has(art)) {
      this.add(lightning(this.layer, [from[0], from[1] - 40], [to[0], to[1] - 30], 0x7fe8ff));
      impactAt = 120;
    } else {
      this.add(recoil(a.node, from, to));
      this.add(muzzle(this.layer, from, to, 1));
      for (let i = 0; i < 3; i++) this.add(delay(i * 70, () => tracer(this.layer, from, to)));
      impactAt = 220;
    }
    this.add(delay(impactAt, () => {
      const big = e.type === "splash" || SHELL.has(art);
      return all([
        shake(t.node, to, big ? 9 : 5),
        flash(t.node),
        big ? explosion(this.layer, to[0], to[1] - 24) : melee ? slash(this.layer, to[0], to[1] - 34) : sparks(this.layer, to[0], to[1] - 30),
        popup(this.layer, `-${e.damage ?? 0}`, to[0] + (e.type === "splash" ? 10 : 0), to[1] - 58,
              e.type === "retaliate" ? 0xffd27a : 0xff8a7a),
      ]);
    }));
    this.add(delay(impactAt + 60, () => {
      t.count = Math.max(0, t.count - (e.kills ?? 0));
      if (t.badge) t.badge.text = String(t.count);
      return null;
    }));
    return impactAt + (e.type === "splash" ? 260 : 420);
  }
}

// ---- primitives -------------------------------------------------------------

function delay(ms: number, make: () => Fx | null): Fx {
  let t = 0, inner: Fx | null = null, started = false;
  return { update(dt) {
    t += dt;
    if (!started && t >= ms) { started = true; inner = make(); }
    return started && (!inner || inner.update(dt));
  } };
}

function all(list: Fx[]): Fx {
  let rest = list;
  return { update(dt) { rest = rest.filter((f) => !f.update(dt)); return !rest.length; } };
}

function tween(node: Container, from: number[], to: number[], ms: number, hop: number): Fx {
  let t = 0;
  return { update(dt) {
    t = Math.min(ms, t + dt);
    const k = ease(t / ms);
    node.position.set(from[0] + (to[0] - from[0]) * k, from[1] + (to[1] - from[1]) * k - Math.sin(Math.PI * k) * hop
      - Math.abs(Math.sin(k * Math.PI * 4)) * 3);
    return t >= ms;
  } };
}

function lunge(node: Container, from: number[], to: number[], ms: number): Fx {
  let t = 0;
  return { update(dt) {
    t = Math.min(ms, t + dt);
    const k = Math.sin(Math.PI * t / ms) * 0.42;
    node.position.set(from[0] + (to[0] - from[0]) * k, from[1] + (to[1] - from[1]) * k - k * 10);
    return t >= ms;
  } };
}

function recoil(node: Container, from: number[], to: number[]): Fx {
  const len = Math.hypot(to[0] - from[0], to[1] - from[1]) || 1;
  const dx = (from[0] - to[0]) / len * 6, dy = (from[1] - to[1]) / len * 6;
  let t = 0;
  return { update(dt) {
    t = Math.min(160, t + dt);
    const k = Math.sin(Math.PI * t / 160);
    node.position.set(from[0] + dx * k, from[1] + dy * k);
    return t >= 160;
  } };
}

function shake(node: Container, at: number[], power: number): Fx {
  let t = 0;
  return { update(dt) {
    t = Math.min(260, t + dt);
    const k = 1 - t / 260;
    node.position.set(at[0] + Math.sin(t / 18) * power * k, at[1] + Math.cos(t / 23) * power * 0.4 * k);
    return t >= 260;
  } };
}

function flash(node: Container): Fx {
  let t = 0;
  return { update(dt) {
    t += dt;
    node.alpha = t < 240 ? (Math.floor(t / 60) % 2 ? 0.45 : 1) : 1;
    return t >= 240;
  } };
}

function fadeOut(node: Container, ms: number): Fx {
  let t = 0;
  const y0 = node.y;
  return { update(dt) {
    t = Math.min(ms, t + dt);
    node.alpha = 1 - t / ms;
    node.y = y0 + (t / ms) * 12;
    return t >= ms;
  } };
}

function glow(node: Container, color: number): Fx {
  const ring = new Graphics().ellipse(0, -2, 38, 13).stroke({ color, width: 3 });
  node.addChildAt(ring, 0);
  let t = 0;
  return { update(dt) {
    t += dt;
    ring.alpha = 1 - t / 600;
    ring.scale.set(1 + t / 900);
    if (t >= 600) { ring.destroy(); return true; }
    return false;
  } };
}

function own(layer: Container, g: Container, ms: number, step: (k: number) => void): Fx {
  layer.addChild(g);
  let t = 0;
  return { update(dt) {
    t = Math.min(ms, t + dt);
    step(t / ms);
    if (t >= ms) { g.destroy({ children: true }); return true; }
    return false;
  } };
}

function muzzle(layer: Container, from: number[], to: number[], size: number): Fx {
  const ang = Math.atan2(to[1] - from[1], to[0] - from[0]);
  const x = from[0] + Math.cos(ang) * 26, y = from[1] - 34 + Math.sin(ang) * 10;
  const g = new Graphics();
  const pts: number[] = [];
  for (let i = 0; i < 10; i++) {
    const r = (i % 2 ? 5 : 13) * size, a = ang + (i / 10) * Math.PI * 2;
    pts.push(Math.cos(a) * r, Math.sin(a) * r);
  }
  g.poly(pts).fill(0xffe08a).stroke({ color: 0xff9a3c, width: 1.5 });
  g.position.set(x, y);
  return own(layer, g, 140, (k) => { g.alpha = 1 - k; g.scale.set(1 + k * 0.6); });
}

function tracer(layer: Container, from: number[], to: number[]): Fx {
  const g = new Graphics().moveTo(0, 0).lineTo(16, 0).stroke({ color: 0xffe9a8, width: 2.5 });
  const sx = from[0], sy = from[1] - 34, ex = to[0] + (Math.random() - .5) * 18, ey = to[1] - 30 + (Math.random() - .5) * 14;
  g.rotation = Math.atan2(ey - sy, ex - sx);
  return own(layer, g, 150, (k) => g.position.set(sx + (ex - sx) * k, sy + (ey - sy) * k));
}

function shell(layer: Container, from: number[], to: number[], ms: number): Fx {
  const g = new Graphics().circle(0, 0, 5).fill(0x2a2a28).stroke({ color: 0xffd27a, width: 1.5 });
  const sx = from[0], sy = from[1] - 40, ex = to[0], ey = to[1] - 24;
  const arc = 34 + Math.hypot(ex - sx, ey - sy) * 0.12;   // keep the shell on screen
  return own(layer, g, ms, (k) => g.position.set(sx + (ex - sx) * k, sy + (ey - sy) * k - Math.sin(Math.PI * k) * arc));
}

function lightning(layer: Container, from: number[], to: number[], color: number): Fx {
  const g = new Graphics();
  const draw = () => {
    g.clear().moveTo(from[0], from[1]);
    for (let i = 1; i < 7; i++) {
      const k = i / 7;
      g.lineTo(from[0] + (to[0] - from[0]) * k + (Math.random() - .5) * 18, from[1] + (to[1] - from[1]) * k + (Math.random() - .5) * 18);
    }
    g.lineTo(to[0], to[1]).stroke({ color, width: 3 }).stroke({ color: 0xffffff, width: 1, alpha: .8 });
  };
  draw();
  return own(layer, g, 260, (k) => { if (Math.random() < .5) draw(); g.alpha = 1 - k * .7; });
}

function explosion(layer: Container, x: number, y: number): Fx {
  const g = new Container();
  const core = new Graphics().circle(0, 0, 14).fill(0xffd27a);
  const ring = new Graphics().circle(0, 0, 18).fill({ color: 0xff7a3c, alpha: .8 });
  const smokeBall = new Graphics().circle(0, -6, 20).fill({ color: 0x4a4d4e, alpha: .6 });
  g.addChild(smokeBall, ring, core);
  g.position.set(x, y);
  return own(layer, g, 520, (k) => {
    core.scale.set(1 + k * 1.2); core.alpha = 1 - k * 1.6;
    ring.scale.set(1 + k * 2); ring.alpha = .8 * (1 - k);
    smokeBall.scale.set(1 + k * 1.6); smokeBall.y = -6 - k * 22; smokeBall.alpha = .6 * (1 - k);
  });
}

function sparks(layer: Container, x: number, y: number): Fx {
  const g = new Container();
  const bits = Array.from({ length: 6 }, (_, i) => {
    const b = new Graphics().circle(0, 0, 2.2).fill(0xffe08a);
    const a = (i / 6) * Math.PI * 2 + Math.random();
    g.addChild(b);
    return { b, vx: Math.cos(a) * 30, vy: Math.sin(a) * 22 - 10 };
  });
  g.position.set(x, y);
  return own(layer, g, 300, (k) => bits.forEach(({ b, vx, vy }) => { b.position.set(vx * k, vy * k + 20 * k * k); b.alpha = 1 - k; }));
}

function slash(layer: Container, x: number, y: number): Fx {
  const g = new Graphics()
    .arc(0, 0, 22, -2.4, -0.6).stroke({ color: 0xffffff, width: 3 })
    .arc(4, 6, 18, -2.2, -0.8).stroke({ color: 0xffd8c8, width: 2 });
  g.position.set(x, y);
  return own(layer, g, 240, (k) => { g.alpha = 1 - k; g.rotation = k * 0.5; g.scale.set(1 + k * .3); });
}

function dust(layer: Container, x: number, y: number): Fx {
  return smoke(layer, x, y, 0xb9a67c, 14);
}

function smoke(layer: Container, x: number, y: number, color: number, size: number): Fx {
  const g = new Graphics().circle(-size * .4, 0, size * .6).circle(size * .4, -size * .2, size * .5).fill({ color, alpha: .55 });
  g.position.set(x, y);
  return own(layer, g, 600, (k) => { g.scale.set(1 + k); g.alpha = .9 * (1 - k); g.y = y - k * 16; });
}

function sparkles(layer: Container, x: number, y: number, color: number): Fx {
  const g = new Container();
  const pluses = Array.from({ length: 5 }, (_, i) => {
    const p = new Graphics().rect(-1.5, -5, 3, 10).rect(-5, -1.5, 10, 3).fill(color);
    p.position.set((i - 2) * 12, 0);
    g.addChild(p);
    return p;
  });
  g.position.set(x, y);
  return own(layer, g, 560, (k) => pluses.forEach((p, i) => { p.y = -k * (24 + i * 4); p.alpha = 1 - k; }));
}

function shield(layer: Container, x: number, y: number): Fx {
  const g = new Graphics().poly([0, -18, 16, -10, 14, 8, 0, 18, -14, 8, -16, -10]).fill({ color: 0x5f8fd0, alpha: .55 })
    .stroke({ color: 0xbfd8ff, width: 2 });
  g.position.set(x, y);
  return own(layer, g, 420, (k) => { g.scale.set(.6 + k * .6); g.alpha = 1 - k * k; });
}

function popup(layer: Container, text: string, x: number, y: number, color: number): Fx {
  const t = new Text({ text, style: { fontSize: 22, fill: color, fontFamily: "sans-serif", fontWeight: "bold",
    stroke: { color: 0x101923, width: 4 } } });
  t.anchor.set(.5);
  t.position.set(x, y);
  return own(layer, t, 820, (k) => { t.y = y - k * 34; t.alpha = k < .7 ? 1 : 1 - (k - .7) / .3; t.scale.set(k < .15 ? .7 + k * 2 : 1); });
}

function banner(layer: Container, text: string, x: number, y: number, color: number, size = 17): Fx {
  const t = new Text({ text, style: { fontSize: size, fill: color, fontFamily: "sans-serif", fontWeight: "bold",
    stroke: { color: 0x101923, width: 4 } } });
  t.anchor.set(.5);
  t.position.set(x, y);
  return own(layer, t, 900, (k) => { t.y = y - k * 14; t.alpha = k < .8 ? 1 : 1 - (k - .8) / .2; });
}
