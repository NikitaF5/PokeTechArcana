from __future__ import annotations

import hashlib
import math
import random
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import build_mekanism_quests as old_mek
import build_create_quests as create_data
import build_immersive_quests as immersive_data
import build_three_chapters as next_chapters


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
BUILD = ROOT / "book-build"
QUESTS = BUILD / "config" / "ftbquests" / "quests"
ASSETS = BUILD / "kubejs" / "assets"
CLIENT_PACK = WORKSPACE / "skyblock-update" / "pack"
# FTB Quests 2101.1.27 parses IDs with Long.parseLong(..., 16), so the
# highest bit must stay clear. IDs beginning with 8-F are silently replaced
# at load time, which breaks translations and dependency references.
GROUP_ID = "271C0B00CAFE1001"
SKY_CHAPTER_ID = "271C0B00CAFE2001"
MEK_CHAPTER_ID = "1A2E2B8D9E0A2001"
CREATE_CHAPTER_ID = "3C0EA7ECAFE3001"
IMMERSIVE_CHAPTER_ID = "4E1E57ECAFE4001"
AE2_CHAPTER_ID = "5A2ECAFEAE2001"
APPMEK_CHAPTER_ID = "5A2ECAFEAE2002"
ARS_CHAPTER_ID = "5A2ECAFEA5001"
OCCULT_CHAPTER_ID = "5A2ECAFE0CC001"
EVIL_CHAPTER_ID = "5A2ECAFE0E001"
FNA_CHAPTER_ID = "5A2ECAFE0F001"
IRONS_CHAPTER_ID = "5A2ECAFE10001"
FARMER_CHAPTER_ID = "5A2ECAFE10002"
MYSTICAL_CHAPTER_ID = "5A2ECAFE10003"
POKEMON_CHAPTER_ID = "5A2ECAFE20001"
TRAINERS_CHAPTER_ID = "5A2ECAFE20002"
ENDGAME_CHAPTER_ID = "5A2ECAFE20003"
APOTHEOSIS_CHAPTER_ID = "5A2ECAFE30001"
CATACLYSM_CHAPTER_ID = "5A2ECAFE30002"
DRACONIC_CHAPTER_ID = "5A2ECAFE30003"
VAMPIRISM_CHAPTER_ID = "5A2ECAFE30004"
COBBLEMON_ADVANCED_CHAPTER_ID = "5A2ECAFE30005"
ACHIEVEMENTS_CHAPTER_ID = "5A2ECAFE30006"
PACKAGE_VERSION = "1.10.0"


@dataclass(frozen=True)
class Quest:
    key: str
    title: str
    phase: str
    desc: str
    x: float
    y: float
    shape: str
    size: float
    tasks: tuple[tuple[str, int], ...]
    deps: tuple[str, ...]
    reward: tuple[str, int]
    xp: int
    tag: str
    icon: str | None = None


def hid(namespace: str, kind: str, key: str) -> str:
    value = int(hashlib.sha256(f"poketech-book-v2:{namespace}:{kind}:{key}".encode()).hexdigest()[:16], 16)
    value &= 0x7FFFFFFFFFFFFFFF
    if value <= 1:
        value += 2
    return f"{value:016X}"


def q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def sky_pos(px: float, py: float) -> tuple[float, float]:
    return round((px - 4.0) * 0.33, 2), round((py - 50.0) * 0.26, 2)


def sq(key, title, phase, desc, px, py, shape, size, task, deps, reward, xp, tag, icon=None):
    x, y = sky_pos(px, py)
    tasks = task if isinstance(task, tuple) and task and isinstance(task[0], tuple) else (task,)
    return Quest(key, title, phase, desc, x, y, shape, size, tuple(tasks), tuple(deps), reward, xp, tag, icon)


