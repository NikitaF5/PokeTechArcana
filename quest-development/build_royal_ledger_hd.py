from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "background-options"
W, H = 4096, 1920
S = 2


def ivory_paper() -> Image.Image:
    """Clean 4K parchment made at native resolution, without stretching a small image."""
    base = Image.new("RGB", (W, H), (249, 246, 237))

    fine = Image.effect_noise((W, H), 5.5)
    fine = ImageOps.colorize(fine, black=(224, 217, 201), white=(255, 254, 248))
    base = Image.blend(base, fine, .11)

    broad = Image.effect_noise((1024, 480), 17).resize((W, H), Image.Resampling.BICUBIC)
    broad = broad.filter(ImageFilter.GaussianBlur(22))
    broad = ImageOps.colorize(broad, black=(232, 224, 206), white=(255, 252, 242))
    base = Image.blend(base, broad, .075)

    # A very soft warm edge keeps the page readable while giving it depth.
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((126, 110, W - 126, H - 110), radius=86, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(105))
    edge = Image.new("RGB", (W, H), (221, 207, 181))
    base = Image.composite(base, edge, mask)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    rng = random.Random(20260925)

    # Fine paper fibres, visible when zoomed but quiet behind quest nodes.
    for _ in range(920):
        x = rng.randrange(140, W - 140)
        y = rng.randrange(120, H - 120)
        length = rng.randrange(16, 110)
        alpha = rng.randrange(3, 10)
        color = (111, 91, 61, alpha) if rng.random() < .55 else (255, 255, 255, alpha)
        draw.arc((x, y, x + length, y + rng.randrange(5, 24)), 175, 355, fill=color, width=1)

    # Only a few very pale natural marks: the page should look kept, not ancient.
    for _ in range(24):
        x = rng.randrange(200, W - 200)
        y = rng.randrange(160, H - 160)
        rx, ry = rng.randrange(7, 31), rng.randrange(3, 14)
        draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=(120, 91, 52, rng.randrange(2, 7)))

    layer = layer.filter(ImageFilter.GaussianBlur(.45))
    return Image.alpha_composite(base.convert("RGBA"), layer)


def diamond(draw: ImageDraw.ImageDraw, x: int, y: int, r: int, fill, outline, width: int) -> None:
    draw.polygon(((x, y - r), (x + r, y), (x, y + r), (x - r, y)),
                 fill=fill, outline=outline, width=width)


def spiral(draw: ImageDraw.ImageDraw, cx: int, cy: int, flip_x: int, flip_y: int,
           color: tuple[int, int, int, int]) -> None:
    pts = []
    for i in range(145):
        t = i / 144 * math.tau * 2.28
        radius = (9 + 8.4 * t) * S
        pts.append((cx + flip_x * math.cos(t) * radius, cy + flip_y * math.sin(t) * radius))
    draw.line(pts, fill=color, width=5 * S, joint="curve")

    # Leaf-shaped flourishes extending from the spiral.
    for angle, dist in ((-.56, 95), (.18, 124), (.70, 151)):
        x = cx + flip_x * int(math.cos(angle) * dist * S)
        y = cy + flip_y * int(math.sin(angle) * dist * S)
        rx, ry = 16 * S, 30 * S
        draw.ellipse((x - rx, y - ry, x + rx, y + ry), outline=color, width=4 * S)
        draw.line((cx, cy, x, y), fill=color, width=3 * S)


def royal_ledger_hd() -> Image.Image:
    img = ivory_paper()
    draw = ImageDraw.Draw(img, "RGBA")

    leather = (91, 43, 18, 247)
    leather_dark = (45, 24, 12, 250)
    gold = (184, 119, 39, 245)
    gold_light = (236, 190, 93, 220)
    ink = (125, 67, 22, 212)

    # Native 4K leather cover and layered gilt frame.
    draw.rounded_rectangle((10, 10, W - 11, H - 11), radius=64,
                           outline=leather, width=96)
    draw.rounded_rectangle((16, 16, W - 17, H - 17), radius=58,
                           outline=leather_dark, width=12)
    draw.rounded_rectangle((108, 108, W - 108, H - 108), radius=48,
                           outline=gold, width=10)
    draw.rounded_rectangle((132, 132, W - 132, H - 132), radius=36,
                           outline=ink, width=8)
    draw.rounded_rectangle((150, 150, W - 150, H - 150), radius=28,
                           outline=(215, 153, 68, 115), width=4)

    # Metal corner protectors, all geometry rendered at the final size.
    for x, y, sx, sy in (
        (68, 68, 1, 1), (W - 68, 68, -1, 1),
        (68, H - 68, 1, -1), (W - 68, H - 68, -1, -1),
    ):
        draw.polygon(((x, y), (x + sx * 210, y), (x + sx * 108, y + sy * 64),
                      (x, y + sy * 210)), fill=gold, outline=gold_light, width=4)
        draw.ellipse((x - 17, y - 17, x + 17, y + 17),
                     fill=leather_dark, outline=gold_light, width=6)

    # Binder rings along the left cover.
    for y in range(250, H - 150, 210):
        draw.ellipse((42, y - 26, 94, y + 26), fill=leather_dark,
                     outline=gold, width=8)
        draw.ellipse((58, y - 10, 78, y + 10), fill=(126, 77, 31, 240))

    # Symmetrical high resolution filigree kept inside the safe edge area.
    for cx, cy, fx, fy in (
        (218, 225, 1, 1), (W - 218, 225, -1, 1),
        (218, H - 225, 1, -1), (W - 218, H - 225, -1, -1),
    ):
        draw.ellipse((cx - 105, cy - 105, cx + 105, cy + 105), outline=ink, width=5)
        spiral(draw, cx - fx * 40, cy - fy * 35, fx, fy, ink)
        draw.ellipse((cx + fx * 37 - 12, cy + fy * 55 - 20,
                      cx + fx * 37 + 12, cy + fy * 55 + 20), outline=ink, width=4)

    # Small page clasps centered at top and bottom.
    for cy in (70, H - 70):
        diamond(draw, W // 2, cy, 37, fill=(119, 67, 27, 225),
                outline=gold_light, width=5)
        draw.ellipse((W // 2 - 15, cy - 15, W // 2 + 15, cy + 15),
                     fill=leather_dark, outline=gold, width=4)

    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    image = royal_ledger_hd()
    full = OUT / "01-royal-ledger-hd.png"
    image.convert("RGB").save(full, optimize=True)
    preview = ImageOps.fit(image.convert("RGB"), (1536, 720), method=Image.Resampling.LANCZOS)
    preview.save(OUT / "01-royal-ledger-hd-preview.jpg", quality=94, optimize=True)
    print(f"{full} {image.width}x{image.height} {full.stat().st_size} bytes")


if __name__ == "__main__":
    main()
