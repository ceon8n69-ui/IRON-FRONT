"""Build the art prompt pack from game config.

Writes docs/ART-PROMPTS.md (for people) and tools/art-manifest.json (for
tools/generate_art.py). Run from the repo root:
    PYTHONPATH=server python tools/build_art_prompts.py
"""
import json
from pathlib import Path
from app.config import UNITS, FACTIONS, HEROES, BUILDINGS
from app.equipment import DEFINITIONS as ITEMS

ROOT = Path(__file__).resolve().parents[1]
ACC = {"raven": "#c8433a crimson", "valkyrie": "#5f8fd0 steel blue", "titan": "#c9a04a brass gold",
       "phoenix": "#d9783a burnt orange", "ghost": "#3fb7a8 teal", "storm": "#a3b34a olive-lime",
       "fleet": "#4c9ce5 blue", "npc": "#8f4a44 dull red (neutral raiders)"}
ART = {
    "rifleman": "three gas-masked riflemen in brodie helmets with long bayonet rifles, canister backpacks, accent armbands",
    "scout": "two light scouts in field caps, one with binoculars, one with a short rifle, light packs",
    "stormtrooper": "two gas-masked assault troopers, one with a trench cleaver, one with a stubby submachine gun",
    "raider": "two saboteurs, one in goggles with a knife, one hooded with a compact gun, no backpacks",
    "sniper": "a hooded kneeling sniper with a very long rifle and a spotter in a cap with binoculars",
    "shieldbearer": "two gas-masked soldiers carrying tall riveted steel shields with an accent stripe",
    "medic": "two field medics in white caps marked with a green plus, carrying white satchels and glowing green vials, one wearing a gas mask",
    "engineer": "two gas-masked sappers with big wrenches, one in a beret",
    "mg_crew": "two gas-masked soldiers crewing a wheeled heavy machine gun with a small gun shield",
    "mortar": "a stubby trench mortar on a baseplate with a masked loader and an officer with binoculars",
    "field_gun": "a big-wheeled field gun with a long barrel, an officer in a cap and a masked gunner",
    "tesla": "a wheeled brass tesla coil cannon crackling with cyan sparks, operated by an engineer in goggles",
    "drone": "two small hovering twin-rotor recon drones with a single amber lamp",
    "automaton": "two boxy riveted combat automatons with one glowing cyan eye and piston arms",
    "armored_car": "a boxy four-wheeled armored car with a small turret",
    "spg": "a tracked self-propelled mortar with a short thick barrel",
    "walker": "a small four-legged scout walker with twin headlamps casting light beams and a masked gunner riding on top",
    "walker_heavy": "a heavy four-legged walker with an armored hull, side guns and headlamps",
    "walker_tank": "a four-legged walking tank with a turret and long gun",
    "exosuit_drill": "a bulky dieselpunk power-armour exosuit with two smoking exhaust stacks, slit visor helmet, giant drill arm, chest stripes",
    "exosuit_cannon": "a bulky power-armour exosuit with smoking exhaust stacks and a heavy arm cannon, thick shoulder pauldrons",
    "exosuit_claw": "a bulky repair exosuit with a mechanical claw arm, a green repair lamp on the chest and smoking stacks",
    "boat_transport": "a small olive landing boat with a ramp and a masked soldier aboard, small waves under the hull",
    "gunboat": "a riveted gunboat with a deckhouse, smoking funnel and a long deck gun, small waves under the hull",
    "ironclad": "an armored ram boat with a pointed steel prow, smoking funnel and short gun, small waves under the hull",
}
UNIT_PROMPT = ("Original game unit sprite for IRON FRONT, chibi dieselpunk 1920s-inspired military, oversized heads, thick dark "
               "ink outline, flat cel shading with soft highlight, muted olive and steel palette with one faction accent colour "
               "{acc}, isometric 3/4 view facing right, transparent background, centered, feet near the bottom, full body visible, "
               "readable at 96px. No text, no logos, no real insignia, no red cross, no existing franchise characters. Subject: {subj}.")