SKY = [
    sq("start", "Первый блок", "I · ОСТРОВ", "Прими стартовый набор и сохрани первый саженец. Потеря дерева в пустоте остановит развитие острова.", 4, 50, "diamond", 1.65, ("minecraft:oak_sapling", 1), (), ("minecraft:dirt", 4), 1, "pta_main"),
    sq("crook", "Крюк", "I · ОСТРОВ", "Сделай крюк и собери листья. Он заметно повышает шанс получить саженцы и шелкопряда.", 11, 50, "circle", 1.1, ("exdeorum:crook", 1), ("start",), ("minecraft:oak_sapling", 4), 1, "pta_main"),
    sq("string", "Шёлковая нить", "I · ОСТРОВ", "Зарази листья шелкопрядом и дождись полного распространения. Так остров получит первую нить.", 18, 50, "circle", 1.1, ("minecraft:string", 16), ("crook",), ("exdeorum:string_mesh", 1), 2, "pta_main"),
    sq("sieve", "Ручное сито", "II · СИТО", "Установи сито, вставь сетку и начинай ручное просеивание. Соседние сита можно использовать одновременно.", 25, 50, "hexagon", 1.45, (("exdeorum:oak_sieve", 1), ("exdeorum:string_mesh", 1)), ("string",), ("minecraft:flint", 8), 2, "pta_main"),
    sq("pebbles", "Камешки", "II · СИТО", "Просей землю или собери камешки доступным рецептом и сложи их в полноценный камень.", 32, 50, "circle", 1.1, ("exdeorum:stone_pebble", 64), ("sieve",), ("minecraft:cobblestone", 16), 2, "pta_main"),
    sq("cobble", "Булыжник", "III · КАМЕНЬ", "Создай устойчивый запас булыжника — основу дробления, лавы и будущей автоматизации.", 39, 50, "circle", 1.1, ("minecraft:cobblestone", 64), ("pebbles",), ("exdeorum:wooden_hammer", 1), 2, "pta_main"),
    sq("hammer", "Дробление", "III · КАМЕНЬ", "Молот превращает булыжник в гравий, гравий в песок, а песок в пыль.", 46, 50, "circle", 1.1, ("exdeorum:stone_hammer", 1), ("cobble",), ("minecraft:flint", 8), 2, "pta_main"),
    sq("flintmesh", "Кремнёвая сетка", "III · КАМЕНЬ", "Улучшенная сетка открывает металлические кусочки и ускоряет начало технической эпохи.", 53, 50, "circle", 1.1, ("exdeorum:flint_mesh", 1), ("hammer",), ("exdeorum:iron_ore_chunk", 8), 3, "pta_main"),
    sq("ores", "Рудный поток", "IV · РЕСУРСЫ", "Наладь постоянное просеивание гравия. Железо и медь станут первыми промышленными металлами.", 60, 50, "circle", 1.1, (("exdeorum:iron_ore_chunk", 32), ("exdeorum:copper_ore_chunk", 32)), ("flintmesh",), ("minecraft:iron_ingot", 8), 4, "pta_main"),
    sq("ironmesh", "Железная сетка", "IV · РЕСУРСЫ", "Железная сетка открывает редстоун, золото и редкие ресурсы для машин.", 67, 50, "circle", 1.1, ("exdeorum:iron_mesh", 1), ("ores",), ("minecraft:redstone", 16), 4, "pta_main"),
    sq("generator", "Бесконечный камень", "V · ИЗМЕРЕНИЯ", "Собери безопасный генератор булыжника и докажи его производительность сжатым блоком.", 74, 50, "octagon", 1.45, ("exdeorum:compressed_cobblestone", 1), ("ironmesh",), ("exdeorum:diamond_hammer", 1), 5, "pta_main"),
    sq("autohammer", "Flux Hammer", "VI · АВТО", "Подай FE в электрический молот и автоматизируй всю цепочку дробления.", 81, 50, "square", 1.35, ("exmachinis:flux_hammer", 1), ("generator",), ("exmachinis:gold_upgrade", 1), 6, "pta_auto"),
    sq("autosieve", "Flux Sieve", "VI · АВТО", "Автоматическое сито превращает стабильный поток блоков в стабильный поток ресурсов.", 88, 50, "square", 1.35, ("exmachinis:flux_sieve", 1), ("autohammer",), ("exmachinis:diamond_upgrade", 1), 7, "pta_auto"),
    sq("core", "Ресурсное ядро", "VII · ПЕРЕХОД", "Объедини дробление, просеивание, уплотнение и вывод предметов. Остров готов к промышленной механизации.", 96, 50, "diamond", 1.75, (("exmachinis:flux_compactor", 1), ("exmachinis:item_buffer", 1)), ("autosieve", "export"), ("create:andesite_alloy", 16), 12, "pta_transition"),

    sq("tree", "Дерево в пустоте", "I · ОСТРОВ", "Выращивай деревья на безопасной площадке и не допускай падения саженцев в пустоту.", 5, 29, "octagon", 1.0, ("minecraft:oak_log", 32), ("start",), ("minecraft:bone_meal", 8), 1, "pta_resource"),
    sq("sapling", "Запас саженцев", "I · ОСТРОВ", "Сохрани резерв саженцев до расширения острова.", 12, 19, "octagon", 1.0, ("minecraft:oak_sapling", 8), ("tree",), ("minecraft:dirt", 2), 1, "pta_resource"),
    sq("silkworm", "Шелкопряд", "I · ОСТРОВ", "Получи шелкопряда крюком и используй его только на отдельном дереве.", 12, 35, "octagon", 1.0, ("exdeorum:silkworm", 1), ("crook",), ("minecraft:string", 8), 1, "pta_resource"),
    sq("stringmesh", "Нитяная сетка", "II · СИТО", "Сплети первую сетку. Её можно зачаровывать на эффективность и удачу.", 24, 34, "octagon", 1.0, ("exdeorum:string_mesh", 1), ("string",), ("minecraft:flint", 4), 1, "pta_resource"),
    sq("barrel", "Деревянная бочка", "I · ОСТРОВ", "Бочка компостирует органику и участвует в превращениях жидкостей.", 20, 68, "octagon", 1.0, ("exdeorum:oak_barrel", 1), ("sieve",), ("minecraft:oak_leaves", 16), 2, "pta_resource"),
    sq("compost", "Компост", "I · ОСТРОВ", "Заполни бочку листьями или растениями и получи возобновляемую землю.", 28, 76, "octagon", 1.0, ("minecraft:dirt", 8), ("barrel",), ("exdeorum:grass_seeds", 1), 2, "pta_resource"),
    sq("water", "Бесконечная вода", "I · ОСТРОВ", "Создай источник воды. Он потребуется для глины, ведьминой воды и производственных линий.", 36, 72, "octagon", 1.0, ("minecraft:water_bucket", 1), ("compost",), ("minecraft:bucket", 2), 2, "pta_resource"),
    sq("clay", "Глина", "III · КАМЕНЬ", "Добавь пыль в воду и получи глину для фарфорового тигля.", 45, 72, "octagon", 1.0, ("minecraft:clay_ball", 16), ("water",), ("minecraft:bone_meal", 8), 2, "pta_resource"),

    sq("gravel", "Гравий", "III · КАМЕНЬ", "Раздроби булыжник молотом.", 43, 61, "octagon", 1.0, ("minecraft:gravel", 64), ("hammer",), ("minecraft:flint", 8), 2, "pta_resource"),
    sq("sand", "Песок", "III · КАМЕНЬ", "Продолжи дробление гравия.", 50, 65, "octagon", 1.0, ("minecraft:sand", 64), ("gravel",), ("minecraft:glass", 8), 2, "pta_resource"),
    sq("dust", "Пыль", "III · КАМЕНЬ", "Раздроби песок до тонкой фракции.", 57, 69, "octagon", 1.0, ("exdeorum:dust", 64), ("sand",), ("minecraft:clay", 4), 3, "pta_resource"),
    sq("porcelain", "Фарфор", "III · КАМЕНЬ", "Смешай глину с костной мукой и подготовь жаростойкий материал.", 63, 75, "octagon", 1.0, ("exdeorum:porcelain_clay_ball", 8), ("clay",), ("exdeorum:unfired_porcelain_crucible", 1), 3, "pta_resource"),
    sq("crucible", "Тигель", "III · КАМЕНЬ", "Обожги фарфоровый тигель и установи его над подходящим источником тепла.", 69, 69, "octagon", 1.0, ("exdeorum:porcelain_crucible", 1), ("porcelain",), ("minecraft:cobblestone", 16), 3, "pta_resource"),
    sq("lava", "Лава", "III · КАМЕНЬ", "Расплавь камень в тигле и получи первое ведро лавы.", 75, 64, "octagon", 1.0, ("exdeorum:porcelain_lava_bucket", 1), ("crucible",), ("minecraft:obsidian", 4), 4, "pta_resource"),
    sq("obsidian", "Обсидиан", "V · ИЗМЕРЕНИЯ", "Соедини воду и лаву безопасной конструкцией.", 81, 69, "octagon", 1.0, ("minecraft:obsidian", 10), ("lava",), ("minecraft:crying_obsidian", 2), 4, "pta_resource"),

    sq("coal", "Уголь из сита", "IV · РЕСУРСЫ", "Подготовь устойчивое топливо для первых печей и генераторов.", 53, 30, "octagon", 1.0, ("minecraft:coal", 32), ("flintmesh",), ("minecraft:coal_block", 1), 3, "pta_resource"),
    sq("iron", "Железные кусочки", "IV · РЕСУРСЫ", "Собери рудные кусочки и переплавь первое промышленное железо.", 56, 23, "octagon", 1.0, ("exdeorum:iron_ore_chunk", 32), ("ores",), ("minecraft:iron_ingot", 8), 3, "pta_resource"),
    sq("copper", "Медные кусочки", "IV · РЕСУРСЫ", "Запаси медь для Create, кабелей и технических рецептов.", 62, 36, "octagon", 1.0, ("exdeorum:copper_ore_chunk", 32), ("ores",), ("minecraft:copper_ingot", 8), 3, "pta_resource"),
    sq("gold", "Золотой поток", "IV · РЕСУРСЫ", "Золото понадобится для улучшенных сеток, электроники и торговли.", 62, 20, "octagon", 1.0, ("exdeorum:gold_ore_chunk", 16), ("ironmesh",), ("minecraft:gold_ingot", 8), 4, "pta_resource"),
    sq("redstone", "Красный камень", "IV · РЕСУРСЫ", "Создай запас редстоуна для автоматических машин и управляющих схем.", 68, 33, "octagon", 1.0, ("minecraft:redstone", 32), ("ironmesh",), ("minecraft:repeater", 2), 4, "pta_resource"),
    sq("diamondmesh", "Алмазная сетка", "IV · РЕСУРСЫ", "Алмазная сетка повышает качество просеивания и открывает редкие материалы.", 71, 24, "octagon", 1.0, ("exdeorum:diamond_mesh", 1), ("gold",), ("minecraft:diamond", 2), 5, "pta_resource"),
    sq("diamonds", "Алмазы", "IV · РЕСУРСЫ", "Получи достаточно алмазов для инструментов и следующего уровня сетки.", 77, 18, "octagon", 1.0, ("minecraft:diamond", 8), ("diamondmesh",), ("minecraft:experience_bottle", 16), 5, "pta_resource"),
    sq("emerald", "Изумруды", "IV · РЕСУРСЫ", "Подготовь торговый ресурс для жителей и серверной экономики.", 77, 31, "octagon", 1.0, ("minecraft:emerald", 8), ("diamondmesh",), ("minecraft:emerald_block", 1), 5, "pta_resource"),
    sq("netheritemesh", "Незеритовая сетка", "IV · РЕСУРСЫ", "Высшая сетка завершает ручную прогрессию просеивания.", 83, 22, "octagon", 1.0, ("exdeorum:netherite_mesh", 1), ("diamonds",), ("exmachinis:netherite_upgrade", 1), 7, "pta_resource"),
    sq("techores", "Технологические руды", "IV · РЕСУРСЫ", "Добудь осмий и уран для будущей главы Mekanism.", 83, 34, "octagon", 1.0, (("exdeorum:osmium_ore_chunk", 16), ("exdeorum:uranium_ore_chunk", 16)), ("emerald",), ("mekanism:ingot_osmium", 4), 7, "pta_resource"),

    sq("witchwater", "Ведьмина вода", "V · ИЗМЕРЕНИЯ", "Поставь бочку с водой над мицелием и дождись тёмного превращения.", 64, 84, "circle", 1.0, ("exdeorum:witch_water_bucket", 1), ("water",), ("exdeorum:mycelium_spores", 1), 4, "pta_danger"),
    sq("soulsand", "Песок душ", "V · ИЗМЕРЕНИЯ", "Используй ведьмину воду для получения песка душ и незерских ресурсов.", 70, 88, "circle", 1.0, ("minecraft:soul_sand", 32), ("witchwater",), ("minecraft:quartz", 16), 4, "pta_danger"),
    sq("doll", "Подготовка призыва", "V · ИЗМЕРЕНИЯ", "Собери материалы для безопасного получения огненных ресурсов на острове.", 76, 84, "circle", 1.0, ("minecraft:blaze_powder", 8), ("soulsand",), ("minecraft:fire_charge", 4), 5, "pta_danger"),
    sq("blaze", "Огненный рубеж", "V · ИЗМЕРЕНИЯ", "Получи огненные стержни и подготовься к варке зелий и измерениям.", 82, 80, "circle", 1.0, ("minecraft:blaze_rod", 8), ("doll",), ("minecraft:brewing_stand", 1), 5, "pta_danger"),
    sq("nether", "Незерские материалы", "V · ИЗМЕРЕНИЯ", "Собери кварц, светокамень и другие ресурсы измерения без разрушения обычных миров.", 89, 75, "circle", 1.0, (("minecraft:quartz", 32), ("minecraft:glowstone_dust", 32)), ("blaze",), ("minecraft:ender_pearl", 4), 6, "pta_danger"),

    sq("power", "Питание машин", "VI · АВТО", "Подготовь стабильный источник FE для Ex Machinis.", 76, 59, "square", 1.0, ("mekanismgenerators:heat_generator", 1), ("generator",), ("mekanism:basic_universal_cable", 8), 5, "pta_auto"),
    sq("fluxhammer", "Электрическое дробление", "VI · АВТО", "Настрой вход сверху и вывод вперёд у Flux Hammer.", 82, 62, "square", 1.0, ("exmachinis:flux_hammer", 1), ("power",), ("exmachinis:gold_upgrade", 1), 5, "pta_auto"),
    sq("fluxsieve", "Электрическое просеивание", "VI · АВТО", "Установи сетку в Flux Sieve и организуй автоматическую подачу блоков.", 84, 55, "square", 1.0, ("exmachinis:flux_sieve", 1), ("power",), ("exmachinis:item_buffer", 1), 5, "pta_auto"),
    sq("upgrades", "Комплект улучшений", "VI · АВТО", "Ускорь обработку золотыми и алмазными улучшениями.", 88, 66, "square", 1.0, (("exmachinis:gold_upgrade", 2), ("exmachinis:diamond_upgrade", 1)), ("fluxhammer",), ("exmachinis:comparator_upgrade", 1), 6, "pta_auto"),
    sq("bulk", "Пакетная переработка", "VI · АВТО", "Используй сжатые блоки для повышения пропускной способности линии.", 93, 63, "square", 1.0, ("exdeorum:compressed_gravel", 8), ("upgrades",), ("exdeorum:compressed_sand", 8), 6, "pta_auto"),
    sq("export", "Вывод в производство", "VII · ПЕРЕХОД", "Установи буфер и уплотнитель, чтобы ресурсы автоматически попадали в общий склад.", 96, 56, "diamond", 1.25, (("exmachinis:item_buffer", 1), ("exmachinis:flux_compactor", 1)), ("bulk",), ("create:cogwheel", 8), 8, "pta_transition"),
]


