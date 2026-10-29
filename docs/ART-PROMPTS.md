# IRON FRONT — пакет промптов для растрового арта

Генерация запускается сама через GitHub Actions: workflow **Generate art** (`tools/generate_art.py`), ключ `OPENAI_API_KEY` в секретах репозитория.
Промпты можно использовать и вручную в любом генераторе. Файлы кладутся по указанным путям.

## Форматы

- Юниты: PNG 256×224 с прозрачностью, фигура смотрит вправо, ноги на 82% высоты. Скрипт сам обрезает и центрирует.
- Портреты: WebP 640×960 (2:3).
- Артефакты: WebP 256×256 с прозрачностью.
- Тайлы и здания: PNG с прозрачностью; в игре пока рисуются кодом.

Файл генерируется из конфига: `PYTHONPATH=server python tools/build_art_prompts.py`.

## Генерал Рейвен — Железный легион

**`raven_line`** → `client/public/art/units/raven_line.png` — Стрелки легиона · способность «Штыковая атака»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #c8433a crimson.

**`raven_scouts`** → `client/public/art/units/raven_scouts.png` — Егеря · способность «Марш-бросок»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two light scouts in field caps, one with binoculars, one with a short rifle, light packs, faction accent #c8433a crimson.

**`raven_assault`** → `client/public/art/units/raven_assault.png` — Ударники · способность «Гранаты»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked assault troopers, one with a trench cleaver, one with a stubby submachine gun, faction accent #c8433a crimson.

**`raven_artillery`** → `client/public/art/units/raven_artillery.png` — Траншейная мортира · способность «Огневой вал»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a stubby trench mortar on a baseplate with a masked loader and an officer with binoculars, faction accent #c8433a crimson.

**`raven_heavy`** → `client/public/art/units/raven_heavy.png` — Экзоброня «Таран» · способность «Таранный удар»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c8433a crimson, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a bulky dieselpunk power-armour exosuit with two smoking exhaust stacks, slit visor helmet, giant drill arm, chest stripes, faction accent #c8433a crimson.

## Командир Валькирия — Серый дозор

**`valkyrie_line`** → `client/public/art/units/valkyrie_line.png` — Стрелки дозора · способность «Прицельный залп»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #5f8fd0 steel blue.

**`valkyrie_walker`** → `client/public/art/units/valkyrie_walker.png` — Шагоход-разведчик · способность «Прожектор»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a small four-legged scout walker with twin headlamps casting light beams and a masked gunner riding on top, faction accent #5f8fd0 steel blue.

**`valkyrie_raiders`** → `client/public/art/units/valkyrie_raiders.png` — Диверсанты · способность «Засада»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two saboteurs, one in goggles with a knife, one hooded with a compact gun, no backpacks, faction accent #5f8fd0 steel blue.

**`valkyrie_snipers`** → `client/public/art/units/valkyrie_snipers.png` — Снайперская пара · способность «Выстрел в офицера»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a hooded kneeling sniper with a very long rifle and a spotter in a cap with binoculars, faction accent #5f8fd0 steel blue.

**`valkyrie_heavy`** → `client/public/art/units/valkyrie_heavy.png` — Шагоход «Гончая» · способность «Прыжок»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #5f8fd0 steel blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a heavy four-legged walker with an armored hull, side guns and headlamps, faction accent #5f8fd0 steel blue.

## Полковник Титан — Стальной заслон

**`titan_line`** → `client/public/art/units/titan_line.png` — Стрелки заслона · способность «Окопаться»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #c9a04a brass gold.

**`titan_mg`** → `client/public/art/units/titan_mg.png` — Пулемётный расчёт · способность «Подавляющий огонь»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked soldiers crewing a wheeled heavy machine gun with a small gun shield, faction accent #c9a04a brass gold.

**`titan_shields`** → `client/public/art/units/titan_shields.png` — Щитоносцы · способность «Стена щитов»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked soldiers carrying tall riveted steel shields with an accent stripe, faction accent #c9a04a brass gold.

**`titan_gun`** → `client/public/art/units/titan_gun.png` — Полевая пушка · способность «Шрапнель»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a big-wheeled field gun with a long barrel, an officer in a cap and a masked gunner, faction accent #c9a04a brass gold.

