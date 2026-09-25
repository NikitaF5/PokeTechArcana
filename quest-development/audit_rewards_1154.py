from __future__ import annotations

import importlib.util
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODULE_PATH = ROOT / "build_book_quests.py"
spec = importlib.util.spec_from_file_location("quest_builder", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

quests = [
    (namespace, quest)
    for namespace, list_name in module.QUEST_LISTS.items()
    for quest in getattr(module, list_name)
]

same_item = []
generic = []
rare = []
large = []
missing_desc = []
egg_rewards = []
for namespace, quest in quests:
    task_ids = {item for item, _ in quest.tasks}
    if quest.reward[0] in task_ids:
        same_item.append((namespace, quest.key, quest.reward, quest.tasks))
    if quest.desc.startswith("Урок «"):
        generic.append((namespace, quest.key))
    if any(token in quest.reward[0] for token in module.RARE_REWARD_PARTS):
        rare.append((namespace, quest.key, quest.reward))
    if quest.reward[1] > 32 or quest.xp > 2:
        large.append((namespace, quest.key, quest.reward, quest.xp))
    if len(quest.desc) < 80:
        missing_desc.append((namespace, quest.key, quest.desc))
    if quest.reward[0].endswith("_spawn_egg"):
        egg_rewards.append((namespace, quest.key, quest.title, quest.reward))

print(f"quests={len(quests)} chapters={len(module.QUEST_LISTS)}")
print(f"generic={len(generic)} same_item={len(same_item)} rare={len(rare)} large={len(large)} short_desc={len(missing_desc)}")
print("xp=" + repr(Counter(quest.xp for _, quest in quests)))
print("reward_namespaces=" + repr(Counter(quest.reward[0].split(":", 1)[0] for _, quest in quests).most_common()))
print("egg_rewards=" + repr(egg_rewards))

for namespace in ("skyblock", "create", "ae2", "farmer", "cataclysm", "services", "finale"):
    list_name = module.QUEST_LISTS[namespace]
    sample = getattr(module, list_name)[:2]
    for quest in sample:
        print(f"SAMPLE {namespace}/{quest.key}: {quest.title} | {quest.desc} | {quest.reward} | xp={quest.xp}")


def ids_from_zip(path: Path) -> tuple[set[str], set[str], set[str]]:
    quest_ids: set[str] = set()
    task_ids: set[str] = set()
    reward_ids: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if "/chapters/" not in name or not name.endswith(".snbt"):
                continue
            text = archive.read(name).decode("utf-8")
            quest_ids.update(re.findall(r"(?m)^\s*id:\s*\"?([0-9A-F]+)\"?\s*$", text))
            task_ids.update(re.findall(r"(?m)^\s*id:\s*\"?([0-9A-F]+)\"?\s*\n\s*item:", text))
            reward_ids.update(re.findall(r"(?m)^\s*id:\s*\"?([0-9A-F]+)\"?\s*\n\s*item:\s*\{", text))
    return quest_ids, task_ids, reward_ids


previous = ROOT / "PokeTechArcana-quests-book-1.15.4.zip"
current = ROOT / f"PokeTechArcana-quests-book-{module.PACKAGE_VERSION}.zip"
if previous.exists():
    old_ids = ids_from_zip(previous)
    new_ids = ids_from_zip(current)
    print("id_counts_old=" + repr(tuple(map(len, old_ids))))
    print("id_counts_new=" + repr(tuple(map(len, new_ids))))
    print("id_sets_equal=" + repr(tuple(old == new for old, new in zip(old_ids, new_ids))))
    assert all(old == new for old, new in zip(old_ids, new_ids))

assert len(quests) == 3751
assert not generic
assert not same_item
assert not rare
assert not large
assert not missing_desc
assert all(count == 2 for _, _, _, (_, count) in egg_rewards)