def mek_quests() -> list[Quest]:
    phase_tags = {
        "I · ОСНОВА": "pta_main", "II · МАШИНЫ": "pta_main", "III · СЕТИ": "pta_resource",
        "IV · ФАБРИКИ": "pta_auto", "V · ХИМИЯ": "pta_resource", "VI · АТОМ": "pta_danger",
        "VII · ФИНАЛ": "pta_transition",
    }
    result = []
    for n in old_mek.NODES:
        key, title, phase, desc, x, y, shape, size, tasks, deps, reward, xp = n
        result.append(Quest(key, title, phase, desc, round(float(x) * 0.55, 2), round(float(y) * 0.58, 2),
                            shape, size, tuple(tasks), tuple(deps), reward, xp, phase_tags[phase], tasks[0][0]))
    return result


MEK = mek_quests()


def create_quests() -> list[Quest]:
    result = []
    for node in create_data.NODES:
        key, title, phase, desc, x, y, shape, size, tasks, deps, reward, xp, tag, icon = node
        result.append(Quest(key, title, phase, desc, float(x), float(y), shape, size,
                            tuple(tasks), tuple(deps), reward, xp, tag, icon or tasks[0][0]))
    return result


CREATE = create_quests()


def immersive_quests() -> list[Quest]:
    result = []
    for node in immersive_data.NODES:
        key, title, phase, desc, x, y, shape, size, tasks, deps, reward, xp, tag, icon = node
        result.append(Quest(key, title, phase, desc, float(x), float(y), shape, size,
                            tuple(tasks), tuple(deps), reward, xp, tag, icon or tasks[0][0]))
    return result


IMMERSIVE = immersive_quests()
AE2 = next_chapters.build_chapter("ae2", Quest)
APPMEK = next_chapters.build_chapter("appmek", Quest)
ARS = next_chapters.build_chapter("ars", Quest)
OCCULT = next_chapters.build_chapter("occult", Quest)
EVIL = next_chapters.build_chapter("evil", Quest)
FNA = next_chapters.build_chapter("fna", Quest)
IRONS = next_chapters.build_chapter("irons", Quest)
FARMER = next_chapters.build_chapter("farmer", Quest)
MYSTICAL = next_chapters.build_chapter("mystical", Quest)
POKEMON = next_chapters.build_chapter("pokemon", Quest)
TRAINERS = next_chapters.build_chapter("trainers", Quest)
ENDGAME = next_chapters.build_chapter("endgame", Quest)
APOTHEOSIS = next_chapters.build_chapter("apotheosis", Quest)
CATACLYSM = next_chapters.build_chapter("cataclysm", Quest)
DRACONIC = next_chapters.build_chapter("draconic", Quest)
VAMPIRISM = next_chapters.build_chapter("vampirism", Quest)
COBBLEMON_ADVANCED = next_chapters.build_chapter("cobblemon_advanced", Quest)
ACHIEVEMENTS = next_chapters.build_chapter("achievements", Quest)
MILESTONES = {
    "skyblock": {"start": 1, "sieve": 2, "cobble": 3, "ores": 4, "generator": 5, "autohammer": 6, "core": 7},
    "mekanism": {"osmium": 1, "enrichment": 2, "cables": 3, "basicfactory": 4, "purification": 5, "wind": 6, "fusion": 7},
    "create": {"rotation": 1, "casing": 2, "belt": 3, "red_sheet": 4, "deployer": 5, "special_series": 6, "auto_factory": 7},
    "immersive": {"manual": 1, "cokeoven": 2, "blastfurnace": 3, "lv_network": 4, "current_transformer": 5, "metal_press": 6, "biodiesel": 7, "arc_furnace": 8, "industrial_complex": 9},
    "ae2": {f"s{i:02d}_01": i for i in range(1, 10)},
    "appmek": {f"s{i:02d}_01": i for i in range(1, 8)},
    "ars": {f"s{i:02d}_01": i for i in range(1, 9)},
    "occult": {f"s{i:02d}_01": i for i in range(1, 10)},
    "evil": {f"s{i:02d}_01": i for i in range(1, 8)},
    "fna": {f"s{i:02d}_01": i for i in range(1, 9)},
    "irons": {f"s{i:02d}_01": i for i in range(1, 9)},
    "farmer": {f"s{i:02d}_01": i for i in range(1, 8)},
    "mystical": {f"s{i:02d}_01": i for i in range(1, 9)},
    "pokemon": {f"s{i:02d}_01": i for i in range(1, 8)},
    "trainers": {f"s{i:02d}_01": i for i in range(1, 7)},
    "endgame": {f"s{i:02d}_01": i for i in range(1, 7)},
    "apotheosis": {f"s{i:02d}_01": i for i in range(1, 7)},
    "cataclysm": {f"s{i:02d}_01": i for i in range(1, 7)},
    "draconic": {f"s{i:02d}_01": i for i in range(1, 6)},
    "vampirism": {f"s{i:02d}_01": i for i in range(1, 7)},
    "cobblemon_advanced": {f"s{i:02d}_01": i for i in range(1, 7)},
    "achievements": {f"s{i:02d}_01": i for i in range(1, 6)},
}


def make_quest(namespace: str, quest: Quest) -> str:
    quest_id = hid(namespace, "quest", quest.key)
    id_for = lambda kind: hid(namespace, kind, quest.key)
    lines = ["\t\t{"]
    if quest.deps:
        deps = [hid(namespace, "quest", d) for d in quest.deps]
        lines.append("\t\t\tdependencies: [" + ", ".join(q(d) for d in deps) + "]")
    lines += [
        f"\t\t\ticon: {{ id: {q(quest.icon or quest.tasks[0][0])} }}",
        f"\t\t\tid: {q(quest_id)}",
        "\t\t\trewards: [",
        "\t\t\t\t{",
        f"\t\t\t\t\tcount: {quest.reward[1]}",
        f"\t\t\t\t\tid: {q(id_for('reward-item'))}",
        f"\t\t\t\t\titem: {{ count: 1, id: {q(quest.reward[0])} }}",
        "\t\t\t\t\ttype: \"item\"",
        "\t\t\t\t}",
        "\t\t\t\t{",
        f"\t\t\t\t\tid: {q(id_for('reward-xp'))}",
        "\t\t\t\t\ttype: \"xp_levels\"",
        f"\t\t\t\t\txp_levels: {quest.xp}",
        "\t\t\t\t}",
        "\t\t\t]",
        f"\t\t\tshape: {q(quest.shape)}",
        f"\t\t\tsize: {quest.size:.2f}d",
        f"\t\t\ttags: [{q(namespace)}, {q(quest.tag)}]",
        "\t\t\ttasks: [",
    ]
    for index, (item_id, count) in enumerate(quest.tasks):
        lines += [
            "\t\t\t\t{",
            f"\t\t\t\t\tid: {q(id_for(f'task-{index}'))}",
            f"\t\t\t\t\titem: {{ count: {count}, id: {q(item_id)} }}",
            "\t\t\t\t\ttype: \"item\"",
            "\t\t\t\t}",
        ]
    lines += ["\t\t\t]", f"\t\t\tx: {quest.x:.2f}d", f"\t\t\ty: {quest.y:.2f}d", "\t\t}"]
    return "\n".join(lines)


def chapter_geometry(quests: list[Quest]) -> tuple[float, float, float, float]:
    xs = [x.x for x in quests]
    ys = [x.y for x in quests]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)
    left_pad, right_pad, top_pad, bottom_pad = 4.0, 4.0, 8.0, 4.0
    width = max_x - min_x + left_pad + right_pad
    height = max_y - min_y + top_pad + bottom_pad
    cx = (min_x + max_x + right_pad - left_pad) / 2
    cy = (min_y + max_y + bottom_pad - top_pad) / 2
    return width, height, cx, cy