PORTRAITS = {
    "raven": "stern but kind veteran general with grey temples and a short grey moustache, charcoal greatcoat with a crimson scarf, plain peaked cap without any emblem, holding a folded map",
    "valkyrie": "calm female scout commander with short ash-blonde hair, binoculars, steel-blue scarf",
    "titan": "huge bald veteran colonel with grey beard in heavy plated armour, brass trims, arms folded",
    "phoenix": "confident female logistics marshal with dark skin, black hair bun, orange scarf, supply tablet",
    "ghost": "young engineer with goggles on forehead, teal circuit module on chest, multitool",
    "storm": "energetic tank general with dark skin, tanker headset around neck, olive crew suit, lime accent patch",
}
PORTRAIT_PROMPT = ("Original chibi dieselpunk commander portrait for IRON FRONT, oversized head, thick dark ink outline, flat cel "
                   "shading, head to mid-thigh, 2:3 vertical, dark navy hangar background #101923 with soft rim light. {d}. "
                   "No text, no logos, no real insignia, no real person likeness.")
TILE_PROMPT = ("Isometric hex diorama tile for IRON FRONT, bright saturated colours, thick dark ink outline, visible dark soil "
               "edge under the tile, transparent background. Subject: {subj}. No text.")
ITEM_PROMPT = ("Original game artifact icon for IRON FRONT, chibi dieselpunk 1920s-inspired style, thick dark ink outline, "
               "flat cel shading with soft highlight, one single object centered, slight 3/4 view, transparent background, "
               "readable at 64px, soft {glow} rim glow. No text, no letters, no logos, no real insignia, no swastika, no red cross. Subject: {subj}.")
GLOW = {"uncommon": "green", "rare": "blue", "epic": "purple"}
ITEM_ART = {
    "field-module": "a compact olive field electronics module with brass dials and a small antenna",
    "garrison-module-v1": "a battered captured tactical module with riveted steel casing and a red status lamp",
    "precision-module-v1": "a precision targeting module with a round lens, crosshair glass and brass rings",
    "vanguard-module-v1": "an ornate vanguard command module with gold trims and a glowing amber core",
    "service-pistol": "an ornate award pistol with engraved steel and a polished wooden grip",
    "marshal-sabre": "a curved officer sabre with a brass guard and a leather-wrapped hilt",
    "field-baton": "a field marshal baton, dark lacquer with gold caps and small stars",
    "plated-greatcoat": "a folded charcoal greatcoat with riveted armour plates on the shoulders",
    "veteran-cuirass": "a dented steel chest cuirass with leather straps and brass buckles",
    "bastion-armor": "a heavy ornate chest armour with layered plates and gold rims",
    "valor-medal": "a round bronze valour medal on a striped ribbon (fictional design, no real order)",
    "staff-badge": "a silver staff officer badge with a compass and crossed pencils",
    "fortune-order": "a star-shaped golden order with a four-leaf clover in the centre",
    "field-binoculars": "a pair of olive field binoculars with leather strap",
    "quartermaster-bag": "a bulging leather quartermaster satchel with coins and papers sticking out",
    "route-atlas": "a thick map atlas with brass corners and a compass on the cover",
}
BUILDING_PROMPT = ("Original isometric game building for IRON FRONT base screen, small cosy diorama: {subj}, standing on a compact "
                   "hexagonal patch of bright grass with a thick dark soil edge, 3/4 isometric view from the south-east, chibi-dieselpunk "
                   "1920s style matching chunky toy-like proportions, thick dark ink outline, flat cel shading with soft highlights, bright "
                   "saturated warm colours, transparent background, centered, whole object visible. No text, no letters, no logos, no flags "
                   "with real symbols, no people.")
