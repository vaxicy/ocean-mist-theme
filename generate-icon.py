"""Generate Ocean Mist Theme store icon (128x128) using PIL.
Colors are read from manifest.json so they stay in sync.
No letter/logo, just a calm coastal abstract mark.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"

def rgb(key):
    c = json.loads(MANIFEST.read_text(encoding="utf-8"))["theme"]["colors"]
    v = c[key]
    return tuple(v)

def main():
    deep = rgb("frame")       # #3368A0
    sky = rgb("bookmark_text") if False else (102, 163, 191)  # #66A3BF
    mist = (200, 223, 219)    # #C8DFDB
    warm = (242, 239, 231)    # #F2EFE7

    S = 128
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Rounded-square background: deep ocean blue
    r = 28
    d.rounded_rectangle([0, 0, S, S], radius=r, fill=deep)

    # Soft horizontal mist bands (coastal atmosphere, no gradient/textures)
    band_colors = [mist, sky, warm]
    bands = [
        (40, 60),    # top mist
        (62, 84),    # mid sky
        (86, 110),   # lower warm
    ]
    for (y0, y1), col in zip(bands, band_colors):
        d.rounded_rectangle([14, y0, S - 14, y1], radius=10, fill=col)

    # A single calm circle (sun/horizon hint) in deep blue over the mist
    cx, cy = S // 2, 71
    rad = 13
    d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=deep)

    out = ROOT / "store-assets" / "icon.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print("wrote", out)

if __name__ == "__main__":
    main()
