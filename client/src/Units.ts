import { Container, Graphics } from "pixi.js";

/*
 * Original code-drawn unit art for IRON FRONT: chunky chibi dieselpunk soldiers
 * and machines with a dark ink outline. Feet sit on (0, 0); a figure is ~44px tall.
 * Nothing here is traced or copied from reference images — shapes are built from
 * primitives so every faction can share parts and differ by silhouette and accent.
 */

export const ACCENTS: Record<string, number> = {
  raven: 0xc8433a, valkyrie: 0x5f8fd0, titan: 0xc9a04a,
  phoenix: 0xd9783a, ghost: 0x3fb7a8, storm: 0xa3b34a, npc: 0x8f4a44,
};

const INK = 0x1b201e;
const OLIVE = 0x6f7655, OLIVE_D = 0x4e5540, OLIVE_L = 0x8e9470;
const STEEL = 0x8a8f86, STEEL_D = 0x5c625d, STEEL_L = 0xb6b9ad;
const BRASS = 0xc8a25a, SKIN = 0xd9b48f, LEATHER = 0x5a4632;
const line = { color: INK, width: 1.6, alignment: 0.5 } as const;

type Kit = {
  helmet?: "brodie" | "cap" | "beret" | "goggles" | "nurse" | "hood";
  mask?: boolean;
  tool?: "rifle" | "smg" | "blade" | "wrench" | "kit" | "binoculars" | "shield" | "longrifle" | "none";
  pack?: boolean;
  kneel?: boolean;
};

function shadow(g: Graphics, w: number, x = 0, y = 0) {
  g.ellipse(x + 2, y + 2, w, w * 0.36).fill({ color: 0x0a1210, alpha: 0.35 });
}

