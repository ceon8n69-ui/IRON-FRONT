// Raster world-map art (client/public/art/world/*.png), generated in the base's diorama style.
// Props decorate terrain; objects stand on a small hex patch like the base buildings.
// Everything falls back to the code-drawn art in Terrain.ts until the textures are loaded.
import { Assets, Container, Graphics, Sprite, Texture } from "pixi.js";

const PROPS = ["tree-oak", "tree-pine", "tree-autumn", "bush", "rocks", "mountain", "palm", "cactus", "reeds", "hillock", "pirates"];
const OBJECTS = ["pile", "chest", "mine", "ruin", "camp", "bunker", "base", "capital", "oil_field", "plant", "radar"];
const url = (k: string) => `/art/world/${k}.png`;
let state: "idle" | "loading" | "ready" | "failed" = "idle";

/** Load every world texture once; `done` fires when they are all in the cache. */
export function preloadWorld(done: () => void) {
  if (state !== "idle") return;
  state = "loading";
  Assets.load([...PROPS, ...OBJECTS].map(url)).then(() => { state = "ready"; done(); }).catch(() => { state = "failed"; });
}
export const worldReady = () => state === "ready";
const tex = (k: string) => (Assets.cache.has(url(k)) ? (Assets.cache.get(url(k)) as Texture) : null);

function hash(q: number, r: number, i: number) {
  let h = (q * 374761393 + r * 668265263 + i * 2147483647) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

function sprite(k: string, x: number, y: number, width: number, anchorY = 0.92, flip = false) {
  const t = tex(k);
  if (!t) return null;
  const s = new Sprite(t);
  s.anchor.set(0.5, anchorY);
  const scale = width / t.width;
  s.scale.set(flip ? -scale : scale, scale);
  s.position.set(x, y);
  return s;
}

/** Terrain decoration for one hex, or null when the textures aren't ready. */
export function rasterEnvironment(x: number, y: number, biome: string, q: number, r: number): Container | null {
  if (!worldReady()) return null;
  const c = new Container();
  const n = (i: number) => hash(q, r, i);
  const put = (k: string, px: number, py: number, w: number) => { const s = sprite(k, px, py, w, 0.92, n(px) < .5); if (s) c.addChild(s); };
  if (biome === "forest") {
    const items = Array.from({ length: 3 }, (_, i) => ({ x: x + (n(i * 3) - .5) * 52, y: y - 6 + i * 9 + (n(i * 3 + 1) - .5) * 6, k: n(i * 3 + 2) }));
    items.sort((a, b) => a.y - b.y);
    for (const it of items) put(it.k < .45 ? "tree-pine" : it.k < .8 ? "tree-oak" : "tree-autumn", it.x, it.y, it.k < .45 ? 34 : 42);
  } else if (biome === "mountain") {
    put("mountain", x, y + 14, 92);
  } else if (biome === "hills") {
    put("hillock", x - 6, y + 12, 62);
    if (n(7) < .5) put("rocks", x + 24, y + 14, 24);
  } else if (biome === "beach") {
    if (n(1) < .55) put("palm", x + (n(2) - .5) * 30, y + 8, 44);
    else if (n(3) < .5) put("rocks", x + (n(4) - .5) * 30, y + 10, 22);
  } else if (biome === "desert") {
    if (n(1) < .55) put("cactus", x + (n(2) - .5) * 30, y + 10, 34);
  } else if (biome === "river") {
    if (n(1) < .45) put("reeds", x + (n(2) < .5 ? -24 : 24), y + 12, 28);
  } else if (biome === "plain") {
    const k = n(1);
    if (k < .3) put("bush", x + (n(2) - .5) * 44, y + (n(3) - .5) * 14 + 8, 26);
    else if (k < .48) put(n(4) < .7 ? "tree-oak" : "tree-autumn", x + (n(5) - .5) * 36, y + 10, 40);
    else if (k < .58) put("rocks", x + (n(6) - .5) * 40, y + 12, 22);
  } else {
    return null;
  }
  return c;
}

/** A map object on its diorama patch (or the pirate ship), with an optional owner flag. */
export function worldObject(kind: string, x: number, y: number, width = 84, flag: number | null = null): Container | null {
  if (!worldReady()) return null;
  const c = new Container();
  const s = kind === "pirates" ? sprite("pirates", x, y + 18, 78, 0.85) : sprite(kind, x, y + 6, width, 0.8);
  if (!s) return null;
  c.addChild(s);
  if (flag !== null) {
    const f = new Graphics();
    f.moveTo(x + width * .36, y + 4).lineTo(x + width * .36, y - 26).stroke({ color: 0xe8ecef, width: 2 });
    f.poly([x + width * .36 + 1, y - 26, x + width * .36 + 15, y - 21, x + width * .36 + 1, y - 16]).fill(flag).stroke({ color: 0x1b201e, width: 1 });
    c.addChild(f);
  }
  return c;
}
