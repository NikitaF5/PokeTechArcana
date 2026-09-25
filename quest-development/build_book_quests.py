from __future__ import annotations

import hashlib
import math
import random
import re
import shutil
import zipfile
from dataclasses import dataclass, replace
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
GROUPS = (
    ("271C0B00CAFE1101", "I · Начало и остров", "minecraft:oak_sapling", ("skyblock", "farmer", "mystical", "builder")),
    ("271C0B00CAFE1102", "II · Технологии и автоматизация", "create:precision_mechanism", ("create", "createplus", "immersive", "mekanism", "mekplus", "oritech", "ae2", "appmek", "silentgear", "integration")),
    ("271C0B00CAFE1103", "III · Магия и ритуалы", "ars_nouveau:archmage_spell_book", ("ars", "arsplus", "occult", "evil", "fna", "irons", "vampirism")),
    ("271C0B00CAFE1104", "IV · Покемоны и тренеры", "cobblemon:poke_ball", ("pokemon", "cobblemon_advanced", "cobbleplus", "trainers", "services")),
    ("271C0B00CAFE1105", "V · Исследование миров", "minecraft:filled_map", ("traveler", "atlas", "starlight", "wildlife", "swem", "minecolonies")),
    ("271C0B00CAFE1106", "VI · Битвы, боссы и снаряжение", "minecraft:netherite_sword", ("epicfight", "apotheosis", "artifacts", "relics", "origins", "threats", "worldbosses", "cataclysm", "draconic")),
    ("271C0B00CAFE1107", "VII · Серверный путь и финал", "minecraft:nether_star", ("achievements", "community", "endgame", "finale")),
)
CHAPTER_GROUP_FOR = {namespace: group_id for group_id, _, _, namespaces in GROUPS for namespace in namespaces}
CHAPTER_ORDER_IN_GROUP = {
    namespace: order
    for _, _, _, namespaces in GROUPS
    for order, namespace in enumerate(namespaces)
}
SKY_CHAPTER_ID = "271C0B00CAFE2001"
MEK_CHAPTER_ID = "1A2E2B8D9E0A2001"
CREATE_CHAPTER_ID = "03C0EA7ECAFE3001"
IMMERSIVE_CHAPTER_ID = "04E1E57ECAFE4001"
AE2_CHAPTER_ID = "005A2ECAFEAE2001"
APPMEK_CHAPTER_ID = "005A2ECAFEAE2002"
ARS_CHAPTER_ID = "0005A2ECAFEA5001"
OCCULT_CHAPTER_ID = "005A2ECAFE0CC001"
EVIL_CHAPTER_ID = "0005A2ECAFE0E001"
FNA_CHAPTER_ID = "0005A2ECAFE0F001"
IRONS_CHAPTER_ID = "0005A2ECAFE10001"
FARMER_CHAPTER_ID = "0005A2ECAFE10002"
MYSTICAL_CHAPTER_ID = "0005A2ECAFE10003"
POKEMON_CHAPTER_ID = "0005A2ECAFE20001"
TRAINERS_CHAPTER_ID = "0005A2ECAFE20002"
ENDGAME_CHAPTER_ID = "0005A2ECAFE20003"
APOTHEOSIS_CHAPTER_ID = "0005A2ECAFE30001"
CATACLYSM_CHAPTER_ID = "0005A2ECAFE30002"
DRACONIC_CHAPTER_ID = "0005A2ECAFE30003"
VAMPIRISM_CHAPTER_ID = "0005A2ECAFE30004"
COBBLEMON_ADVANCED_CHAPTER_ID = "0005A2ECAFE30005"
ACHIEVEMENTS_CHAPTER_ID = "0005A2ECAFE30006"
ARTIFACTS_CHAPTER_ID = "0005A2ECAFE30007"
RELICS_CHAPTER_ID = "0005A2ECAFE30008"
EPICFIGHT_CHAPTER_ID = "0005A2ECAFE30009"
MINECOLONIES_CHAPTER_ID = "0005A2ECAFE40001"
ORITECH_CHAPTER_ID = "0005A2ECAFE40002"
SILENTGEAR_CHAPTER_ID = "0005A2ECAFE40003"
COBBLEPLUS_CHAPTER_ID = "0005A2ECAFE40004"
WORLDBOSSES_CHAPTER_ID = "0005A2ECAFE40005"
CREATEPLUS_CHAPTER_ID = "0005A2ECAFE50001"
TRAVELER_CHAPTER_ID = "0005A2ECAFE50002"
BUILDER_CHAPTER_ID = "0005A2ECAFE50003"
SWEM_CHAPTER_ID = "0005A2ECAFE50004"
ORIGINS_CHAPTER_ID = "0005A2ECAFE50005"
STARLIGHT_CHAPTER_ID = "0005A2ECAFE60001"
WILDLIFE_CHAPTER_ID = "0005A2ECAFE60002"
ARSPLUS_CHAPTER_ID = "0005A2ECAFE60003"
MEKPLUS_CHAPTER_ID = "0005A2ECAFE60004"
COMMUNITY_CHAPTER_ID = "0005A2ECAFE60005"
SERVICES_CHAPTER_ID = "0005A2ECAFE70001"
ATLAS_CHAPTER_ID = "0005A2ECAFE70002"
THREATS_CHAPTER_ID = "0005A2ECAFE70003"
INTEGRATION_CHAPTER_ID = "0005A2ECAFE70004"
FINALE_CHAPTER_ID = "0005A2ECAFE70005"
PACKAGE_VERSION = "1.15.6"


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
ARTIFACTS = next_chapters.build_chapter("artifacts", Quest)
RELICS = next_chapters.build_chapter("relics", Quest)
EPICFIGHT = next_chapters.build_chapter("epicfight", Quest)
MINECOLONIES = next_chapters.build_chapter("minecolonies", Quest)
ORITECH = next_chapters.build_chapter("oritech", Quest)
SILENTGEAR = next_chapters.build_chapter("silentgear", Quest)
COBBLEPLUS = next_chapters.build_chapter("cobbleplus", Quest)
WORLDBOSSES = next_chapters.build_chapter("worldbosses", Quest)
CREATEPLUS = next_chapters.build_chapter("createplus", Quest)
TRAVELER = next_chapters.build_chapter("traveler", Quest)
BUILDER = next_chapters.build_chapter("builder", Quest)
SWEM = next_chapters.build_chapter("swem", Quest)
ORIGINS = next_chapters.build_chapter("origins", Quest)
STARLIGHT = next_chapters.build_chapter("starlight", Quest)
WILDLIFE = next_chapters.build_chapter("wildlife", Quest)
ARSPLUS = next_chapters.build_chapter("arsplus", Quest)
MEKPLUS = next_chapters.build_chapter("mekplus", Quest)
COMMUNITY = next_chapters.build_chapter("community", Quest)
SERVICES = next_chapters.build_chapter("services", Quest)
ATLAS = next_chapters.build_chapter("atlas", Quest)
THREATS = next_chapters.build_chapter("threats", Quest)
INTEGRATION = next_chapters.build_chapter("integration", Quest)
FINALE = next_chapters.build_chapter("finale", Quest)


