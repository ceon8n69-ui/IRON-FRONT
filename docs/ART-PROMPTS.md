# IRON FRONT — пакет промптов для растрового арта

Генерация запускается сама через GitHub Actions: workflow **Generate art** (`tools/generate_art.py`), ключ `OPENAI_API_KEY` в секретах репозитория.
Промпты можно использовать и вручную в любом генераторе. Файлы кладутся по указанным путям.

## Форматы

- Юниты: PNG 256×224 с прозрачностью, фигура смотрит вправо, ноги на 82% высоты. Скрипт сам обрезает и центрирует.
- Портреты: WebP 640×960 (2:3).
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

## Здания (подключение позже)

**`building-hq`** → `client/public/art/buildings/hq.png` — Главный штаб

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Главный штаб building, warm tiled roof, plaster walls, (Командный центр. Уровень штаба ограничивает уровни остальных зданий и открывает новые постройки.). No text.

**`building-power`** → `client/public/art/buildings/power.png` — Электростанция

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Электростанция building, warm tiled roof, plaster walls, (Даёт энергию производственным зданиям.). No text.

**`building-quarry`** → `client/public/art/buildings/quarry.png` — Металлургический карьер

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Металлургический карьер building, warm tiled roof, plaster walls, (Добывает металл каждую минуту.). No text.

**`building-barracks`** → `client/public/art/buildings/barracks.png` — Казармы

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Казармы building, warm tiled roof, plaster walls, (Открывает подготовку стрелков в разделе «Армия».). No text.

**`building-refinery`** → `client/public/art/buildings/refinery.png` — НПЗ

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military НПЗ building, warm tiled roof, plaster walls, (Перерабатывает нефть в топливо.). No text.

**`building-oil_well`** → `client/public/art/buildings/oil_well.png` — Нефтедобывающий комплекс

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Нефтедобывающий комплекс building, warm tiled roof, plaster walls, (Добывает сырую нефть для НПЗ.). No text.

**`building-farm`** → `client/public/art/buildings/farm.png` — Агрокомплекс

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Агрокомплекс building, warm tiled roof, plaster walls, (Производит провизию для подготовки войск.). No text.

**`building-warehouse`** → `client/public/art/buildings/warehouse.png` — Склад

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Склад building, warm tiled roof, plaster walls, (Увеличивает вместимость каждого ресурса.). No text.

**`building-watchtower`** → `client/public/art/buildings/watchtower.png` — Сторожевая башня

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Сторожевая башня building, warm tiled roof, plaster walls, (Расширяет обзор мировой карты вокруг базы.). No text.

**`building-electronics`** → `client/public/art/buildings/electronics.png` — Электронный завод

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Электронный завод building, warm tiled roof, plaster walls, (Превращает металл в электронику.). No text.

**`building-shipyard`** → `client/public/art/buildings/shipyard.png` — Верфь

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Верфь building, warm tiled roof, plaster walls, (Строит корабли. С флотом соединение ходит по морям, озёрам и рекам.). No text.

**`building-repair`** → `client/public/art/buildings/repair.png` — Ремонтный центр

> Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil edge under the tile, transparent background. Subject: dieselpunk military Ремонтный центр building, warm tiled roof, plaster walls, (Восстанавливает здоровье отрядов вне боя.). No text.

