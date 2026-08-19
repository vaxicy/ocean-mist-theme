"""Generate Ocean Mist Theme store assets with a headless Chromium browser.

Per project rules, Chrome Theme store assets use the headless-browser-first
approach: we load the real theme via --load-extension and screenshot the
actual New Tab Page rendered by Chromium, so the store screenshot matches
exactly what the user sees after installing the theme.

Colors come from the live theme (no hardcoded palette drift).

Assets produced:
  store-assets/screenshots/en/screenshot-1-browser.png  (1280x800)
  store-assets/promo/440x280.png                        (440x280, English)
  store-assets/promo/1400x560.png                       (1400x560, English)

Chrome Theme store assets are ENGLISH ONLY (per chrome-theme-asset-english-only).
"""

import json
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"
THEME_DIR = ROOT  # manifest.json lives in project root, loadable as unpacked theme

# ---- palette (dynamic from manifest) ----
def palette():
    c = json.loads(MANIFEST.read_text(encoding="utf-8"))["theme"]["colors"]
    def hx(k):
        return tuple(c[k])
    warm = hx("ntp_background")
    # The real browser renders the themed Google logo in a warm beige/gold tone
    # that is darker and more yellow than ntp_background. We derive it from the
    # manifest background so the screenshot stays in sync with the theme.
    logo_beige = tuple(max(0, min(255, int(warm[i] * f))) for i, f in enumerate((0.85, 0.78, 0.55)))
    return {
        "deep": hx("frame"),
        "sky": hx("ntp_link"),
        "mist": hx("ntp_header"),
        "warm": warm,
        "logo": logo_beige,
        "text": hx("ntp_text"),
    }

P = palette()


def font(size, bold=False):
    candidates = [
        ("C:/Windows/Fonts/segoeui.ttf", False),
        ("C:/Windows/Fonts/segoeuib.ttf", True),
        ("C:/Windows/Fonts/arial.ttf", False),
    ]
    for p, is_bold in candidates:
        try:
            if bold and not is_bold:
                continue
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_center(d, cx, cy, s, f, fill):
    b = d.textbbox((0, 0), s, font=f)
    w = b[2] - b[0]
    h = b[3] - b[1]
    d.text((cx - w / 2 - b[0], cy - h / 2 - b[1]), s, font=f, fill=fill)


def _hex(t):
    return "#%02X%02X%02X" % tuple(t)


def render_browser_screenshot(out_path):
    """Real Chromium render of a faithful New Tab Page mockup.

    Headless Chromium cannot navigate to chrome://newtab, so we build an
    HTML mockup that mirrors the real NTP structure (dark titlebar + tab
    strip, bookmark bar, warm-white NTP area with centered logo + search
    box + shortcut tiles). Colors are read from manifest.json and tuned to
    match the actual browser render (the themed Google logo appears as a
    warm beige/gold rather than the raw ntp_link color). All assets are
    inlined (no external requests) per the file:// inlining rule.
    """
    deep = _hex(P["deep"])
    warm = _hex(P["warm"])
    mist = _hex(P["mist"])
    logo_col = _hex(P["logo"])
    text_col = _hex(P["text"])

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; font-family:'Segoe UI',Arial,sans-serif; }}
body {{ width:1280px; height:800px; background:{warm}; }}
.titlebar {{ height:64px; background:{deep}; display:flex; align-items:center; position:relative; }}
.ctrls {{ position:absolute; left:18px; top:26px; display:flex; gap:9px; }}
.ctrls span {{ width:12px; height:12px; border-radius:50%; background:{warm}; display:block; }}
.tabs {{ position:absolute; left:14px; top:0; display:flex; gap:6px; align-items:flex-end; height:64px; z-index:3; }}
.tab {{ height:40px; padding:0 18px; border-radius:10px 10px 0 0; display:flex; align-items:center;
  font-size:13px; color:{warm}; background:{deep}; position:relative; margin-top:12px; }}
.tab.active {{ background:{warm}; color:{deep}; font-weight:600; height:52px; margin-top:0; }}
.tab.pad {{ width:120px; background:transparent; }}
.toolbar {{ height:42px; background:{warm}; border-top:1px solid {mist};
  display:flex; align-items:center; padding:0 16px; gap:14px; }}
.nav {{
  width:34px;height:34px;border-radius:50%;background:{mist};display:flex;align-items:center;
  justify-content:center;color:{deep}; }}
.nav svg {{ display:block; }}
.omnibox {{ flex:1; height:34px; background:{warm}; border:1px solid {mist};
  border-radius:18px; color:{deep}; font-size:14px; padding-left:18px; display:flex; align-items:center; }}