QUEST_LISTS = {
    "skyblock": "SKY", "create": "CREATE", "immersive": "IMMERSIVE", "mekanism": "MEK",
    "ae2": "AE2", "appmek": "APPMEK", "ars": "ARS", "occult": "OCCULT", "evil": "EVIL",
    "fna": "FNA", "irons": "IRONS", "farmer": "FARMER", "mystical": "MYSTICAL",
    "pokemon": "POKEMON", "trainers": "TRAINERS", "endgame": "ENDGAME",
    "apotheosis": "APOTHEOSIS", "cataclysm": "CATACLYSM", "draconic": "DRACONIC",
    "vampirism": "VAMPIRISM", "cobblemon_advanced": "COBBLEMON_ADVANCED",
    "achievements": "ACHIEVEMENTS", "artifacts": "ARTIFACTS", "relics": "RELICS",
    "epicfight": "EPICFIGHT", "minecolonies": "MINECOLONIES", "oritech": "ORITECH",
    "silentgear": "SILENTGEAR", "cobbleplus": "COBBLEPLUS", "worldbosses": "WORLDBOSSES",
    "createplus": "CREATEPLUS", "traveler": "TRAVELER", "builder": "BUILDER", "swem": "SWEM",
    "origins": "ORIGINS", "starlight": "STARLIGHT", "wildlife": "WILDLIFE",
    "arsplus": "ARSPLUS", "mekplus": "MEKPLUS", "community": "COMMUNITY",
    "services": "SERVICES", "atlas": "ATLAS", "threats": "THREATS",
    "integration": "INTEGRATION", "finale": "FINALE",
}

MOD_NAMES = {
    "skyblock": "Ex Deorum и Ex Machinis", "create": "Create", "immersive": "Immersive Engineering",
    "mekanism": "Mekanism", "ae2": "Applied Energistics 2", "appmek": "Applied Mekanistics",
    "ars": "Ars Nouveau", "occult": "Occultism", "evil": "EvilCraft",
    "fna": "Forbidden & Arcanus", "irons": "Iron's Spells", "farmer": "Farmer's Delight",
    "mystical": "Mystical Agriculture", "pokemon": "Cobblemon", "trainers": "системе тренеров и данжей",
    "endgame": "эндгейме PokeTech Arcana", "apotheosis": "Apotheosis", "cataclysm": "Cataclysm",
    "draconic": "Draconic Evolution", "vampirism": "Vampirism", "cobblemon_advanced": "Cobblemon",
    "achievements": "достижениях сервера", "artifacts": "Artifacts", "relics": "Relics",
    "epicfight": "Epic Fight", "minecolonies": "MineColonies", "oritech": "Oritech",
    "silentgear": "Silent Gear", "cobbleplus": "расширениях Cobblemon", "worldbosses": "мирах и боссах",
    "createplus": "Create", "traveler": "путешествиях", "builder": "строительстве", "swem": "SWEM",
    "origins": "NeoOrigins", "starlight": "Eternal Starlight", "wildlife": "исследовании природы",
    "arsplus": "Ars Nouveau", "mekplus": "Mekanism", "community": "серверном сообществе",
    "services": "сервисах Cobblemon", "atlas": "исследовании структур и миров",
    "threats": "охоте на опасных существ", "integration": "интеграциях модов", "finale": "финале сборки",
}

CHAPTER_FOCUS = {
    "skyblock": "возобновляемую добычу ресурсов и безопасное расширение острова",
    "create": "кинетические линии, обработку деталей и автоматическую сборку покеболов",
    "immersive": "тяжёлые многоблочные машины, электросеть и промышленную переработку",
    "mekanism": "энергосеть, фабрики, химическую переработку и реакторы",
    "ae2": "ME-сеть, каналы, цифровое хранение и автокрафт",
    "appmek": "хранение газов и химикатов внутри ME-сети",
    "ars": "создание заклинаний, управление Source и магическую автоматизацию",
    "occult": "ритуалы, духов, удалённое хранение и добычу ресурсов",
    "evil": "кровь, тёмную энергию и автоматизацию EvilCraft",
    "fna": "Aureal, Hephaestus Forge и улучшение магических реликвий",
    "irons": "заклинания, руны, чернила и экипировку мага",
    "farmer": "устойчивое хозяйство, кухню и снабжение острова едой",
    "mystical": "выращивание ресурсов и автоматическую переработку эссенций",
    "pokemon": "поимку, лечение, развитие и подготовку команды покемонов",
    "trainers": "подготовку к боям с тренерами, башням, рейдам и данжам",
    "endgame": "объединение технологических, магических и покемонских систем",
    "apotheosis": "самоцветы, перековку, зачарования и развитие экипировки",
    "cataclysm": "разведку цитаделей и подготовку к сложным боссам",
    "draconic": "энергохранилища, реактор и высокоуровневую экипировку",
    "vampirism": "развитие вампира или охотника и связанные ритуалы",
    "cobblemon_advanced": "коллекцию, разведение, редкие формы и легендарных покемонов",
    "achievements": "долгосрочные цели и подтверждение общего развития игрока",
    "artifacts": "поиск полезных аксессуаров и подбор снаряжения под стиль игры",
    "relics": "развитие и настройку реликвий без выдачи готовых редких предметов",
    "epicfight": "боевые стойки, навыки и безопасную подготовку к сражениям",
    "minecolonies": "рост колонии, снабжение жителей и строительную логистику",
    "oritech": "энергетику, переработку и орбитальную промышленность",
    "silentgear": "чертежи, материалы и сборку настраиваемого снаряжения",
    "cobbleplus": "питомники, рейды и дополнительные системы Cobblemon",
    "worldbosses": "экспедиционное снабжение и последовательное прохождение боссов",
    "createplus": "масштабирование фабрик Create и транспортировку ресурсов",
    "traveler": "безопасные маршруты, навигацию и полевое снабжение",
    "builder": "планирование построек, палитры блоков и удобство строительства",
    "swem": "уход за лошадьми, конюшню, тренировки и разведение",
    "origins": "освоение сильных и слабых сторон выбранного происхождения",
    "starlight": "исследование измерения, его материалов и боссов",
    "wildlife": "наблюдение за существами и безопасное освоение биомов",
    "arsplus": "продвинутые школы заклинаний и магические производственные линии",
    "mekplus": "полный энергетический комплекс Mekanism и его безопасность",
    "community": "общие постройки, роли игроков и серверные проекты",
    "services": "Pokédex, хранение команд, обмен и полевые инструменты тренера",
    "atlas": "поиск структур, картографию и подготовку экспедиций",
    "threats": "разведку опасностей, безопасную дистанцию и трофеи существ",
    "integration": "связь машин, магии и хранения между разными модами",
    "finale": "итоговый проект сервера и применение всех освоенных систем",
}

DEFAULT_REWARDS = (
    ("minecraft:torch", 12), ("minecraft:bread", 6), ("minecraft:oak_planks", 12),
    ("minecraft:iron_ingot", 3), ("minecraft:redstone", 6), ("minecraft:experience_bottle", 4),
)

REWARD_POOLS: dict[str, tuple[tuple[str, int], ...]] = {}


def reward_pool(namespaces: str, *entries: tuple[str, int]) -> None:
    for namespace in namespaces.split():
        REWARD_POOLS[namespace] = entries


