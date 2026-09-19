# PokeTech Arcana 1.2.0 — безопасное обновление клиента

Этот набор обновляет механизм синхронизации лаунчера для Cobblemon 1.8.

- `poketech_launcher.py` больше не очищает `mods/` по манифесту.
- Новый JAR сначала скачивается во временный файл и проверяется по SHA-1.
- Удаляется только точная прежняя версия из `replacements.json`, и только после успешной проверки её замены.
- Неизвестные моды и содержимое `localmods/` остаются на компьютере игрока.
- `client-exclude.json` не допускает в клиентский релиз серверные Chunky, ChunkyBorder, FTB Essentials и LuckPerms.

## Публикация `pack-v1.2.0`

Нужны Python 3.11+ и токен GitHub с доступом на запись в `NikitaF5/PokeTechArcana`.

```powershell
$env:GITHUB_TOKEN = "<GitHub token>"
python publish_overlay_release.py `
  --baseline "C:\path\to\manifest-1.1.4.json" `
  --mods-dir "C:\path\to\PokeTech Arcana 2\staging\mods" `
  --tag pack-v1.2.0 `
  --server "<CURRENT_SERVER_HOST:PORT>" `
  --neoforge 21.1.234
```

Download the current baseline manifest before the command:
`https://github.com/NikitaF5/PokeTechArcana/releases/latest/download/manifest.json`.

The command publishes a new GitHub Release; it does not alter or delete old releases or their assets. After publishing, rebuild `PokeTechLauncher.exe` from the included `poketech_launcher.py` and distribute that new EXE before using the new manifest. Older EXEs still contain the previous sweeping cleanup behaviour.
