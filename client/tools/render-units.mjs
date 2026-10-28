// Renders every unit sprite to client/public/art/units/<key>.png.
// Usage: TEST_APP_URL=http://127.0.0.1:8000 node tools/render-units.mjs
// The art is the original code-drawn set from src/Units.ts; drop-in raster
// replacements can later overwrite these files under the same names.
import { writeFile } from "node:fs/promises";
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const base = process.env.TEST_APP_URL || "http://127.0.0.1:8000";
const cfg = await (await fetch(base + "/api/v1/config")).json();
const jobs = [];
for (const [hero, f] of Object.entries(cfg.factions)) for (const u of f.units) jobs.push({ key: u.key, art: u.art, faction: hero, side: "player" });
for (const [key, u] of Object.entries(cfg.units)) if (!u.faction) jobs.push({ key, art: u.art, faction: "npc", side: "npc" });
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_EXECUTABLE, args: ["--no-sandbox"] });
const page = await browser.newPage({ viewport: { width: 200, height: 200 }, deviceScaleFactor: 1 });
for (const j of jobs) {
  await page.goto(`${base}/?sprite=${j.art}&faction=${j.faction}&side=${j.side}`);
  await page.waitForFunction(() => window.__spriteReady === true);
  const png = await page.locator("canvas").screenshot({ omitBackground: true });
  await writeFile(new URL(`../public/art/units/${j.key}.png`, import.meta.url), png);
}
await browser.close();
console.log(`Rendered ${jobs.length} unit sprites`);