**`titan_heavy`** → `client/public/art/units/titan_heavy.png` — Экзоброня «Бастион» · способность «Несокрушимость»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #c9a04a brass gold, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a bulky power-armour exosuit with smoking exhaust stacks and a heavy arm cannon, thick shoulder pauldrons, faction accent #c9a04a brass gold.

## Маршал Феникс — Тыловой корпус

**`phoenix_line`** → `client/public/art/units/phoenix_line.png` — Стрелки снабжения · способность «Сухпаёк»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #d9783a burnt orange.

**`phoenix_medics`** → `client/public/art/units/phoenix_medics.png` — Санитары · способность «Полевая операция»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two field medics in white caps marked with a green plus, carrying white satchels and glowing green vials, one wearing a gas mask, faction accent #d9783a burnt orange.

**`phoenix_sappers`** → `client/public/art/units/phoenix_sappers.png` — Сапёры · способность «Подрыв»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked sappers with big wrenches, one in a beret, faction accent #d9783a burnt orange.

**`phoenix_howitzer`** → `client/public/art/units/phoenix_howitzer.png` — Гаубица · способность «Дымовая завеса»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a big-wheeled field gun with a long barrel, an officer in a cap and a masked gunner, faction accent #d9783a burnt orange.

**`phoenix_heavy`** → `client/public/art/units/phoenix_heavy.png` — Ремонтная экзоброня · способность «Ремонтный манипулятор»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #d9783a burnt orange, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a bulky repair exosuit with a mechanical claw arm, a green repair lamp on the chest and smoking stacks, faction accent #d9783a burnt orange.

## Инженер Призрак — Отдел «Призрак»

**`ghost_line`** → `client/public/art/units/ghost_line.png` — Стрелки-техники · способность «Глушилка»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #3fb7a8 teal.

**`ghost_drones`** → `client/public/art/units/ghost_drones.png` — Дроны-разведчики · способность «Целеуказание»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two small hovering twin-rotor recon drones with a single amber lamp, faction accent #3fb7a8 teal.

**`ghost_automatons`** → `client/public/art/units/ghost_automatons.png` — Автоматоны · способность «Перегрузка»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two boxy riveted combat automatons with one glowing cyan eye and piston arms, faction accent #3fb7a8 teal.

**`ghost_tesla`** → `client/public/art/units/ghost_tesla.png` — Разрядная пушка · способность «Цепная молния»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a wheeled brass tesla coil cannon crackling with cyan sparks, operated by an engineer in goggles, faction accent #3fb7a8 teal.

**`ghost_heavy`** → `client/public/art/units/ghost_heavy.png` — Шагоход «Призрак» · способность «Электромагнитный импульс»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #3fb7a8 teal, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a heavy four-legged walker with an armored hull, side guns and headlamps, faction accent #3fb7a8 teal.

## Генерал Шторм — Бронекорпус «Шторм»

**`storm_line`** → `client/public/art/units/storm_line.png` — Мотострелки · способность «Десант с брони»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands, faction accent #a3b34a olive-lime.

**`storm_cars`** → `client/public/art/units/storm_cars.png` — Бронеавтомобиль · способность «Пулемётная очередь»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a boxy four-wheeled armored car with a small turret, faction accent #a3b34a olive-lime.

**`storm_tankers`** → `client/public/art/units/storm_tankers.png` — Танковый десант · способность «Прорыв обороны»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked assault troopers, one with a trench cleaver, one with a stubby submachine gun, faction accent #a3b34a olive-lime.

**`storm_spg`** → `client/public/art/units/storm_spg.png` — Самоходная мортира · способность «Беглый огонь»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a tracked self-propelled mortar with a short thick barrel, faction accent #a3b34a olive-lime.

**`storm_heavy`** → `client/public/art/units/storm_heavy.png` — Шагоход-танк «Шторм» · способность «Главный калибр»

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #a3b34a olive-lime, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a four-legged walking tank with a turret and long gun, faction accent #a3b34a olive-lime.

## Флот

**`transport`** → `client/public/art/units/transport.png` — Десантный катер

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #4c9ce5 blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a small olive landing boat with a ramp and a masked soldier aboard, small waves under the hull.

**`gunboat`** → `client/public/art/units/gunboat.png` — Канонерка

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #4c9ce5 blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a riveted gunboat with a deckhouse, smoking funnel and a long deck gun, small waves under the hull.

**`ironclad`** → `client/public/art/units/ironclad.png` — Бронекатер

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #4c9ce5 blue, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: an armored ram boat with a pointed steel prow, smoking funnel and short gun, small waves under the hull.