reward_pool("skyblock", ("minecraft:dirt", 8), ("minecraft:cobblestone", 16), ("minecraft:oak_planks", 16), ("minecraft:torch", 12), ("minecraft:bone_meal", 6), ("minecraft:bucket", 1))
reward_pool("create createplus", ("create:andesite_alloy", 4), ("create:shaft", 8), ("create:cogwheel", 6), ("create:belt_connector", 4), ("minecraft:copper_ingot", 4), ("minecraft:redstone", 6))
reward_pool("immersive", ("minecraft:iron_ingot", 4), ("minecraft:copper_ingot", 4), ("minecraft:coal", 8), ("minecraft:redstone", 6), ("minecraft:oak_log", 8), ("minecraft:scaffolding", 8))
reward_pool("mekanism mekplus", ("mekanism:ingot_osmium", 4), ("mekanism:alloy_infused", 2), ("mekanism:basic_control_circuit", 2), ("minecraft:redstone", 8), ("minecraft:iron_ingot", 4), ("minecraft:coal", 8))
reward_pool("ae2", ("ae2:certus_quartz_crystal", 4), ("ae2:fluix_crystal", 2), ("ae2:silicon", 4), ("ae2:quartz_fiber", 4), ("minecraft:redstone", 6), ("minecraft:iron_ingot", 3))
reward_pool("appmek integration", ("ae2:certus_quartz_crystal", 4), ("mekanism:ingot_osmium", 3), ("ae2:fluix_crystal", 2), ("minecraft:redstone", 6), ("minecraft:iron_ingot", 3), ("minecraft:copper_ingot", 3))
reward_pool("oritech", ("minecraft:copper_ingot", 5), ("minecraft:iron_ingot", 4), ("minecraft:redstone", 6), ("minecraft:coal", 8), ("minecraft:glass", 6), ("minecraft:quartz", 4))
reward_pool("silentgear", ("minecraft:iron_ingot", 4), ("minecraft:leather", 4), ("minecraft:string", 8), ("minecraft:flint", 6), ("minecraft:paper", 8), ("minecraft:lapis_lazuli", 6))
reward_pool("ars arsplus", ("ars_nouveau:source_gem", 4), ("ars_nouveau:magebloom_fiber", 4), ("ars_nouveau:blank_parchment", 2), ("minecraft:amethyst_shard", 4), ("minecraft:lapis_lazuli", 6), ("minecraft:paper", 8))
reward_pool("occult", ("occultism:otherworld_wood", 4), ("occultism:demonic_meat", 2), ("occultism:chalk_white", 1), ("minecraft:candle", 4), ("minecraft:string", 8), ("minecraft:quartz", 4))
reward_pool("evil", ("evilcraft:dark_gem", 2), ("evilcraft:condensed_blood", 2), ("minecraft:glass_bottle", 6), ("minecraft:rotten_flesh", 8), ("minecraft:redstone", 5), ("minecraft:iron_ingot", 3))
reward_pool("fna", ("forbidden_arcanus:arcane_crystal_dust", 4), ("forbidden_arcanus:arcane_crystal", 2), ("minecraft:amethyst_shard", 4), ("minecraft:quartz", 4), ("minecraft:iron_ingot", 3), ("minecraft:experience_bottle", 4))
reward_pool("irons", ("irons_spellbooks:magic_cloth", 3), ("irons_spellbooks:fire_rune", 1), ("minecraft:paper", 8), ("minecraft:lapis_lazuli", 6), ("minecraft:amethyst_shard", 4), ("minecraft:experience_bottle", 4))
reward_pool("vampirism", ("vampirism:garlic", 4), ("vampirism:blood_bottle", 2), ("vampirism:injection_empty", 2), ("minecraft:glass_bottle", 6), ("minecraft:iron_ingot", 3), ("minecraft:bread", 6))
reward_pool("farmer", ("minecraft:bone_meal", 8), ("minecraft:wheat", 8), ("minecraft:carrot", 8), ("minecraft:hay_block", 2), ("minecraft:dirt", 8), ("minecraft:oak_fence", 8), ("minecraft:lead", 1))
reward_pool("mystical", ("mysticalagriculture:inferium_essence", 8), ("mysticalagriculture:prosperity_shard", 4), ("minecraft:bone_meal", 8), ("minecraft:dirt", 8), ("minecraft:redstone", 5), ("minecraft:iron_ingot", 3))
reward_pool("pokemon cobblemon_advanced cobbleplus trainers services", ("cobblemon:poke_ball", 4), ("cobblemon:potion", 2), ("cobblemon:exp_candy_xs", 4), ("cobblemon:red_apricorn", 4), ("cobblemon:blue_apricorn", 4), ("minecraft:cooked_beef", 6))
reward_pool("minecolonies", ("minecraft:oak_log", 12), ("minecraft:stone_bricks", 16), ("minecraft:bread", 8), ("minecraft:iron_ingot", 4), ("minecraft:glass", 8), ("minecraft:torch", 12))
reward_pool("swem", ("minecraft:apple", 8), ("minecraft:hay_block", 3), ("minecraft:lead", 1), ("minecraft:wheat", 8), ("minecraft:carrot", 8), ("minecraft:oak_fence", 8))
reward_pool("traveler atlas starlight wildlife", ("minecraft:torch", 16), ("minecraft:cooked_beef", 8), ("minecraft:paper", 8), ("minecraft:oak_planks", 12), ("minecraft:arrow", 16), ("minecraft:golden_carrot", 4))
reward_pool("builder community", ("minecraft:stone_bricks", 16), ("minecraft:oak_planks", 16), ("minecraft:glass", 8), ("minecraft:scaffolding", 8), ("minecraft:lantern", 4), ("minecraft:white_banner", 2))
reward_pool("epicfight cataclysm worldbosses threats", ("minecraft:arrow", 16), ("minecraft:cooked_beef", 8), ("minecraft:golden_carrot", 4), ("minecraft:iron_ingot", 4), ("minecraft:obsidian", 3), ("minecraft:experience_bottle", 4))
reward_pool("apotheosis artifacts relics", ("minecraft:experience_bottle", 5), ("minecraft:lapis_lazuli", 8), ("minecraft:bread", 6), ("minecraft:torch", 12), ("minecraft:iron_ingot", 3), ("minecraft:bookshelf", 2))
reward_pool("draconic endgame finale", ("minecraft:redstone", 8), ("minecraft:gold_ingot", 3), ("minecraft:diamond", 1), ("minecraft:experience_bottle", 6), ("minecraft:golden_carrot", 5), ("minecraft:obsidian", 4))
reward_pool("origins", ("minecraft:bread", 6), ("minecraft:leather", 4), ("minecraft:feather", 8), ("minecraft:arrow", 12), ("minecraft:golden_carrot", 4), ("minecraft:ender_pearl", 1))
reward_pool("achievements", ("minecraft:firework_rocket", 8), ("minecraft:experience_bottle", 6), ("minecraft:golden_carrot", 6), ("minecraft:emerald", 2), ("minecraft:diamond", 1), ("minecraft:torch", 16))

RARE_REWARD_PARTS = (
    "nether_star", "dragon_egg", "chaos", "antimatter", "awakened", "creative", "master_ball",
    "eternal_stella", "insanium", "supremium", "legendary", "mythic", "totem_of_undying",
    "elytra", "netherite", "beacon", "deorum_ingot", "stella_arcanum", "mega_stone",
    "red_orb", "blue_orb", "griseous_orb", "adamant_orb", "azure_flute",
)

ALL_TASK_ITEMS = {
    item_id
    for list_name in QUEST_LISTS.values()
    for quest in globals()[list_name]
    for item_id, _ in quest.tasks
}


def pretty_item(item_id: str) -> str:
    namespace, name = item_id.split(":", 1)
    label = name.replace("_", " ").replace("/", " ").strip().title()
    mod = namespace.replace("_", " ").title()
    return f"{label} ({mod})"


