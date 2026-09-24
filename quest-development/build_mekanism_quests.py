from __future__ import annotations

import hashlib
import math
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "current" / "config" / "ftbquests" / "quests"
GROUP_ID = "9A2E2B8D9E0A1001"
CHAPTER_ID = "9A2E2B8D9E0A2001"


def hid(kind: str, key: str) -> str:
    return hashlib.sha256(f"poketech-mekanism-v2:{kind}:{key}".encode()).hexdigest()[:16].upper()


def item(mod: str, name: str, count: int = 1) -> tuple[str, int]:
    return f"{mod}:{name}", count


NODES = [
    # key, title, phase, description, x, y, shape, size, tasks, dependencies, reward item, reward count, xp
    ("osmium", "Осмиевая жила", "I · ОСНОВА", "Получи первые слитки осмия. На скайблоке основной путь к руде начинается с просеивания и переработки ресурсов.", 0, 0, "diamond", 1.45, [item("mekanism", "ingot_osmium", 24)], [], item("mekanism", "enriched_iron", 8), 2),
    ("steel", "Стальной рубеж", "I · ОСНОВА", "Подготовь сталь для корпусов, кабелей и большинства машин Mekanism.", 3, 0, "circle", 1.1, [item("mekanism", "ingot_steel", 16)], ["osmium"], item("mekanism", "basic_control_circuit", 2), 2),
    ("heat", "Тепловой генератор", "I · ОСНОВА", "Собери простой источник энергии. Лава под генератором заметно увеличивает выработку.", 6, -2, "circle", 1.1, [item("mekanismgenerators", "heat_generator")], ["steel"], item("mekanism", "energy_tablet"), 2),
    ("manual", "Инженерный набор", "I · ОСНОВА", "Создай конфигуратор и сетевой считыватель: ими настраивают стороны машин и проверяют сети.", 6, 2, "circle", 1.1, [item("mekanism", "configurator"), item("mekanism", "network_reader")], ["steel"], item("mekanism", "basic_universal_cable", 8), 2),
    ("infuser", "Металлургический инфузор", "I · ОСНОВА", "Центральная машина раннего этапа. Освой углерод, красный камень и производство сплавов.", 9, 0, "hexagon", 1.4, [item("mekanism", "metallurgic_infuser")], ["heat", "manual"], item("mekanism", "enriched_redstone", 8), 3),

    ("enrichment", "Обогащение", "II · МАШИНЫ", "Построй камеру обогащения и начни удваивать рудное сырьё.", 12, -3, "circle", 1.1, [item("mekanism", "enrichment_chamber")], ["infuser"], item("mekanism", "upgrade_energy", 2), 3),
    ("crusher", "Дробилка", "II · МАШИНЫ", "Дробилка превращает материалы в пыль и открывает биотопливную цепочку.", 12, 0, "circle", 1.1, [item("mekanism", "crusher")], ["infuser"], item("mekanism", "bio_fuel", 8), 3),
    ("cube", "Энергокуб", "II · МАШИНЫ", "Собери буфер энергии, чтобы машины не останавливались при скачках потребления.", 12, 3, "circle", 1.1, [item("mekanism", "basic_energy_cube")], ["infuser"], item("mekanism", "advanced_control_circuit", 2), 3),
    ("smelter", "Электропечь", "II · МАШИНЫ", "Переведи плавку на FE и подготовь линию к полной автоматизации.", 15, -3, "circle", 1.1, [item("mekanism", "energized_smelter")], ["enrichment"], item("mekanism", "upgrade_speed", 2), 3),
    ("tank", "Резервуары", "II · МАШИНЫ", "Создай базовые хранилища жидкости и химикатов для следующих производственных цепочек.", 15, 1, "circle", 1.1, [item("mekanism", "basic_fluid_tank"), item("mekanism", "basic_chemical_tank")], ["crusher"], item("mekanism", "advanced_fluid_tank"), 3),

    ("cables", "Универсальная сеть", "III · СЕТИ", "Проложи первую энергетическую сеть. Используй конфигуратор для режимов подключения.", 15, 4, "hexagon", 1.25, [item("mekanism", "basic_universal_cable", 16)], ["cube"], item("mekanism", "advanced_universal_cable", 8), 3),
    ("transport", "Транспортёры", "III · СЕТИ", "Автоматизируй перемещение предметов между сундуками и машинами.", 16, -0.7, "circle", 1.0, [item("mekanism", "basic_logistical_transporter", 16)], ["crusher"], item("mekanism", "advanced_logistical_transporter", 8), 3),
    ("pipes", "Механические трубы", "III · СЕТИ", "Соедини резервуары и машины механическими трубами для передачи жидкостей.", 18, 1.2, "circle", 1.0, [item("mekanism", "basic_mechanical_pipe", 16)], ["tank"], item("mekanism", "advanced_mechanical_pipe", 8), 3),
    ("sorter", "Умная сортировка", "III · СЕТИ", "Настрой логистический сортировщик и хотя бы один фильтр предметов.", 19, -1.2, "circle", 1.0, [item("mekanism", "logistical_sorter")], ["transport"], item("mekanism", "diversion_transporter", 4), 4),
    ("pressure", "Газовые трубы", "III · СЕТИ", "Подготовь сеть pressurized tube для водорода, кислорода и других химикатов.", 19, 4, "circle", 1.0, [item("mekanism", "basic_pressurized_tube", 16)], ["tank"], item("mekanism", "advanced_pressurized_tube", 8), 3),
    ("pump", "Электропомпа", "III · СЕТИ", "Обеспечь производственные линии постоянной подачей воды.", 21, 1.2, "circle", 1.0, [item("mekanism", "electric_pump")], ["pipes"], item("mekanism", "upgrade_filter", 2), 4),
    ("electrolyzer", "Электролиз", "III · СЕТИ", "Разделяй воду на водород и кислород. Оба химиката понадобятся дальше.", 19, 7, "hexagon", 1.25, [item("mekanism", "electrolytic_separator")], ["cables", "pressure"], item("mekanism", "advanced_chemical_tank", 2), 4),
    ("gasburn", "Газовая энергия", "III · СЕТИ", "Запусти газовый генератор. Этилен станет главным источником энергии среднего этапа.", 22, 8, "circle", 1.1, [item("mekanismgenerators", "gas_burning_generator")], ["electrolyzer"], item("mekanism", "elite_energy_cube"), 5),

    ("basicfactory", "Базовая фабрика", "IV · ФАБРИКИ", "Увеличь число параллельных операций с помощью базовой обогащающей фабрики.", 15, -7, "circle", 1.0, [item("mekanism", "basic_enriching_factory")], ["enrichment"], item("mekanism", "basic_control_circuit", 4), 4),
    ("advancedfactory", "Продвинутая фабрика", "IV · ФАБРИКИ", "Расширь фабрику до пяти одновременных операций.", 19, -8.5, "circle", 1.0, [item("mekanism", "advanced_enriching_factory")], ["basicfactory"], item("mekanism", "advanced_control_circuit", 4), 5),
    ("elitefactory", "Элитная фабрика", "IV · ФАБРИКИ", "Перейди к семи операциям и подготовь промышленный выпуск компонентов.", 23, -8.5, "circle", 1.0, [item("mekanism", "elite_enriching_factory")], ["advancedfactory"], item("mekanism", "elite_control_circuit", 4), 6),
    ("ultimatefactory", "Высшая фабрика", "IV · ФАБРИКИ", "Создай фабрику высшего уровня на девять параллельных операций.", 27, -7, "octagon", 1.25, [item("mekanism", "ultimate_enriching_factory")], ["elitefactory"], item("mekanism", "ultimate_control_circuit", 2), 8),
    ("upgrades", "Точная настройка", "IV · ФАБРИКИ", "Подготовь полный комплект улучшений скорости и энергии для промышленной линии.", 19, -4.5, "circle", 1.0, [item("mekanism", "upgrade_speed", 8), item("mekanism", "upgrade_energy", 8)], ["smelter"], item("mekanism", "upgrade_muffling", 4), 5),
    ("auto", "Без рук", "IV · ФАБРИКИ", "Собери Formulaic Assemblicator и включи автоматическую подачу и вывод предметов.", 23, -3.3, "circle", 1.0, [item("mekanism", "formulaic_assemblicator")], ["sorter", "upgrades"], item("mekanism", "crafting_formula", 4), 6),
    ("miner", "Цифровой шахтёр", "IV · ФАБРИКИ", "Освой точечную добычу по фильтрам. На острове используй его только там, где добыча разрешена правилами мира.", 23, -0.5, "hexagon", 1.25, [item("mekanism", "digital_miner")], ["sorter"], item("mekanism", "upgrade_anchor"), 8),
    ("qio", "Первый QIO", "IV · ФАБРИКИ", "Создай QIO Drive Array и первый накопитель для цифрового хранения предметов.", 22, 22, "hexagon", 1.25, [item("mekanism", "qio_drive_array"), item("mekanism", "qio_drive_base")], ["cables"], item("mekanism", "portable_qio_dashboard"), 7),

    ("purification", "Очистительная камера", "V · ХИМИЯ", "Подай кислород в Purification Chamber и открой переработку руды ×3.", 23, 4, "circle", 1.0, [item("mekanism", "purification_chamber")], ["electrolyzer"], item("mekanism", "advanced_control_circuit", 4), 5),
    ("injection", "Камера впрыска", "V · ХИМИЯ", "Используй хлороводород для переработки руды ×4.", 27, 4, "circle", 1.0, [item("mekanism", "chemical_injection_chamber")], ["purification"], item("mekanism", "elite_control_circuit", 3), 6),
    ("dissolution", "Растворение", "V · ХИМИЯ", "Растворяй руду серной кислотой и получай рудную суспензию.", 31, 4, "circle", 1.0, [item("mekanism", "chemical_dissolution_chamber")], ["injection"], item("mekanism", "elite_chemical_tank"), 7),
    ("washer", "Промывка", "V · ХИМИЯ", "Очищай грязную суспензию водой перед кристаллизацией.", 35, 4, "circle", 1.0, [item("mekanism", "chemical_washer")], ["dissolution"], item("mekanism", "upgrade_speed", 4), 7),
    ("crystallizer", "Кристаллизация ×5", "V · ХИМИЯ", "Заверши полную пятиступенчатую линию переработки руды.", 42, 4, "octagon", 1.35, [item("mekanism", "chemical_crystallizer")], ["washer"], item("mekanism", "ultimate_control_circuit", 2), 10),
    ("brine", "Солнечный рассол", "V · ХИМИЯ", "Собери Thermal Evaporation Plant и начни производство рассола.", 25, 1, "circle", 1.0, [item("mekanism", "thermal_evaporation_controller"), item("mekanism", "thermal_evaporation_block", 8)], ["pump"], item("mekanismgenerators", "advanced_solar_generator", 2), 6),
    ("lithium", "Жидкий литий", "V · ХИМИЯ", "Преврати рассол в литий и подготовь сырьё для термоядерной цепочки.", 29, 1, "circle", 1.0, [item("mekanism", "lithium_bucket")], ["brine"], item("mekanism", "rotary_condensentrator"), 7),
    ("sulfur", "Серная цепь", "V · ХИМИЯ", "Построй устойчивое производство серной кислоты для химической переработки и ядерного топлива.", 19, 12, "hexagon", 1.25, [item("mekanism", "chemical_oxidizer"), item("mekanism", "chemical_infuser")], ["gasburn"], item("mekanism", "sulfuric_acid_bucket", 4), 7),

    ("wind", "Ветряной парк", "VI · АТОМ", "Создай стабильную генерацию энергии на высоте с помощью четырёх ветрогенераторов.", 26, 8, "circle", 1.0, [item("mekanismgenerators", "wind_generator", 4)], ["gasburn"], item("mekanism", "elite_universal_cable", 16), 6),
    ("matrix", "Индукционная матрица", "VI · АТОМ", "Собери многоблочное хранилище энергии с ячейкой и поставщиком высшего уровня.", 30, 8, "hexagon", 1.25, [item("mekanism", "induction_casing", 16), item("mekanism", "ultimate_induction_cell"), item("mekanism", "ultimate_induction_provider")], ["wind"], item("mekanism", "ultimate_energy_cube"), 10),
    ("fissile", "Делящийся материал", "VI · АТОМ", "Подготовь изотопную центрифугу и полную линию производства делящегося топлива.", 27, 12, "circle", 1.0, [item("mekanism", "isotopic_centrifuge")], ["sulfur"], item("mekanism", "dosimeter"), 8),
    ("fission", "Реактор деления", "VI · АТОМ", "Собери корпус и порт реактора. Перед запуском обязательно подготовь охлаждение и аварийное отключение.", 31, 12, "octagon", 1.35, [item("mekanismgenerators", "fission_reactor_casing", 18), item("mekanismgenerators", "fission_reactor_port")], ["fissile"], item("mekanismgenerators", "turbine_casing", 8), 12),
    ("turbine", "Промышленная турбина", "VI · АТОМ", "Преврати реакторный пар в большую и стабильную выработку энергии.", 35, 10, "circle", 1.0, [item("mekanismgenerators", "turbine_casing", 18), item("mekanismgenerators", "turbine_rotor")], ["fission"], item("mekanismgenerators", "electromagnetic_coil", 2), 10),
    ("waste", "Ядерные отходы", "VI · АТОМ", "Организуй закрытое и безопасное хранение радиоактивных отходов.", 35, 14, "circle", 1.0, [item("mekanism", "radioactive_waste_barrel", 4)], ["fission"], item("mekanism", "geiger_counter"), 9),
    ("polonium", "Полоний", "VI · АТОМ", "Обработай отходы в Solar Neutron Activator и получи гранулу полония.", 39, 14, "circle", 1.0, [item("mekanism", "pellet_polonium")], ["waste"], item("mekanism", "pellet_plutonium"), 10),
    ("sps", "SPS", "VI · АТОМ", "Собери Supercritical Phase Shifter и произведи первую гранулу антиматерии.", 43, 14, "octagon", 1.45, [item("mekanism", "sps_casing", 16), item("mekanism", "supercharged_coil"), item("mekanism", "pellet_antimatter")], ["polonium"], item("mekanism", "alloy_atomic", 4), 15),

    ("fusionfuel", "Топливо синтеза", "VII · ФИНАЛ", "Подготовь дейтерий, тритий и заполненный Hohlraum для запуска термоядерного реактора.", 46, 1, "circle", 1.1, [item("mekanismgenerators", "deuterium_bucket"), item("mekanismgenerators", "tritium_bucket"), item("mekanismgenerators", "hohlraum")], ["lithium", "crystallizer"], item("mekanismgenerators", "laser_focus_matrix", 4), 10),
    ("laser", "Лазерная матрица", "VII · ФИНАЛ", "Накопи импульс зажигания в усилителе лазера и направь его в Laser Focus Matrix.", 46, 8, "circle", 1.1, [item("mekanism", "laser_amplifier"), item("mekanismgenerators", "laser_focus_matrix")], ["matrix"], item("mekanism", "laser", 4), 10),
    ("fusion", "Термоядерный реактор", "VII · ФИНАЛ", "Запусти стабильный синтез дейтерия и трития — собственную звезду в машине.", 50, 4.5, "octagon", 1.5, [item("mekanismgenerators", "fusion_reactor_controller")], ["fusionfuel", "laser"], item("mekanism", "ultimate_induction_cell"), 18),
    ("mekasuit", "MekaSuit", "VII · ФИНАЛ", "Создай полный комплект MekaSuit. Модули выбирай под собственный стиль игры.", 50, 12, "octagon", 1.3, [item("mekanism", "mekasuit_helmet"), item("mekanism", "mekasuit_bodyarmor"), item("mekanism", "mekasuit_pants"), item("mekanism", "mekasuit_boots")], ["sps"], item("mekanism", "module_energy_unit", 4), 15),
    ("mekatool", "Meka-Tool", "VII · ФИНАЛ", "Создай универсальный инструмент и установи добывающие или боевые модули.", 50, 16, "octagon", 1.3, [item("mekanism", "meka_tool")], ["sps"], item("mekanism", "module_excavation_escalation_unit", 2), 15),
    ("qio2", "Квантовый склад", "VII · ФИНАЛ", "Увеличь ёмкость QIO-сети до накопителя высшего уровня.", 34, 22, "circle", 1.1, [item("mekanism", "qio_drive_supermassive")], ["qio"], item("mekanism", "qio_drive_time_dilating"), 12),
    ("qiologistics", "Квантовая логистика", "VII · ФИНАЛ", "Подключи импорт, экспорт и управление красным камнем к своей QIO-сети.", 50, 18, "octagon", 1.3, [item("mekanism", "qio_importer"), item("mekanism", "qio_exporter"), item("mekanism", "qio_redstone_adapter")], ["qio2"], item("mekanism", "portable_qio_dashboard"), 15),
    ("core", "Сердце технологии", "VII · ФИНАЛ", "Докажи полное освоение Mekanism: антиматерия, высшая схема и квантовое ядро завершают главу.", 58, 6, "octagon", 1.75, [item("mekanism", "pellet_antimatter"), item("mekanism", "ultimate_control_circuit"), item("mekanism", "teleportation_core")], ["fusion", "mekasuit", "mekatool", "qiologistics"], item("mekanism", "pellet_antimatter", 2), 25),
]


