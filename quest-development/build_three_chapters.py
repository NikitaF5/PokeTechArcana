from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
OLD_CHAPTERS = WORKSPACE / "backups" / "old-quests-extracted" / "quests" / "chapters"


CHAPTERS = {
    "ae2": {
        "title": "Applied Energistics 2: архитектура сети",
        "file": "ae2",
        "icon": "ae2:controller",
        "stages": [
            ("I · КРИСТАЛЛЫ", "Первые кристаллы", ["Компас", "Метеоритный компас", "Поиск метеорита", "Небесный камень", "Кварц Certus", "Заряженный Certus", "Пыль Certus", "Кварцевое стекло", "Кварцевое волокно"]),
            ("II · ПРЕССЫ", "Четыре пресса", ["Инженерный пресс", "Логический пресс", "Вычислительный пресс", "Кремниевый пресс", "Inscriber", "Печатный кремний", "Логическая схема", "Вычислительная схема", "Инженерная схема"]),
            ("III · ЯДРО СЕТИ", "Первая ME-сеть", ["Энергоприёмник", "Энергетическая ячейка", "ME Controller", "ME Glass Cable", "Терминал", "Crafting Terminal", "Interface", "Pattern Access Terminal", "Network Tool"]),
            ("IV · ХРАНИЛИЩЕ", "Цифровой склад", ["Cell Workbench", "1k Storage Cell", "4k Storage Cell", "16k Storage Cell", "64k Storage Cell", "256k Storage Cell", "ME Drive", "Storage Bus", "Priority и partitioning"]),
            ("V · КАНАЛЫ", "Канальная архитектура", ["Smart Cable", "Dense Cable", "Cable Anchor", "Covered Cable", "Fluix Cable", "Color coding", "32 канала", "Контроллерный крест", "Диагностика каналов"]),
            ("VI · АВТОКРАФТ", "Автокрафт", ["Blank Pattern", "Pattern Provider", "Molecular Assembler", "Crafting Unit", "4k Crafting Storage", "16k Crafting Storage", "64k Crafting Storage", "Crafting Co-Processor", "Processing Pattern", "Smithing Pattern", "Параллельный заказ"]),
            ("VII · ПОДСЕТИ", "Подсети и логистика", ["Import Bus", "Export Bus", "Formation Plane", "Annihilation Plane", "Level Emitter", "Toggle Bus", "Inverted Toggle Bus", "Storage subnet", "Интерфейс между сетями"]),
            ("VIII · ПРОСТРАНСТВО", "Пространственные технологии", ["Spatial Pylon", "Spatial IO Port", "2³ Spatial Cell", "16³ Spatial Cell", "128³ Spatial Cell", "Matter Condenser", "Singularity", "Quantum Entangled Singularity", "Безопасный тест"]),
            ("IX · КВАНТ", "Квантовая фабрика", ["Quantum Ring", "Quantum Link Chamber", "Беспроводная точка", "Wireless Terminal", "Wireless Crafting Terminal", "P2P Tunnel ME", "P2P FE", "P2P Item", "P2P Fluid", "P2P Redstone", "Финальная фабрика"]),
        ],
        "centers": [(0, 12), (14, 2), (28, 2), (42, 11), (56, 18), (70, 12), (84, 3), (98, 3), (112, 12)],
        "patterns": ["crescentR", "ring", "diamond", "ring", "grid", "diamond", "crescentL", "ring", "doubleRing"],
    },
    "appmek": {
        "title": "Applied Mekanistics: цифровой химзавод",
        "file": "ae2",
        "icon": "mekanism:chemical_tank",
        "stages": [
            ("I · МОСТ", "Соединение систем", ["ME Chemical Interface", "Химический терминал", "Chemical Storage Bus", "Проверка совместимости", "Первый химикат"]),
            ("II · ЯЧЕЙКИ", "Хранилище химикатов", ["1k Chemical Cell", "4k Chemical Cell", "16k Chemical Cell", "64k Chemical Cell", "256k Chemical Cell"]),
            ("III · ВВОД И ВЫВОД", "Потоки химикатов", ["Chemical Import Bus", "Chemical Export Bus", "Фильтр химиката", "Приоритеты", "Уровень заполнения"]),
            ("IV · АВТОКРАФТ", "Химические шаблоны", ["Processing Pattern", "Chemical Pattern Provider", "Хлор и водород", "Серная кислота", "Рудная суспензия", "Параллельная обработка"]),
            ("V · ГАЗЫ", "Сеть газов", ["Кислород", "Водород", "Этилен", "Хлороводород", "Буферные ячейки"]),
            ("VI · ЯДЕРНАЯ ЛИНИЯ", "Ядерная интеграция", ["Делящееся топливо", "Ядерные отходы", "Полоний", "Плутоний", "Антиматерия"]),
            ("VII · ЕДИНАЯ ФАБРИКА", "Полная интеграция", ["ME-управление ×5 рудой", "Автозаказ топлива", "Контроль запасов", "Резервная химическая сеть", "Аварийная изоляция", "Цифровой химзавод"]),
        ],
        "centers": [(0, 4), (16, 4), (32, 4), (48, 12), (64, 20), (80, 20), (96, 12)],
        "patterns": ["fanR", "stack", "mirror", "hex", "fanL", "containment", "doubleFan"],
    },
    "ars": {
        "title": "Ars Nouveau: созвездие архимага",
        "file": "ars",
        "icon": "ars_nouveau:archmage_spell_book",
        "stages": [
            ("I · НОВИЧОК", "Книга заклинаний", ["Worn Notebook", "Novice Spell Book", "Манипуляционный стол", "Первый глиф", "Touch", "Projectile", "Break"]),
            ("II · ИСТОЧНИК", "Получение Source", ["Sourcestone", "Source Jar", "Agronomic Sourcelink", "Volcanic Sourcelink", "Alchemical Sourcelink", "Vitalic Sourcelink", "Mycelial Sourcelink", "Source Relay"]),
            ("III · ЗАКЛИНАНИЯ", "Грамматика магии", ["Форма заклинания", "Эффект заклинания", "Усилитель", "Extend Time", "Amplify", "AOE", "Pierce", "Delay"]),
            ("IV · ТИРЫ", "Продвинутая книга", ["Magebloom", "Magebloom Fiber", "Apprentice Book", "Archmage Book", "Tier 2 Glyph", "Tier 3 Glyph", "Регенерация маны", "Сложное заклинание"]),
            ("V · АВТОМАТИЗАЦИЯ", "Магическая автоматика", ["Spell Turret", "Spell Prism", "Relay Splitter", "Relay Collector", "Relay Depositor", "Source Gem Block", "Автодобыча", "Автоферма"]),
            ("VI · СУЩЕСТВА", "Фамильяры", ["Wixie Cauldron", "Whirlisprig", "Starbuncle", "Drygmy", "Amethyst Golem", "Bookwyrm", "Фамильяр", "Автоматический склад"]),
            ("VII · РИТУАЛЫ", "Ритуальная магия", ["Ritual Brazier", "Tablet of Sunrise", "Tablet of Overgrowth", "Tablet of Flight", "Tablet of Warping", "Tablet of Containment", "Модификаторы ритуала"]),
            ("VIII · АРХИМАГ", "Мастерская архимага", ["Enchanter Sword", "Enchanter Shield", "Battlemage Armor", "Threads", "Dominion Wand", "Warp Portal", "Stable Warp Scroll", "Интеграция с островом"]),
        ],
        "centers": [(0, 15), (14, 4), (28, 0), (42, 1), (56, 5), (70, 14), (56, 23), (42, 15)],
        "patterns": ["crescentR", "star", "ring", "crescentD", "star", "crescentL", "ritual", "doubleRing"],
    },
}


