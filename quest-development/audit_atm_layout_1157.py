"""Prove that the preview and generated game quests use one geometry graph."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import atm_layout_engine
import build_book_quests as book
import build_three_chapters as chapters


def quest_map(namespace: str):
    quests = chapters.build_chapter(namespace, book.Quest)
    return {quest.key: quest for quest in quests}


report = []
for index, (namespace, config) in enumerate(chapters.CHAPTERS.items()):
    layout = atm_layout_engine.chapter_layout(namespace, index, config)
    actual = quest_map(namespace)
    expected_edges = {tuple(edge) for edge in layout["edges"]}
    actual_edges = {(dependency, quest.key) for quest in actual.values() for dependency in quest.deps}
    assert set(actual) == {node["id"] for node in layout["nodes"]}, namespace
    assert expected_edges == actual_edges, namespace
    for node in layout["nodes"]:
        quest = actual[node["id"]]
        assert (quest.x, quest.y) == (round(node["x"], 2), round(node["y"], 2)), (namespace, node["id"])
    report.append({
        "chapter": namespace,
        "quests": len(actual),
        "edges": len(actual_edges),
        "style": layout["style"],
        "bounds": [
            min(q.x for q in actual.values()), max(q.x for q in actual.values()),
            min(q.y for q in actual.values()), max(q.y for q in actual.values()),
        ],
    })

build = ROOT / "book-build" / "config" / "ftbquests" / "quests" / "chapters"
assert build.exists(), "run build_book_quests.py first"
for entry in report:
    text = (build / f"{entry['chapter']}.snbt").read_text("utf-8")
    assert "default_hide_dependency_lines: true" in text, entry["chapter"]
    assert len(re.findall(r"\n\t\t\tid: \"[0-9A-F]{16}\"", text)) >= entry["quests"], entry["chapter"]

out = ROOT / "layout-audit-1.15.7.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
print(f"PASS: {len(report)} chapters, {sum(x['quests'] for x in report)} quests, {sum(x['edges'] for x in report)} edges")
print(out)
