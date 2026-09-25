// priority: 900
// PokeTech Arcana — настройки серверных скриптов. Этот файл правится вручную.
// Списки измерений берутся из 00_pokeworld_ids.js (его пишет генератор pokeworld-gen).

var PT_CONFIG = {
  // Измерение хаба (FTB Team Bases, lobby_dimension)
  lobbyDimension: 'ftbteambases:lobby',
  lobbySpawn: { x: -185, y: -9, z: 270 },

  pokeworldDimensions: (typeof PT_GENERATED !== 'undefined')
    ? PT_GENERATED.pokeworldDimensions
    : ['pokeworld:pokeworld', 'pokeworld:pokeworld_nether', 'pokeworld:pokeworld_end'],

  // Где разрешён естественный спавн диких покемонов (страховка к правилу спавна Cobblemon)
  cobblemonSpawnDimensions: (typeof PT_GENERATED !== 'undefined')
    ? PT_GENERATED.cobblemonSpawnDimensions
    : ['pokeworld:pokeworld', 'pokeworld:pokeworld_nether', 'pokeworld:pokeworld_end',
       'cobblemonraiddens:raid_dimension', 'cobblemonnestsdens:den_dimension'],

  bell: {
    // Колокол тренеров в Port Norhaven.
    dimension: 'ftbteambases:lobby',
    x: -179, y: -7, z: 216,
    // Проверенная свободная точка в четырёх блоках восточнее колокола.
    // Y=-7 — уровень пола/ног игрока. Y=-6 ставил NPC на блок выше,
    // и высокие модели тренеров оказывались внутри декора/перекрытия.
    summon: { x: -175, y: -7, z: 216, spread: 0 },
    cooldownSeconds: 1200,        // перезарядка колокола для одного игрока
    trainerLifetimeSeconds: 300,  // через сколько убрать тренера, если бой не начат
    searchRadius: 6               // радиус поиска призванного тренера вокруг точки
  },

  // На /is блоки работают обычно. В других мирах блоки ломаются без добычи.
  // В хабе изменять блоки могут только игроки с правами оператора (уровень 2+).
  blockProtection: {
    islandDimensionPrefix: 'ftbteambases:private_for_',
    messageCooldownSeconds: 2
  },

  heal: {
    command: 'pheal',
    cooldownSeconds: 300
  },

  // Поправки к FTB Team Bases (см. team_bases_fixes.js)
  teamBasesFixes: {
    keepBedRespawn: true,       // с кроватью возрождаться у кровати, без неё — в хабе
    keepOverworldPortals: true  // портал Незер -> верхний мир не уводит на остров, если вход был из верхнего мира
  },

  // Короткие команды-обёртки: имя -> команда Team Bases (выполняется от имени игрока)
  aliases: {
    hub: 'ftbteambases lobby',
    lobby: 'ftbteambases lobby',
    is: 'ftbteambases create poketech:island',
    island: 'ftbteambases create poketech:island',
    home: 'ftbteambases home',
    base: 'ftbteambases home'
  }
}
