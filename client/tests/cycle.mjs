// Run only against a disposable APP_ENV=test deployment with a test BOT_TOKEN.
// No mocked API responses: real signed auth, construction timers, training and battle.
import { createHmac } from "node:crypto";
import assert from "node:assert/strict";
const { chromium } = await import(
  process.env.PLAYWRIGHT_MODULE || "playwright"
);
const base = process.env.TEST_APP_URL || "http://127.0.0.1:8000";
const bot = process.env.BOT_TOKEN;
if (!bot || !process.env.TEST_APP_URL)
  throw new Error("Set TEST_APP_URL and test BOT_TOKEN");
const data = {
  auth_date: String(Math.floor(Date.now() / 1000)),
  user: JSON.stringify({ id: 9000001, first_name: "Test Commander" }),
};
const secret = createHmac("sha256", "WebAppData").update(bot).digest();
const hash = createHmac("sha256", secret)
  .update(
    Object.entries(data)
      .sort()
      .map(([k, v]) => `${k}=${v}`)
      .join("\n"),
  )
  .digest("hex");
const response = await fetch(base + "/api/v1/auth/telegram", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    init_data: new URLSearchParams({ ...data, hash }).toString(),
  }),
});
assert.equal(response.status, 200);
const { token } = await response.json();
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CHROMIUM_EXECUTABLE,
  args: ["--no-sandbox"],
});
const page = await browser.newPage({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 1,
  isMobile: true,
  hasTouch: true,
});
process.on("uncaughtException", async (error) => {
  console.error(error);
  try {
    await page.screenshot({path: "/tmp/iron-browser-failure.png", fullPage: true});
    console.error((await page.locator("body").innerText()).slice(-5000));
    await browser.close();
  } finally { process.exit(1); }
});
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.addInitScript(
  (token) => sessionStorage.setItem("iron-session", token),
  token,
);
await page.goto(base);
await page.locator(".hero-grid").waitFor();
for (const id of ["raven","valkyrie","titan","phoenix","ghost","storm"]) {
  const asset = await fetch(base + `/art/commanders/${id}-v1.webp`);
  assert.equal(asset.status, 200);
  assert.match(asset.headers.get("content-type"), /image\/webp/);
}
const moduleAsset = await fetch(base + "/art/equipment/field-module-v1.webp");
assert.equal(moduleAsset.status, 200);
await page.locator(".selection-portrait img").first().evaluate(img => img.decode());
await page.screenshot({path:"/tmp/iron-hero-selection.png",fullPage:true});
await page.getByRole("button", { name: /Генерал Рейвен/ }).click();
await page.getByRole("heading", { name: "Передовая база" }).waitFor();
await page.getByRole("button", {name:"План первой операции"}).click();
await page.locator(".guide-list").waitFor();
assert.match(await page.locator(".guide-list .current").innerText(), /Постройте электростанцию/);
await page.getByRole("button", {name:"План первой операции"}).click();
const state = async () => {
  const r = await fetch(base + "/api/v1/player/me", {
    headers: { Authorization: "Bearer " + token },
  });
  assert.equal(r.status, 200);
  return r.json();
};
const waitFor = async (fn, timeout = 75000) => {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    if (await fn()) return;
    await new Promise((r) => setTimeout(r, 1200));
  }
  throw new Error("Timed out waiting for game state");
};
async function build(name, kind, q, r) {
  if (kind === "power") {
    await page.getByRole("button", {name:"Выбрать участок →"}).click();
    await page.locator(".building-option.recommended").waitFor();
  } else {
    const box = await page.locator("canvas").boundingBox();
    await page.mouse.click(
      box.x + box.width / 2 + 54 * Math.sqrt(3) * (q + r / 2),
      box.y + box.height * 0.5 + 54 * 0.975 * r,
    );
  }
  await page.getByRole("button", { name: new RegExp(name) }).click();
  await waitFor(async () =>
    (await state()).buildings.some(
      (b) => b.kind === kind && b.status === "ready",
    ),
  );
  console.log("Built", kind);
}
await build("Электростанция", "power", 1, 0);
await build("Металлургический карьер", "quarry", 0, 1);
await build("Казармы", "barracks", -1, 1);
await page.getByRole("button", { name: "К армии →", exact: true }).click();
await page.getByRole("button", { name: /Подготовить стрелков/ }).click();
await waitFor(async () => (await state()).units.length === 1);
await page.getByRole("button", { name: "В бой", exact: true }).click();
await page.getByRole("heading", { name: "Патруль «Рубеж»" }).waitFor();
const box = await page.locator("canvas").boundingBox();
// Battle camera: scale 0.72, shifted 70px up (Map.tsx BATTLE_SCALE / BATTLE_SHIFT).
await page.mouse.click(
  box.x + box.width / 2 - 54 * Math.sqrt(3) * 0.72,
  box.y + box.height * 0.5 - 70,
);
await page.getByRole("button", { name: "Переместить", exact: true }).click();
await waitFor(async () => (await state()).battles[0].state.turn === 2, 10000);
for (let i = 0; i < 12; i++) {
  if ((await state()).first_victory) break;
  const prev = (await state()).battles[0].state.turn;
  await page.getByRole("button", { name: "Атаковать", exact: true }).click();
  await waitFor(
    async () => (await state()).battles[0].state.turn > prev,
    10000,
  );
}
assert.equal((await state()).first_victory, true);
await page.getByRole("button", { name: "Снарядить", exact: true }).click();
await page.reload();
await page.getByRole("heading", { name: "Передовая база" }).waitFor();
await page.getByRole("button", { name: "Армия", exact: true }).click();
await page.getByRole("button", { name: "Снять", exact: true }).waitFor();
assert.equal(await page.getByRole("button",{name:"Командир",exact:true}).getAttribute("aria-pressed"), "true");
await page.getByRole("button",{name:"Снаряжено",exact:true}).click();
assert.equal(await page.locator(".equipment-card").count(),1);
await page.getByRole("button",{name:"Карточка полевого модуля"}).click();
await page.getByText((await state()).inventory[0].id,{exact:true}).waitFor();
await page.locator(".commander-art img").evaluate(img => img.decode());
await page.screenshot({path:"/tmp/iron-commander-mobile.png",fullPage:true});
await page.getByRole("button",{name:"Карточка полевого модуля"}).click();
await page.getByRole("button",{name:"Все",exact:true}).click();
assert.equal((await state()).inventory.length, 1);
await page.getByText("Первая операция завершена",{exact:true}).waitFor();
assert.equal(
  await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
  true,
);
await page.screenshot({
  path: process.env.SCREENSHOT_PATH || "/tmp/iron-cycle.png",
  fullPage: true,
});
await page.setViewportSize({ width: 1280, height: 900 });
await page.getByRole("button", { name: "База", exact: true }).click();
await page.screenshot({ path: "/tmp/iron-base-desktop.png", fullPage: true });
await page.setViewportSize({width:390,height:844});
await page.emulateMedia({reducedMotion:"reduce"});
await page.screenshot({path:"/tmp/iron-base-mobile.png",fullPage:true});
// Real server-side march and capture after the original vertical slice.
await page.getByRole("button",{name:"Армия",exact:true}).click();
await page.getByRole("button",{name:"Подразделения",exact:true}).click();
await page.getByRole("button",{name:"Новое соединение",exact:true}).click();
await page.locator(".world-stage canvas").waitFor();
await page.locator("canvas").scrollIntoViewIfNeeded();
const worldBox=await page.locator("canvas").boundingBox();
await page.mouse.click(worldBox.x+worldBox.width/2+54*Math.sqrt(3),worldBox.y+worldBox.height*.5);
const captureButton=page.getByRole("button",{name:"Захватить гекс",exact:true});
const bounds=await captureButton.boundingBox();
assert.ok(bounds && bounds.y>=0 && bounds.y+bounds.height<=844);
assert.equal(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight),true);
await page.screenshot({path:"/tmp/iron-map-actions.png",fullPage:true});
await page.setViewportSize({width:390,height:640});
const compactBounds=await captureButton.boundingBox();
const navigationBounds=await page.locator('nav').boundingBox();
assert.ok(compactBounds && navigationBounds && compactBounds.y+compactBounds.height<=navigationBounds.y);
await page.screenshot({path:"/tmp/iron-map-compact.png",fullPage:true});
await page.setViewportSize({width:390,height:844});
await captureButton.click();
const marching=await state();
assert.equal(marching.armies[0].status,"moving");
assert.equal(marching.territories.length,0);
await waitFor(async()=>(await state()).territories.length===1,45000);
await page.reload();
await page.getByRole("heading",{name:"Передовая база"}).waitFor();
await page.getByRole("button",{name:"Карта",exact:true}).click();
await page.getByText(/Под контролем 1\/12/).waitFor();
const captured=await state();
assert.ok(captured.base);
assert.equal(captured.armies[0].q,captured.base.q+1);
assert.equal(captured.armies[0].r,captured.base.r);
assert.equal(captured.armies[0].status,"idle");
assert.equal(captured.resources.fuel,199);
await page.getByRole("button",{name:"К соединению",exact:true}).click();
await page.screenshot({path:"/tmp/iron-world-capture.png",fullPage:true});
assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
// Attack the adjacent persistent world garrison and survive a reload mid-battle.
const garrisonMap=await page.locator('canvas').boundingBox();
await page.mouse.click(garrisonMap.x+garrisonMap.width/2-54*Math.sqrt(3)/2,garrisonMap.y+garrisonMap.height*.5+54*.975);
await page.getByRole('button',{name:'Атаковать гарнизон',exact:true}).click();
await waitFor(async()=>(await state()).battles.some(b=>b.status==='active'&&b.state.expedition),45000);
await page.reload();
await page.getByRole('heading',{name:/NPC ·/}).waitFor();
const battleBox=await page.locator('canvas').boundingBox();
await page.mouse.click(battleBox.x+battleBox.width/2-54*Math.sqrt(3)*.72,battleBox.y+battleBox.height*.5-70);
await page.getByRole('button',{name:'Переместить',exact:true}).click();
await waitFor(async()=>(await state()).battles.some(b=>b.status==='active'&&b.state.expedition&&b.state.turn===2),10000);
await page.screenshot({path:'/tmp/iron-garrison-battle.png',fullPage:true});
for(let i=0;i<12;i++){
 const current=(await state()).battles.find(b=>b.status==='active'&&b.state.expedition);
 if(!current)break;
 await page.getByRole('button',{name:'Атаковать',exact:true}).click();
 await waitFor(async()=>(await state()).battles.find(b=>b.id===current.id).state.turn>current.state.turn,10000);
}
const conquered=await state();
assert.equal(conquered.territories.length,2);
assert.equal(conquered.armies[0].q,conquered.base.q);
assert.equal(conquered.armies[0].r,conquered.base.r+1);
assert.equal(conquered.hero.xp,150);
assert.equal(conquered.inventory.length,2);
assert.ok(conquered.inventory.some(i=>i.source==="garrison"));
const worldLoaded=page.waitForResponse(r=>r.url().includes('/world/tiles')&&r.status()===200);
await page.getByRole('button',{name:'Карта',exact:true}).click();
await worldLoaded;
await page.getByText(/Под контролем 2\/12/).waitFor();
await page.waitForTimeout(500);
await page.screenshot({path:'/tmp/iron-garrison-victory.png',fullPage:true});
await page.getByRole('button',{name:'Армия',exact:true}).click();
await page.getByRole('button',{name:'Командир',exact:true}).click();
const trophy=conquered.inventory.find(i=>i.source==='garrison');
const trophyCard=page.locator('.equipment-card').filter({has:page.getByRole('heading',{name:trophy.definition.name,exact:true})});
await trophyCard.getByRole('button',{name:'Снарядить',exact:true}).click();
await waitFor(async()=>(await state()).inventory.find(i=>i.id===trophy.id).equipped===true,10000);
await page.reload();
await page.getByRole('button',{name:'Армия',exact:true}).click();
await page.getByRole('button',{name:'Командир',exact:true}).click();
await page.getByRole('heading',{name:trophy.definition.name,exact:true}).waitFor();
await page.locator('.commander-art img').evaluate(img=>img.decode());
await page.screenshot({path:'/tmp/iron-loot-inventory.png',fullPage:true});
assert.equal((await state()).inventory.filter(i=>i.equipped).length,1);
assert.deepEqual(errors, []);
console.log(
  "PASS: mobile end-to-end cycle, real timers, reload persistence, equipment, real march/capture, no JS errors",
);
await browser.close();