## NPC

**`rifles`** → `client/public/art/units/rifles.png` — Стрелки (NPC)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands.

**`scouts`** → `client/public/art/units/scouts.png` — Разведчики (NPC)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two light scouts in field caps, one with binoculars, one with a short rifle, light packs.

**`assault`** → `client/public/art/units/assault.png` — Штурмовики (NPC)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: two gas-masked assault troopers, one with a trench cleaver, one with a stubby submachine gun.

**`artillery`** → `client/public/art/units/artillery.png` — Артиллерия (NPC)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a stubby trench mortar on a baseplate with a masked loader and an officer with binoculars.

**`armor`** → `client/public/art/units/armor.png` — Бронетехника (NPC)

> Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour #8f4a44 dull red (neutral raiders), isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: a bulky dieselpunk power-armour exosuit with two smoking exhaust stacks, slit visor helmet, giant drill arm, chest stripes.

## Портреты командиров

**`portrait-raven`** → `client/public/art/commanders/raven-v2.webp` — Генерал Рейвен

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. stern but kind veteran general with grey temples and a short grey moustache, charcoal greatcoat with a crimson scarf, plain peaked cap without any emblem, holding a folded map. No text, no logos, no real insignia, no real person likeness.

**`portrait-valkyrie`** → `client/public/art/commanders/valkyrie-v2.webp` — Командир Валькирия

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. calm female scout commander with short ash-blonde hair, binoculars, steel-blue scarf. No text, no logos, no real insignia, no real person likeness.

**`portrait-titan`** → `client/public/art/commanders/titan-v2.webp` — Полковник Титан

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. huge bald veteran colonel with grey beard in heavy plated armour, brass trims, arms folded. No text, no logos, no real insignia, no real person likeness.

**`portrait-phoenix`** → `client/public/art/commanders/phoenix-v2.webp` — Маршал Феникс

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. confident female logistics marshal with dark skin, black hair bun, orange scarf, supply tablet. No text, no logos, no real insignia, no real person likeness.

**`portrait-ghost`** → `client/public/art/commanders/ghost-v2.webp` — Инженер Призрак

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. young engineer with goggles on forehead, teal circuit module on chest, multitool. No text, no logos, no real insignia, no real person likeness.

**`portrait-storm`** → `client/public/art/commanders/storm-v2.webp` — Генерал Шторм

> Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. energetic tank general with dark skin, tanker headset around neck, olive crew suit, lime accent patch. No text, no logos, no real insignia, no real person likeness.

## Артефакты командира

**`item-field-module`** → `client/public/art/equipment/field-module.webp` — Полевой модуль

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft green rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a compact olive field electronics module with brass dials and a small antenna.

**`item-garrison-module-v1`** → `client/public/art/equipment/garrison-module-v1.webp` — Трофейный модуль

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft green rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a battered captured tactical module with riveted steel casing and a red status lamp.

**`item-precision-module-v1`** → `client/public/art/equipment/precision-module-v1.webp` — Модуль точности

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft blue rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a precision targeting module with a round lens, crosshair glass and brass rings.

**`item-vanguard-module-v1`** → `client/public/art/equipment/vanguard-module-v1.webp` — Модуль «Авангард»

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft purple rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: an ornate vanguard command module with gold trims and a glowing amber core.

**`item-service-pistol`** → `client/public/art/equipment/service-pistol.webp` — Наградной пистолет

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft green rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: an ornate award pistol with engraved steel and a polished wooden grip.

**`item-marshal-sabre`** → `client/public/art/equipment/marshal-sabre.webp` — Сабля маршала

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft blue rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a curved officer sabre with a brass guard and a leather-wrapped hilt.

**`item-field-baton`** → `client/public/art/equipment/field-baton.webp` — Жезл фельдмаршала

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft purple rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a field marshal baton, dark lacquer with gold caps and small stars.

**`item-plated-greatcoat`** → `client/public/art/equipment/plated-greatcoat.webp` — Шинель с бронепластинами

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft green rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a folded charcoal greatcoat with riveted armour plates on the shoulders.

**`item-veteran-cuirass`** → `client/public/art/equipment/veteran-cuirass.webp` — Кираса ветерана

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft blue rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a dented steel chest cuirass with leather straps and brass buckles.