def q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def make_quest(node: tuple) -> str:
    key, _title, _phase, _desc, x, y, shape, size, tasks, deps, reward, xp = node
    quest_id = hid("quest", key)
    lines = ["\t\t{"]
    if deps:
        dep_ids = ", ".join(q(hid("quest", dep)) for dep in deps)
        lines.append(f"\t\t\tdependencies: [{dep_ids}]")
    lines += [
        f"\t\t\ticon: {{ id: {q(tasks[0][0])} }}",
        f"\t\t\tid: {q(quest_id)}",
        "\t\t\trewards: [",
        "\t\t\t\t{",
        f"\t\t\t\t\tcount: {reward[1]}",
        f"\t\t\t\t\tid: {q(hid('reward-item', key))}",
        f"\t\t\t\t\titem: {{ count: 1, id: {q(reward[0])} }}",
        "\t\t\t\t\ttype: \"item\"",
        "\t\t\t\t}",
        "\t\t\t\t{",
        f"\t\t\t\t\tid: {q(hid('reward-xp', key))}",
        "\t\t\t\t\ttype: \"xp_levels\"",
        f"\t\t\t\t\txp_levels: {xp}",
        "\t\t\t\t}",
        "\t\t\t]",
        f"\t\t\tshape: {q(shape)}",
        f"\t\t\tsize: {size:.2f}d",
        "\t\t\ttags: [\"mekanism\"]",
        "\t\t\ttasks: [",
    ]
    for i, (item_id, count) in enumerate(tasks):
        lines += [
            "\t\t\t\t{",
            f"\t\t\t\t\tid: {q(hid(f'task-{i}', key))}",
            f"\t\t\t\t\titem: {{ count: {count}, id: {q(item_id)} }}",
            "\t\t\t\t\ttype: \"item\"",
            "\t\t\t\t}",
        ]
    lines += [
        "\t\t\t]",
        f"\t\t\tx: {float(x):.1f}d",
        f"\t\t\ty: {float(y):.1f}d",
        "\t\t}",
    ]
    return "\n".join(lines)


