// Match rooms end to end: a duel by room code with instant turn hand-off, and a game against the AI.
// Run only against a disposable APP_ENV=test deployment with a test BOT_TOKEN.
import { createHmac } from "node:crypto";
import assert from "node:assert/strict";
const pw = await import(process.env.PLAYWRIGHT_MODULE || "playwright");
const { chromium } = pw.default ?? pw;
const base = process.env.TEST_APP_URL, bot = process.env.BOT_TOKEN;
if (!base || !bot) throw new Error("Set TEST_APP_URL and test BOT_TOKEN");
const stamp = Date.now() % 100000;

async function login(id, name) {
  const data = { auth_date: String(Math.floor(Date.now() / 1000)), user: JSON.stringify({ id, first_name: name }) };
  const secret = createHmac("sha256", "WebAppData").update(bot).digest();
  const hash = createHmac("sha256", secret).update(Object.entries(data).sort().map(([k, v]) => `${k}=${v}`).join("\n")).digest("hex");
  const r = await fetch(base + "/api/v1/auth/telegram", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ init_data: new URLSearchParams({ ...data, hash }).toString() }) });
  const { token } = await r.json();
  await fetch(base + "/api/v1/heroes/choose", { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + token, "Idempotency-Key": `hero-${id}` }, body: JSON.stringify({ kind: "storm" }) });
  return token;
}
const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_EXECUTABLE, args: ["--no-sandbox"] });
const errors = [];
async function open(token) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  page.on("pageerror", (e) => errors.push(e.message));
  await page.addInitScript((t) => { sessionStorage.setItem("iron-session", t); }, token);
  await page.goto(base);
  await page.getByRole("button", { name: "Играть с ИИ" }).waitFor();
  return page;
}

// Duel: A creates a private room, B joins by code, the turn passes the moment A ends his.
const a = await open(await login(9200000 + stamp, "Альфа"));
const b = await open(await login(9300000 + stamp, "Браво"));
await a.getByLabel("Название").fill("Дуэль " + stamp);
await a.getByText("Закрытая (вход по коду)").click();
await a.getByRole("button", { name: "Создать комнату" }).click();
const code = (await a.locator(".invite .code").textContent()).trim();
assert.match(code, /^[0-9A-F]{6}$/);
await b.getByLabel("Код комнаты").fill(code);
await b.getByRole("button", { name: "Войти" }).click();
await b.locator(".match-stage canvas").waitFor();
await b.getByText("ходит Альфа").waitFor();
await a.getByRole("button", { name: "Конец хода" }).waitFor({ timeout: 10000 });
await a.screenshot({ path: "/tmp/iron-match-duel.png" });
await a.getByRole("button", { name: "Конец хода" }).click();
await b.getByRole("button", { name: "Конец хода" }).waitFor({ timeout: 10000 });   // polled within seconds
await a.getByText("ходит Браво").waitFor();

// Versus AI: start, select a unit, see moves, end the turn and get it straight back.
await a.getByRole("button", { name: "К списку партий" }).click();
await a.getByRole("button", { name: "Играть с ИИ" }).click();
await a.locator(".match-stage canvas").waitFor();
await a.getByRole("button", { name: "Следующий отряд" }).click();
await a.getByText("Стрелки").first().waitFor();
await a.getByRole("button", { name: "Технологии" }).click();
await a.getByRole("button", { name: /^Моторы/ }).click();   // 5 ★ at the start
await a.getByText("✔ Изучено").waitFor();
await a.getByRole("button", { name: "Закрыть" }).click();
await a.getByRole("button", { name: "Конец хода" }).click();
await a.getByText(/Ход 2 · ваш ход/).waitFor({ timeout: 10000 });
await a.screenshot({ path: "/tmp/iron-match-ai.png" });
assert.deepEqual(errors, []);
console.log("PASS: match rooms — duel by code with instant hand-off, game against the AI, no JS errors");
await browser.close();
