"""Composite AI-generated logos onto the NTP screenshot for preview."""
import io
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "store-assets" / "screenshots" / "en" / "screenshot-1-browser.png"
OUT_DIR = ROOT / "store-assets" / "logo-previews"

def remove_white_background(img, tolerance=35):
    """Remove only edge-connected white background (preserve internal whites)."""
    img = img.convert("RGBA")
    w, h = img.size
    px = list(img.getdata())

    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    bg_r = sum(px[y * w + x][0] for x, y in corners) // 4
    bg_g = sum(px[y * w + x][1] for x, y in corners) // 4
    bg_b = sum(px[y * w + x][2] for x, y in corners) // 4

    def is_bg(idx):
        r, g, b, _ = px[idx]
        return (
            abs(r - bg_r) <= tolerance
            and abs(g - bg_g) <= tolerance
            and abs(b - bg_b) <= tolerance
        )

    mask = [False] * (w * h)
    q = deque()
    for y in range(h):
        for x in (0, w - 1):
            idx = y * w + x
            if not mask[idx] and is_bg(idx):
                mask[idx] = True
                q.append(idx)
    for x in range(1, w - 1):
        for y in (0, h - 1):
            idx = y * w + x
            if not mask[idx] and is_bg(idx):
                mask[idx] = True
                q.append(idx)

    while q:
        idx = q.popleft()
        x, y = idx % w, idx // w
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    nidx = ny * w + nx
                    if not mask[nidx] and is_bg(nidx):
                        mask[nidx] = True
                        q.append(nidx)

    new = [(r, g, b, 0) if mask[i] else (r, g, b, a) for i, (r, g, b, a) in enumerate(px)]
    img.putdata(new)
    return img


def _apply_matte(logo, bg, tolerance=55):
    w, h = logo.size
    bg_r, bg_g, bg_b = bg
    px = list(logo.getdata())
    new = []
    for r, g, b, a in px:
        dist = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
        if dist < tolerance:
            new.append((r, g, b, 0))
        else:
            alpha = min(255, int(a * min(1.0, dist / tolerance)))
            new.append((r, g, b, alpha))
    logo.putdata(new)
    return logo


def _crop_to_content(logo, padding=4):
    """Crop to the bounding box of non-transparent pixels."""
    w, h = logo.size
    px = logo.load()
    min_x, min_y, max_x, max_y = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            if px[x, y][3] > 10:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x <= min_x or max_y <= min_y:
        return logo
    return logo.crop((max(0, min_x - padding), max(0, min_y - padding),
                      min(w, max_x + padding + 1), min(h, max_y + padding + 1)))


def matte_background(logo_raw, tolerance=55):
    """Remove the uniform light background from an AI-generated logo.

    AI-generated logos on white/light backgrounds need the background removed
    before compositing. For simple logos without internal white fills, a
    global color-distance mask is more reliable than edge flood-fill because
    AI images often have soft anti-aliased fringe around the icon.
    """
    logo = logo_raw.convert("RGBA")
    w, h = logo.size
    px = list(logo.getdata())

    corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
    corner_pixels = [px[y * w + x] for x, y in corners]
    # Some AI outputs have transparent corners; fall back to white if so.
    solid_corners = [p for p in corner_pixels if p[3] > 200]
    if solid_corners:
        bg = (
            sum(p[0] for p in solid_corners) // len(solid_corners),
            sum(p[1] for p in solid_corners) // len(solid_corners),
            sum(p[2] for p in solid_corners) // len(solid_corners),
        )
    else:
        bg = (255, 255, 255)

    logo = _apply_matte(logo, bg, tolerance)
    # If AI put the icon inside a white square on top of another background,
    # cropping to content removes the square and lets a second matte pass work.
    logo = _crop_to_content(logo, padding=2)
    logo = _apply_matte(logo, (255, 255, 255), tolerance=tolerance)
    logo = _crop_to_content(logo, padding=2)
    return logo


def composite_preview(base_path, logo_path, out_path, target_height=130):
    base = Image.open(base_path).convert("RGBA")
    logo_raw = Image.open(logo_path)
    logo = matte_background(logo_raw)

    # Scale logo to target height
    ratio = target_height / logo.height
    new_w = int(logo.width * ratio)
    logo = logo.resize((new_w, target_height), Image.LANCZOS)

    # Erase the original "Google" text area with the NTP background color
    # so the new logo sits on a clean background.
    import importlib.util
    spec = importlib.util.spec_from_file_location("gsa", ROOT / "generate-store-assets.py")
    gsa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gsa)
    warm = gsa.P["warm"] + (255,)
    erase_box = (640 - 200, 245, 640 + 200, 365)
    d = ImageDraw.Draw(base)
    d.rectangle(erase_box, fill=warm)

    # Center on NTP logo area
    cx, cy = 640, 305
    x = cx - logo.width // 2
    y = cy - logo.height // 2

    base.paste(logo, (x, y), logo)
    base.convert("RGB").save(out_path, "PNG")
    print("wrote", out_path)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    logos = sorted(OUT_DIR.glob("A_minimalist_*.png"))
    for i, logo_path in enumerate(logos, 1):
        composite_preview(BASE, logo_path, OUT_DIR / f"preview-{i}.png")


if __name__ == "__main__":
    main()
