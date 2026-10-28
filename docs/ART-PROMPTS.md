# IRON FRONT — пакет промптов для растрового арта

Сгенерируй картинки в любом генераторе (Midjourney, DALL·E, Leonardo и т. п.) и положи файлы по указанным путям. Игра подхватит их без изменений кода.

## Общие правила

- Юниты: PNG с прозрачным фоном, **256×224 px**. Фигура смотрит вправо, ноги на высоте ~82% от верха, центр по горизонтали. Путь: `client/public/art/units/<key>.png`.
- Тот же стиль во всех файлах: толстый тёмный контур, плоская заливка, крупные головы. Генерируй сериями с одним seed или style reference.
- Не используй чужие картинки как образец для копирования. Никаких настоящих эмблем и красного креста.
- После замены файлов выполни `npm run build` в `client/` и задеплой.

## Юниты фракций

### Генерал Рейвен — Железный легион (акцент #c8433a)

**`raven_line.png`** — Стрелки легиона · способность «Штыковая атака»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #c8433a crimson.

**`raven_scouts.png`** — Егеря · способность «Марш-бросок»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two light scouts in field caps, one with binoculars, one with a short rifle, light packs, faction accent #c8433a crimson.

**`raven_assault.png`** — Ударники · способность «Гранаты»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked assault troopers, one with a trench cleaver, one with a stubby submachine gun, faction accent #c8433a crimson.

**`raven_artillery.png`** — Траншейная мортира · способность «Огневой вал»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a stubby trench mortar on a baseplate with a masked loader and an officer with binoculars, faction accent #c8433a crimson.

**`raven_heavy.png`** — Экзоброня «Таран» · способность «Таранный удар»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a bulky dieselpunk power-armour exosuit with two smoking exhaust stacks, slit visor helmet, giant drill arm, chest stripes, faction accent #c8433a crimson.

### Командир Валькирия — Серый дозор (акцент #5f8fd0)

**`valkyrie_line.png`** — Стрелки дозора · способность «Прицельный залп»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #5f8fd0 steel blue.

**`valkyrie_walker.png`** — Шагоход-разведчик · способность «Прожектор»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a small four-legged scout walker with twin headlamps casting light beams and a masked gunner riding on top, faction accent #5f8fd0 steel blue.

**`valkyrie_raiders.png`** — Диверсанты · способность «Засада»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two saboteurs, one in goggles with a knife, one hooded with a compact gun, no backpacks, faction accent #5f8fd0 steel blue.

**`valkyrie_snipers.png`** — Снайперская пара · способность «Выстрел в офицера»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a hooded kneeling sniper with a very long rifle and a spotter in a cap with binoculars, faction accent #5f8fd0 steel blue.

**`valkyrie_heavy.png`** — Шагоход «Гончая» · способность «Прыжок»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a heavy four-legged walker with an armored hull, side guns and headlamps, faction accent #5f8fd0 steel blue.

### Полковник Титан — Стальной заслон (акцент #c9a04a)

**`titan_line.png`** — Стрелки заслона · способность «Окопаться»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #c9a04a brass gold.

**`titan_mg.png`** — Пулемётный расчёт · способность «Подавляющий огонь»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked soldiers crewing a wheeled heavy machine gun with a small gun shield, faction accent #c9a04a brass gold.

**`titan_shields.png`** — Щитоносцы · способность «Стена щитов»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked soldiers carrying tall riveted steel shields with an accent stripe, faction accent #c9a04a brass gold.

**`titan_gun.png`** — Полевая пушка · способность «Шрапнель»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a big-wheeled field gun with a long barrel, an officer in a cap and a masked gunner, faction accent #c9a04a brass gold.

**`titan_heavy.png`** — Экзоброня «Бастион» · способность «Несокрушимость»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a bulky power-armour exosuit with smoking exhaust stacks and a heavy arm cannon, thick shoulder pauldrons, faction accent #c9a04a brass gold.

### Маршал Феникс — Тыловой корпус (акцент #d9783a)

**`phoenix_line.png`** — Стрелки снабжения · способность «Сухпаёк»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #d9783a burnt orange.

**`phoenix_medics.png`** — Санитары · способность «Полевая операция»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two field medics in white caps marked with a green plus, carrying white satchels and glowing green vials, one wearing a gas mask, faction accent #d9783a burnt orange.