/** One chibi soldier; big head, short body, helmet and mask from the kit. */
function soldier(g: Graphics, x: number, y: number, accent: number, kit: Kit, flip = 1) {
  const s = flip;
  const k = kit.kneel ? 5 : 0;
  shadow(g, 9, x, y);
  // Legs and boots.
  if (!kit.kneel) {
    g.roundRect(x - 5, y - 10, 4, 9, 1.5).fill(OLIVE_D).stroke(line);
    g.roundRect(x + 1, y - 10, 4, 9, 1.5).fill(OLIVE_D).stroke(line);
  } else {
    g.roundRect(x - 6, y - 5, 10, 4, 1.5).fill(OLIVE_D).stroke(line);
  }
  g.roundRect(x - 6, y - 3, 5, 3, 1).fill(LEATHER).stroke(line);
  g.roundRect(x + 1, y - 3, 5, 3, 1).fill(LEATHER).stroke(line);
  // Backpack and canister.
  if (kit.pack !== false) {
    g.roundRect(x - 10 * s - (s < 0 ? -2 : 0), y - 23 + k, 7, 11, 2).fill(STEEL_D).stroke(line);
    g.roundRect(x - 9 * s - (s < 0 ? -2 : 0), y - 28 + k, 5, 6, 2).fill(STEEL).stroke(line);
  }
  // Tunic, belt, accent armband.
  g.roundRect(x - 7, y - 24 + k, 14, 15, 4).fill(OLIVE).stroke(line);
  g.rect(x - 7, y - 13 + k, 14, 2.5).fill(LEATHER);
  g.roundRect(x - 8 * s - (s < 0 ? 3 : 0), y - 21 + k, 4, 6, 1.5).fill(accent).stroke(line);
  // Head.
  const hy = y - 31 + k;
  if (kit.mask) {
    g.circle(x, hy, 7).fill(STEEL).stroke(line);
    g.circle(x - 2.8, hy - 1, 2).fill(0x2b3a3c).stroke({ color: INK, width: 1 });
    g.circle(x + 2.8, hy - 1, 2).fill(0x2b3a3c).stroke({ color: INK, width: 1 });
    g.roundRect(x - 2, hy + 3, 4, 4, 1.5).fill(STEEL_D).stroke({ color: INK, width: 1 });
  } else {
    g.circle(x, hy, 6.5).fill(SKIN).stroke(line);
    g.circle(x - 2.2, hy, 0.9).fill(INK);
    g.circle(x + 2.2, hy, 0.9).fill(INK);
  }
  // Headgear.
  switch (kit.helmet ?? "brodie") {
    case "brodie":
      g.ellipse(x, hy - 3, 11, 3.2).fill(OLIVE_D).stroke(line);
      g.ellipse(x, hy - 5, 7, 5).fill(OLIVE).stroke(line);
      break;
    case "cap":
      g.roundRect(x - 7, hy - 9, 14, 6, 2).fill(OLIVE_D).stroke(line);
      g.roundRect(x - 8, hy - 4, 10 * s + (s < 0 ? 6 : 0), 2.5, 1).fill(LEATHER);
      break;
    case "beret":
      g.ellipse(x - 1, hy - 6, 8, 3.6).fill(accent).stroke(line);
      break;
    case "goggles":
      g.ellipse(x, hy - 5, 7.5, 4.5).fill(LEATHER).stroke(line);
      g.circle(x - 3, hy - 4, 2).fill(BRASS).stroke({ color: INK, width: 1 });
      g.circle(x + 3, hy - 4, 2).fill(BRASS).stroke({ color: INK, width: 1 });
      break;
    case "nurse":
      g.roundRect(x - 7, hy - 9, 14, 5, 2).fill(0xe9e4d8).stroke(line);
      g.rect(x - 0.9, hy - 8.5, 1.8, 4).fill(0x4f9a63);
      g.rect(x - 2.2, hy - 7.2, 4.4, 1.6).fill(0x4f9a63);
      break;
    case "hood":
      g.ellipse(x, hy - 3, 8, 7).fill(0x4a4f45).stroke(line);
      break;
  }
  // Tool.
  const hx = x + 6 * s, hand = y - 17 + k;
  switch (kit.tool ?? "rifle") {
    case "rifle":
      g.moveTo(hx - 8 * s, hand + 3).lineTo(hx + 12 * s, hand - 3).stroke({ color: LEATHER, width: 3 });
      g.moveTo(hx + 12 * s, hand - 3).lineTo(hx + 19 * s, hand - 5).stroke({ color: STEEL_L, width: 1.5 });
      break;
    case "longrifle":
      g.moveTo(hx - 10 * s, hand + 2).lineTo(hx + 18 * s, hand - 2).stroke({ color: LEATHER, width: 3 });
      g.circle(hx + 4 * s, hand - 3, 1.8).fill(BRASS);
      break;
    case "smg":
      g.roundRect(hx - 3, hand - 3, 10 * s + (s < 0 ? 6 : 0), 4, 1).fill(STEEL_D).stroke(line);
      break;
    case "blade":
      g.moveTo(hx, hand).lineTo(hx + 7 * s, hand - 9).stroke({ color: STEEL_L, width: 2.5 });
      break;
    case "wrench":
      g.moveTo(hx, hand + 2).lineTo(hx + 4 * s, hand - 8).stroke({ color: STEEL_L, width: 2.5 });
      g.circle(hx + 4 * s, hand - 9, 2.2).stroke({ color: STEEL_L, width: 1.6 });
      break;
    case "kit":
      g.roundRect(hx - 2, hand - 1, 6, 6, 1.5).fill(0xe9e4d8).stroke(line);
      g.roundRect(hx + 2 * s, hand - 6, 3, 4, 1).fill(0x86d29a).stroke({ color: INK, width: 1 });
      break;
    case "binoculars":
      g.roundRect(x - 4, hy - 1, 8, 3.5, 1.5).fill(INK);
      break;
    case "shield":
      g.roundRect(hx - 2, hand - 12, 9, 16, 2).fill(STEEL).stroke(line);
      g.rect(hx + 1, hand - 9, 3, 1.5).fill(INK);
      g.rect(hx - 2, hand - 2, 9, 2).fill(accent);
      break;
  }
}

function stripes(g: Graphics, x: number, y: number, w: number, accent: number) {
  g.rect(x, y, w, 2.5).fill(accent);
  g.rect(x, y + 2.5, w, 2).fill(0xe9e4d8);
  g.rect(x, y + 4.5, w, 2.5).fill(accent);
}

function smoke(g: Graphics, x: number, y: number) {
  g.circle(x, y, 2.5).stroke({ color: INK, width: 1.2 });
  g.circle(x + 3, y - 4, 3.2).stroke({ color: INK, width: 1.2 });
}