**`item-bastion-armor`** → `client/public/art/equipment/bastion-armor.webp` — Доспех «Бастион»

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft purple rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a heavy ornate chest armour with layered plates and gold rims.

**`item-valor-medal`** → `client/public/art/equipment/valor-medal.webp` — Медаль за отвагу

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft green rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a round bronze valour medal on a striped ribbon (fictional design, no real order).

**`item-staff-badge`** → `client/public/art/equipment/staff-badge.webp` — Знак штабиста

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft blue rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a silver staff officer badge with a compass and crossed pencils.

**`item-fortune-order`** → `client/public/art/equipment/fortune-order.webp` — Орден Фортуны

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft purple rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a star-shaped golden order with a four-leaf clover in the centre.

**`item-field-binoculars`** → `client/public/art/equipment/field-binoculars.webp` — Полевой бинокль

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft green rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a pair of olive field binoculars with leather strap.

**`item-quartermaster-bag`** → `client/public/art/equipment/quartermaster-bag.webp` — Сумка интенданта

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft blue rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a bulging leather quartermaster satchel with coins and papers sticking out.

**`item-route-atlas`** → `client/public/art/equipment/route-atlas.webp` — Атлас маршрутов

> Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, readable at 64px, soft purple rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: a thick map atlas with brass corners and a compass on the cover.

## Карта мира: природа

**`world-tree-oak`** → `client/public/art/world/tree-oak.png` — tree-oak

> Original isometric game map decoration for IRON FRONT world map: a round leafy green oak tree. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-tree-pine`** → `client/public/art/world/tree-pine.png` — tree-pine

> Original isometric game map decoration for IRON FRONT world map: a tall dark green pine tree. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-tree-autumn`** → `client/public/art/world/tree-autumn.png` — tree-autumn

> Original isometric game map decoration for IRON FRONT world map: a round orange and yellow autumn tree. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-bush`** → `client/public/art/world/bush.png` — bush

> Original isometric game map decoration for IRON FRONT world map: a small round green bush with a few flowers. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-rocks`** → `client/public/art/world/rocks.png` — rocks

> Original isometric game map decoration for IRON FRONT world map: a cluster of mossy grey boulders. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-mountain`** → `client/public/art/world/mountain.png` — mountain

> Original isometric game map decoration for IRON FRONT world map: a tall rocky grey mountain peak with a snow cap. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-palm`** → `client/public/art/world/palm.png` — palm

> Original isometric game map decoration for IRON FRONT world map: a palm tree with a coconut cluster. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-cactus`** → `client/public/art/world/cactus.png` — cactus

> Original isometric game map decoration for IRON FRONT world map: a desert cactus with a dry shrub and small rocks. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-reeds`** → `client/public/art/world/reeds.png` — reeds

> Original isometric game map decoration for IRON FRONT world map: a clump of green reeds and cattails. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-hillock`** → `client/public/art/world/hillock.png` — hillock

> Original isometric game map decoration for IRON FRONT world map: a small grassy hillock with a boulder on top. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

**`world-pirates`** → `client/public/art/world/pirates.png` — pirates

> Original isometric game map decoration for IRON FRONT world map: a rusty pirate gunboat with a patched sail, a small cannon and a smoking funnel, floating on a little patch of blue water. Single standalone object with only a tiny grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.

## Карта мира: объекты

**`world-pile`** → `client/public/art/world/pile.png` — pile

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a stack of supply crates, fuel barrels and metal ingots under a tarp, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-chest`** → `client/public/art/world/chest.png` — chest

> Original isometric game building for IRON FRONT base screen, small cosy diorama: an iron-bound treasure chest with brass corners, lid slightly open, warm gold glow inside, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-mine`** → `client/public/art/world/mine.png` — mine

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a mine entrance in a rock face with wooden supports, little rails and an ore cart, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-ruin`** → `client/public/art/world/ruin.png` — ruin

> Original isometric game building for IRON FRONT base screen, small cosy diorama: ancient overgrown stone ruins with broken columns and a fallen arch, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-camp`** → `client/public/art/world/camp.png` — camp

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a mercenary camp with two canvas tents, a campfire and a weapon rack, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-bunker`** → `client/public/art/world/bunker.png` — bunker

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a concrete military bunker with sandbags, a dark gun slit and barbed wire, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-base`** → `client/public/art/world/base.png` — base

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a fortified military outpost with log and stone walls, a gate, a central tower and an empty flagpole, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-capital`** → `client/public/art/world/capital.png` — capital

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a grand walled citadel city with a domed central keep, four towers and red tiled roofs, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-oil_field`** → `client/public/art/world/oil_field.png` — oil_field

> Original isometric game building for IRON FRONT base screen, small cosy diorama: an oil field with a steel lattice derrick, a pumpjack and a round storage tank, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-plant`** → `client/public/art/world/plant.png` — plant

