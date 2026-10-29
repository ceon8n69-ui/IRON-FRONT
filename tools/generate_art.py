"""Generate IRON FRONT raster art with the OpenAI Images API.

Reads tools/art-manifest.json, generates the selected entries and writes the
game-ready files in place:
  unit      -> 256x224 RGBA PNG, figure trimmed, centred, feet at 82% height
  portrait  -> 640x960 WebP
  tile / building -> 512px-wide RGBA PNG (not wired into the game yet)
Originals are kept under art-source/ (git-ignored) for re-cropping.

    OPENAI_API_KEY=... python tools/generate_art.py --keys raven_line,titan_mg
    OPENAI_API_KEY=... python tools/generate_art.py --kind unit            # every unit
    python tools/generate_art.py --keys raven_line --from-file img.png     # post-process only

Options: --quality low|medium|high (default medium), --model (default gpt-image-2.5-flare;
also gpt-image-2.5-sunburst for finer detail),
--dry-run (print what would be generated).
"""
import argparse, base64, io, json, os, sys, time
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools/art-manifest.json"
SOURCE = ROOT / "art-source"
API = "https://api.openai.com/v1/images/generations"
SIZE = {"unit": "1536x1024", "portrait": "1024x1536", "tile": "1024x1024", "building": "1024x1024", "item": "1024x1024", "world": "1024x1024"}
UNIT_W, UNIT_H, FEET = 256, 224, 0.82


def generate(prompt, kind, model, quality):
    import requests
    body = {"model": model, "prompt": prompt, "size": SIZE[kind], "quality": quality, "n": 1}
    if kind != "portrait":
        body.update({"background": "transparent", "output_format": "png"})
    for attempt in range(4):
        r = requests.post(API, timeout=300, json=body,
                          headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"})
        if r.status_code == 200:
            return base64.b64decode(r.json()["data"][0]["b64_json"])
        if r.status_code in (429, 500, 502, 503) and attempt < 3:
            time.sleep(10 * (attempt + 1))
            continue
        raise RuntimeError(f"OpenAI {r.status_code}: {r.text[:400]}")


def fit_unit(img):
    """Trim to the figure, scale into 256x224 with feet at 82% height, centred."""
    img = img.convert("RGBA")
    box = img.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    if not box:
        raise ValueError("image is fully transparent")
    fig = img.crop(box)
    feet_y = round(UNIT_H * FEET)
    scale = min((UNIT_W * 0.92) / fig.width, (feet_y - 6) / fig.height)
    fig = fig.resize((max(1, round(fig.width * scale)), max(1, round(fig.height * scale))), Image.LANCZOS)
    out = Image.new("RGBA", (UNIT_W, UNIT_H), (0, 0, 0, 0))
    out.alpha_composite(fig, ((UNIT_W - fig.width) // 2, feet_y - fig.height))
    return out


def fit_portrait(img):
    img = img.convert("RGB")
    target = 2 / 3
    w, h = img.size
    if w / h > target:
        nw = round(h * target); img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = round(w / target); img = img.crop((0, 0, w, nh))
    return img.resize((640, 960), Image.LANCZOS)


def fit_item(img):
    """Trim to the object and centre it in a 256x256 transparent square."""
    img = img.convert("RGBA")
    box = img.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox() or (0, 0, *img.size)
    obj = img.crop(box)
    scale = 232 / max(obj.width, obj.height)
    obj = obj.resize((max(1, round(obj.width * scale)), max(1, round(obj.height * scale))), Image.LANCZOS)
    out = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    out.alpha_composite(obj, ((256 - obj.width) // 2, (256 - obj.height) // 2))
    return out


def fit_tile(img):
    img = img.convert("RGBA")
    box = img.getchannel("A").getbbox() or (0, 0, *img.size)
    img = img.crop(box)
    return img.resize((512, max(1, round(512 * img.height / img.width))), Image.LANCZOS)


def save(entry, raw):
    img = Image.open(io.BytesIO(raw))
    kind = entry["kind"]
    out = (fit_unit(img) if kind == "unit" else fit_portrait(img) if kind == "portrait"
           else fit_item(img) if kind == "item" else fit_tile(img))
    path = ROOT / entry["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".webp":
        out.save(path, "WEBP", quality=86, method=6)
    else:
        out.save(path, "PNG", optimize=True)
    return path, out.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", default="", help="comma-separated manifest keys")
    ap.add_argument("--kind", default="", help="unit, portrait, tile or building")
    ap.add_argument("--quality", default="medium", choices=["low", "medium", "high"])
    ap.add_argument("--model", default="gpt-image-2.5-flare")  # gpt-image-1 was shut down 2026-10-23
    ap.add_argument("--from-file", help="post-process an existing image instead of calling the API (one key)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    items = json.loads(MANIFEST.read_text())
    keys = {k.strip() for k in a.keys.split(",") if k.strip()}
    chosen = [e for e in items if (not keys or e["key"] in keys) and (not a.kind or e["kind"] == a.kind)]
    unknown = keys - {e["key"] for e in items}
    if unknown:
        sys.exit(f"Unknown keys: {', '.join(sorted(unknown))}")
    if not chosen:
        sys.exit("Nothing selected: pass --keys and/or --kind")
    if a.dry_run:
        for e in chosen:
            print(e["key"], "->", e["path"])
        return
    if not a.from_file and not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set")
    SOURCE.mkdir(exist_ok=True)
    failures = []
    for e in chosen:
        try:
            raw = Path(a.from_file).read_bytes() if a.from_file else generate(e["prompt"], e["kind"], a.model, a.quality)
            (SOURCE / f"{e['key']}.png").write_bytes(raw)
            path, size = save(e, raw)
            print(f"OK   {e['key']:22} {size[0]}x{size[1]} -> {path.relative_to(ROOT)}", flush=True)
        except Exception as exc:  # keep going; report at the end
            failures.append(e["key"])
            print(f"FAIL {e['key']:22} {exc}", flush=True)
    if failures:
        sys.exit(f"{len(failures)} failed: {', '.join(failures)}")


if __name__ == "__main__":
    main()
