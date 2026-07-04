@echo off
setlocal
echo === Build PokeTech Launcher EXE ===
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onefile --windowed --name PokeTechLauncher ^
  --collect-all customtkinter ^
  poketech_launcher.py
echo.
echo Done: dist\PokeTechLauncher.exe
