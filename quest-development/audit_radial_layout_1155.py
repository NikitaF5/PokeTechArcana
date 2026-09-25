from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
MODULE_PATH = ROOT / "build_book_quests.py"
spec = importlib.util.spec_from_file_location("quest_builder_layout", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

chapter_count = 0
stage_count = 0
quest_count = 0
for namespace, config in module.next_chapters.CHAPTERS.items():
    quests = getattr(module, module.QUEST_LISTS[namespace])
    for stage_index, centre in enumerate(config["centers"], start=1):
        prefix = f"s{stage_index:02d}_"
        cluster = [quest for quest in quests if quest.key.startswith(prefix)]
        root = next(quest for quest in cluster if quest.key == f"s{stage_index:02d}_01")
        assert math.isclose(root.x, centre[0], abs_tol=1e-9)
        assert math.isclose(root.y, centre[1], abs_tol=1e-9)
        for child in cluster:
            if child is root:
                continue
            radius = math.hypot((child.x - root.x) / 6.2, (child.y - root.y) / 5.8)
            assert math.isclose(radius, 1.0, abs_tol=1e-9), (namespace, child.key, radius)
            assert child.deps == (root.key,), (namespace, child.key, child.deps, root.key)
        stage_count += 1
        quest_count += len(cluster)
    chapter_count += 1

print(f"radial_chapters={chapter_count} stages={stage_count} quests={quest_count}")
print("all roots are centred; every child is exactly on its stage ellipse")

# Produce one rendered audit image using the same coordinate transform as FTB
# Quests, so the visual relationship between the background and icons can be
# inspected without joining the server.
namespace = "services"
quests = getattr(module, module.QUEST_LISTS[namespace])
background_path = (
    WORKSPACE / "skyblock-update" / "pack" / "kubejs" / "assets" / "poketech"
    / "textures" / "quests" / "backgrounds" / "services_book.png"
)
background = Image.open(background_path).convert("RGBA")
canvas = Image.new("RGBA", background.size, (235, 228, 215, 255))
canvas.alpha_composite(background)
draw = ImageDraw.Draw(canvas, "RGBA")
width_units, height_units, _, _ = module.chapter_geometry(quests)
min_x, max_x = min(q.x for q in quests) - 4, max(q.x for q in quests) + 4
min_y, max_y = min(q.y for q in quests) - 8, max(q.y for q in quests) + 4


def point(x: float, y: float) -> tuple[float, float]:
    return (
        (x - min_x) / (max_x - min_x) * canvas.width,
        (y - min_y) / (max_y - min_y) * canvas.height,
    )


for stage_index in range(1, len(module.next_chapters.CHAPTERS[namespace]["stages"]) + 1):
    cluster = [quest for quest in quests if quest.key.startswith(f"s{stage_index:02d}_")]
    root = next(quest for quest in cluster if quest.key.endswith("_01"))
    rx, ry = point(root.x, root.y)
    for child in cluster:
        if child is root:
            continue
        x, y = point(child.x, child.y)
        draw.line((rx, ry, x, y), fill=(86, 78, 69, 170), width=4)
    for child in cluster:
        x, y = point(child.x, child.y)
        radius = 9 if child is root else 6
        fill = (39, 126, 157, 255) if child is root else (61, 56, 52, 255)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill, outline=(245, 239, 226, 255), width=2)

preview = ROOT / "layout-audit-services-1.15.5.png"
canvas.convert("RGB").save(preview, quality=94)
print(preview)
