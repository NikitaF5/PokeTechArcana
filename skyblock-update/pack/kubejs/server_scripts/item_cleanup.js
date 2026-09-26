const CLEANUP_INTERVAL_MINUTES = 15
const CLEANUP_INTERVAL_TICKS = CLEANUP_INTERVAL_MINUTES * 60 * 20
const ONE_MINUTE_TICKS = 60 * 20
const TEN_SECONDS_TICKS = 10 * 20

let ticksUntilCleanup = CLEANUP_INTERVAL_TICKS

function dimensionId(level) {
  return String(level.dimension().location())
}

function clearDroppedItems(server) {
  let removed = 0
  let worlds = 0

  server.getAllLevels().forEach(level => {
    const dimension = dimensionId(level)
    removed += Number(server.runCommandSilent(
      `execute in ${dimension} run kill @e[type=minecraft:item]`
    ))
    worlds++
  })

  console.info(
    `[item_cleanup] Removed ${removed} dropped item entities in ${worlds} loaded worlds`
  )
}

console.info(
  `[item_cleanup] Ground loot cleanup is scheduled every ${CLEANUP_INTERVAL_MINUTES} minutes in every world`
)

ServerEvents.tick(event => {
  ticksUntilCleanup--

  if (ticksUntilCleanup === ONE_MINUTE_TICKS) {
    event.server.runCommandSilent(
      'tellraw @a {"text":"[Очистка] Предметы на земле будут удалены через 1 минуту.","color":"gold"}'
    )
  } else if (ticksUntilCleanup === TEN_SECONDS_TICKS) {
    event.server.runCommandSilent(
      'tellraw @a {"text":"[Очистка] Предметы на земле будут удалены через 10 секунд.","color":"red"}'
    )
  }

  if (ticksUntilCleanup > 0) {
    return
  }

  ticksUntilCleanup = CLEANUP_INTERVAL_TICKS
  clearDroppedItems(event.server)
})