**`phoenix_sappers.png`** — Сапёры · способность «Подрыв»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked sappers with big wrenches, one in a beret, faction accent #d9783a burnt orange.

**`phoenix_howitzer.png`** — Гаубица · способность «Дымовая завеса»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a big-wheeled field gun with a long barrel, an officer in a cap and a masked gunner, faction accent #d9783a burnt orange.

**`phoenix_heavy.png`** — Ремонтная экзоброня · способность «Ремонтный манипулятор»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a bulky repair exosuit with a mechanical claw arm, a green repair lamp on the chest and smoking stacks, faction accent #d9783a burnt orange.

### Инженер Призрак — Отдел «Призрак» (акцент #3fb7a8)

**`ghost_line.png`** — Стрелки-техники · способность «Глушилка»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #3fb7a8 teal.

**`ghost_drones.png`** — Дроны-разведчики · способность «Целеуказание»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two small hovering twin-rotor recon drones with a single amber lamp, faction accent #3fb7a8 teal.

**`ghost_automatons.png`** — Автоматоны · способность «Перегрузка»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two boxy riveted combat automatons with one glowing cyan eye and piston arms, faction accent #3fb7a8 teal.

**`ghost_tesla.png`** — Разрядная пушка · способность «Цепная молния»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a wheeled brass tesla coil cannon crackling with cyan sparks, operated by an engineer in goggles, faction accent #3fb7a8 teal.

**`ghost_heavy.png`** — Шагоход «Призрак» · способность «Электромагнитный импульс»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a heavy four-legged walker with an armored hull, side guns and headlamps, faction accent #3fb7a8 teal.

### Генерал Шторм — Бронекорпус «Шторм» (акцент #a3b34a)

**`storm_line.png`** — Мотострелки · способность «Десант с брони»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #a3b34a olive-lime.

**`storm_cars.png`** — Бронеавтомобиль · способность «Пулемётная очередь»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a boxy four-wheeled armored car with a small turret, faction accent #a3b34a olive-lime.

**`storm_tankers.png`** — Танковый десант · способность «Прорыв обороны»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked assault troopers, one with a trench cleaver, one with a stubby submachine gun, faction accent #a3b34a olive-lime.

**`storm_spg.png`** — Самоходная мортира · способность «Беглый огонь»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a tracked self-propelled mortar with a short thick barrel, faction accent #a3b34a olive-lime.

**`storm_heavy.png`** — Шагоход-танк «Шторм» · способность «Главный калибр»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a four-legged walking tank with a turret and long gun, faction accent #a3b34a olive-lime.

## Флот (общий для всех командиров)

**`transport.png`** — Десантный катер

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #4c9ce5 blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a small olive landing boat with a ramp and a masked soldier aboard, small waves.

**`gunboat.png`** — Канонерка

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #4c9ce5 blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a riveted gunboat with a deckhouse, smoking funnel and a long deck gun, small waves.

**`ironclad.png`** — Бронекатер

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #4c9ce5 blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: an armored ram boat with a pointed steel prow, smoking funnel and short gun, small waves.

## Нейтральные войска (NPC и пираты)

**`rifles.png`** — Стрелки (NPC, смотрит вправо, игра сама отзеркалит)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands.

**`scouts.png`** — Разведчики (NPC, смотрит вправо, игра сама отзеркалит)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two light scouts in field caps, one with binoculars, one with a short rifle, light packs.

**`assault.png`** — Штурмовики (NPC, смотрит вправо, игра сама отзеркалит)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked assault troopers, one with a trench cleaver, one with a stubby submachine gun.

**`artillery.png`** — Артиллерия (NPC, смотрит вправо, игра сама отзеркалит)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a stubby trench mortar on a baseplate with a masked loader and an officer with binoculars.

**`armor.png`** — Бронетехника (NPC, смотрит вправо, игра сама отзеркалит)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a bulky dieselpunk power-armour exosuit with two smoking exhaust stacks, slit visor helmet, giant drill arm, chest stripes.

## Портреты командиров (2:3, 640×960, `client/public/art/commanders/<id>-v2.webp`)