# Each objective uses a real registered item that matches the lesson instead of
# a generic placeholder. The last item in every row is the stage capstone.
ITEMS = {
    "ae2": [
        ["minecraft:compass", "ae2:meteorite_compass", "ae2:meteorite_compass", "ae2:sky_stone_block", "ae2:certus_quartz_crystal", "ae2:charged_certus_quartz_crystal", "ae2:certus_quartz_dust", "ae2:quartz_glass", "ae2:quartz_fiber", "ae2:fluix_crystal"],
        ["ae2:engineering_processor_press", "ae2:logic_processor_press", "ae2:calculation_processor_press", "ae2:silicon_press", "ae2:inscriber", "ae2:printed_silicon", "ae2:printed_logic_processor", "ae2:printed_calculation_processor", "ae2:printed_engineering_processor", "ae2:engineering_processor"],
        ["ae2:energy_acceptor", "ae2:energy_cell", "ae2:controller", "ae2:fluix_glass_cable", "ae2:terminal", "ae2:crafting_terminal", "ae2:interface", "ae2:pattern_access_terminal", "ae2:network_tool", "ae2:controller"],
        ["ae2:cell_workbench", "ae2:item_storage_cell_1k", "ae2:item_storage_cell_4k", "ae2:item_storage_cell_16k", "ae2:item_storage_cell_64k", "ae2:item_storage_cell_256k", "ae2:drive", "ae2:storage_bus", "ae2:view_cell", "ae2:drive"],
        ["ae2:fluix_smart_cable", "ae2:fluix_smart_dense_cable", "ae2:cable_anchor", "ae2:fluix_covered_cable", "ae2:fluix_glass_cable", "ae2:color_applicator", "ae2:controller", "ae2:controller", "ae2:network_tool", "ae2:fluix_smart_dense_cable"],
        ["ae2:blank_pattern", "ae2:pattern_provider", "ae2:molecular_assembler", "ae2:crafting_unit", "ae2:4k_crafting_storage", "ae2:16k_crafting_storage", "ae2:64k_crafting_storage", "ae2:crafting_accelerator", "ae2:processing_pattern", "ae2:smithing_table_pattern", "ae2:crafting_terminal", "ae2:256k_crafting_storage"],
        ["ae2:import_bus", "ae2:export_bus", "ae2:formation_plane", "ae2:annihilation_plane", "ae2:level_emitter", "ae2:toggle_bus", "ae2:inverted_toggle_bus", "ae2:storage_bus", "ae2:interface", "ae2:controller"],
        ["ae2:spatial_pylon", "ae2:spatial_io_port", "ae2:spatial_storage_cell_2", "ae2:spatial_storage_cell_16", "ae2:spatial_storage_cell_128", "ae2:condenser", "ae2:singularity", "ae2:quantum_entangled_singularity", "ae2:spatial_storage_cell_2", "ae2:spatial_io_port"],
        ["ae2:quantum_ring", "ae2:quantum_link", "ae2:wireless_access_point", "ae2:wireless_terminal", "ae2:wireless_crafting_terminal", "ae2:me_p2p_tunnel", "ae2:fe_p2p_tunnel", "ae2:item_p2p_tunnel", "ae2:fluid_p2p_tunnel", "ae2:redstone_p2p_tunnel", "ae2:controller", "ae2:quantum_link"],
    ],
    "appmek": [
        ["appmek:chemical_cell_housing", "appmek:portable_chemical_cell_1k", "appmek:chemical_p2p_tunnel", "mekanism:basic_chemical_tank", "appmek:chemical_storage_cell_1k", "appmek:chemical_cell_housing"],
        ["appmek:chemical_storage_cell_1k", "appmek:chemical_storage_cell_4k", "appmek:chemical_storage_cell_16k", "appmek:chemical_storage_cell_64k", "appmek:chemical_storage_cell_256k", "appmek:portable_chemical_cell_256k"],
        ["appmek:chemical_p2p_tunnel", "appmek:chemical_p2p_tunnel", "appmek:chemical_storage_cell_4k", "appmek:chemical_storage_cell_16k", "appmek:portable_chemical_cell_16k", "appmek:chemical_p2p_tunnel"],
        ["ae2:processing_pattern", "ae2:pattern_provider", "mekanism:chemical_infuser", "mekanism:chemical_infuser", "mekanism:chemical_washer", "ae2:crafting_accelerator", "appmek:chemical_storage_cell_64k"],
        ["mekanism:electrolytic_separator", "mekanism:electrolytic_separator", "mekanism:pressurized_reaction_chamber", "mekanism:chemical_infuser", "appmek:portable_chemical_cell_64k", "appmek:chemical_storage_cell_64k"],
        ["mekanismgenerators:fission_reactor_casing", "mekanism:radioactive_waste_barrel", "mekanism:pellet_polonium", "mekanism:pellet_plutonium", "mekanism:pellet_antimatter", "appmek:chemical_storage_cell_256k"],
        ["mekanism:chemical_injection_chamber", "ae2:pattern_provider", "ae2:level_emitter", "appmek:portable_chemical_cell_256k", "appmek:chemical_p2p_tunnel", "appmek:chemical_storage_cell_256k", "ae2:controller"],
    ],
    "ars": [
        ["ars_nouveau:worn_notebook", "ars_nouveau:novice_spell_book", "ars_nouveau:scribes_table", "ars_nouveau:blank_glyph", "ars_nouveau:glyph_touch", "ars_nouveau:glyph_projectile", "ars_nouveau:glyph_break", "ars_nouveau:novice_spell_book"],
        ["ars_nouveau:sourcestone", "ars_nouveau:source_jar", "ars_nouveau:agronomic_sourcelink", "ars_nouveau:volcanic_sourcelink", "ars_nouveau:alchemical_sourcelink", "ars_nouveau:vitalic_sourcelink", "ars_nouveau:mycelial_sourcelink", "ars_nouveau:relay", "ars_nouveau:source_jar"],
        ["ars_nouveau:glyph_touch", "ars_nouveau:glyph_break", "ars_nouveau:glyph_amplify", "ars_nouveau:glyph_extend_time", "ars_nouveau:glyph_amplify", "ars_nouveau:glyph_aoe", "ars_nouveau:glyph_pierce", "ars_nouveau:glyph_delay", "ars_nouveau:spell_parchment"],
        ["ars_nouveau:magebloom", "ars_nouveau:magebloom_fiber", "ars_nouveau:apprentice_spell_book", "ars_nouveau:archmage_spell_book", "ars_nouveau:glyph_amplify", "ars_nouveau:glyph_blink", "ars_nouveau:amulet_of_mana_regen", "ars_nouveau:archmage_spell_book", "ars_nouveau:archmage_spell_book"],
        ["ars_nouveau:spell_turret", "ars_nouveau:spell_prism", "ars_nouveau:relay_splitter", "ars_nouveau:relay_collector", "ars_nouveau:relay_deposit", "ars_nouveau:source_gem_block", "ars_nouveau:glyph_break", "ars_nouveau:glyph_harvest", "ars_nouveau:timer_spell_turret"],
        ["ars_nouveau:wixie_cauldron", "ars_nouveau:whirlisprig_charm", "ars_nouveau:starbuncle_charm", "ars_nouveau:drygmy_charm", "ars_nouveau:amethyst_golem_charm", "ars_nouveau:bookwyrm_charm", "ars_nouveau:familiar_starbuncle", "ars_nouveau:storage_lectern", "ars_nouveau:summoning_crystal"],
        ["ars_nouveau:ritual_brazier", "ars_nouveau:ritual_sunrise", "ars_nouveau:ritual_overgrowth", "ars_nouveau:ritual_flight", "ars_nouveau:ritual_warping", "ars_nouveau:ritual_containment", "ars_nouveau:ritual_binding", "ars_nouveau:ritual_brazier"],
        ["ars_nouveau:enchanters_sword", "ars_nouveau:enchanters_shield", "ars_nouveau:battlemage_robes", "ars_nouveau:blank_thread", "ars_nouveau:dominion_wand", "ars_nouveau:portal", "ars_nouveau:stable_warp_scroll", "ars_nouveau:archmage_spell_book", "ars_nouveau:archmage_spell_book"],
    ],
}