def build_lang() -> str:
    lines = ["{"]
    lines.append(f"\tchapter.{CHAPTER_ID}.title: \"Mekanism: эра атома\"")
    lines.append(f"\tchapter_group.{GROUP_ID}.title: \"Технологии\"")
    for node in NODES:
        key, title, phase, desc, *_ = node
        quest_id = hid("quest", key)
        reward = node[-2]
        reward_name = reward[0].split(":", 1)[1].replace("_", " ")
        lines += [
            f"\tquest.{quest_id}.title: {q(title)}",
            f"\tquest.{quest_id}.quest_desc: [",
            f"\t\t{q('&8' + phase)}",
            f"\t\t{q('&7' + desc)}",
            "\t\t\"\"",
            f"\t\t{q('&b▶ Задача: &fсобрать указанные предметы')}",
            f"\t\t{q('&a◆ Награда: &f' + str(reward[1]) + '× ' + reward_name + ' и опыт')}",
            "\t]",
        ]
    lines.append("}")
    return "\n".join(lines) + "\n"


def validate() -> None:
    keys = {n[0] for n in NODES}
    if len(keys) != len(NODES) or len(NODES) != 50:
        raise ValueError(f"Expected 50 unique quests, got {len(keys)}")
    for node in NODES:
        for dep in node[9]:
            if dep not in keys:
                raise ValueError(f"Unknown dependency {dep!r} in {node[0]}")

    ids = []
    for n in NODES:
        ids += [hid("quest", n[0]), hid("reward-item", n[0]), hid("reward-xp", n[0])]
        ids += [hid(f"task-{i}", n[0]) for i in range(len(n[8]))]
    if len(ids) != len(set(ids)):
        raise ValueError("Generated IDs are not unique")

    core_items = set((ROOT.parent / "backups" / "mekanism-item-ids.txt").read_text(encoding="utf-8-sig").split())
    generator_items = set((ROOT.parent / "backups" / "mekanismgenerators-item-ids.txt").read_text(encoding="utf-8-sig").split())
    for node in NODES:
        for item_id, _count in [*node[8], node[10]]:
            namespace, name = item_id.split(":", 1)
            known = core_items if namespace == "mekanism" else generator_items
            if name not in known:
                raise ValueError(f"Unknown item {item_id} in quest {node[0]}")

    # FTB Quests draws straight dependency lines. Reject any line that runs through another node.
    by_key = {n[0]: n for n in NODES}
    collisions = []
    for node in NODES:
        bx, by = float(node[4]), float(node[5])
        for dep in node[9]:
            a = by_key[dep]
            ax, ay = float(a[4]), float(a[5])
            vx, vy = bx - ax, by - ay
            denom = vx * vx + vy * vy
            for other in NODES:
                if other[0] in (node[0], dep):
                    continue
                px, py = float(other[4]), float(other[5])
                t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / denom))
                distance = math.hypot(px - (ax + t * vx), py - (ay + t * vy))
                if 0.02 < t < 0.98 and distance < 0.80:
                    collisions.append((dep, node[0], other[0], round(distance, 2)))
    if collisions:
        raise ValueError(f"Dependency lines cross quest nodes: {collisions}")