Новые портреты в чиби-стиле заменят текущие полуреалистичные. После генерации поменяй суффикс `-v1` на `-v2` в `client/src/Commander.tsx`.

**`raven-v2.webp`** — Генерал Рейвен

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. stern general with grey temples, charcoal coat, crimson armband, officer cap. No text, no logos, no real insignia, no real person likeness.

**`valkyrie-v2.webp`** — Командир Валькирия

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. calm female scout commander with short ash-blonde hair, binoculars, steel-blue scarf. No text, no logos, no real insignia, no real person likeness.

**`titan-v2.webp`** — Полковник Титан

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. huge bald veteran colonel with grey beard in heavy plated armour, brass trims, arms folded. No text, no logos, no real insignia, no real person likeness.

**`phoenix-v2.webp`** — Маршал Феникс

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. confident female logistics marshal with dark skin, black hair bun, orange scarf, supply tablet. No text, no logos, no real insignia, no real person likeness.

**`ghost-v2.webp`** — Инженер Призрак

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. young engineer with goggles on forehead, teal circuit module on chest, multitool. No text, no logos, no real insignia, no real person likeness.

**`storm-v2.webp`** — Генерал Шторм

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. energetic tank general with dark skin, tanker headset around neck, olive crew suit, lime accent patch. No text, no logos, no real insignia, no real person likeness.

## Ландшафт (на будущее, `client/public/art/tiles/<biome>.png`)

Тайлы пока рисует код. Растровые тайлы подключаются отдельным шагом, файлы можно готовить уже сейчас.

**`plain.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: lush grass with tufts, small flowers and pebbles. No text.

**`forest.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dense mix of round leafy trees and pines. No text.

**`hills.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: grassy hills with mossy grey boulders. No text.

**`mountain.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: two rocky peaks with snow caps. No text.

**`desert.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: sand with dune ridges and a dry shrub. No text.

**`beach.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: pale sand with a palm tree and small rocks. No text.

**`river.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: grass tile with a winding blue river. No text.

**`lake.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: calm blue water with ripples. No text.

**`sea.png`**

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: deep blue sea with white wave crests. No text.

## Здания (на будущее, `client/public/art/buildings/<kind>-<stage>.png`, stage 1–4)

**`hq`** — Главный штаб

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Главный штаб building, warm tiled roof, plaster walls, (Командный центр. Уровень штаба ограничивает уровни остальных зданий и открывает новые постройки.). No text.

**`power`** — Электростанция

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Электростанция building, warm tiled roof, plaster walls, (Даёт энергию производственным зданиям.). No text.

**`quarry`** — Металлургический карьер

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Металлургический карьер building, warm tiled roof, plaster walls, (Добывает металл каждую минуту.). No text.

**`barracks`** — Казармы

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Казармы building, warm tiled roof, plaster walls, (Открывает подготовку стрелков в разделе «Армия».). No text.

**`refinery`** — НПЗ

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military НПЗ building, warm tiled roof, plaster walls, (Перерабатывает нефть в топливо.). No text.

**`oil_well`** — Нефтедобывающий комплекс

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Нефтедобывающий комплекс building, warm tiled roof, plaster walls, (Добывает сырую нефть для НПЗ.). No text.

**`farm`** — Агрокомплекс

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Агрокомплекс building, warm tiled roof, plaster walls, (Производит провизию для подготовки войск.). No text.

**`warehouse`** — Склад

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Склад building, warm tiled roof, plaster walls, (Увеличивает вместимость каждого ресурса.). No text.

**`watchtower`** — Сторожевая башня

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Сторожевая башня building, warm tiled roof, plaster walls, (Расширяет обзор мировой карты вокруг базы.). No text.

**`electronics`** — Электронный завод

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Электронный завод building, warm tiled roof, plaster walls, (Превращает металл в электронику.). No text.

**`shipyard`** — Верфь

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Верфь building, warm tiled roof, plaster walls, (Строит корабли. С флотом соединение ходит по морям, озёрам и рекам.). No text.

**`repair`** — Ремонтный центр

> Isometric hex diorama tile for IRON FRONT, flat-top view at 30°, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background, 256×192 px. Subject: dieselpunk military Ремонтный центр building, warm tiled roof, plaster walls, (Восстанавливает здоровье отрядов вне боя.). No text.