BUILDING_ART = {
    "hq": "a command headquarters: two-storey brick and plaster building with a red tiled roof, a radio mast with a plain red pennant, sandbags at the door",
    "power": "a power plant: brick generator hall with two tall chimneys puffing smoke, copper pipes and a transformer with insulators",
    "quarry": "an open-pit metal quarry with a wooden crane, ore carts on little rails and piles of grey ore",
    "barracks": "military barracks: long wooden hut with a green tin roof, sandbag wall, a training dummy and an empty flagpole",
    "refinery": "a small fuel refinery with two round storage tanks, a distillation tower, pipes and fuel barrels",
    "oil_well": "an oil derrick: steel lattice tower with a pumpjack, a black oil puddle and barrels",
    "farm": "a farm: red barn with a tiled roof, golden wheat field rows and round haystacks",
    "warehouse": "a supply depot: big corrugated hangar with stacked crates, barrels and a small forklift",
    "watchtower": "a wooden watchtower with a searchlight on top, a ladder and sandbags around its legs",
    "electronics": "an electronics factory: brick workshop with teal glass windows, radio antennas and glowing cables",
    "shipyard": "a small shipyard: wooden slipway on a water edge with a half-built boat hull and a crane",
    "repair": "a repair workshop: garage with an open door, workbench, big wrench sign and a small armored car on jacks",
}
WORLD_PROP = ("Original isometric game map decoration for IRON FRONT world map: {subj}. Single standalone object with only a tiny "
              "grass tuft at its base, 3/4 isometric view, chibi-dieselpunk toy-like proportions, thick dark ink outline, flat cel shading "
              "with soft highlights, bright saturated colours, transparent background, centered, whole object visible. No text, no ground tile.")
WORLD_PROPS = {
    "tree-oak": "a round leafy green oak tree", "tree-pine": "a tall dark green pine tree",
    "tree-autumn": "a round orange and yellow autumn tree", "bush": "a small round green bush with a few flowers",
    "rocks": "a cluster of mossy grey boulders", "mountain": "a tall rocky grey mountain peak with a snow cap",
    "palm": "a palm tree with a coconut cluster", "cactus": "a desert cactus with a dry shrub and small rocks",
    "reeds": "a clump of green reeds and cattails", "hillock": "a small grassy hillock with a boulder on top",
    "pirates": "a rusty pirate gunboat with a patched sail, a small cannon and a smoking funnel, floating on a little patch of blue water",
}
WORLD_OBJECTS = {
    "pile": "a stack of supply crates, fuel barrels and metal ingots under a tarp",
    "chest": "an iron-bound treasure chest with brass corners, lid slightly open, warm gold glow inside",
    "mine": "a mine entrance in a rock face with wooden supports, little rails and an ore cart",
    "ruin": "ancient overgrown stone ruins with broken columns and a fallen arch",
    "camp": "a mercenary camp with two canvas tents, a campfire and a weapon rack",
    "bunker": "a concrete military bunker with sandbags, a dark gun slit and barbed wire",
    "base": "a fortified military outpost with log and stone walls, a gate, a central tower and an empty flagpole",
    "capital": "a grand walled citadel city with a domed central keep, four towers and red tiled roofs",
    "oil_field": "an oil field with a steel lattice derrick, a pumpjack and a round storage tank",
    "plant": "an electronics plant with brick halls, teal glass roofs and radio antennas",
    "radar": "a radar station with a large dish on a steel tower and a small operations hut",
}
TERRAIN = {"plain": "lush grass with tufts, small flowers and pebbles", "forest": "dense mix of round leafy trees and pines",
           "hills": "grassy hills with mossy grey boulders", "mountain": "two rocky peaks with snow caps",
           "desert": "sand with dune ridges and a dry shrub", "beach": "pale sand with a palm tree and small rocks",
           "river": "grass tile with a winding blue river", "lake": "calm blue water with ripples",
           "sea": "deep blue sea with white wave crests"}