def main() -> None:
    validate()
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "chapters").mkdir(parents=True)
    (OUT / "lang").mkdir(parents=True)

    data = '''{
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
'''
    groups = f'''{{
\tchapter_groups: [{{ icon: {{ id: "mekanism:metallurgic_infuser" }}, id: "{GROUP_ID}" }}]
}}
'''
    chapter = "\n".join([
        "{",
        "\tdefault_hide_dependency_lines: false",
        "\tdefault_quest_shape: \"circle\"",
        "\tfilename: \"mekanism\"",
        f"\tgroup: \"{GROUP_ID}\"",
        "\ticon: { id: \"mekanism:metallurgic_infuser\" }",
        f"\tid: \"{CHAPTER_ID}\"",
        "\torder_index: 0",
        "\tquest_links: [ ]",
        "\tquests: [",
        "\n".join(make_quest(n) for n in NODES),
        "\t]",
        "}",
        "",
    ])
    lang = build_lang()

    (OUT / "data.snbt").write_text(data, encoding="utf-8")
    (OUT / "chapter_groups.snbt").write_text(groups, encoding="utf-8")
    (OUT / "chapters" / "mekanism.snbt").write_text(chapter, encoding="utf-8")
    (OUT / "lang" / "ru_ru.snbt").write_text(lang, encoding="utf-8")
    (OUT / "lang" / "en_us.snbt").write_text(lang, encoding="utf-8")
    print(f"Generated {len(NODES)} quests in {OUT}")


if __name__ == "__main__":
    main()
