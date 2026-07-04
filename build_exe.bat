@echo off
chcp 65001 >nul
echo === Сборка PokeTech Launcher в exe ===
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name PokeTechLauncher ^
  --collect-all customtkinter ^
  poketech_launcher.py
echo.
echo Готово: dist\PokeTechLauncher.exe
pause