def entries():
    out = []
    for hero, f in FACTIONS.items():
        for v in f["units"]:
            u = UNITS[v["key"]]
            out.append({"key": v["key"], "kind": "unit", "group": f"{HEROES[hero]['name']} — {f['name']}",
                        "title": f"{u['name']} · способность «{u['ability']['name']}»",
                        "path": f"client/public/art/units/{v['key']}.png",
                        "prompt": UNIT_PROMPT.format(acc=ACC[hero], subj=f"{ART[v['art']]}, faction accent {ACC[hero]}")})
    for k in ("transport", "gunboat", "ironclad"):
        out.append({"key": k, "kind": "unit", "group": "Флот", "title": UNITS[k]["name"],
                    "path": f"client/public/art/units/{k}.png",
                    "prompt": UNIT_PROMPT.format(acc=ACC["fleet"], subj=ART[UNITS[k]["art"]])})
    for k in ("rifles", "scouts", "assault", "artillery", "armor"):
        out.append({"key": k, "kind": "unit", "group": "NPC", "title": f"{UNITS[k]['name']} (NPC)",
                    "path": f"client/public/art/units/{k}.png",
                    "prompt": UNIT_PROMPT.format(acc=ACC["npc"], subj=ART[UNITS[k]["art"]])})
    for h, d in PORTRAITS.items():
        out.append({"key": f"portrait-{h}", "kind": "portrait", "group": "Портреты командиров", "title": HEROES[h]["name"],
                    "path": f"client/public/art/commanders/{h}-v2.webp", "prompt": PORTRAIT_PROMPT.format(d=d)})
    for k, d in ITEMS.items():
        out.append({"key": f"item-{k}", "kind": "item", "group": "Артефакты командира", "title": d["name"],
                    "path": f"client/public/art/equipment/{k}.webp",
                    "prompt": ITEM_PROMPT.format(glow=GLOW[d["rarity"]], subj=ITEM_ART[k])})
    for k, d in WORLD_PROPS.items():
        out.append({"key": f"world-{k}", "kind": "world", "group": "Карта мира: природа", "title": k,
                    "path": f"client/public/art/world/{k}.png", "prompt": WORLD_PROP.format(subj=d)})
    for k, d in WORLD_OBJECTS.items():
        out.append({"key": f"world-{k}", "kind": "world", "group": "Карта мира: объекты", "title": k,
                    "path": f"client/public/art/world/{k}.png", "prompt": BUILDING_PROMPT.format(subj=d)})
    for b, d in TERRAIN.items():
        out.append({"key": f"tile-{b}", "kind": "tile", "group": "Ландшафт (подключение позже)", "title": b,
                    "path": f"client/public/art/tiles/{b}.png", "prompt": TILE_PROMPT.format(subj=d)})
    for k, b in BUILDINGS.items():
        out.append({"key": f"building-{k}", "kind": "building", "group": "Здания базы", "title": b["name"],
                    "path": f"client/public/art/buildings/{k}.png",
                    "prompt": BUILDING_PROMPT.format(subj=BUILDING_ART[k])})
    return out


def main():
    items = entries()
    (ROOT / "tools/art-manifest.json").write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n")
    md = ["# IRON FRONT — пакет промптов для растрового арта", "",
          "Генерация запускается сама через GitHub Actions: workflow **Generate art** (`tools/generate_art.py`), ключ `OPENAI_API_KEY` в секретах репозитория.",
          "Промпты можно использовать и вручную в любом генераторе. Файлы кладутся по указанным путям.", "",
          "## Форматы", "",
          "- Юниты: PNG 256×224 с прозрачностью, фигура смотрит вправо, ноги на 82% высоты. Скрипт сам обрезает и центрирует.",
          "- Портреты: WebP 640×960 (2:3).",
          "- Артефакты: WebP 256×256 с прозрачностью.",
          "- Тайлы и здания: PNG с прозрачностью; в игре пока рисуются кодом.", "",
          "Файл генерируется из конфига: `PYTHONPATH=server python tools/build_art_prompts.py`.", ""]
    group = None
    for e in items:
        if e["group"] != group:
            group = e["group"]
            md += [f"## {group}", ""]
        md += [f"**`{e['key']}`** → `{e['path']}` — {e['title']}", "", "> " + e["prompt"], ""]
    (ROOT / "docs/ART-PROMPTS.md").write_text("\n".join(md) + "\n")
    print(f"{len(items)} prompts")


if __name__ == "__main__":
    main()