/** Bulky dieselpunk exosuit, ~60px tall. */
function exosuit(g: Graphics, accent: number, arm: "drill" | "cannon" | "claw") {
  shadow(g, 22);
  // Legs.
  g.roundRect(-14, -18, 10, 18, 3).fill(STEEL_D).stroke(line);
  g.roundRect(4, -18, 10, 18, 3).fill(STEEL_D).stroke(line);
  g.roundRect(-16, -5, 13, 6, 2).fill(OLIVE_D).stroke(line);
  g.roundRect(3, -5, 13, 6, 2).fill(OLIVE_D).stroke(line);
  // Exhaust stacks.
  g.roundRect(-14, -66, 5, 14, 2).fill(STEEL_D).stroke(line);
  g.roundRect(9, -66, 5, 14, 2).fill(STEEL_D).stroke(line);
  smoke(g, -12, -70); smoke(g, 11, -72);
  // Torso and tabard.
  g.poly([-19, -52, 19, -52, 15, -18, -15, -18]).fill(OLIVE).stroke(line);
  g.poly([-6, -40, 6, -40, 5, -8, -5, -8]).fill(0x2a2d29).stroke(line);
  g.poly([-3, -24, 3, -24, 0, -18]).fill(BRASS);
  stripes(g, -18, -50, 36, accent);
  // Helmet with visor slit.
  g.roundRect(-9, -66, 18, 16, 6).fill(OLIVE_L).stroke(line);
  g.rect(-6, -60, 12, 2.5).fill(0xf2d16b);
  // Pauldrons.
  g.ellipse(-21, -48, 9, 8).fill(OLIVE_L).stroke(line);
  g.ellipse(21, -48, 9, 8).fill(OLIVE_L).stroke(line);
  // Left arm: heavy fist.
  g.roundRect(-30, -44, 10, 20, 4).fill(STEEL_D).stroke(line);
  g.roundRect(-31, -26, 12, 9, 3).fill(STEEL).stroke(line);
  // Right arm: signature weapon.
  g.roundRect(20, -44, 10, 16, 4).fill(STEEL_D).stroke(line);
  if (arm === "drill") {
    g.poly([22, -28, 34, -28, 28, -6]).fill(STEEL_L).stroke(line);
    for (let i = 0; i < 3; i++) g.moveTo(24 + i, -24 + i * 6).lineTo(32 - i, -22 + i * 6).stroke({ color: INK, width: 1 });
  } else if (arm === "cannon") {
    g.roundRect(22, -32, 24, 9, 3).fill(STEEL).stroke(line);
    g.roundRect(44, -33, 5, 11, 2).fill(STEEL_D).stroke(line);
  } else {
    g.roundRect(21, -30, 10, 8, 2).fill(STEEL).stroke(line);
    g.moveTo(23, -22).lineTo(20, -14).moveTo(29, -22).lineTo(32, -14).stroke({ color: STEEL_L, width: 3 });
    g.roundRect(-4, -36, 8, 6, 2).fill(0x86d29a).stroke({ color: INK, width: 1 });
  }
}

/** Four-legged walker with headlamps; heavy and tank variants grow and arm up. */
function walker(g: Graphics, accent: number, size: "light" | "heavy" | "tank") {
  const k = size === "light" ? 1 : size === "heavy" ? 1.25 : 1.4;
  shadow(g, 24 * k);
  const legs: [number, number][] = [[-20, 0], [-8, 4], [10, 4], [22, 0]];
  for (const [lx, ly] of legs) {
    g.moveTo(lx * k * 0.6, -18 * k).lineTo(lx * k, -10 * k).lineTo(lx * k * 1.05, ly).stroke({ color: INK, width: 4.5 });
    g.moveTo(lx * k * 0.6, -18 * k).lineTo(lx * k, -10 * k).lineTo(lx * k * 1.05, ly).stroke({ color: STEEL_D, width: 2.6 });
  }
  g.roundRect(-18 * k, -32 * k, 36 * k, 16 * k, 4).fill(OLIVE).stroke(line);
  g.roundRect(-18 * k, -22 * k, 36 * k, 4, 1).fill(accent);
  // Headlamp cone.
  g.poly([16 * k, -27 * k, 46 * k, -34 * k, 46 * k, -14 * k]).fill({ color: 0xf5e7a0, alpha: 0.22 });
  g.circle(16 * k, -26 * k, 3).fill(0xf8e58c).stroke(line);
  g.circle(10 * k, -26 * k, 2.4).fill(0xf8e58c).stroke({ color: INK, width: 1 });
  if (size === "tank") {
    g.roundRect(-10 * k, -42 * k, 22 * k, 11 * k, 4).fill(OLIVE_L).stroke(line);
    g.roundRect(10 * k, -40 * k, 22 * k, 5, 2).fill(STEEL).stroke(line);
  } else if (size === "heavy") {
    g.roundRect(-6 * k, -40 * k, 16 * k, 9 * k, 3).fill(OLIVE_L).stroke(line);
    g.roundRect(8 * k, -38 * k, 18 * k, 4, 2).fill(STEEL_D).stroke(line);
    g.roundRect(-14 * k, -40 * k, 6 * k, 9 * k, 2).fill(STEEL_D).stroke(line);
  } else {
    // Light walker carries a masked gunner.
    soldier(g, -4, -30 * k, accent, { mask: true, tool: "smg", pack: false });
  }
}