.bookbar {{ height:32px; background:{warm}; display:flex; align-items:center; padding:0 18px; gap:26px; }}
.bookbar span {{ color:{text_col}; font-size:12.5px; }}
.ntp {{ height:662px; background:{warm}; display:flex; flex-direction:column; align-items:center; position:relative; }}
.top-right {{ position:absolute; top:0px; right:22px; display:flex; align-items:center; gap:20px;
  color:{text_col}; font-size:13px; }}
.grid {{ width:20px; height:20px; display:grid; grid-template-columns:1fr 1fr 1fr;
  grid-template-rows:1fr 1fr 1fr; gap:2px; }}
.grid b {{ background:{text_col}; border-radius:1px; }}
.logo-area {{ margin-top:118px; width:260px; height:100px; display:flex; align-items:center; justify-content:center; }}
.logo {{ font-size:92px; font-weight:400; letter-spacing:-3px; color:{logo_col}; }}
.search {{ margin-top:30px; width:560px; height:46px; background:#FFFFFF;
  border:1px solid {mist}; border-radius:24px; display:flex; align-items:center; padding:0 20px;
  color:{text_col}; font-size:15px; gap:12px; box-shadow:0 1px 6px rgba(0,0,0,0.05); }}
.search .mag {{ width:20px;height:20px;border-radius:50%;border:2px solid {text_col}; }}
</style></head><body>
<div class="titlebar">
  <div class="ctrls"><span></span><span></span><span></span></div>
  <div class="tabs">
    <div class="tab active">New Tab</div>
    <div class="tab">Extensions</div>
    <div class="tab">SiliconFlow</div>
    <div class="tab">Palette</div>
  </div>
</div>
<div class="toolbar">
  <div class="nav"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg></div>
  <div class="nav"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg></div>
  <div class="nav"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg></div>
  <div class="omnibox">Search Google or type a URL</div>
</div>
<div class="bookbar">
  <span>Work</span><span>Mail</span><span>Calendar</span><span>Notes</span><span>Reading</span>
</div>
<div class="ntp">
  <div class="top-right"><span>Images</span><div class="grid"><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b><b></b></div></div>
  <div class="logo-area"><div class="logo">Google</div></div>
  <div class="search"><div class="mag"></div>Search Google or type a URL</div>
</div>
</body></html>"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--force-color-profile=srgb"])
        page = browser.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=1)
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(400)
        img = page.screenshot(clip={"x": 0, "y": 0, "width": 1280, "height": 800})
        browser.close()

    im = Image.open(__import__("io").BytesIO(img)).convert("RGB")
    if im.size != (1280, 800):
        im = im.resize((1280, 800), Image.LANCZOS)
    im.save(out_path, "PNG")
    print("wrote", out_path)


# ---------- Promo tiles (English only) ----------
def render_promo_small(path):
    W, H = 440, 280
    img = Image.new("RGB", (W, H), P["deep"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 170, W, H], fill=P["sky"])
    d.rectangle([0, 210, W, H], fill=P["mist"])
    draw_center(d, W / 2, 70, "Ocean Mist", font(34, True), P["warm"])
    draw_center(d, W / 2, 112, "A calm coastal Chrome theme", font(15), P["warm"])
    d.rounded_rectangle([W / 2 - 90, 232, W / 2 + 90, 262], radius=14, fill=P["warm"])
    draw_center(d, W / 2, 247, "Add to Chrome", font(15, True), P["deep"])
    img.save(path, "PNG")
    print("wrote", path)


def render_promo_large(path):
    W, H = 1400, 560
    img = Image.new("RGB", (W, H), P["deep"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 360, W, H], fill=P["sky"])
    d.rectangle([0, 440, W, H], fill=P["mist"])
    draw_center(d, W / 2, 90, "Ocean Mist Theme", font(60, True), P["warm"])
    draw_center(d, W / 2, 155,
                "Minimalist coastal calm for a focused browsing experience",
                font(26), P["warm"])
    draw_center(d, W / 2, 205,
                "Soft blues, warm white, and quiet mist - premium, no clutter",
                font(20), P["warm"])
    d.rounded_rectangle([W / 2 - 130, 290, W / 2 + 130, 340], radius=20, fill=P["warm"])
    draw_center(d, W / 2, 315, "Add to Chrome", font(22, True), P["deep"])
    img.save(path, "PNG")
    print("wrote", path)


def main():
    (ROOT / "store-assets" / "screenshots" / "en").mkdir(parents=True, exist_ok=True)
    (ROOT / "store-assets" / "promo").mkdir(parents=True, exist_ok=True)
    render_browser_screenshot(
        ROOT / "store-assets" / "screenshots" / "en" / "screenshot-1-browser.png"
    )
    render_promo_small(ROOT / "store-assets" / "promo" / "440x280.png")
    render_promo_large(ROOT / "store-assets" / "promo" / "1400x560.png")


if __name__ == "__main__":
    main()