def _pool(filename: str) -> list[str]:
    text = (OLD_CHAPTERS / f"{filename}.snbt").read_text("utf-8")
    result = []
    for item in re.findall(r'item:\s*\{[^}]*?id:\s*"([^"]+)"', text, re.S):
        if item.startswith(("minecraft:", "ae2:", "ars_nouveau:", "ars_elemental:")) or ":" in item:
            if "debug_" not in item and item not in result:
                result.append(item)
    return result


def _points(pattern: str, count: int, cx: float, cy: float) -> list[tuple[float, float]]:
    import math
    points = []
    if pattern in {"ring", "ritual"}:
        for i in range(count):
            a = -math.pi / 2 + i * math.pi * 2 / count
            points.append((cx + math.cos(a) * 5.2, cy + math.sin(a) * 4.8))
    elif pattern == "doubleRing":
        for i in range(count):
            ring, slot, n = i % 2, i // 2, (count + 1) // 2
            a = -math.pi / 2 + slot * math.pi * 2 / n
            radius = 6.2 if ring else 4.0
            points.append((cx + math.cos(a) * radius, cy + math.sin(a) * (radius * .9)))
    elif pattern == "diamond":
        anchors = [(0, -6), (5.5, 0), (0, 6), (-5.5, 0)]
        for i in range(count):
            t = i / count * 4; j = int(t); f = t - j; a = anchors[j % 4]; b = anchors[(j + 1) % 4]
            points.append((cx + a[0] + (b[0] - a[0]) * f, cy + a[1] + (b[1] - a[1]) * f))
    elif pattern == "grid":
        cols, dx, dy = 3, 3.4, 3.1
        for i in range(count):
            row, col, rows = i // cols, i % cols, (count + cols - 1) // cols
            points.append((cx + (col - 1) * dx, cy + (row - (rows - 1) / 2) * dy))
    elif pattern in {"stack", "mirror"}:
        for i in range(count):
            row = i // 2 if pattern == "mirror" else i
            side = (-1 if i % 2 else 1) if pattern == "mirror" else 1
            points.append((cx + side * (6.2 if pattern == "mirror" else 5.8), cy + (row - ((count + 1) // 2 - 1) / 2) * 3.1))
    elif pattern == "hex":
        for i in range(count):
            a = -math.pi / 2 + i * math.pi * 2 / count
            points.append((cx + math.cos(a) * 6, cy + math.sin(a) * 5.5))
    elif pattern == "containment":
        for i in range(count):
            a = -math.pi / 2 + i * math.pi * 2 / count
            r = 4.2 + i * .35
            points.append((cx + math.cos(a) * r, cy + math.sin(a) * r * .9))
    elif pattern == "star":
        for i in range(count):
            a = -math.pi / 2 + i * math.pi * 2 / count; r = 3.1 if i % 2 else 6.2
            points.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    elif pattern in {"fanR", "fanL", "doubleFan"}:
        side = -1 if pattern == "fanL" else 1
        for i in range(count):
            a = -1.15 + i * 2.3 / max(1, count - 1); r = 6.2 if pattern != "doubleFan" or i % 2 else 4.2
            points.append((cx + side * math.cos(a) * r, cy + math.sin(a) * r))
    else:
        side = -1 if pattern == "crescentL" else 1
        for i in range(count):
            a = -1.25 + i * 2.5 / max(1, count - 1)
            points.append((cx + side * math.cos(a) * 6.2, cy + math.sin(a) * 5.8))
    return points


def build_chapter(namespace: str, quest_cls, tag_main: str = "pta_main", tag_branch: str = "pta_resource"):
    config = CHAPTERS[namespace]
    result = []
    prior_root = None
    for stage_index, (phase, stage_name, configured_titles) in enumerate(config["stages"]):
        titles = [*configured_titles, f"Контрольная сборка: {stage_name}"]
        cx, cy = config["centers"][stage_index]
        points = _points(config["patterns"][stage_index], len(titles), cx, cy)
        for quest_index, title in enumerate(titles):
            key = f"s{stage_index + 1:02d}_{quest_index + 1:02d}"
            item = ITEMS[namespace][stage_index][quest_index]
            deps = (prior_root,) if quest_index == 0 and prior_root else (f"s{stage_index + 1:02d}_01",)
            if quest_index == 0:
                deps = (prior_root,) if prior_root else ()
            result.append(quest_cls(key, title, phase, f"Практический урок этапа «{stage_name}». Выполни действие и проверь результат перед переходом дальше.", points[quest_index][0], points[quest_index][1], "diamond" if quest_index == 0 else ("hexagon" if quest_index % 3 == 0 else "circle"), 1.45 if quest_index == 0 else 1.0, ((item, 1),), deps, (item, 1), 2 + stage_index, tag_main if quest_index == 0 else tag_branch, item))
        prior_root = f"s{stage_index + 1:02d}_01"
    return result


def stage_names(namespace: str) -> list[str]:
    return [stage[1] for stage in CHAPTERS[namespace]["stages"]]
