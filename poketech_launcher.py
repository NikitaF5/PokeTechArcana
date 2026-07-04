# -*- coding: utf-8 -*-
"""
PokeTech Arcana Launcher
========================
Кастомный лаунчер для приватного сервера: сам ставит Minecraft 1.21.1 + NeoForge,
синхронизирует моды/конфиги с GitHub Releases и запускает игру.

Автор сборки: Obeziana. Сгенерировано при помощи Claude.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import traceback
import uuid as uuid_mod
import zipfile
from pathlib import Path

import requests
import customtkinter as ctk
import minecraft_launcher_lib as mll

# ============================ НАСТРОЙКИ ПАКА ============================
PACK_NAME = "PokeTech Arcana"
GITHUB_REPO = "NikitaF5/PokeTechArcana"          # <-- твой репозиторий с релизами
MANIFEST_URL = f"https://github.com/{GITHUB_REPO}/releases/latest/download/manifest.json"
ACCENT = "#ef5350"        # красный покебола
ACCENT_HOVER = "#c62828"
BG_DARK = "#101622"
# =======================================================================

APPDATA = Path(os.environ.get("APPDATA", Path.home()))
GAME_DIR = APPDATA / "PokeTechArcana"
LAUNCHER_DIR = APPDATA / "PokeTechLauncher"
SETTINGS_FILE = LAUNCHER_DIR / "settings.json"
LOCAL_MODS_DIR = GAME_DIR / "localmods"   # моды игрока, не трогаем при синке


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def offline_uuid(name: str) -> str:
    """UUID оффлайн-игрока — как в ванильном сервере (md5 от OfflinePlayer:<ник>)."""
    digest = hashlib.md5(f"OfflinePlayer:{name}".encode("utf-8")).digest()
    b = bytearray(digest)
    b[6] = (b[6] & 0x0F) | 0x30   # version 3
    b[8] = (b[8] & 0x3F) | 0x80   # variant
    return str(uuid_mod.UUID(bytes=bytes(b)))


class Launcher(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(f"{PACK_NAME} — Launcher")
        self.geometry("640x520")
        self.minsize(560, 480)
        self.configure(fg_color=BG_DARK)

        self.settings = self._load_settings()
        self.busy = False

        # ---------- UI ----------
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=24, pady=(22, 6))
        ctk.CTkLabel(head, text=PACK_NAME, font=("Segoe UI", 30, "bold"),
                     text_color=ACCENT).pack(anchor="w")
        self.sub_label = ctk.CTkLabel(head, text="Проверка обновлений…",
                                      font=("Segoe UI", 13), text_color="#8fa0b3")
        self.sub_label.pack(anchor="w")

        form = ctk.CTkFrame(self, fg_color="#171f2e", corner_radius=14)
        form.pack(fill="x", padx=24, pady=12)

        ctk.CTkLabel(form, text="Ник", font=("Segoe UI", 13)).grid(
            row=0, column=0, sticky="w", padx=(18, 8), pady=(16, 4))
        self.nick_entry = ctk.CTkEntry(form, width=220, placeholder_text="Steve")
        self.nick_entry.grid(row=0, column=1, sticky="w", pady=(16, 4))
        self.nick_entry.insert(0, self.settings.get("nickname", ""))

        ctk.CTkLabel(form, text="Память (ГБ)", font=("Segoe UI", 13)).grid(
            row=1, column=0, sticky="w", padx=(18, 8), pady=4)
        self.ram_slider = ctk.CTkSlider(form, from_=4, to=16, number_of_steps=12,
                                        width=220, command=self._on_ram)
        self.ram_slider.grid(row=1, column=1, sticky="w", pady=4)
        self.ram_slider.set(self.settings.get("ram_gb", 8))
        self.ram_label = ctk.CTkLabel(form, text="", font=("Segoe UI", 12))
        self.ram_label.grid(row=1, column=2, sticky="w", padx=8)
        self._on_ram(self.ram_slider.get())

        form.grid_columnconfigure(3, weight=1)

        self.play_btn = ctk.CTkButton(
            self, text="ИГРАТЬ", height=52, corner_radius=14,
            font=("Segoe UI", 20, "bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            command=self._on_play)
        self.play_btn.pack(fill="x", padx=24, pady=(6, 4))

        self.progress = ctk.CTkProgressBar(self, height=10, corner_radius=6,
                                           progress_color=ACCENT)
        self.progress.pack(fill="x", padx=24, pady=(6, 2))
        self.progress.set(0)

        self.status = ctk.CTkLabel(self, text="Готов", font=("Segoe UI", 12),
                                   text_color="#8fa0b3")
        self.status.pack(anchor="w", padx=26)

        self.log_box = ctk.CTkTextbox(self, fg_color="#0b0f18", corner_radius=12,
                                      font=("Consolas", 11))
        self.log_box.pack(fill="both", expand=True, padx=24, pady=(8, 20))
        self.log_box.configure(state="disabled")

        self.manifest = None
        threading.Thread(target=self._fetch_manifest, daemon=True).start()

    # ---------------- helpers ----------------
    def _load_settings(self):
        try:
            return json.loads(SETTINGS_FILE.read_text("utf-8"))
        except Exception:
            return {}

    def _save_settings(self):
        LAUNCHER_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), "utf-8")

    def _on_ram(self, v):
        self.ram_label.configure(text=f"{int(v)} ГБ")

    def log(self, msg):
        def _do():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _do)

    def set_status(self, text, prog=None):
        def _do():
            self.status.configure(text=text)
            if prog is not None:
                self.progress.set(prog)
        self.after(0, _do)

    # ---------------- manifest ----------------
    def _fetch_manifest(self):
        try:
            r = requests.get(MANIFEST_URL, timeout=20)
            r.raise_for_status()
            self.manifest = r.json()
            v = self.manifest.get("pack_version", "?")
            n = len(self.manifest.get("files", []))
            self.after(0, lambda: self.sub_label.configure(
                text=f"Сборка v{v} · {n} файлов · MC {self.manifest.get('minecraft')} · NeoForge {self.manifest.get('neoforge')}"))
            self.log(f"Манифест получен: v{v}, {n} файлов")
        except Exception as e:
            self.after(0, lambda: self.sub_label.configure(
                text="Не удалось получить манифест — проверь интернет"))
            self.log(f"[!] Ошибка манифеста: {e}")

    # ---------------- play ----------------
    def _on_play(self):
        if self.busy:
            return
        nick = self.nick_entry.get().strip()
        if not nick or len(nick) < 3:
            self.set_status("Введи ник (3+ символа)")
            return
        if self.manifest is None:
            self.set_status("Манифест ещё не загружен — подожди пару секунд")
            return
        self.settings["nickname"] = nick
        self.settings["ram_gb"] = int(self.ram_slider.get())
        self._save_settings()
        self.busy = True
        self.play_btn.configure(state="disabled", text="ЗАПУСК…")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            self._ensure_game()
            self._sync_files()
            self._launch()
        except Exception as e:
            self.log("[!] " + "".join(traceback.format_exception_only(type(e), e)).strip())
            self.set_status("Ошибка — смотри лог", 0)
        finally:
            self.busy = False
            self.after(0, lambda: self.play_btn.configure(state="normal", text="ИГРАТЬ"))

    # ---------------- install ----------------
    def _mll_callback(self):
        state = {"max": 1}
        def set_max(v): state["max"] = max(v, 1)
        def set_prog(v): self.set_status(self.status.cget("text"), v / state["max"])
        def set_stat(s): self.set_status(s)
        return {"setStatus": set_stat, "setProgress": set_prog, "setMax": set_max}

    def _ensure_game(self):
        GAME_DIR.mkdir(parents=True, exist_ok=True)
        mc_ver = self.manifest["minecraft"]
        nf_ver = self.manifest.get("neoforge")

        self.set_status(f"Проверка Minecraft {mc_ver}…", 0.02)
        installed = [v["id"] for v in mll.utils.get_installed_versions(str(GAME_DIR))]

        nf = mll.mod_loader.get_mod_loader("neoforge")
        want_id = nf.get_installed_version(mc_ver, nf_ver) if nf_ver else None

        if want_id and want_id in installed:
            self.log(f"NeoForge {nf_ver} уже установлен ({want_id})")
            self.version_id = want_id
            return

        self.set_status(f"Установка Minecraft {mc_ver} (ванилла)…", 0.05)
        self.log("Скачиваю ваниллу и JVM — при первом запуске это несколько минут")
        mll.install.install_minecraft_version(mc_ver, str(GAME_DIR),
                                              callback=self._mll_callback())

        self.set_status(f"Установка NeoForge {nf_ver}…", 0.35)
        self.version_id = nf.install(mc_ver, str(GAME_DIR),
                                     loader_version=nf_ver,
                                     callback=self._mll_callback())
        self.log(f"NeoForge установлен: {self.version_id}")

    # ---------------- sync ----------------
    def _sync_files(self):
        files = self.manifest.get("files", [])
        mods_dir = GAME_DIR / "mods"
        mods_dir.mkdir(exist_ok=True)
        LOCAL_MODS_DIR.mkdir(exist_ok=True)

        # 1. Индекс нужных файлов
        wanted = {}
        for f in files:
            rel = f["path"].replace("\\", "/")
            wanted[rel] = f

        # 2. Удаляем лишние jar'ы из mods (кроме локальных)
        manifest_mod_names = {Path(p).name for p in wanted if p.startswith("mods/")}
        removed = 0
        for jar in mods_dir.glob("*.jar"):
            if jar.name not in manifest_mod_names:
                jar.unlink()
                removed += 1
        if removed:
            self.log(f"Удалено устаревших модов: {removed}")

        # 3. Качаем недостающее/изменённое
        todo = []
        for rel, f in wanted.items():
            local = GAME_DIR / rel
            if not local.exists() or sha1_of(local) != f["sha1"]:
                todo.append((rel, f))
        self.log(f"К загрузке: {len(todo)} файлов")

        for i, (rel, f) in enumerate(todo, 1):
            local = GAME_DIR / rel
            local.parent.mkdir(parents=True, exist_ok=True)
            self.set_status(f"Загрузка {i}/{len(todo)}: {Path(rel).name}",
                            0.4 + 0.5 * i / max(len(todo), 1))
            with requests.get(f["url"], stream=True, timeout=120) as r:
                r.raise_for_status()
                tmp = local.with_suffix(local.suffix + ".part")
                with open(tmp, "wb") as out:
                    for chunk in r.iter_content(1 << 20):
                        out.write(chunk)
                tmp.replace(local)

        # 4. Конфиг-архив (config/, kubejs/, resourcepacks/) — по хэшу
        cz = self.manifest.get("config_zip")
        if cz:
            marker = GAME_DIR / ".config_zip_sha1"
            cur = marker.read_text().strip() if marker.exists() else ""
            if cur != cz["sha1"]:
                self.set_status("Обновление конфигов…", 0.93)
                zpath = GAME_DIR / "configs_update.zip"
                with requests.get(cz["url"], stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(zpath, "wb") as out:
                        for chunk in r.iter_content(1 << 20):
                            out.write(chunk)
                with zipfile.ZipFile(zpath) as z:
                    z.extractall(GAME_DIR)
                zpath.unlink()
                marker.write_text(cz["sha1"])
                self.log("Конфиги обновлены")

        # 5. Подмешиваем локальные моды игрока
        for jar in LOCAL_MODS_DIR.glob("*.jar"):
            dst = mods_dir / jar.name
            if not dst.exists():
                shutil.copy2(jar, dst)

        self.set_status("Файлы синхронизированы", 0.96)

    # ---------------- launch ----------------
    def _launch(self):
        nick = self.settings["nickname"]
        ram = self.settings.get("ram_gb", 8)
        options = {
            "username": nick,
            "uuid": offline_uuid(nick),
            "token": "0",
            "jvmArguments": [f"-Xmx{ram}G", "-Xms2G"] + self.manifest.get("java_args", []),
            "launcherName": "PokeTechLauncher",
            "launcherVersion": "1.0",
        }
        srv = self.manifest.get("server_address")
        if srv and ":" in srv:
            host, port = srv.rsplit(":", 1)
            options["server"] = host
            options["port"] = port
        elif srv:
            options["server"] = srv

        cmd = mll.command.get_minecraft_command(self.version_id, str(GAME_DIR), options)
        self.set_status("Игра запускается…", 1.0)
        self.log("Запуск: " + " ".join(cmd[:3]) + " …")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        subprocess.Popen(cmd, cwd=str(GAME_DIR), creationflags=flags)
        self.after(4000, self.iconify)


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()