function wheel(g: Graphics, x: number, y: number, r: number) {
  g.circle(x, y, r).fill(LEATHER).stroke(line);
  g.circle(x, y, r * 0.35).fill(STEEL_D);
  for (let i = 0; i < 6; i++) {
    const a = (i * Math.PI) / 3;
    g.moveTo(x, y).lineTo(x + Math.cos(a) * r * 0.85, y + Math.sin(a) * r * 0.85).stroke({ color: INK, width: 1 });
  }
}

function gun(g: Graphics, kind: "mg" | "field" | "mortar" | "tesla") {
  if (kind === "mortar") {
    g.roundRect(-6, -4, 14, 4, 1).fill(STEEL_D).stroke(line);
    g.poly([-2, -4, 4, -4, 10, -24, 4, -26]).fill(STEEL).stroke(line);
    g.moveTo(0, -4).lineTo(-6, -14).stroke({ color: INK, width: 2 });
    return;
  }
  if (kind === "tesla") {
    wheel(g, -8, -6, 6); wheel(g, 10, -6, 6);
    g.roundRect(-10, -16, 22, 8, 2).fill(STEEL_D).stroke(line);
    g.roundRect(-2, -34, 6, 20, 2).fill(BRASS).stroke(line);
    for (let i = 0; i < 4; i++) g.ellipse(1, -32 + i * 5, 7, 2).stroke({ color: INK, width: 1.2 });
    g.circle(1, -38, 4).fill(0x8ff1e2).stroke(line);
    g.moveTo(5, -40).lineTo(11, -44).lineTo(8, -46).lineTo(14, -50).stroke({ color: 0x8ff1e2, width: 1.6 });
    return;
  }
  const big = kind === "field";
  wheel(g, big ? -4 : -3, -7, big ? 9 : 6);
  g.roundRect(-14, -14, big ? 16 : 12, 5, 2).fill(OLIVE_D).stroke(line);
  g.roundRect(-4, big ? -17 : -15, big ? 34 : 24, big ? 6 : 4, 2).fill(STEEL).stroke(line);
  if (kind === "mg") g.roundRect(0, -21, 9, 6, 2).fill(STEEL_D).stroke(line);
  else g.roundRect(-8, -26, 12, 10, 2).fill(OLIVE).stroke(line);
}

function car(g: Graphics, accent: number, tracked: boolean) {
  shadow(g, 26);
  if (tracked) {
    g.roundRect(-24, -10, 48, 10, 5).fill(INK);
    for (let i = 0; i < 6; i++) g.circle(-19 + i * 7.6, -5, 3).fill(STEEL_D);
  } else {
    wheel(g, -15, -5, 6); wheel(g, 15, -5, 6);
  }
  g.poly([-24, -10, 24, -10, 20, -24, -16, -26]).fill(OLIVE).stroke(line);
  g.rect(-22, -16, 44, 3).fill(accent);
  g.roundRect(-8, -34, 18, 10, 3).fill(OLIVE_L).stroke(line);
  g.roundRect(8, -31, tracked ? 12 : 18, tracked ? 7 : 4, 2).fill(STEEL).stroke(line);
  g.rect(14, -22, 6, 4).fill(0x2a3a3d);
}

function drone(g: Graphics, x: number, y: number, accent: number) {
  g.ellipse(x + 2, y + 16, 7, 2.5).fill({ color: 0x0a1210, alpha: 0.3 });
  g.roundRect(x - 7, y - 5, 14, 9, 3).fill(STEEL).stroke(line);
  g.circle(x + 4, y - 1, 2).fill(0xf8e58c);
  g.rect(x - 7, y + 1, 14, 2).fill(accent);
  for (const dx of [-10, 10]) {
    g.moveTo(x, y - 4).lineTo(x + dx, y - 9).stroke({ color: INK, width: 1.5 });
    g.ellipse(x + dx, y - 10, 6, 1.6).fill({ color: STEEL_L, alpha: 0.8 }).stroke({ color: INK, width: 1 });
  }
}