def obtain_advice(item_id: str) -> str:
    namespace, name = item_id.split(":", 1)
    if name.endswith("_spawn_egg"):
        return "Используй яйца призыва внутри огороженного и освещённого загона, чтобы животные не упали с острова."
    if namespace in {"artifacts", "relics"}:
        return "Проверь предмет в JEI: такие находки обычно добываются в сундуках структур, с мимиков или за исследование, а не обычным крафтом."
    if namespace in {"cataclysm", "mowziesmobs", "bosses_of_mass_destruction", "block_factorys_bosses", "born_in_chaos_v1", "mutantmonsters"}:
        return "Сначала нажми R в JEI. Если рецепта нет, подготовь еду, точку возврата и свободный инвентарь: предмет является трофеем существа или структуры."
    if any(part in name for part in ("ingot", "dust", "nugget", "shard", "essence", "crystal", "gem", "chunk", "plate", "wire")):
        return "Нажми R по предмету в JEI и выбери доступную цепочку переработки; начни с сырья и проверь требуемую машину, температуру или реагент."
    if any(part in name for part in ("seed", "sapling", "crop", "food", "bread", "meat", "apple", "carrot", "wheat", "apricorn")):
        return "Получи первый экземпляр через крафт, урожай или добычу, затем организуй возобновляемый запас до расходования предмета."
    if any(part in name for part in ("sword", "axe", "pickaxe", "shovel", "hoe", "helmet", "chestplate", "leggings", "boots", "shield", "bow", "staff", "wand")):
        return "Открой рецепт в JEI, подготовь материалы нужного уровня и изготовь предмет; перед боем проверь прочность, зачарования и подходящую стойку."
    if any(part in name for part in ("machine", "factory", "furnace", "generator", "reactor", "controller", "press", "crusher", "sieve", "hammer", "storage", "tank", "cell", "cable", "pipe", "gearbox", "motor")):
        return "Собери компоненты по рецепту JEI снизу вверх, установи устройство в безопасной тестовой линии и только затем подключай питание, жидкости или сеть."
    return "Нажми R по значку цели в JEI, чтобы увидеть рецепт или способ получения; если рецепта нет, проверь книгу мода, структуры и таблицы добычи."


def educational_description(namespace: str, quest: Quest) -> str:
    goals = ", ".join(f"{count}× {pretty_item(item_id)}" for item_id, count in quest.tasks)
    first_item = quest.tasks[0][0]
    return (
        f"Для задания «{quest.title}» подготовь {goals}. {obtain_advice(first_item)} "
        f"В {MOD_NAMES[namespace]} этот шаг развивает {CHAPTER_FOCUS[namespace]}. "
        "После получения нажми U в JEI, посмотри применения предмета и испытай его в небольшой рабочей сборке перед масштабированием."
    )


ANIMAL_EGG_REWARDS = (
    (("коровник", "cow barn"), ("minecraft:cow_spawn_egg", 2)),
    (("курятник", "куриный загон", "chicken coop"), ("minecraft:chicken_spawn_egg", 2)),
    (("овчарня", "пастух", "sheep pen"), ("minecraft:sheep_spawn_egg", 2)),
    (("свинарник", "pig pen"), ("minecraft:pig_spawn_egg", 2)),
)


def balanced_reward(namespace: str, quest: Quest) -> tuple[str, int]:
    title = quest.title.lower()
    if namespace in {"farmer", "minecolonies"}:
        for terms, reward in ANIMAL_EGG_REWARDS:
            if any(term in title for term in terms):
                return reward
    if namespace == "skyblock":
        special = {
            "start": ("minecraft:dirt", 8), "tree": ("minecraft:dirt", 4),
            "sapling": ("minecraft:bone_meal", 6), "barrel": ("minecraft:oak_leaves", 12),
            "compost": ("minecraft:cobblestone", 16), "water": ("minecraft:bucket", 1),
        }
        if quest.key in special:
            return special[quest.key]

    task_items = {item_id for item_id, _ in quest.tasks}
    candidates = []
    for item_id, count in REWARD_POOLS.get(namespace, DEFAULT_REWARDS):
        if item_id in task_items or any(part in item_id for part in RARE_REWARD_PARTS):
            continue
        if not item_id.startswith("minecraft:") and item_id not in ALL_TASK_ITEMS:
            continue
        candidates.append((item_id, count))
    if not candidates:
        candidates = [entry for entry in DEFAULT_REWARDS if entry[0] not in task_items]
    seed = int(hashlib.sha256(f"reward-v3:{namespace}:{quest.key}".encode()).hexdigest()[:8], 16)
    return candidates[seed % len(candidates)]


def refine_quest(namespace: str, quest: Quest) -> Quest:
    generic = quest.desc.startswith("Урок «")
    if generic:
        description = educational_description(namespace, quest)
    else:
        goals = ", ".join(f"{count}× {pretty_item(item_id)}" for item_id, count in quest.tasks)
        description = (
            f"{quest.desc.rstrip()} Цель этапа: {goals}. {obtain_advice(quest.tasks[0][0])} "
            f"Этот шаг помогает освоить {CHAPTER_FOCUS[namespace]}; после получения нажми U в JEI и проверь дальнейшие применения предмета."
        )
    reward = balanced_reward(namespace, quest)
    stage_root = quest.key.endswith("_01") or quest.key in MILESTONES_PREVIEW.get(namespace, ())
    xp = 2 if stage_root else 1
    return replace(quest, desc=description, reward=reward, xp=xp)


MILESTONES_PREVIEW = {
    "skyblock": ("start", "sieve", "cobble", "ores", "generator", "autohammer", "core"),
    "mekanism": ("osmium", "enrichment", "cables", "basicfactory", "purification", "wind", "fusion"),
    "create": ("rotation", "casing", "belt", "red_sheet", "deployer", "special_series", "auto_factory"),
    "immersive": ("manual", "cokeoven", "blastfurnace", "lv_network", "current_transformer", "metal_press", "biodiesel", "arc_furnace", "industrial_complex"),
}