> Original isometric game building for IRON FRONT base screen, small cosy diorama: an electronics plant with brick halls, teal glass roofs and radio antennas, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`world-radar`** → `client/public/art/world/radar.png` — radar

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a radar station with a large dish on a steel tower and a small operations hut, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

## Ландшафт (подключение позже)

**`tile-plain`** → `client/public/art/tiles/plain.png` — plain

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: lush grass with tufts, small flowers and pebbles. No text.

**`tile-forest`** → `client/public/art/tiles/forest.png` — forest

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dense mix of round leafy trees and pines. No text.

**`tile-hills`** → `client/public/art/tiles/hills.png` — hills

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: grassy hills with mossy grey boulders. No text.

**`tile-mountain`** → `client/public/art/tiles/mountain.png` — mountain

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: two rocky peaks with snow caps. No text.

**`tile-desert`** → `client/public/art/tiles/desert.png` — desert

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: sand with dune ridges and a dry shrub. No text.

**`tile-beach`** → `client/public/art/tiles/beach.png` — beach

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: pale sand with a palm tree and small rocks. No text.

**`tile-river`** → `client/public/art/tiles/river.png` — river

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: grass tile with a winding blue river. No text.

**`tile-lake`** → `client/public/art/tiles/lake.png` — lake

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: calm blue water with ripples. No text.

**`tile-sea`** → `client/public/art/tiles/sea.png` — sea

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: deep blue sea with white wave crests. No text.

## Здания базы

**`building-hq`** → `client/public/art/buildings/hq.png` — Главный штаб

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a command headquarters: two-storey brick and plaster building with a red tiled roof, a radio mast with a plain red pennant, sandbags at the door, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-power`** → `client/public/art/buildings/power.png` — Электростанция

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a power plant: brick generator hall with two tall chimneys puffing smoke, copper pipes and a transformer with insulators, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-quarry`** → `client/public/art/buildings/quarry.png` — Металлургический карьер

> Original isometric game building for IRON FRONT base screen, small cosy diorama: an open-pit metal quarry with a wooden crane, ore carts on little rails and piles of grey ore, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-barracks`** → `client/public/art/buildings/barracks.png` — Казармы

> Original isometric game building for IRON FRONT base screen, small cosy diorama: military barracks: long wooden hut with a green tin roof, sandbag wall, a training dummy and an empty flagpole, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-refinery`** → `client/public/art/buildings/refinery.png` — НПЗ

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a small fuel refinery with two round storage tanks, a distillation tower, pipes and fuel barrels, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-oil_well`** → `client/public/art/buildings/oil_well.png` — Нефтедобывающий комплекс

> Original isometric game building for IRON FRONT base screen, small cosy diorama: an oil derrick: steel lattice tower with a pumpjack, a black oil puddle and barrels, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-farm`** → `client/public/art/buildings/farm.png` — Агрокомплекс

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a farm: red barn with a tiled roof, golden wheat field rows and round haystacks, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-warehouse`** → `client/public/art/buildings/warehouse.png` — Склад

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a supply depot: big corrugated hangar with stacked crates, barrels and a small forklift, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-watchtower`** → `client/public/art/buildings/watchtower.png` — Сторожевая башня

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a wooden watchtower with a searchlight on top, a ladder and sandbags around its legs, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-electronics`** → `client/public/art/buildings/electronics.png` — Электронный завод

> Original isometric game building for IRON FRONT base screen, small cosy diorama: an electronics factory: brick workshop with teal glass windows, radio antennas and glowing cables, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-shipyard`** → `client/public/art/buildings/shipyard.png` — Верфь

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a small shipyard: wooden slipway on a water edge with a half-built boat hull and a crane, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

**`building-repair`** → `client/public/art/buildings/repair.png` — Ремонтный центр

> Original isometric game building for IRON FRONT base screen, small cosy diorama: a repair workshop: garage with an open door, workbench, big wrench sign and a small armored car on jacks, standing on a compact hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk 1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags with real symbols, no people.

