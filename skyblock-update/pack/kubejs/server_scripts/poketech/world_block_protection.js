// PokeTech Arcana — protection and resource rules for shared worlds.
// /is dimensions: normal building and drops.
// /hub: only operators (permission level 2+) may change blocks.
// Other dimensions: blocks may be broken, but never yield items or experience.

(function () {
  var settings = PT_CONFIG.blockProtection || {}
  var islandPrefix = String(settings.islandDimensionPrefix || 'ftbteambases:private_for_')
  var lobbyDimension = String(PT_CONFIG.lobbyDimension || 'ftbteambases:lobby')
  var messageCooldownMs = Number(settings.messageCooldownSeconds || 2) * 1000
  var lastMessageAt = {}

  function dimensionId(level) {
    try {
      return String(level.dimension().location())
    } catch (ignored) {
    }
    try {
      return String(level.dimension)
    } catch (e) {
      return ''
    }
  }

  function isIsland(level) {
    return dimensionId(level).indexOf(islandPrefix) === 0
  }

  function isLobby(level) {
    return dimensionId(level) === lobbyDimension
  }

  function isOperator(player) {
    try {
      return player != null && player.hasPermissions(2)
    } catch (e) {
      return false
    }
  }

  function warnHub(player) {
    if (player == null) return
    var name = String(player.getScoreboardName())
    var now = Date.now()
    if (!lastMessageAt[name] || now - lastMessageAt[name] >= messageCooldownMs) {
      lastMessageAt[name] = now
      player.setStatusMessage(Text.red('Hub защищён. Изменять блоки могут только операторы сервера.'))
    }
  }

  // BreakEvent is fired before the block changes and reliably restores the block
  // client-side when cancelled.
  NativeEvents.onEvent('HIGHEST', 'net.neoforged.neoforge.event.level.BlockEvent$BreakEvent', function (event) {
    try {
      var level = event.getLevel()
      var player = event.getPlayer()
      if (isLobby(level) && !isOperator(player)) {
        event.setCanceled(true)
        warnHub(player)
      }
    } catch (e) {
      console.warn('[world_block_protection] break: ' + e)
    }
  })

  // Covers regular placement and multi-block placement (doors, beds, etc.).
  NativeEvents.onEvent('HIGHEST', 'net.neoforged.neoforge.event.level.BlockEvent$EntityPlaceEvent', function (event) {
    try {
      var level = event.getLevel()
      var entity = event.getEntity()
      if (isLobby(level) && !isOperator(entity)) {
        event.setCanceled(true)
        warnHub(entity)
      }
    } catch (e) {
      console.warn('[world_block_protection] place: ' + e)
    }
  })

  // Axes, hoes and shovels modify blocks without placing or breaking them.
  NativeEvents.onEvent('HIGHEST', 'net.neoforged.neoforge.event.level.BlockEvent$BlockToolModificationEvent', function (event) {
    try {
      var level = event.getLevel()
      var player = event.getPlayer()
      if (isLobby(level) && !isOperator(player)) {
        event.setCanceled(true)
        warnHub(player)
      }
    } catch (e) {
      console.warn('[world_block_protection] tool modification: ' + e)
    }
  })

  // NeoForge calculates drops here, before spawning them. Cancelling suppresses
  // both item drops and experience while leaving the broken block removed.
  NativeEvents.onEvent('HIGHEST', 'net.neoforged.neoforge.event.level.BlockDropsEvent', function (event) {
    try {
      var level = event.getLevel()
      if (isIsland(level)) return

      // Outside /is nobody receives resources, including operators maintaining
      // the hub. Operators can break its blocks, but the blocks do not drop.
      event.setCanceled(true)
    } catch (e) {
      console.warn('[world_block_protection] drops: ' + e)
    }
  })

  // Explosions may still damage entities, but cannot grief shared worlds or
  // bypass the no-resource rule.
  NativeEvents.onEvent('NORMAL', 'net.neoforged.neoforge.event.level.ExplosionEvent$Detonate', function (event) {
    try {
      if (!isIsland(event.getLevel())) event.getAffectedBlocks().clear()
    } catch (e) {
      console.warn('[world_block_protection] explosion: ' + e)
    }
  })
})()
