"""Quest data for the Create and automated Poké Ball production chapter."""


def n(key, title, phase, desc, px, py, shape, size, task, deps, reward, xp, tag, icon=None):
    x = round((px - 70) * 0.035, 2)
    y = round((py - 350) * 0.035, 2)
    tasks = task if isinstance(task, tuple) and task and isinstance(task[0], tuple) else (task,)
    return key, title, phase, desc, x, y, shape, size, tuple(tasks), tuple(deps), reward, xp, tag, icon


NODES = [
    # Main path: left to right.
    n("rotation", "Первое вращение", "I · КИНЕТИКА", "Запусти устойчивый источник кинетической энергии. Водяное колесо станет сердцем первой мастерской.", 70, 365, "diamond", 1.6, ("create:water_wheel", 1), (), ("create:shaft", 8), 2, "pta_main"),
    n("shafts", "Линия валов", "I · КИНЕТИКА", "Передай вращение валами и подготовь место для нескольких независимых механизмов.", 160, 350, "circle", 1.15, ("create:shaft", 8), ("rotation",), ("create:cogwheel", 4), 2, "pta_main"),
    n("stress", "Контроль нагрузки", "I · КИНЕТИКА", "Измерь скорость и нагрузку сети. Перегруженная линия остановит всю фабрику.", 250, 330, "circle", 1.15, ("create:stressometer", 1), ("shafts",), ("create:goggles", 1), 3, "pta_main"),
    n("andesite", "Андезитовый сплав", "II · МЕХАНИЗМЫ", "Получи основной сплав Create и заверши учебную ветку управления вращением.", 340, 350, "hexagon", 1.4, ("create:andesite_alloy", 16), ("stress", "speed_controller"), ("create:andesite_alloy", 8), 4, "pta_main"),
    n("casing", "Корпус механизма", "II · МЕХАНИЗМЫ", "Собери андезитовые корпуса для прессов, смесителей и логистических блоков.", 430, 330, "circle", 1.15, ("create:andesite_casing", 8), ("andesite",), ("create:andesite_alloy", 8), 4, "pta_main"),
    n("press", "Механический пресс", "II · МЕХАНИЗМЫ", "Пресс формует металлические листы, основания и верхние полусферы покеболов.", 520, 350, "square", 1.35, ("create:mechanical_press", 1), ("casing",), ("create:depot", 1), 5, "pta_main"),
    n("mixer", "Смеситель и чан", "II · МЕХАНИЗМЫ", "Собери смеситель над чаном. Эта пара открывает смешивание и компактирование.", 610, 330, "square", 1.35, (("create:mechanical_mixer", 1), ("create:basin", 1)), ("press",), ("create:whisk", 1), 5, "pta_main"),
    n("belt", "Конвейерная линия", "III · КОНВЕЙЕР", "Соедини обработку лентами после завершения ветки дробления и фильтрации.", 700, 350, "hexagon", 1.4, ("create:belt_connector", 8), ("mixer", "crushing_wheels"), ("create:andesite_funnel", 4), 6, "pta_main"),
    n("apricorns", "Поток априкорнов", "IV · ДЕТАЛИ ШАРА", "Подготовь крупный запас красных и синих априкорнов для двух первых серий.", 790, 330, "circle", 1.2, (("cobblemon:red_apricorn", 32), ("cobblemon:blue_apricorn", 32)), ("belt",), ("minecraft:bone_meal", 16), 6, "pta_main"),
    n("ball_parts", "Две половины", "IV · ДЕТАЛИ ШАРА", "Сформуй базовое дно и цветную верхнюю часть. Две линии должны сходиться без заторов.", 880, 350, "circle", 1.2, (("createcobblemonintegrations:pokeball_bottom", 16), ("createcobblemonintegrations:pokeball_top", 16)), ("apricorns",), ("create:brass_funnel", 2), 7, "pta_main", "cobblemon:poke_ball"),
    n("deployer", "Механическая сборка", "V · СБОРКА", "Размещатель соединяет подготовленные половины в готовый Poké Ball.", 970, 330, "square", 1.45, ("create:deployer", 1), ("ball_parts", "parts_routing"), ("cobblemon:poke_ball", 16), 8, "pta_main"),
    n("special_series", "Особые серии", "VI · ОСОБЫЕ СЕРИИ", "Объедини нагрев, улучшенные основания и специальные листы в единый каталог шаров.", 1060, 350, "octagon", 1.5, ("cobblemon:ultra_ball", 16), ("deployer", "master_ball"), ("cobblemon:quick_ball", 8), 10, "pta_transition"),
    n("auto_factory", "Автоматическая фабрика", "VII · ФАБРИКА", "Финал главы: сырьё автоматически поступает на обработку, а готовые покеболы сортируются по складам.", 1170, 330, "diamond", 1.8, (("cobblemon:poke_ball", 256), ("create:item_vault", 3)), ("special_series", "medical_center", "mechanical_arm"), ("cobblemon:ultra_ball", 32), 16, "pta_transition"),

    # Kinetic branch.
    n("small_cog", "Малая шестерня", "I · КИНЕТИКА", "Освой компактную передачу вращения между соседними валами.", 120, 245, "octagon", 1.0, ("create:cogwheel", 8), ("rotation",), ("create:shaft", 8), 2, "pta_resource"),
    n("large_cog", "Большая шестерня", "I · КИНЕТИКА", "Используй большие шестерни для изменения скорости механизма.", 165, 185, "octagon", 1.0, ("create:large_cogwheel", 4), ("small_cog",), ("create:cogwheel", 4), 2, "pta_resource"),
    n("gearbox", "Редуктор", "I · КИНЕТИКА", "Разведи вращение по нескольким направлениям без громоздкой передачи.", 220, 145, "octagon", 1.0, ("create:gearbox", 2), ("large_cog",), ("create:vertical_gearbox", 1), 3, "pta_resource"),
    n("chain_drive", "Цепной привод", "I · КИНЕТИКА", "Передай одинаковую скорость группе механизмов на разных уровнях.", 275, 165, "octagon", 1.0, ("create:encased_chain_drive", 8), ("gearbox",), ("create:shaft", 8), 3, "pta_resource"),
    n("clutch", "Сцепление", "I · КИНЕТИКА", "Добавь возможность отключать отдельную секцию фабрики сигналом редстоуна.", 315, 220, "octagon", 1.0, ("create:clutch", 1), ("chain_drive",), ("minecraft:redstone", 8), 3, "pta_resource"),
    n("speed_controller", "Регулятор скорости", "I · КИНЕТИКА", "Управляй скоростью машин без полной перестройки зубчатой передачи.", 330, 285, "octagon", 1.05, ("create:rotation_speed_controller", 1), ("clutch",), ("create:precision_mechanism", 1), 5, "pta_resource"),

    # Processing branch.
    n("depot", "Депо", "II · МЕХАНИЗМЫ", "Останови предмет в точке обработки под прессом или размещателем.", 370, 455, "octagon", 1.0, ("create:depot", 2), ("andesite",), ("create:andesite_funnel", 2), 2, "pta_resource"),
    n("funnel", "Направленная подача", "III · КОНВЕЙЕР", "Управляй входом и выходом предметов при помощи воронок Create.", 425, 505, "octagon", 1.0, ("create:andesite_funnel", 4), ("depot",), ("create:filter", 1), 3, "pta_resource"),
    n("filter", "Фильтры", "III · КОНВЕЙЕР", "Раздели сырьё, полуфабрикаты и готовые предметы по назначению.", 490, 545, "octagon", 1.0, ("create:filter", 2), ("funnel",), ("create:attribute_filter", 1), 3, "pta_resource"),
    n("basin", "Производственный чан", "II · МЕХАНИЗМЫ", "Подготовь отдельный чан для рецептов априкорнов и лекарств.", 555, 535, "octagon", 1.0, ("create:basin", 2), ("filter",), ("create:fluid_tank", 2), 3, "pta_resource"),
    n("millstone", "Жернова", "II · МЕХАНИЗМЫ", "Автоматизируй измельчение ягод, трав и вторичного сырья Cobblemon.", 620, 495, "octagon", 1.0, ("create:millstone", 1), ("basin",), ("create:andesite_alloy", 4), 4, "pta_resource"),
    n("crushing_wheels", "Дробительные колёса", "II · МЕХАНИЗМЫ", "Построй участок массовой переработки и подключи его к общей конвейерной линии.", 675, 435, "octagon", 1.05, ("create:crushing_wheel", 2), ("millstone",), ("create:belt_connector", 4), 5, "pta_resource"),

    # Poké Ball component branch.
    n("apricorn_farm", "Ферма априкорнов", "IV · ДЕТАЛИ ШАРА", "Создай возобновляемую ферму и автоматический сбор цветных априкорнов.", 705, 245, "octagon", 1.05, (("cobblemon:red_apricorn", 64), ("cobblemon:blue_apricorn", 64)), ("belt",), ("minecraft:bone_meal", 32), 4, "pta_resource"),
    n("compacting", "Компактирование", "IV · ДЕТАЛИ ШАРА", "Спрессуй четыре априкорна в цветные листы по рецептам интеграции Create.", 735, 175, "octagon", 1.0, ("createcobblemonintegrations:red_apricorn_sheet", 24), ("apricorn_farm",), ("createcobblemonintegrations:blue_apricorn_sheet", 12), 5, "pta_auto"),
    n("red_sheet", "Красный лист", "IV · ДЕТАЛИ ШАРА", "Подготовь серийный материал для верхней части базового Poké Ball.", 780, 115, "octagon", 1.0, ("createcobblemonintegrations:red_apricorn_sheet", 48), ("compacting",), ("cobblemon:red_apricorn", 16), 5, "pta_auto"),
    n("copper_sheet", "Медный лист", "IV · ДЕТАЛИ ШАРА", "Прокатай медь в листы для нижних заготовок базового уровня.", 835, 95, "octagon", 1.0, ("create:copper_sheet", 16), ("red_sheet",), ("minecraft:copper_ingot", 8), 5, "pta_auto"),
    n("cutting_blank", "Распил заготовок", "IV · ДЕТАЛИ ШАРА", "Распили медный лист: один лист даёт шесть базовых заготовок основания.", 890, 120, "octagon", 1.0, ("createcobblemonintegrations:basic_bottom_blank", 24), ("copper_sheet",), ("create:copper_sheet", 4), 5, "pta_auto"),
    n("ball_bottom", "Базовое дно", "IV · ДЕТАЛИ ШАРА", "Спрессуй плоские заготовки в готовые нижние части шара.", 925, 175, "octagon", 1.0, ("createcobblemonintegrations:pokeball_bottom", 24), ("cutting_blank",), ("create:andesite_funnel", 2), 6, "pta_auto"),
    n("ball_top", "Красный верх", "IV · ДЕТАЛИ ШАРА", "Спрессуй красные листы в верхние полусферы Poké Ball.", 945, 235, "octagon", 1.0, ("createcobblemonintegrations:pokeball_top", 24), ("red_sheet",), ("create:depot", 1), 6, "pta_auto"),
    n("parts_routing", "Сведение потоков", "IV · ДЕТАЛИ ШАРА", "Подай верх и дно к одному размещателю с разных направлений без смешивания предметов.", 965, 285, "octagon", 1.05, (("create:brass_funnel", 2), ("create:filter", 2)), ("ball_bottom", "ball_top"), ("create:deployer", 1), 7, "pta_auto"),

    # Special Poké Ball branch.
    n("heated", "Управляемый нагрев", "VI · ОСОБЫЕ СЕРИИ", "Разожги горелку под чаном и открой рецепты усиленных цветных листов.", 775, 450, "circle", 1.05, ("create:blaze_burner", 1), ("deployer",), ("minecraft:blaze_rod", 4), 6, "pta_danger"),
    n("reinforced_bottom", "Усиленное дно", "VI · ОСОБЫЕ СЕРИИ", "Сформуй основания для Great, Heavy, Fast и других усиленных серий.", 810, 520, "circle", 1.0, ("createcobblemonintegrations:reinforced_ball_bottom", 16), ("heated",), ("create:iron_sheet", 8), 7, "pta_danger"),
    n("great_ball", "Серия Great Ball", "VI · ОСОБЫЕ СЕРИИ", "Смешай красные и синие априкорны с нагревом и запусти первую усиленную серию.", 860, 575, "circle", 1.0, ("cobblemon:great_ball", 32), ("reinforced_bottom",), ("cobblemon:great_ball", 8), 8, "pta_danger"),
    n("advanced_bottom", "Продвинутое дно", "VI · ОСОБЫЕ СЕРИИ", "Подготовь более прочное основание для Ultra, Dusk и Luxury Ball.", 915, 605, "circle", 1.0, ("createcobblemonintegrations:advanced_ball_bottom", 16), ("great_ball",), ("create:golden_sheet", 4), 8, "pta_danger"),
    n("ultra_ball", "Серия Ultra Ball", "VI · ОСОБЫЕ СЕРИИ", "Настрой стабильное производство Ultra Ball с отдельными входами сырья.", 965, 575, "circle", 1.05, ("cobblemon:ultra_ball", 32), ("advanced_bottom",), ("cobblemon:ultra_ball", 8), 9, "pta_danger"),
    n("precision_bottom", "Точное дно", "VI · ОСОБЫЕ СЕРИИ", "Сформуй точные основания для Beast, Dream и других редких шаров.", 995, 515, "circle", 1.0, ("createcobblemonintegrations:precision_ball_bottom", 8), ("ultra_ball",), ("create:precision_mechanism", 1), 10, "pta_danger"),
    n("master_ball", "Мастерская Master Ball", "VI · ОСОБЫЕ СЕРИИ", "Создай демонстрационный участок сверхнагретого компактирования и собери Master Ball.", 1010, 440, "circle", 1.2, ("cobblemon:master_ball", 1), ("precision_bottom",), ("minecraft:netherite_ingot", 1), 12, "pta_danger"),

    # Pokémon chemistry branch.
    n("medicine_mix", "Рецептуры лекарств", "VII · ФАБРИКА", "Используй механический смеситель для массового приготовления лекарств Cobblemon.", 1005, 235, "square", 1.0, ("cobblemon:potion", 16), ("special_series",), ("cobblemon:super_potion", 4), 6, "pta_auto"),
    n("medicine_fluids", "Жидкие лекарства", "VII · ФАБРИКА", "Организуй резервуар и трубопровод для лечебных жидкостей.", 1045, 175, "square", 1.0, ("create:fluid_tank", 4), ("medicine_mix",), ("create:fluid_pipe", 8), 6, "pta_auto"),
    n("spout", "Разливочный носик", "VII · ФАБРИКА", "Автоматически наполняй бутылки и контейнеры через разливочный носик.", 1090, 140, "square", 1.0, ("create:spout", 1), ("medicine_fluids",), ("minecraft:glass_bottle", 16), 7, "pta_auto"),
    n("bottle_feed", "Автоподача тары", "VII · ФАБРИКА", "Подай пустые бутылки и выведи готовые лекарства отдельной конвейерной веткой.", 1135, 175, "square", 1.0, (("minecraft:glass_bottle", 32), ("create:andesite_funnel", 2)), ("spout",), ("create:belt_connector", 4), 7, "pta_auto"),
    n("medical_center", "Автоматический медцентр", "VII · ФАБРИКА", "Объедини смешивание, хранение жидкости и розлив в непрерывную линию лечения покемонов.", 1160, 235, "square", 1.15, (("cobblemon:super_potion", 32), ("cobblemon:full_restore", 8)), ("bottle_feed",), ("cobblemon:max_potion", 4), 10, "pta_auto"),

    # Factory logistics branch.
    n("brass", "Латунная эпоха", "VII · ФАБРИКА", "Создай латунь и открой точную фильтрацию сложной фабрики.", 1100, 445, "hexagon", 1.0, ("create:brass_ingot", 16), ("special_series",), ("create:brass_casing", 4), 7, "pta_resource"),
    n("smart_chute", "Умная воронка", "VII · ФАБРИКА", "Фильтруй разные типы покеболов до попадания на склад.", 1130, 505, "hexagon", 1.0, ("create:smart_chute", 2), ("brass",), ("create:brass_funnel", 2), 7, "pta_auto"),
    n("vault", "Буферный склад", "VII · ФАБРИКА", "Собери общее хранилище сырья, деталей и готовой продукции.", 1160, 570, "hexagon", 1.0, ("create:item_vault", 3), ("smart_chute",), ("create:item_vault", 1), 8, "pta_auto"),
    n("stockpile", "Контроль запаса", "VII · ФАБРИКА", "Останавливай отдельные линии, когда соответствующий склад заполнен.", 1200, 525, "hexagon", 1.0, ("create:stockpile_switch", 2), ("vault",), ("create:content_observer", 1), 8, "pta_auto"),
    n("mechanical_arm", "Механическая рука", "VII · ФАБРИКА", "Свяжи удалённые участки фабрики и распределяй предметы между несколькими выходами.", 1205, 440, "hexagon", 1.15, ("create:mechanical_arm", 1), ("stockpile",), ("create:precision_mechanism", 2), 10, "pta_auto"),
]
