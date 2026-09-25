from __future__ import annotations

import math


CHAPTER_PATHS = (
    "river", "double_arc", "terraces", "crown", "wave", "stairs", "constellation",
    "valley", "ribbon", "skyline", "braid", "islands",
)
STAGE_FORMS = ("split", "arch", "ladder", "fan", "diamond", "wave", "fork", "loop")


def stage_anchors(kind: str, count: int) -> list[tuple[float, float]]:
    xs = [10 + i * (180 / max(1, count - 1)) for i in range(count)]
    if kind == "river":
        ys = [50 + 15 * math.sin(i * 1.15) for i in range(count)]
    elif kind == "double_arc":
        ys = [55 - 23 * math.sin(i / max(1, count - 1) * math.pi * 2) for i in range(count)]
    elif kind == "terraces":
        ys = [30, 30, 48, 48, 68, 68, 48, 32, 32][:count]
    elif kind == "crown":
        ys = [58 - 30 * math.sin(i / max(1, count - 1) * math.pi) for i in range(count)]
    elif kind == "wave":
        ys = [50 + 22 * math.sin(i * math.pi / 2) for i in range(count)]
    elif kind == "stairs":
        ys = [70 - (i % 4) * 14 for i in range(count)]
    elif kind == "constellation":
        ys = [54, 31, 44, 23, 58, 72, 45, 26, 49][:count]
    elif kind == "valley":
        ys = [28 + 38 * math.sin(i / max(1, count - 1) * math.pi) for i in range(count)]
    elif kind == "ribbon":
        ys = [44 + 18 * math.sin(i * .86 + .6) for i in range(count)]
    elif kind == "skyline":
        ys = [68, 54, 54, 34, 34, 48, 26, 42, 42][:count]
    elif kind == "braid":
        ys = [34 if i % 2 == 0 else 66 for i in range(count)]
    else:
        ys = [50, 27, 68, 37, 58, 24, 64, 43, 52][:count]
    while len(ys) < count:
        ys.append(50 + 18 * math.sin(len(ys) * 1.2))
    return list(zip(xs, ys))