def make_chapter(namespace: str, chapter_id: str, title: str, order: int, icon: str, quests: list[Quest], background: str) -> str:
    width, height, cx, cy = chapter_geometry(quests)
    return "\n".join([
        "{",
        "\tdefault_hide_dependency_lines: false",
        "\tdefault_min_width: 270",
        "\tdefault_quest_shape: \"circle\"",
        f"\tfilename: {q(namespace)}",
        f"\tgroup: {q(GROUP_ID)}",
        f"\ticon: {{ id: {q(icon)} }}",
        f"\tid: {q(chapter_id)}",
        f"\ttitle: {q(title)}",
        "\timages: [{",
        f"\t\theight: {height:.2f}d",
        f"\t\timage: {q(background)}",
        "\t\torder: -10",
        "\t\trotation: 0.0d",
        f"\t\twidth: {width:.2f}d",
        f"\t\tx: {cx:.2f}d",
        f"\t\ty: {cy:.2f}d",
        "\t}]",
        f"\torder_index: {order}",
        "\tquest_links: [ ]",
        "\tquests: [",
        "\n".join(make_quest(namespace, quest) for quest in quests),
        "\t]",
        "}",
        "",
    ])


def language_for(namespace: str, chapter_id: str, title: str, quests: list[Quest]) -> str:
    lines = ["{", f"\tchapter.{chapter_id}.title: {q(title)}"]
    for quest in quests:
        quest_id = hid(namespace, "quest", quest.key)
        lines.append(f"\tquest.{quest_id}.title: {q(quest.title)}")
        lines.append(f"\tquest.{quest_id}.quest_subtitle: {q(quest.phase)}")
        lines.append(f"\tquest.{quest_id}.quest_desc: [")
        stage = MILESTONES[namespace].get(quest.key)
        if stage:
            lines.append(f"\t\t{q('{image:poketech:textures/quests/guides/' + namespace + '_' + str(stage) + '.png width:240 height:88 align:center}')}")
            lines.append("\t\t\"\"")
        lines += [
            f"\t\t{q('&6&l' + quest.phase)}",
            f"\t\t{q('&7' + quest.desc)}",
            "\t\t\"\"",
            f"\t\t{q('&9▶ Цель: &f' + ', '.join(str(c) + '× ' + i for i, c in quest.tasks))}",
            f"\t\t{q('&2◆ Награда: &f' + str(quest.reward[1]) + '× ' + quest.reward[0] + ' и ' + str(quest.xp) + ' ур. опыта')}",
            "\t]",
        ]
    lines.append("}")
    return "\n".join(lines) + "\n"


def merge_languages(*texts: str) -> str:
    body = []
    for text in texts:
        body.extend(text.strip()[1:-1].strip().splitlines())
    return "{\n" + "\n".join(body) + "\n}\n"


