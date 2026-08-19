"""Generate Ocean Mist Theme store assets (screenshots + promo) using PIL.

Code-first approach (per project rules). All colors are read dynamically
from manifest.json so they never drift from the actual theme.

Assets produced:
  store-assets/screenshots/en/screenshot-1-browser.png  (1280x800)
  store-assets/promo/440x280.png                        (440x280, English)
  store-assets/promo/1400x560.png                       (1400x560, English)

Chrome Theme store assets are ENGLISH ONLY (per chrome-theme-asset-english-only).
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"

# ---- palette (dynamic from manifest) ----
def palette():
    c = json.loads(MANIFEST.read_text(encoding="utf-8"))["theme"]["colors"]
    def hx(k):
        return tuple(c[k])
    return {
        "deep": hx("frame"),        # #3368A0
        "sky": (102, 163, 191),      # #66A3BF
        "mist": (200, 223, 219),     # #C8DFDB
        "warm": (242, 239, 231),     # #F2EFE7
    }

P = palette()

def font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

def draw_center(d, cx, cy, s, f, fill):
    b = d.textbbox((0, 0), s, font=f)
    w = b[2] - b[0]
    h = b[3] - b[1]
    d.text((cx - w / 2 - b[0], cy - h / 2 - b[1]), s, font=f, fill=fill)

# ---------- Browser mockup (1280x800) ----------
def render_browser(path):
    W, H = 1280, 800
    img = Image.new("RGB", (W, H), P["warm"])
    d = ImageDraw.Draw(img)

    # --- Frame + tab strip (deep ocean blue, height 64) ---
    d.rectangle([0, 0, W, 64], fill=P["deep"])
    # inactive tabs sit on the frame
    d.rounded_rectangle([380, 14, 610, 64], radius=10, fill=P["sky"])
    draw_center(d, 495, 39, "Reference", font(14), P["warm"])
    d.rounded_rectangle([620, 14, 850, 64], radius=10, fill=P["deep"])
    draw_center(d, 735, 39, "Inbox", font(14), P["warm"])
    # active tab overlaps the toolbar seam
    d.rounded_rectangle([70, 6, 370, 64], radius=10, fill=P["warm"])
    draw_center(d, 220, 35, "Coastal Workspace", font(14, True), P["deep"])

    # window controls + title stay on top of tab
    for off in [20, 38, 56]:
        d.ellipse([off, 26, off + 12, 38], fill=P["warm"])
    draw_center(d, W - 200, 32, "Ocean Mist  -  New Tab", font(18), P["warm"])

    # --- Toolbar (warm white) ---
    d.rectangle([0, 64, W, 104], fill=P["warm"])
    # back/forward/reload icons (sky)
    for x in [28, 60, 92]:
        d.ellipse([x, 80, x + 18, 98], fill=P["sky"])
    # omnibox
    d.rounded_rectangle([140, 76, 1000, 100], radius=12, fill=P["warm"],
                        outline=P["mist"], width=2)
    draw_center(d, 570, 88, "https://coastal.example.com", font(15), P["deep"])

    # --- Bookmarks bar (mist cyan) ---
    d.rectangle([0, 104, W, 136], fill=P["mist"])
    bm = ["Work", "Mail", "Calendar", "Notes", "Reading"]
    x = 28
    for t in bm:
        draw_center(d, x + 40, 120, t, font(13), P["deep"])
        x += 110

    # --- Content area ---
    d.rectangle([0, 136, W, H], fill=P["warm"])
    cards = [
        (40, 180, 400, 460, "Deep Ocean Blue", "#3368A0", P["deep"]),
        (440, 180, 800, 460, "Soft Sky Blue", "#66A3BF", P["sky"]),
        (840, 180, 1200, 460, "Mist Cyan", "#C8DFDB", P["mist"]),
    ]
    for (x0, y0, x1, y1, name, hexv, swatch) in cards:
        d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=P["warm"],
                            outline=P["mist"], width=2)
        # swatch
        sw = (x0 + 24, y0 + 24, x1 - 24, y0 + 120)
        d.rounded_rectangle(sw, radius=12, fill=swatch)
        # accent line
        d.rounded_rectangle([x0 + 24, y0 + 140, x1 - 24, y0 + 156],
                            radius=8, fill=P["sky"])
        draw_center(d, (x0 + x1) / 2, y0 + 200, name, font(20, True), P["deep"])
        draw_center(d, (x0 + x1) / 2, y0 + 232, hexv, font(16), P["sky"])
        d.rounded_rectangle([x0 + 40, y1 - 70, x1 - 40, y1 - 30],
                            radius=14, fill=P["mist"])
        draw_center(d, (x0 + x1) / 2, y1 - 50, "Add to Chrome", font(15, True), P["deep"])

    # --- Bottom note card ---
    d.rounded_rectangle([40, 500, 1200, 760], radius=16, fill=P["warm"],
                        outline=P["mist"], width=2)
    draw_center(d, 620, 560, "A calm, minimalist coastal workspace", font(22, True), P["deep"])
    draw_center(d, 620, 600, "Soft blues, warm white, and quiet mist for a premium browsing feel.",
                font(16), P["sky"])
    draw_center(d, 620, 650,
                "No gradients. No patterns. Just the stillness of ocean morning light.",
                font(15), P["deep"])
    draw_center(d, 620, 710,
                "Ocean Mist Theme  -  built for focused, comfortable daily browsing.",
                font(14), P["sky"])

    img.convert("RGB").save(path, "PNG")
    print("wrote", path)

# ---------- Promo tiles (English only) ----------
def render_promo_small(path):
    W, H = 440, 280
    img = Image.new("RGB", (W, H), P["deep"])
    d = ImageDraw.Draw(img)
    # soft mist band
    d.rounded_rectangle([0, 170, W, H], radius=0, fill=P["sky"])
    d.rounded_rectangle([0, 210, W, H], radius=0, fill=P["mist"])
    draw_center(d, W / 2, 70, "Ocean Mist", font(34, True), P["warm"])
    draw_center(d, W / 2, 112, "A calm coastal Chrome theme", font(15), P["warm"])
    # CTA
    d.rounded_rectangle([W / 2 - 90, 232, W / 2 + 90, 262], radius=14, fill=P["warm"])
    draw_center(d, W / 2, 247, "Add to Chrome", font(15, True), P["deep"])
    img.convert("RGB").save(path, "PNG")
    print("wrote", path)

def render_promo_large(path):
    W, H = 1400, 560
    img = Image.new("RGB", (W, H), P["deep"])
    d = ImageDraw.Draw(img)
    # layered calm bands
    d.rounded_rectangle([0, 360, W, H], radius=0, fill=P["sky"])
    d.rounded_rectangle([0, 440, W, H], radius=0, fill=P["mist"])
    draw_center(d, W / 2, 150, "Ocean Mist Theme", font(60, True), P["warm"])
    draw_center(d, W / 2, 220,
                "Minimalist coastal calm for a focused browsing experience",
                font(26), P["warm"])
    draw_center(d, W / 2, 280,
                "Soft blues, warm white, and quiet mist - premium, no clutter",
                font(20), P["warm"])
    # CTA
    d.rounded_rectangle([W / 2 - 130, 480, W / 2 + 130, 530], radius=20, fill=P["warm"])
    draw_center(d, W / 2, 505, "Add to Chrome", font(22, True), P["deep"])
    img.convert("RGB").save(path, "PNG")
    print("wrote", path)

def main():
    (ROOT / "store-assets" / "screenshots" / "en").mkdir(parents=True, exist_ok=True)
    (ROOT / "store-assets" / "promo").mkdir(parents=True, exist_ok=True)
    render_browser(ROOT / "store-assets" / "screenshots" / "en" / "screenshot-1-browser.png")
    render_promo_small(ROOT / "store-assets" / "promo" / "440x280.png")
    render_promo_large(ROOT / "store-assets" / "promo" / "1400x560.png")

if __name__ == "__main__":
    main()