def make_stage_nodes(
    stage_index: int,
    anchor: tuple[float, float],
    next_anchor: tuple[float, float] | None,
    titles: list[str],
    form: str,
) -> tuple[list[dict], list[list[str]], str]:
    ax, ay = anchor
    if next_anchor:
        nx, ny = next_anchor
        width = max(9.0, nx - ax - 2.2)
        dy = ny - ay
    else:
        width, dy = 11.0, 0.0

    count = len(titles)
    root = f"s{stage_index + 1:02d}_01"
    nodes = [{"id": root, "title": titles[0], "x": ax, "y": ay, "main": True}]
    edges: list[list[str]] = []
    if count == 1:
        return nodes, edges, root

    ids = [f"s{stage_index + 1:02d}_{i + 1:02d}" for i in range(count)]
    available = max(7.0, min(18.0, width))

    if form == "split" and count >= 6:
        upper = list(range(1, (count + 1) // 2))
        lower = list(range((count + 1) // 2, count - 1))
        end = count - 1
        for branch, sign in ((upper, -1), (lower, 1)):
            prev = 0
            for order, idx in enumerate(branch, 1):
                t = order / (len(branch) + 1)
                nodes.append({"id": ids[idx], "title": titles[idx], "x": ax + available * t, "y": ay + sign * (7 + math.sin(t * math.pi) * 7), "main": False})
                edges.append([ids[prev], ids[idx]])
                prev = idx
            edges.append([ids[prev], ids[end]])
        nodes.append({"id": ids[end], "title": titles[end], "x": ax + available, "y": ay + dy * .55, "main": True})
    elif form == "diamond" and count >= 5:
        end = count - 1
        middle = list(range(1, end))
        upper = middle[::2]
        lower = middle[1::2]
        for branch, sign in ((upper, -1), (lower, 1)):
            prev = 0
            for order, idx in enumerate(branch, 1):
                t = order / (len(branch) + 1)
                nodes.append({"id": ids[idx], "title": titles[idx], "x": ax + available * t, "y": ay + sign * (7 + 6 * math.sin(t * math.pi)), "main": False})
                edges.append([ids[prev], ids[idx]])
                prev = idx
            edges.append([ids[prev], ids[end]])
        nodes.append({"id": ids[end], "title": titles[end], "x": ax + available, "y": ay + dy * .5, "main": True})
    elif form == "ladder":
        for i in range(1, count):
            t = i / (count - 1)
            nodes.append({"id": ids[i], "title": titles[i], "x": ax + available * t, "y": ay + (-1 if i % 2 else 1) * 7 + dy * t * .45, "main": i == count - 1})
            edges.append([ids[i - 1], ids[i]])
            if i >= 3 and i % 2:
                edges.append([ids[i - 2], ids[i]])
    elif form == "fan":
        hub = min(3, count - 1)
        for i in range(1, count):
            if i <= hub:
                t = i / max(1, hub)
                x, y = ax + available * .34 * t, ay + dy * .18 * t
                parent = i - 1
            else:
                spoke = i - hub - 1
                spokes = count - hub - 1
                angle = -1.0 + 2.0 * spoke / max(1, spokes - 1)
                x = ax + available * (.55 + .42 * math.cos(angle))
                y = ay + dy * .45 + 15 * math.sin(angle)
                parent = hub
            nodes.append({"id": ids[i], "title": titles[i], "x": x, "y": y, "main": i <= hub})
            edges.append([ids[parent], ids[i]])
    elif form == "fork":
        trunk = max(2, count // 3)
        for i in range(1, count):
            if i <= trunk:
                t = i / trunk
                x, y, parent = ax + available * .45 * t, ay + dy * .25 * t, i - 1
            else:
                branch = i - trunk - 1
                total = count - trunk - 1
                sign = -1 if branch % 2 == 0 else 1
                rank = branch // 2 + 1
                x = ax + available * (.48 + .45 * rank / max(1, math.ceil(total / 2)))
                y = ay + dy * .45 + sign * (6 + rank * 4)
                parent = trunk if rank == 1 else i - 2
            nodes.append({"id": ids[i], "title": titles[i], "x": x, "y": y, "main": i <= trunk})
            edges.append([ids[parent], ids[i]])
    elif form == "loop":
        for i in range(1, count):
            t = i / (count - 1)
            angle = math.pi * (1.15 + 1.7 * t)
            nodes.append({"id": ids[i], "title": titles[i], "x": ax + available * t, "y": ay + 14 * math.sin(angle) + dy * t * .45, "main": i == count - 1})
            edges.append([ids[i - 1], ids[i]])
    else:
        for i in range(1, count):
            t = i / (count - 1)
            curve = (-15 * math.sin(t * math.pi)) if form == "arch" else (10 * math.sin(t * math.pi * 2))
            nodes.append({"id": ids[i], "title": titles[i], "x": ax + available * t, "y": ay + curve + dy * t * .5, "main": i == count - 1})
            edges.append([ids[i - 1], ids[i]])
    return nodes, edges, ids[-1]


def chapter_layout(namespace: str, chapter_index: int, config: dict) -> dict:
    stages = config["stages"]
    style = CHAPTER_PATHS[chapter_index % len(CHAPTER_PATHS)]
    anchors = stage_anchors(style, len(stages))
    nodes: list[dict] = []
    edges: list[list[str]] = []
    stage_meta = []
    prior_exit: str | None = None
    append_control = config.get("append_control", True)
    target = config.get("target_count")
    base = sum(len(stage[2]) + (1 if append_control else 0) for stage in stages)
    extras = max(0, (target or base) - base)
    stage_extras = [0] * len(stages)
    for extra in range(extras):
        stage_extras[extra % len(stages)] += 1

    for stage_index, (phase, stage_name, configured_titles) in enumerate(stages):
        titles = list(configured_titles)
        titles += [f"Практика: {stage_name} {n + 1}" for n in range(stage_extras[stage_index])]
        if append_control:
            titles.append(f"Контрольная сборка: {stage_name}")
        form = STAGE_FORMS[(chapter_index * 3 + stage_index * 5) % len(STAGE_FORMS)]
        next_anchor = anchors[stage_index + 1] if stage_index + 1 < len(anchors) else None
        stage_nodes, stage_edges, exit_id = make_stage_nodes(stage_index, anchors[stage_index], next_anchor, titles, form)
        if prior_exit:
            stage_edges.insert(0, [prior_exit, stage_nodes[0]["id"]])
        nodes.extend(stage_nodes)
        edges.extend(stage_edges)
        stage_meta.append({"phase": phase, "name": stage_name, "x": anchors[stage_index][0], "y": anchors[stage_index][1], "form": form})
        prior_exit = exit_id
    return {"namespace": namespace, "style": style, "nodes": nodes, "edges": edges, "stages": stage_meta}