def font(size: int, bold: bool = False):
    name = "seguisb.ttf" if bold else "segoeui.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def make_tile(path: Path):
    rng = random.Random(713)
    size = 512
    image = Image.new("RGBA", (size, size), (232, 225, 212, 255))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            noise = rng.choice((-2, -1, 0, 0, 0, 1, 2))
            pixels[x, y] = (232 + noise, 225 + noise, 212 + noise, 255)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_background(path: Path, title: str, stages: list[str], palette: list[tuple[int, int, int]],
                    quests: list[Quest]):
    width_units, height_units, _, _ = chapter_geometry(quests)
    image_w = 2048
    image_h = max(1200, round(image_w * height_units / width_units))
    image = Image.new("RGBA", (image_w, image_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    margin = 22
    draw.rounded_rectangle((margin, margin, image_w - margin, image_h - margin), radius=24,
                           fill=(246, 240, 228, 24), outline=(91, 71, 47, 120), width=5)
    draw.line((72, 174, image_w - 72, 174), fill=(111, 83, 51, 125), width=3)
    draw.text((72, 54), title, font=font(50, True), fill=(62, 48, 31, 215))
    draw.text((74, 122), "POKETECH ARCANA · КНИГА РАЗВИТИЯ", font=font(20, True), fill=(91, 70, 45, 165))
    cell = (image_w - 144) / len(stages)
    strip_top, strip_bottom = 206, 282
    for i, stage in enumerate(stages):
        x0 = 72 + i * cell
        color = palette[i % len(palette)]
        draw.rectangle((x0, strip_top, x0 + cell, strip_bottom),
                       fill=(248, 244, 236, 205), outline=(103, 82, 55, 105), width=2)
        draw.rectangle((x0, strip_top, x0 + 8, strip_bottom), fill=(*color, 155))
        draw.text((x0 + 20, strip_top + 26), stage, font=font(17, True), fill=(69, 54, 37, 220))
        band_top = strip_bottom + 18
        draw.rectangle((x0, band_top, x0 + cell, image_h - 54), fill=(*color, 10))
        draw.line((x0 + cell / 2, band_top + 18, x0 + cell / 2, image_h - 72),
                  fill=(*color, 24), width=2)
    draw.line((72, strip_bottom + 1, image_w - 72, strip_bottom + 1), fill=(91, 71, 47, 95), width=3)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_atlas_background(path: Path, title: str, namespace: str, quests: list[Quest],
                          palette: list[tuple[int, int, int]]):
    width_units, height_units, _, _ = chapter_geometry(quests)
    min_x, max_x = min(q.x for q in quests) - 4, max(q.x for q in quests) + 4
    min_y, max_y = min(q.y for q in quests) - 8, max(q.y for q in quests) + 4
    image_w = 2048
    image_h = max(960, round(image_w * height_units / width_units))
    image = Image.new("RGBA", (image_w, image_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    margin = 22
    draw.rounded_rectangle((margin, margin, image_w - margin, image_h - margin), radius=24,
                           fill=(246, 240, 228, 28), outline=(91, 71, 47, 125), width=5)
    draw.text((64, 48), title, font=font(42, True), fill=(62, 48, 31, 215))
    draw.text((66, 106), "POKETECH ARCANA · КАРТА ПРОГРЕССИИ", font=font(18, True), fill=(91, 70, 45, 165))

    def point(x: float, y: float) -> tuple[float, float]:
        return ((x - min_x) / (max_x - min_x) * image_w,
                (y - min_y) / (max_y - min_y) * image_h)

    centers = next_chapters.CHAPTERS[namespace]["centers"]
    mapped = [point(x, y) for x, y in centers]
    for index, ((x, y), stage) in enumerate(zip(mapped, next_chapters.CHAPTERS[namespace]["stages"])):
        color = palette[index % len(palette)]
        radius_x = max(62, image_w / (len(centers) * 2.7))
        radius_y = max(70, image_h / 5.2)
        draw.ellipse((x - radius_x, y - radius_y, x + radius_x, y + radius_y),
                     fill=(*color, 12), outline=(*color, 75), width=3)
        label = stage[1]
        bbox = draw.textbbox((0, 0), label, font=font(15, True))
        draw.rounded_rectangle((x - (bbox[2] - bbox[0]) / 2 - 10, y - radius_y + 8,
                                x + (bbox[2] - bbox[0]) / 2 + 10, y - radius_y + 34),
                               radius=9, fill=(246, 240, 228, 185))
        draw.text((x - (bbox[2] - bbox[0]) / 2, y - radius_y + 12), label,
                  font=font(15, True), fill=(*color, 205))
    for index in range(len(mapped) - 1):
        x1, y1 = mapped[index]
        x2, y2 = mapped[index + 1]
        color = palette[index % len(palette)]
        if namespace == "appmek":
            mid = (x1 + x2) / 2
            draw.line((x1, y1, mid, y1, mid, y2, x2, y2), fill=(*color, 80), width=12, joint="curve")
        else:
            # A smooth-looking route assembled from short interpolated segments.
            pts = []
            for step in range(21):
                t = step / 20
                u = 1 - t
                mx = (x1 + x2) / 2
                px = u * u * u * x1 + 3 * u * u * t * mx + 3 * u * t * t * mx + t * t * t * x2
                py = u * u * u * y1 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y2
                pts.append((px, py))
            draw.line(pts, fill=(*color, 80), width=12, joint="curve")
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def make_guide(path: Path, title: str, subtitle: str, color: tuple[int, int, int], stage: int):
    image = Image.new("RGBA", (720, 264), (238, 232, 220, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle((4, 4, 716, 260), radius=20, fill=(244, 239, 229, 255), outline=(*color, 150), width=5)
    draw.rectangle((4, 4, 126, 260), fill=(*color, 30))
    draw.ellipse((34, 76, 96, 138), outline=(*color, 210), width=6)
    draw.ellipse((47, 89, 83, 125), fill=(*color, 40), outline=(*color, 150), width=3)
    draw.text((39, 158), f"{stage:02d}", font=font(40, True), fill=(*color, 190))
    draw.text((158, 55), title, font=font(32, True), fill=(55, 48, 39, 255))
    draw.text((158, 110), subtitle, font=font(20), fill=(105, 91, 72, 255))
    draw.line((158, 160, 660, 160), fill=(*color, 80), width=3)
    for i in range(4):
        x = 180 + i * 120
        draw.ellipse((x, 187, x + 28, 215), fill=(246, 242, 233, 255), outline=(*color, 150), width=3)
        if i < 3:
            draw.line((x + 30, 201, x + 116, 201), fill=(*color, 80), width=3)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def theme_text() -> str:
    return """[*]
background: poketech:textures/quests/ui/parchment_tile.png; tile_size=512
chapter_panel_background: color:#F0E8DA; border=#B3A48E; border_round_edges=true
key_reference_background: color:#E8E0D1; border=#B3A48E
selected_chapter_highlight_1: #48B56718
selected_chapter_highlight_2: #20B56718
text_color: #2D2923
hover_text_color: #8B4C13
disabled_text_color: #8B806F
widget_border: #B3A48E
widget_background: #30FFFFFF
button: color:#EEE7DA; border=#AD9F8B; border_round_edges=true
panel: color:#EEE7DA; border=#AD9F8B
disabled_button: color:#D8CFC0; border=#B9AE9E
hover_button: color:#F7F1E7; border=#8B6B45; border_round_edges=true
context_menu: color:#F4EEE3; border=#A99B87; border_round_edges=true
scroll_bar_background: color:#D8CFC0
scroll_bar: color:#A79780; border=#786B59
quest_view_background: color:#F6F1E6; border=#A99B87; border_round_edges=true
quest_view_border: #A99B87
quest_view_title: #2D2923
tasks_text_color: #247FA0
rewards_text_color: #477F45
quest_completed_color: #4F477F45
quest_started_color: #FF247FA0
quest_not_started_color: #FF736858
quest_locked_color: #88736858
dependency_line_completed_color: #E0477F45
dependency_line_uncompleted_color: #E06B6256
dependency_line_unavailable_color: #B86B6256
dependency_line_requires_color: #FF247FA0
dependency_line_required_for_color: #FFB36416
dependency_line_selected_speed: 0.5
dependency_line_unselected_speed: 0.0
dependency_line_thickness: 0.34
quest_spacing: 1.0

[#pta_main]
quest_not_started_color: #FF247FA0
quest_started_color: #FF247FA0

[#pta_resource]
quest_not_started_color: #FF477F45
quest_started_color: #FF477F45

[#pta_auto]
quest_not_started_color: #FF7B4D95
quest_started_color: #FF7B4D95

[#pta_danger]
quest_not_started_color: #FFA54F3B
quest_started_color: #FFA54F3B

[#pta_transition]
quest_not_started_color: #FFB36416
quest_started_color: #FFB36416
"""


def validate(quests: list[Quest], namespace: str, expected: int = 50):
    if len(quests) != expected or len({x.key for x in quests}) != expected:
        raise ValueError(f"{namespace}: expected {expected} unique quests, got {len(quests)}")
    keys = {x.key for x in quests}
    all_ids: set[str] = set()
    for quest in quests:
        missing = set(quest.deps) - keys
        if missing:
            raise ValueError(f"{namespace}/{quest.key}: missing dependencies {missing}")
        for kind in ("quest", *(f"task-{index}" for index in range(len(quest.tasks))), "reward-item", "reward-xp"):
            object_id = hid(namespace, kind, quest.key)
            if int(object_id, 16) > 0x7FFFFFFFFFFFFFFF:
                raise ValueError(f"{namespace}/{quest.key}: signed-long unsafe ID {object_id}")
            if object_id in all_ids:
                raise ValueError(f"{namespace}/{quest.key}: duplicate ID {object_id}")
            all_ids.add(object_id)
    if namespace == "skyblock":
        exd = {p.stem for p in (WORKSPACE / "skyblock-update" / "extract" / "exdeorum" / "assets" / "exdeorum" / "models" / "item").glob("*.json")}
        exm = {p.stem for p in (WORKSPACE / "skyblock-update" / "extract" / "exmachinis" / "assets" / "exmachinis" / "models" / "item").glob("*.json")}
        for quest in quests:
            for item_id, _ in (*quest.tasks, quest.reward):
                if item_id.startswith("exdeorum:") and item_id.split(":", 1)[1] not in exd:
                    raise ValueError(f"Unknown Ex Deorum item {item_id}")
                if item_id.startswith("exmachinis:") and item_id.split(":", 1)[1] not in exm:
                    raise ValueError(f"Unknown Ex Machinis item {item_id}")


def write_build():
    validate(SKY, "skyblock")
    validate(MEK, "mekanism")
    validate(CREATE, "create")
    validate(IMMERSIVE, "immersive", 82)
    validate(AE2, "ae2", 94)
    validate(APPMEK, "appmek", 44)
    validate(ARS, "ars", 70)
    validate(OCCULT, "occult", 89)
    validate(EVIL, "evil", 65)
    validate(FNA, "fna", 77)
    validate(IRONS, "irons", 84)
    validate(FARMER, "farmer", 72)
    validate(MYSTICAL, "mystical", 86)
    validate(POKEMON, "pokemon", 78)
    validate(TRAINERS, "trainers", 66)
    validate(ENDGAME, "endgame", 92)
    validate(APOTHEOSIS, "apotheosis", 76)
    validate(CATACLYSM, "cataclysm", 70)
    validate(DRACONIC, "draconic", 88)
    validate(VAMPIRISM, "vampirism", 72)
    validate(COBBLEMON_ADVANCED, "cobblemon_advanced", 80)
    validate(ACHIEVEMENTS, "achievements", 64)
    if BUILD.exists():
        shutil.rmtree(BUILD)
    (QUESTS / "chapters").mkdir(parents=True)
    (QUESTS / "lang").mkdir(parents=True)

    data = """{
\tdefault_autoclaim_rewards: "disabled"
\tdefault_consume_items: false
\tdefault_quest_disable_jei: false
\tdefault_quest_shape: "circle"
\tdefault_reward_team: false
\tdetection_delay: 20
\tdisable_gui: false
\tdrop_book_on_death: false
\tdrop_loot_crates: false
\temergency_items_cooldown: 0
\tfallback_locale: "ru_ru"
\tgrid_scale: 0.5d
\thide_excluded_quests: false
\tlock_message: "&cСначала завершите предыдущий этап"
\tloot_crate_no_drop: { boss: 0, monster: 600, passive: 4000 }
\tpause_game: false
\tprogression_mode: "linear"
\tshow_lock_icons: true
\tverify_on_load: false
\tversion: 13
}
"""
    groups = f'{{\n\tchapter_groups: [{{ icon: {{ id: "minecraft:book" }}, id: "{GROUP_ID}", title: "PokeTech Arcana · Книга развития" }}]\n}}\n'
    (QUESTS / "data.snbt").write_text(data, encoding="utf-8")
    (QUESTS / "chapter_groups.snbt").write_text(groups, encoding="utf-8")
    sky_title = "Skyblock: из пустоты к производству"
    mek_title = "Mekanism: эра атома"
    create_title = "Create: фабрика покеболов"
    immersive_title = "Immersive Engineering: тяжёлая промышленность"
    ae2_title = next_chapters.CHAPTERS["ae2"]["title"]
    appmek_title = next_chapters.CHAPTERS["appmek"]["title"]
    ars_title = next_chapters.CHAPTERS["ars"]["title"]
    occult_title = next_chapters.CHAPTERS["occult"]["title"]
    evil_title = next_chapters.CHAPTERS["evil"]["title"]
    fna_title = next_chapters.CHAPTERS["fna"]["title"]
    irons_title = next_chapters.CHAPTERS["irons"]["title"]
    farmer_title = next_chapters.CHAPTERS["farmer"]["title"]
    mystical_title = next_chapters.CHAPTERS["mystical"]["title"]
    pokemon_title = next_chapters.CHAPTERS["pokemon"]["title"]
    trainers_title = next_chapters.CHAPTERS["trainers"]["title"]
    endgame_title = next_chapters.CHAPTERS["endgame"]["title"]
    apotheosis_title = next_chapters.CHAPTERS["apotheosis"]["title"]
    cataclysm_title = next_chapters.CHAPTERS["cataclysm"]["title"]
    draconic_title = next_chapters.CHAPTERS["draconic"]["title"]
    vampirism_title = next_chapters.CHAPTERS["vampirism"]["title"]
    cobblemon_advanced_title = next_chapters.CHAPTERS["cobblemon_advanced"]["title"]
    achievements_title = next_chapters.CHAPTERS["achievements"]["title"]
    (QUESTS / "chapters" / "skyblock.snbt").write_text(make_chapter("skyblock", SKY_CHAPTER_ID, sky_title, 0, "exdeorum:oak_sieve", SKY, "poketech:textures/quests/backgrounds/skyblock_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "create.snbt").write_text(make_chapter("create", CREATE_CHAPTER_ID, create_title, 1, "create:mechanical_press", CREATE, "poketech:textures/quests/backgrounds/create_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "immersive.snbt").write_text(make_chapter("immersive", IMMERSIVE_CHAPTER_ID, immersive_title, 2, "immersiveengineering:hammer", IMMERSIVE, "poketech:textures/quests/backgrounds/immersive_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "mekanism.snbt").write_text(make_chapter("mekanism", MEK_CHAPTER_ID, mek_title, 3, "mekanism:metallurgic_infuser", MEK, "poketech:textures/quests/backgrounds/mekanism_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "ae2.snbt").write_text(make_chapter("ae2", AE2_CHAPTER_ID, ae2_title, 4, "ae2:controller", AE2, "poketech:textures/quests/backgrounds/ae2_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "appmek.snbt").write_text(make_chapter("appmek", APPMEK_CHAPTER_ID, appmek_title, 5, "mekanism:chemical_tank", APPMEK, "poketech:textures/quests/backgrounds/appmek_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "ars.snbt").write_text(make_chapter("ars", ARS_CHAPTER_ID, ars_title, 6, "ars_nouveau:archmage_spell_book", ARS, "poketech:textures/quests/backgrounds/ars_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "occult.snbt").write_text(make_chapter("occult", OCCULT_CHAPTER_ID, occult_title, 7, "occultism:dictionary_of_spirits", OCCULT, "poketech:textures/quests/backgrounds/occult_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "evil.snbt").write_text(make_chapter("evil", EVIL_CHAPTER_ID, evil_title, 8, "evilcraft:dark_gem", EVIL, "poketech:textures/quests/backgrounds/evil_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "fna.snbt").write_text(make_chapter("fna", FNA_CHAPTER_ID, fna_title, 9, "forbidden_arcanus:arcane_crystal", FNA, "poketech:textures/quests/backgrounds/fna_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "irons.snbt").write_text(make_chapter("irons", IRONS_CHAPTER_ID, irons_title, 10, "irons_spellbooks:scroll", IRONS, "poketech:textures/quests/backgrounds/irons_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "farmer.snbt").write_text(make_chapter("farmer", FARMER_CHAPTER_ID, farmer_title, 11, "farmersdelight:cooking_pot", FARMER, "poketech:textures/quests/backgrounds/farmer_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "mystical.snbt").write_text(make_chapter("mystical", MYSTICAL_CHAPTER_ID, mystical_title, 12, "mysticalagriculture:inferium_essence", MYSTICAL, "poketech:textures/quests/backgrounds/mystical_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "pokemon.snbt").write_text(make_chapter("pokemon", POKEMON_CHAPTER_ID, pokemon_title, 13, "cobblemon:poke_ball", POKEMON, "poketech:textures/quests/backgrounds/pokemon_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "trainers.snbt").write_text(make_chapter("trainers", TRAINERS_CHAPTER_ID, trainers_title, 14, "rctmod:trainer_card", TRAINERS, "poketech:textures/quests/backgrounds/trainers_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "endgame.snbt").write_text(make_chapter("endgame", ENDGAME_CHAPTER_ID, endgame_title, 15, "draconicevolution:chaos_shard", ENDGAME, "poketech:textures/quests/backgrounds/endgame_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "apotheosis.snbt").write_text(make_chapter("apotheosis", APOTHEOSIS_CHAPTER_ID, apotheosis_title, 16, "apotheosis:reforging_table", APOTHEOSIS, "poketech:textures/quests/backgrounds/apotheosis_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "cataclysm.snbt").write_text(make_chapter("cataclysm", CATACLYSM_CHAPTER_ID, cataclysm_title, 17, "cataclysm:witherite_ingot", CATACLYSM, "poketech:textures/quests/backgrounds/cataclysm_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "draconic.snbt").write_text(make_chapter("draconic", DRACONIC_CHAPTER_ID, draconic_title, 18, "draconicevolution:chaos_shard", DRACONIC, "poketech:textures/quests/backgrounds/draconic_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "vampirism.snbt").write_text(make_chapter("vampirism", VAMPIRISM_CHAPTER_ID, vampirism_title, 19, "vampirism:vampire_book", VAMPIRISM, "poketech:textures/quests/backgrounds/vampirism_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "cobblemon_advanced.snbt").write_text(make_chapter("cobblemon_advanced", COBBLEMON_ADVANCED_CHAPTER_ID, cobblemon_advanced_title, 20, "cobblemon:master_ball", COBBLEMON_ADVANCED, "poketech:textures/quests/backgrounds/cobblemon_advanced_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "achievements.snbt").write_text(make_chapter("achievements", ACHIEVEMENTS_CHAPTER_ID, achievements_title, 21, "minecraft:nether_star", ACHIEVEMENTS, "poketech:textures/quests/backgrounds/achievements_book.png"), encoding="utf-8")

    sky_lang = language_for("skyblock", SKY_CHAPTER_ID, sky_title, SKY)
    mek_lang = language_for("mekanism", MEK_CHAPTER_ID, mek_title, MEK)
    create_lang = language_for("create", CREATE_CHAPTER_ID, create_title, CREATE)
    immersive_lang = language_for("immersive", IMMERSIVE_CHAPTER_ID, immersive_title, IMMERSIVE)
    ae2_lang = language_for("ae2", AE2_CHAPTER_ID, ae2_title, AE2)
    appmek_lang = language_for("appmek", APPMEK_CHAPTER_ID, appmek_title, APPMEK)
    ars_lang = language_for("ars", ARS_CHAPTER_ID, ars_title, ARS)
    occult_lang = language_for("occult", OCCULT_CHAPTER_ID, occult_title, OCCULT)
    evil_lang = language_for("evil", EVIL_CHAPTER_ID, evil_title, EVIL)
    fna_lang = language_for("fna", FNA_CHAPTER_ID, fna_title, FNA)
    irons_lang = language_for("irons", IRONS_CHAPTER_ID, irons_title, IRONS)
    farmer_lang = language_for("farmer", FARMER_CHAPTER_ID, farmer_title, FARMER)
    mystical_lang = language_for("mystical", MYSTICAL_CHAPTER_ID, mystical_title, MYSTICAL)
    pokemon_lang = language_for("pokemon", POKEMON_CHAPTER_ID, pokemon_title, POKEMON)
    trainers_lang = language_for("trainers", TRAINERS_CHAPTER_ID, trainers_title, TRAINERS)
    endgame_lang = language_for("endgame", ENDGAME_CHAPTER_ID, endgame_title, ENDGAME)
    apotheosis_lang = language_for("apotheosis", APOTHEOSIS_CHAPTER_ID, apotheosis_title, APOTHEOSIS)
    cataclysm_lang = language_for("cataclysm", CATACLYSM_CHAPTER_ID, cataclysm_title, CATACLYSM)
    draconic_lang = language_for("draconic", DRACONIC_CHAPTER_ID, draconic_title, DRACONIC)
    vampirism_lang = language_for("vampirism", VAMPIRISM_CHAPTER_ID, vampirism_title, VAMPIRISM)
    cobblemon_advanced_lang = language_for("cobblemon_advanced", COBBLEMON_ADVANCED_CHAPTER_ID, cobblemon_advanced_title, COBBLEMON_ADVANCED)
    achievements_lang = language_for("achievements", ACHIEVEMENTS_CHAPTER_ID, achievements_title, ACHIEVEMENTS)
    group_lang = "{\n\tchapter_group.%s.title: %s\n}\n" % (GROUP_ID, q("PokeTech Arcana · Книга развития"))
    merged = merge_languages(group_lang, sky_lang, create_lang, immersive_lang, mek_lang, ae2_lang, appmek_lang, ars_lang, occult_lang, evil_lang, fna_lang, irons_lang, farmer_lang, mystical_lang, pokemon_lang, trainers_lang, endgame_lang, apotheosis_lang, cataclysm_lang, draconic_lang, vampirism_lang, cobblemon_advanced_lang, achievements_lang)
    for locale in ("ru_ru", "en_us"):
        (QUESTS / "lang" / f"{locale}.snbt").write_text(merged, encoding="utf-8")
        split = QUESTS / "lang" / locale
        (split / "chapters").mkdir(parents=True)
        (split / "chapter_group.snbt").write_text(group_lang, encoding="utf-8")
        chapter_lang = "{\n" + "\n".join(f"\tchapter.{cid}.title: {q(title)}" for cid, title in (
            (SKY_CHAPTER_ID, sky_title), (CREATE_CHAPTER_ID, create_title), (IMMERSIVE_CHAPTER_ID, immersive_title),
            (MEK_CHAPTER_ID, mek_title), (AE2_CHAPTER_ID, ae2_title), (APPMEK_CHAPTER_ID, appmek_title), (ARS_CHAPTER_ID, ars_title),
            (OCCULT_CHAPTER_ID, occult_title), (EVIL_CHAPTER_ID, evil_title), (FNA_CHAPTER_ID, fna_title),
            (IRONS_CHAPTER_ID, irons_title), (FARMER_CHAPTER_ID, farmer_title), (MYSTICAL_CHAPTER_ID, mystical_title),
            (POKEMON_CHAPTER_ID, pokemon_title), (TRAINERS_CHAPTER_ID, trainers_title), (ENDGAME_CHAPTER_ID, endgame_title),
            (APOTHEOSIS_CHAPTER_ID, apotheosis_title), (CATACLYSM_CHAPTER_ID, cataclysm_title), (DRACONIC_CHAPTER_ID, draconic_title),
            (VAMPIRISM_CHAPTER_ID, vampirism_title), (COBBLEMON_ADVANCED_CHAPTER_ID, cobblemon_advanced_title), (ACHIEVEMENTS_CHAPTER_ID, achievements_title)
        )) + "\n}\n"
        (split / "chapter.snbt").write_text(chapter_lang, encoding="utf-8")
        sky_quest_lang = "{\n" + "\n".join(sky_lang.strip().splitlines()[2:-1]) + "\n}\n"
        mek_quest_lang = "{\n" + "\n".join(mek_lang.strip().splitlines()[2:-1]) + "\n}\n"
        create_quest_lang = "{\n" + "\n".join(create_lang.strip().splitlines()[2:-1]) + "\n}\n"
        immersive_quest_lang = "{\n" + "\n".join(immersive_lang.strip().splitlines()[2:-1]) + "\n}\n"
        ae2_quest_lang = "{\n" + "\n".join(ae2_lang.strip().splitlines()[2:-1]) + "\n}\n"
        appmek_quest_lang = "{\n" + "\n".join(appmek_lang.strip().splitlines()[2:-1]) + "\n}\n"
        ars_quest_lang = "{\n" + "\n".join(ars_lang.strip().splitlines()[2:-1]) + "\n}\n"
        occult_quest_lang = "{\n" + "\n".join(occult_lang.strip().splitlines()[2:-1]) + "\n}\n"
        evil_quest_lang = "{\n" + "\n".join(evil_lang.strip().splitlines()[2:-1]) + "\n}\n"
        fna_quest_lang = "{\n" + "\n".join(fna_lang.strip().splitlines()[2:-1]) + "\n}\n"
        irons_quest_lang = "{\n" + "\n".join(irons_lang.strip().splitlines()[2:-1]) + "\n}\n"
        farmer_quest_lang = "{\n" + "\n".join(farmer_lang.strip().splitlines()[2:-1]) + "\n}\n"
        mystical_quest_lang = "{\n" + "\n".join(mystical_lang.strip().splitlines()[2:-1]) + "\n}\n"
        pokemon_quest_lang = "{\n" + "\n".join(pokemon_lang.strip().splitlines()[2:-1]) + "\n}\n"
        trainers_quest_lang = "{\n" + "\n".join(trainers_lang.strip().splitlines()[2:-1]) + "\n}\n"
        endgame_quest_lang = "{\n" + "\n".join(endgame_lang.strip().splitlines()[2:-1]) + "\n}\n"
        apotheosis_quest_lang = "{\n" + "\n".join(apotheosis_lang.strip().splitlines()[2:-1]) + "\n}\n"
        cataclysm_quest_lang = "{\n" + "\n".join(cataclysm_lang.strip().splitlines()[2:-1]) + "\n}\n"
        draconic_quest_lang = "{\n" + "\n".join(draconic_lang.strip().splitlines()[2:-1]) + "\n}\n"
        vampirism_quest_lang = "{\n" + "\n".join(vampirism_lang.strip().splitlines()[2:-1]) + "\n}\n"
        cobblemon_advanced_quest_lang = "{\n" + "\n".join(cobblemon_advanced_lang.strip().splitlines()[2:-1]) + "\n}\n"
        achievements_quest_lang = "{\n" + "\n".join(achievements_lang.strip().splitlines()[2:-1]) + "\n}\n"
        (split / "chapters" / "skyblock.snbt").write_text(sky_quest_lang, encoding="utf-8")
        (split / "chapters" / "mekanism.snbt").write_text(mek_quest_lang, encoding="utf-8")
        (split / "chapters" / "create.snbt").write_text(create_quest_lang, encoding="utf-8")
        (split / "chapters" / "immersive.snbt").write_text(immersive_quest_lang, encoding="utf-8")
        (split / "chapters" / "ae2.snbt").write_text(ae2_quest_lang, encoding="utf-8")
        (split / "chapters" / "appmek.snbt").write_text(appmek_quest_lang, encoding="utf-8")
        (split / "chapters" / "ars.snbt").write_text(ars_quest_lang, encoding="utf-8")
        (split / "chapters" / "occult.snbt").write_text(occult_quest_lang, encoding="utf-8")
        (split / "chapters" / "evil.snbt").write_text(evil_quest_lang, encoding="utf-8")
        (split / "chapters" / "fna.snbt").write_text(fna_quest_lang, encoding="utf-8")
        (split / "chapters" / "irons.snbt").write_text(irons_quest_lang, encoding="utf-8")
        (split / "chapters" / "farmer.snbt").write_text(farmer_quest_lang, encoding="utf-8")
        (split / "chapters" / "mystical.snbt").write_text(mystical_quest_lang, encoding="utf-8")
        (split / "chapters" / "pokemon.snbt").write_text(pokemon_quest_lang, encoding="utf-8")
        (split / "chapters" / "trainers.snbt").write_text(trainers_quest_lang, encoding="utf-8")
        (split / "chapters" / "endgame.snbt").write_text(endgame_quest_lang, encoding="utf-8")
        (split / "chapters" / "apotheosis.snbt").write_text(apotheosis_quest_lang, encoding="utf-8")
        (split / "chapters" / "cataclysm.snbt").write_text(cataclysm_quest_lang, encoding="utf-8")
        (split / "chapters" / "draconic.snbt").write_text(draconic_quest_lang, encoding="utf-8")
        (split / "chapters" / "vampirism.snbt").write_text(vampirism_quest_lang, encoding="utf-8")
        (split / "chapters" / "cobblemon_advanced.snbt").write_text(cobblemon_advanced_quest_lang, encoding="utf-8")
        (split / "chapters" / "achievements.snbt").write_text(achievements_quest_lang, encoding="utf-8")

    ftb_assets = ASSETS / "ftbquests"
    ftb_assets.mkdir(parents=True)
    (ftb_assets / "ftb_quests_theme.txt").write_text(theme_text(), encoding="utf-8")
    tex = ASSETS / "poketech" / "textures" / "quests"
    make_tile(tex / "ui" / "parchment_tile.png")
    make_background(tex / "backgrounds" / "skyblock_book.png", "SKYBLOCK: ИЗ ПУСТОТЫ К ПРОИЗВОДСТВУ", ["I · ОСТРОВ", "II · СИТО", "III · КАМЕНЬ", "IV · РЕСУРСЫ", "V · МИРЫ", "VI · АВТО", "VII · ПЕРЕХОД"], [(71, 127, 69), (36, 127, 160), (123, 77, 149), (179, 100, 22)], SKY)
    make_background(tex / "backgrounds" / "mekanism_book.png", "MEKANISM: ЭРА АТОМА", ["I · ОСНОВА", "II · МАШИНЫ", "III · СЕТИ", "IV · ФАБРИКИ", "V · ХИМИЯ", "VI · АТОМ", "VII · ФИНАЛ"], [(36, 127, 160), (71, 127, 69), (123, 77, 149), (165, 79, 59)], MEK)
    make_background(tex / "backgrounds" / "create_book.png", "CREATE: ФАБРИКА ПОКЕБОЛОВ", ["I · КИНЕТИКА", "II · МЕХАНИЗМЫ", "III · КОНВЕЙЕР", "IV · ДЕТАЛИ", "V · СБОРКА", "VI · ОСОБЫЕ", "VII · ФАБРИКА"], [(187, 137, 45), (69, 126, 72), (35, 128, 143), (176, 70, 65), (122, 75, 148), (57, 111, 168), (140, 91, 47)], CREATE)
    make_background(tex / "backgrounds" / "immersive_book.png", "IMMERSIVE ENGINEERING: ТЯЖЁЛАЯ ПРОМЫШЛЕННОСТЬ", ["I · РУКОВОДСТВО", "II · МАТЕРИАЛЫ", "III · СТАЛЬ", "IV · ЭНЕРГИЯ LV", "V · ЭЛЕКТРОСЕТЬ", "VI · МАШИНЫ", "VII · ТОПЛИВО", "VIII · ТЯЖЁЛАЯ", "IX · ИНТЕГРАЦИЯ"], [(47, 127, 137), (118, 143, 69), (104, 118, 133), (188, 129, 38), (60, 131, 170), (154, 95, 53), (110, 142, 79), (162, 75, 62), (134, 88, 149)], IMMERSIVE)
    make_atlas_background(tex / "backgrounds" / "ae2_book.png", "APPLIED ENERGISTICS 2: АРХИТЕКТУРА СЕТИ", "ae2", AE2, [(57, 127, 146), (91, 104, 157), (66, 135, 115), (175, 121, 54)])
    make_atlas_background(tex / "backgrounds" / "appmek_book.png", "APPLIED MEKANISTICS: ЦИФРОВОЙ ХИМЗАВОД", "appmek", APPMEK, [(118, 84, 150), (52, 125, 120), (175, 107, 54), (94, 116, 147)])
    make_atlas_background(tex / "backgrounds" / "ars_book.png", "ARS NOUVEAU: СОЗВЕЗДИЕ АРХИМАГА", "ars", ARS, [(118, 84, 154), (151, 105, 58), (75, 126, 155), (137, 83, 135)])
    make_atlas_background(tex / "backgrounds" / "occult_book.png", "OCCULTISM: КРУГИ И ДУХИ", "occult", OCCULT, [(139, 90, 158), (182, 123, 57), (91, 77, 139), (78, 123, 126)])
    make_atlas_background(tex / "backgrounds" / "evil_book.png", "EVILCRAFT: ЭНЕРГИЯ ЖИЗНИ", "evil", EVIL, [(163, 79, 87), (94, 120, 150), (121, 63, 74), (183, 116, 58)])
    make_atlas_background(tex / "backgrounds" / "fna_book.png", "FORBIDDEN & ARCANUS: ЗАПРЕТНЫЕ РЕЛИКВИИ", "fna", FNA, [(61, 122, 114), (176, 131, 69), (77, 103, 145), (135, 78, 120)])
    make_atlas_background(tex / "backgrounds" / "irons_book.png", "IRON'S SPELLS: ГРИМУАР АРКАНЫ", "irons", IRONS, [(118, 87, 168), (189, 138, 73), (85, 117, 159), (145, 79, 129)])
    make_atlas_background(tex / "backgrounds" / "farmer_book.png", "FARMER'S DELIGHT: СЕЗОНЫ ОСТРОВА", "farmer", FARMER, [(178, 111, 61), (111, 153, 88), (192, 146, 66), (81, 132, 95)])
    make_atlas_background(tex / "backgrounds" / "mystical_book.png", "MYSTICAL AGRICULTURE: СЕМЕНА ЭЛЕМЕНТОВ", "mystical", MYSTICAL, [(77, 131, 166), (165, 110, 72), (91, 108, 160), (115, 78, 145)])
    make_atlas_background(tex / "backgrounds" / "pokemon_book.png", "POKÉMON: ПУТЬ ТРЕНЕРА", "pokemon", POKEMON, [(78, 134, 170), (208, 139, 61), (88, 151, 102), (154, 83, 96)])
    make_atlas_background(tex / "backgrounds" / "trainers_book.png", "ТРЕНЕРЫ И ДАНЖИ: ИСПЫТАНИЯ МИРОВ", "trainers", TRAINERS, [(155, 91, 85), (184, 139, 72), (77, 112, 143), (114, 78, 128)])
    make_atlas_background(tex / "backgrounds" / "endgame_book.png", "ЭНДГЕЙМ: ЯДРО POKETECH ARCANA", "endgame", ENDGAME, [(118, 89, 159), (180, 126, 67), (72, 126, 158), (146, 70, 105)])
    make_atlas_background(tex / "backgrounds" / "apotheosis_book.png", "APOTHEOSIS: КУЗНИЦА ГЕРОЯ", "apotheosis", APOTHEOSIS, [(120, 58, 83), (167, 75, 73), (74, 82, 123), (176, 126, 58)])
    make_atlas_background(tex / "backgrounds" / "cataclysm_book.png", "CATACLYSM: ЦИТАДЕЛИ БОССОВ", "cataclysm", CATACLYSM, [(75, 132, 166), (212, 139, 57), (99, 151, 108), (148, 83, 125)])
    make_atlas_background(tex / "backgrounds" / "draconic_book.png", "DRACONIC EVOLUTION: СЕРДЦЕ ХАОСА", "draconic", DRACONIC, [(112, 101, 62), (73, 121, 142), (153, 95, 55), (103, 77, 139)])
    make_atlas_background(tex / "backgrounds" / "vampirism_book.png", "VAMPIRISM: ДВЕ ДОРОГИ НОЧИ", "vampirism", VAMPIRISM, [(143, 53, 79), (115, 80, 165), (62, 67, 111), (187, 117, 72)])
    make_atlas_background(tex / "backgrounds" / "cobblemon_advanced_book.png", "COBBLEMON: МАСТЕРСТВО РЕГИОНА", "cobblemon_advanced", COBBLEMON_ADVANCED, [(57, 127, 146), (194, 131, 61), (77, 112, 143), (119, 81, 145)])
    make_atlas_background(tex / "backgrounds" / "achievements_book.png", "ДОСТИЖЕНИЯ СЕРВЕРА: СОЗВЕЗДИЕ ГЕРОЯ", "achievements", ACHIEVEMENTS, [(154, 113, 53), (114, 86, 164), (64, 107, 127), (182, 78, 69)])
    palettes = [(36, 127, 160), (71, 127, 69), (123, 77, 149), (179, 100, 22), (71, 127, 69), (123, 77, 149), (179, 100, 22), (165, 79, 59), (57, 111, 168), (139, 90, 158), (163, 79, 87), (61, 122, 114), (118, 87, 168), (178, 111, 61), (77, 131, 166)]
    for namespace, title in (("skyblock", "Skyblock"), ("mekanism", "Mekanism"), ("create", "Create"), ("immersive", "Immersive Engineering"), ("ae2", "Applied Energistics 2"), ("appmek", "Applied Mekanistics"), ("ars", "Ars Nouveau"), ("occult", "Occultism"), ("evil", "EvilCraft"), ("fna", "Forbidden & Arcanus"), ("irons", "Iron's Spells"), ("farmer", "Farmer's Delight"), ("mystical", "Mystical Agriculture"), ("pokemon", "Pokémon"), ("trainers", "Тренеры и данжи"), ("endgame", "Эндгейм"), ("apotheosis", "Apotheosis"), ("cataclysm", "Cataclysm"), ("draconic", "Draconic Evolution"), ("vampirism", "Vampirism"), ("cobblemon_advanced", "Cobblemon: мастерство"), ("achievements", "Достижения сервера")):
        names = ({
            "skyblock": ["Остров", "Просеивание", "Камень", "Ресурсы", "Измерения", "Автоматизация", "Переход"],
            "mekanism": ["Основа", "Машины", "Сети", "Фабрики", "Химия", "Атом", "Финал"],
            "create": ["Кинетика", "Механизмы", "Конвейер", "Детали", "Сборка", "Особые серии", "Фабрика"],
            "immersive": ["Руководство", "Материалы", "Сталь", "Энергия LV", "Электросеть", "Машины", "Топливо", "Тяжёлая индустрия", "Интеграция"],
            "ae2": next_chapters.stage_names("ae2"),
            "appmek": next_chapters.stage_names("appmek"),
            "ars": next_chapters.stage_names("ars"),
            "occult": next_chapters.stage_names("occult"),
            "evil": next_chapters.stage_names("evil"),
            "fna": next_chapters.stage_names("fna"),
            "irons": next_chapters.stage_names("irons"),
            "farmer": next_chapters.stage_names("farmer"),
            "mystical": next_chapters.stage_names("mystical"),
            "pokemon": next_chapters.stage_names("pokemon"),
            "trainers": next_chapters.stage_names("trainers"),
            "endgame": next_chapters.stage_names("endgame"),
            "apotheosis": next_chapters.stage_names("apotheosis"),
            "cataclysm": next_chapters.stage_names("cataclysm"),
            "draconic": next_chapters.stage_names("draconic"),
            "vampirism": next_chapters.stage_names("vampirism"),
            "cobblemon_advanced": next_chapters.stage_names("cobblemon_advanced"),
            "achievements": next_chapters.stage_names("achievements"),
        }[namespace])
        for stage, (name, color) in enumerate(zip(names, palettes), 1):
            make_guide(tex / "guides" / f"{namespace}_{stage}.png", f"{title} · {name}", "Схема этапа и ключевой производственный поток", color, stage)

    client_quests = CLIENT_PACK / "config" / "ftbquests" / "quests"
    if client_quests.exists():
        shutil.rmtree(client_quests)
    shutil.copytree(QUESTS, client_quests)
    for rel in (Path("ftbquests"), Path("poketech") / "textures" / "quests"):
        src, dst = ASSETS / rel, CLIENT_PACK / "kubejs" / "assets" / rel
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    package = ROOT / f"PokeTechArcana-quests-book-{PACKAGE_VERSION}.zip"
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as archive:
        for base in (BUILD / "config", BUILD / "kubejs"):
            for path in base.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(BUILD))
    print(f"Built {len(SKY)} Skyblock + {len(CREATE)} Create + {len(IMMERSIVE)} Immersive Engineering + {len(MEK)} Mekanism + {len(AE2)} AE2 + {len(APPMEK)} Applied Mekanistics + {len(ARS)} Ars Nouveau + {len(OCCULT)} Occultism + {len(EVIL)} EvilCraft + {len(FNA)} Forbidden & Arcanus + {len(IRONS)} Iron's Spells + {len(FARMER)} Farmer's Delight + {len(MYSTICAL)} Mystical Agriculture + {len(POKEMON)} Pokemon + {len(TRAINERS)} Trainers + {len(ENDGAME)} Endgame + {len(APOTHEOSIS)} Apotheosis + {len(CATACLYSM)} Cataclysm + {len(DRACONIC)} Draconic Evolution + {len(VAMPIRISM)} Vampirism + {len(COBBLEMON_ADVANCED)} Cobblemon advanced + {len(ACHIEVEMENTS)} Achievements quests")
    print(f"Server package: {package} ({package.stat().st_size} bytes)")


if __name__ == "__main__":
    write_build()