function automaton(g: Graphics, x: number, accent: number) {
  shadow(g, 10, x);
  g.roundRect(x - 5, -10, 4, 10, 1).fill(STEEL_D).stroke(line);
  g.roundRect(x + 1, -10, 4, 10, 1).fill(STEEL_D).stroke(line);
  g.roundRect(x - 9, -30, 18, 21, 4).fill(STEEL).stroke(line);
  g.rect(x - 9, -20, 18, 3).fill(accent);
  g.roundRect(x - 6, -40, 12, 10, 3).fill(STEEL_L).stroke(line);
  g.circle(x, -35, 2.6).fill(0x8ff1e2).stroke({ color: INK, width: 1 });
  g.roundRect(x + 8, -28, 5, 14, 2).fill(STEEL_D).stroke(line);
  g.roundRect(x - 13, -28, 5, 14, 2).fill(STEEL_D).stroke(line);
}

/** Dieselpunk boats: hull, deckhouse, stack; flag in accent colour. */
function ship(g: Graphics, accent: number, kind: "transport" | "gunboat" | "ironclad" | "pirate") {
  const big = kind === "ironclad" || kind === "pirate";
  const w = big ? 34 : 28;
  g.ellipse(2, 4, w + 6, 8).fill({ color: 0x0f3a66, alpha: 0.35 });
  for (const dx of [-w + 6, -4, w - 10]) g.moveTo(dx, 6).quadraticCurveTo(dx + 4, 3, dx + 8, 6).stroke({ color: 0xd6efff, width: 1.4 });
  g.poly([-w, -10, w + 6, -10, w - 4, 2, -w + 6, 2]).fill(kind === "pirate" ? 0x3b2f2a : kind === "ironclad" ? STEEL_D : OLIVE_D).stroke(line);
  g.rect(-w + 4, -9, 2 * w - 4, 3).fill(accent);
  if (kind === "transport") {
    g.roundRect(-w + 6, -18, 16, 8, 2).fill(OLIVE).stroke(line);
    g.roundRect(0, -16, 22, 6, 2).fill(OLIVE_L).stroke(line);
    soldier(g, 10, -16, accent, { mask: true, tool: "none", pack: false });
  } else {
    g.roundRect(-10, -24, 20, 14, 3).fill(kind === "pirate" ? 0x5a4632 : OLIVE).stroke(line);
    g.rect(-6, -20, 12, 3).fill(0xf8e58c);
    g.roundRect(-18, -34, 6, 14, 2).fill(STEEL_D).stroke(line); smoke(g, -15, -38);
    g.roundRect(10, -20, kind === "gunboat" ? 26 : 18, 5, 2).fill(STEEL).stroke(line);
    if (kind === "ironclad") g.poly([w + 6, -10, w + 14, -4, w - 4, 2]).fill(STEEL_L).stroke(line);
  }
  g.moveTo(2, -24).lineTo(2, -40).stroke({ color: INK, width: 2 });
  g.poly([3, -40, 15, -36, 3, -32]).fill(kind === "pirate" ? 0x1b1b1b : accent).stroke({ color: INK, width: 1 });
}

export function pirateShip() {
  const g = new Graphics();
  ship(g, 0x8f4a44, "pirate");
  return g;
}

