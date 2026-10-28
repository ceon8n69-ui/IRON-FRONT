"""Build the art prompt pack from game config.

Writes docs/ART-PROMPTS.md (for people) and tools/art-manifest.json (for
tools/generate_art.py). Run from the repo root:
    PYTHONPATH=server python tools/build_art_prompts.py
"""
import json
from pathlib import Path
from app.config import UNITS, FACTIONS, HEROES, BUILDINGS

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
    for b, d in TERRAIN.items():
        out.append({"key": f"tile-{b}", "kind": "tile", "group": "Ландшафт (подключение позже)", "title": b,
                    "path": f"client/public/art/tiles/{b}.png", "prompt": TILE_PROMPT.format(subj=d)})
    for k, b in BUILDINGS.items():
        out.append({"key": f"building-{k}", "kind": "building", "group": "Здания (подключение позже)", "title": b["name"],
                    "path": f"client/public/art/buildings/{k}.png",
                    "prompt": TILE_PROMPT.format(subj=f"dieselpunk military {b['name']} building, warm tiled roof, plaster walls, ({b['about']})")})
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
