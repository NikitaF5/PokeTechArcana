from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
spec = importlib.util.spec_from_file_location("route_builder", ROOT / "build_book_quests.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

chapters = stages = quests_total = 0
for namespace, config in module.next_chapters.CHAPTERS.items():
    quests = getattr(module, module.QUEST_LISTS[namespace])
    for index in range(1, len(config["stages"]) + 1):
        cluster = [q for q in quests if q.key.startswith(f"s{index:02d}_")]
        assert cluster
        for current, previous in zip(cluster[1:], cluster[:-1]):
            assert current.deps == (previous.key,), (namespace, current.key, current.deps, previous.key)
        stages += 1
        quests_total += len(cluster)
    chapters += 1
print(f"route_chapters={chapters} stages={stages} quests={quests_total}")
print("all stage branches are sequential routes; stage transitions use the previous route endpoint")

namespace = "wildlife"
quests = getattr(module, module.QUEST_LISTS[namespace])
background_path = WORKSPACE / "skyblock-update/pack/kubejs/assets/poketech/textures/quests/backgrounds/wildlife_book.png"
canvas = Image.open(background_path).convert("RGBA")
draw = ImageDraw.Draw(canvas, "RGBA")
width_units, height_units, _, _ = module.chapter_geometry(quests)
min_x, max_x = min(q.x for q in quests) - 4, max(q.x for q in quests) + 4
min_y, max_y = min(q.y for q in quests) - 8, max(q.y for q in quests) + 4
point = lambda x, y: ((x - min_x) / (max_x - min_x) * canvas.width, (y - min_y) / (max_y - min_y) * canvas.height)
for index in range(1, len(module.next_chapters.CHAPTERS[namespace]["stages"]) + 1):
    cluster = [q for q in quests if q.key.startswith(f"s{index:02d}_")]
    for current, previous in zip(cluster[1:], cluster[:-1]):
        draw.line((*point(previous.x, previous.y), *point(current.x, current.y)), fill=(71, 64, 57, 190), width=4)
    for q in cluster:
        x, y = point(q.x, q.y)
        radius = 9 if q.key.endswith("_01") else 6
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(47, 122, 151, 255) if q.key.endswith("_01") else (59, 54, 49, 255), outline=(246, 239, 225, 255), width=2)
preview = ROOT / "layout-audit-wildlife-1.15.6.png"
canvas.convert("RGB").save(preview, quality=94)
print(preview)