/** Draw a unit stack. Returns a container whose origin is the stack's hex centre. */
export function unitSprite(art: string | undefined, faction: string | undefined, side: string, ratio: number) {
  const accent = side === "npc" ? ACCENTS.npc : ACCENTS[faction ?? ""] ?? 0x4c9ce5;
  const node = new Container();
  const g = new Graphics();
  node.addChild(g);
  const flip = side === "npc" ? -1 : 1;
  switch (art ?? "rifleman") {
    case "rifleman":
      soldier(g, -12, -2, accent, { mask: true, tool: "rifle" }, flip);
      soldier(g, 12, -4, accent, { mask: true, tool: "rifle" }, flip);
      soldier(g, 0, 8, accent, { mask: true, tool: "rifle" }, flip);
      break;
    case "scout":
      soldier(g, -9, 2, accent, { helmet: "cap", tool: "binoculars" }, flip);
      soldier(g, 10, 4, accent, { helmet: "cap", tool: "rifle" }, flip);
      break;
    case "stormtrooper":
      soldier(g, -10, 0, accent, { mask: true, tool: "blade" }, flip);
      soldier(g, 10, 2, accent, { mask: true, tool: "smg" }, flip);
      break;
    case "raider":
      soldier(g, -9, 0, accent, { helmet: "goggles", tool: "blade", pack: false }, flip);
      soldier(g, 9, 4, accent, { helmet: "hood", tool: "smg", pack: false }, flip);
      break;
    case "sniper":
      soldier(g, -8, 4, accent, { helmet: "hood", tool: "longrifle", kneel: true }, flip);
      soldier(g, 12, 0, accent, { helmet: "cap", tool: "binoculars" }, flip);
      break;
    case "shieldbearer":
      soldier(g, -10, 0, accent, { mask: true, tool: "shield" }, flip);
      soldier(g, 10, 4, accent, { mask: true, tool: "shield" }, flip);
      break;
    case "medic":
      soldier(g, -9, 2, accent, { helmet: "nurse", tool: "kit" }, flip);
      soldier(g, 10, 4, accent, { helmet: "nurse", mask: true, tool: "kit" }, flip);
      break;
    case "engineer":
      soldier(g, -9, 2, accent, { helmet: "beret", mask: true, tool: "wrench" }, flip);
      soldier(g, 10, 4, accent, { helmet: "brodie", mask: true, tool: "wrench" }, flip);
      break;
    case "mg_crew":
      { const c = new Graphics(); gun(c, "mg"); c.position.set(-4, 6); node.addChild(c); }
      soldier(g, -16, 0, accent, { mask: true, tool: "none" }, flip);
      soldier(g, 16, -2, accent, { mask: true, tool: "none" }, flip);
      break;
    case "mortar":
      { const c = new Graphics(); gun(c, "mortar"); c.position.set(0, 8); node.addChild(c); }
      soldier(g, -14, 0, accent, { mask: true, tool: "none" }, flip);
      soldier(g, 15, 2, accent, { helmet: "cap", tool: "binoculars" }, flip);
      break;
    case "field_gun":
      { const c = new Graphics(); gun(c, "field"); c.position.set(0, 8); c.scale.x = flip; node.addChild(c); }
      soldier(g, -18, -2, accent, { helmet: "cap", tool: "none" }, flip);
      soldier(g, 18, 2, accent, { mask: true, tool: "none" }, flip);
      break;
    case "tesla":
      { const c = new Graphics(); gun(c, "tesla"); c.position.set(0, 8); node.addChild(c); }
      soldier(g, -16, 2, accent, { helmet: "goggles", tool: "wrench" }, flip);
      break;
    case "drone":
      drone(g, -10, -18, accent); drone(g, 12, -10, accent);
      break;
    case "automaton":
      automaton(g, -10, accent); automaton(g, 12, accent);
      break;
    case "armored_car":
      car(g, accent, false); g.scale.x = flip;
      break;
    case "spg":
      car(g, accent, true); g.scale.x = flip;
      break;
    case "walker":
    case "walker_heavy":
    case "walker_tank":
      walker(g, accent, art === "walker" ? "light" : art === "walker_heavy" ? "heavy" : "tank"); g.scale.x = flip;
      break;
    case "exosuit_drill":
    case "exosuit_cannon":
    case "exosuit_claw":
      exosuit(g, accent, art === "exosuit_drill" ? "drill" : art === "exosuit_cannon" ? "cannon" : "claw");
      g.scale.set(0.8 * flip, 0.8);
      break;
    case "boat_transport":
      ship(g, accent, "transport"); g.scale.x = flip;
      break;
    case "gunboat":
      ship(g, accent, "gunboat"); g.scale.x = flip;
      break;
    case "ironclad":
      ship(g, accent, "ironclad"); g.scale.x = flip;
      break;
    default:
      soldier(g, 0, 0, accent, { mask: true });
  }
  // Health bar in side colour.
  const bar = new Graphics();
  bar.roundRect(-21, 21, 42, 5, 2).fill(0x101923);
  bar.roundRect(-20, 22, 40 * Math.max(0.01, Math.min(1, ratio)), 3, 1).fill(side === "npc" ? 0xd95a52 : 0x4c9ce5);
  node.addChild(bar);
  return node;
}

/** Every art key, for previews and tests. */
export const ART_KEYS = ["rifleman", "scout", "stormtrooper", "raider", "sniper", "shieldbearer", "medic", "engineer",
  "mg_crew", "mortar", "field_gun", "tesla", "drone", "automaton", "armored_car", "spg", "walker", "walker_heavy",
  "walker_tank", "exosuit_drill", "exosuit_cannon", "exosuit_claw", "boat_transport", "gunboat", "ironclad"];