for _namespace, _list_name in QUEST_LISTS.items():
    globals()[_list_name] = [refine_quest(_namespace, quest) for quest in globals()[_list_name]]

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
    "artifacts": {f"s{i:02d}_01": i for i in range(1, 9)},
    "relics": {f"s{i:02d}_01": i for i in range(1, 9)},
    "epicfight": {f"s{i:02d}_01": i for i in range(1, 10)},
    "minecolonies": {f"s{i:02d}_01": i for i in range(1, 12)},
    "oritech": {f"s{i:02d}_01": i for i in range(1, 10)},
    "silentgear": {f"s{i:02d}_01": i for i in range(1, 10)},
    "cobbleplus": {f"s{i:02d}_01": i for i in range(1, 13)},
    "worldbosses": {f"s{i:02d}_01": i for i in range(1, 12)},
    "createplus": {f"s{i:02d}_01": i for i in range(1, 11)},
    "traveler": {f"s{i:02d}_01": i for i in range(1, 10)},
    "builder": {f"s{i:02d}_01": i for i in range(1, 10)},
    "swem": {f"s{i:02d}_01": i for i in range(1, 11)},
    "origins": {f"s{i:02d}_01": i for i in range(1, 9)},
    "starlight": {f"s{i:02d}_01": i for i in range(1, 10)},
    "wildlife": {f"s{i:02d}_01": i for i in range(1, 9)},
    "arsplus": {f"s{i:02d}_01": i for i in range(1, 10)},
    "mekplus": {f"s{i:02d}_01": i for i in range(1, 11)},
    "community": {f"s{i:02d}_01": i for i in range(1, 9)},
    "services": {f"s{i:02d}_01": i for i in range(1, 10)},
    "atlas": {f"s{i:02d}_01": i for i in range(1, 10)},
    "threats": {f"s{i:02d}_01": i for i in range(1, 10)},
    "integration": {f"s{i:02d}_01": i for i in range(1, 11)},
    "finale": {f"s{i:02d}_01": i for i in range(1, 13)},
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
        f"\tgroup: {q(CHAPTER_GROUP_FOR[namespace])}",
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
        f"\torder_index: {CHAPTER_ORDER_IN_GROUP[namespace]}",
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
            f"\t\t{q('&8' + quest.desc)}",
            "\t\t\"\"",
            f"\t\t{q('&9▶ Цель: &0' + ', '.join(str(c) + '× ' + pretty_item(i) for i, c in quest.tasks))}",
            f"\t\t{q('&2◆ Награда: &0' + str(quest.reward[1]) + '× ' + pretty_item(quest.reward[0]) + ' и ' + str(quest.xp) + ' ур. опыта')}",
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

    config = next_chapters.CHAPTERS[namespace]
    stage_count = len(config["stages"])
    stage_quests: list[list[Quest]] = [[] for _ in range(stage_count)]
    for quest in quests:
        match = re.fullmatch(r"s(\d{2})_\d{2}", quest.key)
        if not match:
            raise ValueError(f"{namespace}: quest {quest.key!r} has no stage number")
        stage_index = int(match.group(1)) - 1
        if not 0 <= stage_index < stage_count:
            raise ValueError(f"{namespace}: invalid stage in quest {quest.key!r}")
        stage_quests[stage_index].append(quest)
    if any(not cluster for cluster in stage_quests):
        raise ValueError(f"{namespace}: an empty stage cannot be decorated")

    # Draw the coloured routes between the same stage entry/exit nodes used by
    # the quest dependencies.  A stage starts at _01 and enters the next stage
    # from its last quest, so the route reads left-to-right through the book.
    roots = [next(quest for quest in cluster if quest.key.endswith("_01")) for cluster in stage_quests]
    mapped_roots = [point(quest.x, quest.y) for quest in roots]
    stage_exits = [cluster[-1] for cluster in stage_quests]
    stage_parents = config.get("stage_parents")
    for index in range(stage_count):
        parents = stage_parents[index] if stage_parents is not None else ([] if index == 0 else [index - 1])
        for parent in parents:
            x1, y1 = point(stage_exits[parent].x, stage_exits[parent].y)
            x2, y2 = mapped_roots[index]
            color = palette[index % len(palette)]
            draw.line((x1, y1, x2, y2), fill=(*color, 72), width=14)

    # Keep the background deliberately clean: no decorative circles are drawn
    # behind icons.  A chapter legend and the actual dependency paths provide
    # the grouping without introducing a second, scale-sensitive coordinate
    # system.
    strip_top, strip_bottom = 150, 222
    cell = (image_w - 128) / stage_count
    for index, (cluster, stage) in enumerate(zip(stage_quests, config["stages"])):
        color = palette[index % len(palette)]
        left = 64 + index * cell
        right = left + cell
        draw.rectangle((left, strip_top, right, strip_bottom),
                       fill=(248, 244, 236, 215), outline=(103, 82, 55, 105), width=2)
        draw.rectangle((left, strip_top, left + 8, strip_bottom), fill=(*color, 190))
        label = stage[1]
        bbox = draw.textbbox((0, 0), label, font=font(15, True))
        draw.text((left + 18, strip_top + 13), f"{index + 1:02d} · {label}",
                  font=font(15, True), fill=(*color, 205))
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
text_color: #18130E
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
quest_view_title: #18130E
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
    validate(ARTIFACTS, "artifacts", 72)
    validate(RELICS, "relics", 80)
    validate(EPICFIGHT, "epicfight", 90)
    validate(MINECOLONIES, "minecolonies", 110)
    validate(ORITECH, "oritech", 90)
    validate(SILENTGEAR, "silentgear", 90)
    validate(COBBLEPLUS, "cobbleplus", 120)
    validate(WORLDBOSSES, "worldbosses", 110)
    validate(CREATEPLUS, "createplus", 100)
    validate(TRAVELER, "traveler", 90)
    validate(BUILDER, "builder", 90)
    validate(SWEM, "swem", 100)
    validate(ORIGINS, "origins", 80)
    validate(STARLIGHT, "starlight", 90)
    validate(WILDLIFE, "wildlife", 80)
    validate(ARSPLUS, "arsplus", 90)
    validate(MEKPLUS, "mekplus", 100)
    validate(COMMUNITY, "community", 80)
    validate(SERVICES, "services", 90)
    validate(ATLAS, "atlas", 90)
    validate(THREATS, "threats", 90)
    validate(INTEGRATION, "integration", 100)
    validate(FINALE, "finale", 120)
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
    group_rows = [
        f'\t\t{{ icon: {{ id: {q(icon)} }}, id: {q(group_id)}, title: {q(title)} }}'
        for group_id, title, icon, _ in GROUPS
    ]
    groups = "{\n\tchapter_groups: [\n" + ",\n".join(group_rows) + "\n\t]\n}\n"
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
    # FTB Library treats ampersands as formatting markers. A literal ampersand
    # before whitespace must be escaped or the chapter list shows an error.
    fna_title = next_chapters.CHAPTERS["fna"]["title"].replace(" & ", r" \& ")
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
    artifacts_title = next_chapters.CHAPTERS["artifacts"]["title"]
    relics_title = next_chapters.CHAPTERS["relics"]["title"]
    epicfight_title = next_chapters.CHAPTERS["epicfight"]["title"]
    minecolonies_title = next_chapters.CHAPTERS["minecolonies"]["title"]
    oritech_title = next_chapters.CHAPTERS["oritech"]["title"]
    silentgear_title = next_chapters.CHAPTERS["silentgear"]["title"]
    cobbleplus_title = next_chapters.CHAPTERS["cobbleplus"]["title"]
    worldbosses_title = next_chapters.CHAPTERS["worldbosses"]["title"]
    createplus_title = next_chapters.CHAPTERS["createplus"]["title"]
    traveler_title = next_chapters.CHAPTERS["traveler"]["title"]
    builder_title = next_chapters.CHAPTERS["builder"]["title"]
    swem_title = next_chapters.CHAPTERS["swem"]["title"]
    origins_title = next_chapters.CHAPTERS["origins"]["title"]
    starlight_title = next_chapters.CHAPTERS["starlight"]["title"]
    wildlife_title = next_chapters.CHAPTERS["wildlife"]["title"]
    arsplus_title = next_chapters.CHAPTERS["arsplus"]["title"]
    mekplus_title = next_chapters.CHAPTERS["mekplus"]["title"]
    community_title = next_chapters.CHAPTERS["community"]["title"]
    services_title = next_chapters.CHAPTERS["services"]["title"]
    atlas_title = next_chapters.CHAPTERS["atlas"]["title"]
    threats_title = next_chapters.CHAPTERS["threats"]["title"]
    integration_title = next_chapters.CHAPTERS["integration"]["title"]
    finale_title = next_chapters.CHAPTERS["finale"]["title"]
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
    (QUESTS / "chapters" / "artifacts.snbt").write_text(make_chapter("artifacts", ARTIFACTS_CHAPTER_ID, artifacts_title, 22, "artifacts:crystal_heart", ARTIFACTS, "poketech:textures/quests/backgrounds/artifacts_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "relics.snbt").write_text(make_chapter("relics", RELICS_CHAPTER_ID, relics_title, 23, "relics:chorus_staff", RELICS, "poketech:textures/quests/backgrounds/relics_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "epicfight.snbt").write_text(make_chapter("epicfight", EPICFIGHT_CHAPTER_ID, epicfight_title, 24, "epicfight:skillbook", EPICFIGHT, "poketech:textures/quests/backgrounds/epicfight_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "minecolonies.snbt").write_text(make_chapter("minecolonies", MINECOLONIES_CHAPTER_ID, minecolonies_title, 25, "minecolonies:blockhuttownhall", MINECOLONIES, "poketech:textures/quests/backgrounds/minecolonies_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "oritech.snbt").write_text(make_chapter("oritech", ORITECH_CHAPTER_ID, oritech_title, 26, "oritech:atomic_forge_block", ORITECH, "poketech:textures/quests/backgrounds/oritech_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "silentgear.snbt").write_text(make_chapter("silentgear", SILENTGEAR_CHAPTER_ID, silentgear_title, 27, "silentgear:blueprint_book", SILENTGEAR, "poketech:textures/quests/backgrounds/silentgear_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "cobbleplus.snbt").write_text(make_chapter("cobbleplus", COBBLEPLUS_CHAPTER_ID, cobbleplus_title, 28, "cobblemonraiddens:raid_pouch", COBBLEPLUS, "poketech:textures/quests/backgrounds/cobbleplus_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "worldbosses.snbt").write_text(make_chapter("worldbosses", WORLDBOSSES_CHAPTER_ID, worldbosses_title, 29, "bosses_of_mass_destruction:soul_star", WORLDBOSSES, "poketech:textures/quests/backgrounds/worldbosses_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "createplus.snbt").write_text(make_chapter("createplus", CREATEPLUS_CHAPTER_ID, createplus_title, 30, "minecraft:rail", CREATEPLUS, "poketech:textures/quests/backgrounds/createplus_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "traveler.snbt").write_text(make_chapter("traveler", TRAVELER_CHAPTER_ID, traveler_title, 31, "minecraft:compass", TRAVELER, "poketech:textures/quests/backgrounds/traveler_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "builder.snbt").write_text(make_chapter("builder", BUILDER_CHAPTER_ID, builder_title, 32, "minecraft:bricks", BUILDER, "poketech:textures/quests/backgrounds/builder_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "swem.snbt").write_text(make_chapter("swem", SWEM_CHAPTER_ID, swem_title, 33, "minecraft:saddle", SWEM, "poketech:textures/quests/backgrounds/swem_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "origins.snbt").write_text(make_chapter("origins", ORIGINS_CHAPTER_ID, origins_title, 34, "minecraft:nether_star", ORIGINS, "poketech:textures/quests/backgrounds/origins_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "starlight.snbt").write_text(make_chapter("starlight", STARLIGHT_CHAPTER_ID, starlight_title, 35, "eternal_starlight:aethersent_ingot", STARLIGHT, "poketech:textures/quests/backgrounds/starlight_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "wildlife.snbt").write_text(make_chapter("wildlife", WILDLIFE_CHAPTER_ID, wildlife_title, 36, "minecraft:spyglass", WILDLIFE, "poketech:textures/quests/backgrounds/wildlife_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "arsplus.snbt").write_text(make_chapter("arsplus", ARSPLUS_CHAPTER_ID, arsplus_title, 37, "ars_nouveau:archmage_spell_book", ARSPLUS, "poketech:textures/quests/backgrounds/arsplus_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "mekplus.snbt").write_text(make_chapter("mekplus", MEKPLUS_CHAPTER_ID, mekplus_title, 38, "mekanismgenerators:wind_generator", MEKPLUS, "poketech:textures/quests/backgrounds/mekplus_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "community.snbt").write_text(make_chapter("community", COMMUNITY_CHAPTER_ID, community_title, 39, "minecraft:bell", COMMUNITY, "poketech:textures/quests/backgrounds/community_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "services.snbt").write_text(make_chapter("services", SERVICES_CHAPTER_ID, services_title, 40, "cobbledex:cobbledex_item", SERVICES, "poketech:textures/quests/backgrounds/services_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "atlas.snbt").write_text(make_chapter("atlas", ATLAS_CHAPTER_ID, atlas_title, 41, "minecraft:filled_map", ATLAS, "poketech:textures/quests/backgrounds/atlas_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "threats.snbt").write_text(make_chapter("threats", THREATS_CHAPTER_ID, threats_title, 42, "mutantmonsters:creeper_shard", THREATS, "poketech:textures/quests/backgrounds/threats_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "integration.snbt").write_text(make_chapter("integration", INTEGRATION_CHAPTER_ID, integration_title, 43, "ae2:controller", INTEGRATION, "poketech:textures/quests/backgrounds/integration_book.png"), encoding="utf-8")
    (QUESTS / "chapters" / "finale.snbt").write_text(make_chapter("finale", FINALE_CHAPTER_ID, finale_title, 44, "minecraft:nether_star", FINALE, "poketech:textures/quests/backgrounds/finale_book.png"), encoding="utf-8")

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
    artifacts_lang = language_for("artifacts", ARTIFACTS_CHAPTER_ID, artifacts_title, ARTIFACTS)
    relics_lang = language_for("relics", RELICS_CHAPTER_ID, relics_title, RELICS)
    epicfight_lang = language_for("epicfight", EPICFIGHT_CHAPTER_ID, epicfight_title, EPICFIGHT)
    minecolonies_lang = language_for("minecolonies", MINECOLONIES_CHAPTER_ID, minecolonies_title, MINECOLONIES)
    oritech_lang = language_for("oritech", ORITECH_CHAPTER_ID, oritech_title, ORITECH)
    silentgear_lang = language_for("silentgear", SILENTGEAR_CHAPTER_ID, silentgear_title, SILENTGEAR)
    cobbleplus_lang = language_for("cobbleplus", COBBLEPLUS_CHAPTER_ID, cobbleplus_title, COBBLEPLUS)
    worldbosses_lang = language_for("worldbosses", WORLDBOSSES_CHAPTER_ID, worldbosses_title, WORLDBOSSES)
    createplus_lang = language_for("createplus", CREATEPLUS_CHAPTER_ID, createplus_title, CREATEPLUS)
    traveler_lang = language_for("traveler", TRAVELER_CHAPTER_ID, traveler_title, TRAVELER)
    builder_lang = language_for("builder", BUILDER_CHAPTER_ID, builder_title, BUILDER)
    swem_lang = language_for("swem", SWEM_CHAPTER_ID, swem_title, SWEM)
    origins_lang = language_for("origins", ORIGINS_CHAPTER_ID, origins_title, ORIGINS)
    starlight_lang = language_for("starlight", STARLIGHT_CHAPTER_ID, starlight_title, STARLIGHT)
    wildlife_lang = language_for("wildlife", WILDLIFE_CHAPTER_ID, wildlife_title, WILDLIFE)
    arsplus_lang = language_for("arsplus", ARSPLUS_CHAPTER_ID, arsplus_title, ARSPLUS)
    mekplus_lang = language_for("mekplus", MEKPLUS_CHAPTER_ID, mekplus_title, MEKPLUS)
    community_lang = language_for("community", COMMUNITY_CHAPTER_ID, community_title, COMMUNITY)
    services_lang = language_for("services", SERVICES_CHAPTER_ID, services_title, SERVICES)
    atlas_lang = language_for("atlas", ATLAS_CHAPTER_ID, atlas_title, ATLAS)
    threats_lang = language_for("threats", THREATS_CHAPTER_ID, threats_title, THREATS)
    integration_lang = language_for("integration", INTEGRATION_CHAPTER_ID, integration_title, INTEGRATION)
    finale_lang = language_for("finale", FINALE_CHAPTER_ID, finale_title, FINALE)
    group_lang = "{\n" + "\n".join(
        f"\tchapter_group.{group_id}.title: {q(title)}" for group_id, title, _, _ in GROUPS
    ) + "\n}\n"
    merged = merge_languages(group_lang, sky_lang, create_lang, immersive_lang, mek_lang, ae2_lang, appmek_lang, ars_lang, occult_lang, evil_lang, fna_lang, irons_lang, farmer_lang, mystical_lang, pokemon_lang, trainers_lang, endgame_lang, apotheosis_lang, cataclysm_lang, draconic_lang, vampirism_lang, cobblemon_advanced_lang, achievements_lang, artifacts_lang, relics_lang, epicfight_lang, minecolonies_lang, oritech_lang, silentgear_lang, cobbleplus_lang, worldbosses_lang, createplus_lang, traveler_lang, builder_lang, swem_lang, origins_lang, starlight_lang, wildlife_lang, arsplus_lang, mekplus_lang, community_lang, services_lang, atlas_lang, threats_lang, integration_lang, finale_lang)
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
            (VAMPIRISM_CHAPTER_ID, vampirism_title), (COBBLEMON_ADVANCED_CHAPTER_ID, cobblemon_advanced_title), (ACHIEVEMENTS_CHAPTER_ID, achievements_title),
            (ARTIFACTS_CHAPTER_ID, artifacts_title), (RELICS_CHAPTER_ID, relics_title), (EPICFIGHT_CHAPTER_ID, epicfight_title),
            (MINECOLONIES_CHAPTER_ID, minecolonies_title), (ORITECH_CHAPTER_ID, oritech_title), (SILENTGEAR_CHAPTER_ID, silentgear_title),
            (COBBLEPLUS_CHAPTER_ID, cobbleplus_title), (WORLDBOSSES_CHAPTER_ID, worldbosses_title), (CREATEPLUS_CHAPTER_ID, createplus_title), (TRAVELER_CHAPTER_ID, traveler_title), (BUILDER_CHAPTER_ID, builder_title), (SWEM_CHAPTER_ID, swem_title), (ORIGINS_CHAPTER_ID, origins_title), (STARLIGHT_CHAPTER_ID, starlight_title), (WILDLIFE_CHAPTER_ID, wildlife_title), (ARSPLUS_CHAPTER_ID, arsplus_title), (MEKPLUS_CHAPTER_ID, mekplus_title), (COMMUNITY_CHAPTER_ID, community_title), (SERVICES_CHAPTER_ID, services_title), (ATLAS_CHAPTER_ID, atlas_title), (THREATS_CHAPTER_ID, threats_title), (INTEGRATION_CHAPTER_ID, integration_title), (FINALE_CHAPTER_ID, finale_title)
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
        artifacts_quest_lang = "{\n" + "\n".join(artifacts_lang.strip().splitlines()[2:-1]) + "\n}\n"
        relics_quest_lang = "{\n" + "\n".join(relics_lang.strip().splitlines()[2:-1]) + "\n}\n"
        epicfight_quest_lang = "{\n" + "\n".join(epicfight_lang.strip().splitlines()[2:-1]) + "\n}\n"
        minecolonies_quest_lang = "{\n" + "\n".join(minecolonies_lang.strip().splitlines()[2:-1]) + "\n}\n"
        oritech_quest_lang = "{\n" + "\n".join(oritech_lang.strip().splitlines()[2:-1]) + "\n}\n"
        silentgear_quest_lang = "{\n" + "\n".join(silentgear_lang.strip().splitlines()[2:-1]) + "\n}\n"
        cobbleplus_quest_lang = "{\n" + "\n".join(cobbleplus_lang.strip().splitlines()[2:-1]) + "\n}\n"
        worldbosses_quest_lang = "{\n" + "\n".join(worldbosses_lang.strip().splitlines()[2:-1]) + "\n}\n"
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
        (split / "chapters" / "artifacts.snbt").write_text(artifacts_quest_lang, encoding="utf-8")
        (split / "chapters" / "relics.snbt").write_text(relics_quest_lang, encoding="utf-8")
        (split / "chapters" / "epicfight.snbt").write_text(epicfight_quest_lang, encoding="utf-8")
        (split / "chapters" / "minecolonies.snbt").write_text(minecolonies_quest_lang, encoding="utf-8")
        (split / "chapters" / "oritech.snbt").write_text(oritech_quest_lang, encoding="utf-8")
        (split / "chapters" / "silentgear.snbt").write_text(silentgear_quest_lang, encoding="utf-8")
        (split / "chapters" / "cobbleplus.snbt").write_text(cobbleplus_quest_lang, encoding="utf-8")
        (split / "chapters" / "worldbosses.snbt").write_text(worldbosses_quest_lang, encoding="utf-8")

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
    make_atlas_background(tex / "backgrounds" / "artifacts_book.png", "ARTIFACTS: КАРТА ПОТЕРЯННЫХ СОКРОВИЩ", "artifacts", ARTIFACTS, [(166, 109, 53), (57, 127, 146), (116, 84, 55), (78, 113, 91)])
    make_atlas_background(tex / "backgrounds" / "relics_book.png", "RELICS: МУЗЕЙ ЖИВЫХ РЕЛИКВИЙ", "relics", RELICS, [(115, 80, 165), (184, 130, 61), (81, 112, 148), (141, 82, 118)])
    make_atlas_background(tex / "backgrounds" / "epicfight_book.png", "EPIC FIGHT: ШКОЛЫ БОЕВОГО МАСТЕРСТВА", "epicfight", EPICFIGHT, [(155, 78, 73), (57, 127, 146), (176, 119, 57), (87, 91, 127)])
    make_atlas_background(tex / "backgrounds" / "minecolonies_book.png", "MINECOLONIES: ГОРОД НА ОСТРОВЕ", "minecolonies", MINECOLONIES, [(147, 105, 63), (72, 120, 91), (176, 132, 69), (91, 101, 137)])
    make_atlas_background(tex / "backgrounds" / "oritech_book.png", "ORITECH: ОРБИТАЛЬНАЯ ПРОМЫШЛЕННОСТЬ", "oritech", ORITECH, [(58, 125, 145), (182, 118, 54), (96, 88, 144), (63, 138, 119)])
    make_atlas_background(tex / "backgrounds" / "silentgear_book.png", "SILENT GEAR: КУЗНЕЧНОЕ ДРЕВО", "silentgear", SILENTGEAR, [(142, 86, 58), (85, 119, 143), (179, 125, 60), (82, 133, 100)])
    make_atlas_background(tex / "backgrounds" / "cobbleplus_book.png", "COBBLEMON+: КАРТА ЖИВОГО РЕГИОНА", "cobbleplus", COBBLEPLUS, [(57, 127, 146), (194, 131, 61), (77, 135, 94), (169, 83, 92)])
    make_atlas_background(tex / "backgrounds" / "worldbosses_book.png", "МИРЫ И БОССЫ: АТЛАС ЭКСПЕДИЦИЙ", "worldbosses", WORLDBOSSES, [(153, 74, 70), (91, 80, 142), (188, 126, 61), (69, 113, 134)])
    make_atlas_background(tex / "backgrounds" / "createplus_book.png", "CREATE+: БОЛЬШАЯ ФАБРИКА", "createplus", CREATEPLUS, [(163, 91, 42), (57, 127, 157), (188, 126, 61), (77, 83, 130)])
    make_atlas_background(tex / "backgrounds" / "traveler_book.png", "ПУТЬ ПУТЕШЕСТВЕННИКА", "traveler", TRAVELER, [(57, 123, 105), (76, 125, 150), (176, 132, 69), (91, 101, 137)])
    make_atlas_background(tex / "backgrounds" / "builder_book.png", "МАСТЕРСКАЯ АРХИТЕКТОРА", "builder", BUILDER, [(128, 100, 72), (91, 101, 137), (176, 132, 69), (116, 86, 63)])
    make_atlas_background(tex / "backgrounds" / "swem_book.png", "SWEM: КОННЫЙ МИР", "swem", SWEM, [(155, 79, 66), (76, 126, 89), (176, 132, 69), (91, 101, 137)])
    make_atlas_background(tex / "backgrounds" / "origins_book.png", "NEOORIGINS: СОЗВЕЗДИЕ ГЕРОЯ", "origins", ORIGINS, [(103, 87, 164), (57, 127, 157), (176, 132, 69), (91, 101, 137)])
    make_atlas_background(tex / "backgrounds" / "starlight_book.png", "ETERNAL STARLIGHT: СЕРДЦЕ ИЗМЕРЕНИЯ", "starlight", STARLIGHT, [(72, 91, 154), (85, 139, 173), (137, 84, 156), (195, 135, 67)])
    make_atlas_background(tex / "backgrounds" / "wildlife_book.png", "ЖИВАЯ ПРИРОДА: БОЛЬШОЙ АТЛАС", "wildlife", WILDLIFE, [(78, 133, 82), (68, 126, 151), (142, 112, 65), (180, 139, 70)])
    make_atlas_background(tex / "backgrounds" / "arsplus_book.png", "ARS NOUVEAU+: ШКОЛЫ СТИХИЙ", "arsplus", ARSPLUS, [(123, 80, 164), (187, 85, 59), (58, 126, 164), (76, 139, 96)])
    make_atlas_background(tex / "backgrounds" / "mekplus_book.png", "MEKANISM+: ЭНЕРГЕТИЧЕСКИЙ КОМПЛЕКС", "mekplus", MEKPLUS, [(46, 130, 153), (178, 119, 49), (82, 137, 91), (150, 83, 83)])
    make_atlas_background(tex / "backgrounds" / "community_book.png", "СООБЩЕСТВО: ОБЩИЙ ПРОЕКТ", "community", COMMUNITY, [(176, 121, 56), (65, 123, 150), (79, 135, 92), (125, 84, 153)])
    make_atlas_background(tex / "backgrounds" / "services_book.png", "COBBLEMON SERVICES: TRAINER NETWORK", "services", SERVICES, [(57, 127, 157), (77, 135, 94), (123, 83, 151), (190, 131, 61)])
    make_atlas_background(tex / "backgrounds" / "atlas_book.png", "СТРУКТУРЫ И МИРЫ: БОЛЬШОЙ АТЛАС", "atlas", ATLAS, [(69, 123, 145), (166, 112, 59), (82, 132, 90), (120, 91, 145)])
    make_atlas_background(tex / "backgrounds" / "threats_book.png", "ДИКИЕ УГРОЗЫ: СУЩЕСТВА И МУТАНТЫ", "threats", THREATS, [(158, 74, 68), (176, 121, 57), (91, 80, 142), (65, 112, 133)])
    make_atlas_background(tex / "backgrounds" / "integration_book.png", "ЕДИНАЯ МАСТЕРСКАЯ: ИНТЕГРАЦИИ МОДОВ", "integration", INTEGRATION, [(57, 127, 157), (123, 83, 151), (176, 121, 57), (77, 135, 94)])
    make_atlas_background(tex / "backgrounds" / "finale_book.png", "ФИНАЛЬНАЯ ХРОНИКА: НАСЛЕДИЕ POKETECH ARCANA", "finale", FINALE, [(178, 119, 51), (118, 83, 157), (58, 126, 151), (151, 75, 69)])
    palettes = [(36, 127, 160), (71, 127, 69), (123, 77, 149), (179, 100, 22), (71, 127, 69), (123, 77, 149), (179, 100, 22), (165, 79, 59), (57, 111, 168), (139, 90, 158), (163, 79, 87), (61, 122, 114), (118, 87, 168), (178, 111, 61), (77, 131, 166)]
    for namespace, title in (("skyblock", "Skyblock"), ("mekanism", "Mekanism"), ("create", "Create"), ("immersive", "Immersive Engineering"), ("ae2", "Applied Energistics 2"), ("appmek", "Applied Mekanistics"), ("ars", "Ars Nouveau"), ("occult", "Occultism"), ("evil", "EvilCraft"), ("fna", "Forbidden & Arcanus"), ("irons", "Iron's Spells"), ("farmer", "Farmer's Delight"), ("mystical", "Mystical Agriculture"), ("pokemon", "Pokémon"), ("trainers", "Тренеры и данжи"), ("endgame", "Эндгейм"), ("apotheosis", "Apotheosis"), ("cataclysm", "Cataclysm"), ("draconic", "Draconic Evolution"), ("vampirism", "Vampirism"), ("cobblemon_advanced", "Cobblemon: мастерство"), ("achievements", "Достижения сервера"), ("artifacts", "Artifacts"), ("relics", "Relics"), ("epicfight", "Epic Fight"), ("minecolonies", "MineColonies"), ("oritech", "Oritech"), ("silentgear", "Silent Gear"), ("cobbleplus", "Cobblemon+"), ("worldbosses", "Миры и боссы")):
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
            "artifacts": next_chapters.stage_names("artifacts"),
            "relics": next_chapters.stage_names("relics"),
            "epicfight": next_chapters.stage_names("epicfight"),
            "minecolonies": next_chapters.stage_names("minecolonies"),
            "oritech": next_chapters.stage_names("oritech"),
            "silentgear": next_chapters.stage_names("silentgear"),
            "cobbleplus": next_chapters.stage_names("cobbleplus"),
            "worldbosses": next_chapters.stage_names("worldbosses"),
        }[namespace])
        for stage, (name, color) in enumerate(zip(names, palettes), 1):
            make_guide(tex / "guides" / f"{namespace}_{stage}.png", f"{title} · {name}", "Схема этапа и ключевой производственный поток", color, stage)

    for namespace in ("createplus", "traveler", "builder", "swem", "origins", "starlight", "wildlife", "arsplus", "mekplus", "community", "services", "atlas", "threats", "integration", "finale"):
        title = next_chapters.CHAPTERS[namespace]["title"]
        for stage, name in enumerate(next_chapters.stage_names(namespace), 1):
            color = palettes[(stage + len(namespace)) % len(palettes)]
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
    total = sum(map(len, (SKY, CREATE, IMMERSIVE, MEK, AE2, APPMEK, ARS, OCCULT, EVIL, FNA, IRONS, FARMER, MYSTICAL, POKEMON, TRAINERS, ENDGAME, APOTHEOSIS, CATACLYSM, DRACONIC, VAMPIRISM, COBBLEMON_ADVANCED, ACHIEVEMENTS, ARTIFACTS, RELICS, EPICFIGHT, MINECOLONIES, ORITECH, SILENTGEAR, COBBLEPLUS, WORLDBOSSES, CREATEPLUS, TRAVELER, BUILDER, SWEM, ORIGINS, STARLIGHT, WILDLIFE, ARSPLUS, MEKPLUS, COMMUNITY, SERVICES, ATLAS, THREATS, INTEGRATION, FINALE)))
    print(f"Built 45 chapters and {total} quests; finale: {len(SERVICES)} Services + {len(ATLAS)} Atlas + {len(THREATS)} Threats + {len(INTEGRATION)} Integration + {len(FINALE)} Finale")
    print(f"Server package: {package} ({package.stat().st_size} bytes)")


if __name__ == "__main__":
    write_build()

