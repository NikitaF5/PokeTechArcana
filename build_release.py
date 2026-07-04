# -*- coding: utf-8 -*-
"""
build_release.py — публикатор сборки PokeTech Arcana на GitHub Releases.

Что делает:
 1. Сканирует папку сборки (mods/, config/, kubejs/, resourcepacks/).
 2. Считает SHA1 всех модов, пакует конфиги в configs.zip.
 3. Создаёт релиз в GitHub-репозитории и грузит:
      - только НОВЫЕ/ИЗМЕНЁННЫЕ jar'ы (неизменные переиспользуются из прошлого релиза)
      - configs.zip
      - manifest.json
 4. Лаунчер друзей всегда берёт manifest.json из releases/latest — обновление
    у них подхватится автоматически при следующем запуске.

Использование (PowerShell):
  $env:GITHUB_TOKEN = "ghp_..."     # токен с правом repo
  python build_release.py --pack-dir "C:\\путь\\к\\сборке" --tag pack-v1.0.1 ^
      --neoforge 21.1.77 --server play.myserver.ru:25565

Требования: pip install requests
"""
import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import requests

REPO = "NikitaF5/PokeTechArcana"     # <-- твой репозиторий
MINECRAFT_VERSION = "1.21.1"
CONFIG_FOLDERS = ["config", "kubejs", "resourcepacks", "defaultconfigs"]
CONFIG_EXCLUDE = {"options.txt", "servers.dat"}   # никогда не перетирать у игроков

API = "https://api.github.com"


def sha1_of(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gh(session, method, url, **kw):
    r = session.request(method, url, **kw)
    if r.status_code >= 300:
        sys.exit(f"GitHub API {method} {url} -> {r.status_code}: {r.text[:300]}")
    return r.json() if r.text else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack-dir", required=True, help="папка со сборкой (внутри mods/, config/ …)")
    ap.add_argument("--tag", required=True, help="тег релиза, например pack-v1.0.1")
    ap.add_argument("--neoforge", required=True, help="версия NeoForge, например 21.1.77")
    ap.add_argument("--server", default="", help="адрес сервера host:port (автоконнект)")
    ap.add_argument("--pack-version", default=None, help="версия сборки (по умолчанию = из тега)")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Задай переменную окружения GITHUB_TOKEN (токен с правом repo)")

    pack = Path(args.pack_dir)
    mods = sorted((pack / "mods").glob("*.jar"))
    if not mods:
        sys.exit(f"В {pack/'mods'} нет jar-файлов")
    print(f"Модов найдено: {len(mods)}")

    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}",
                      "Accept": "application/vnd.github+json"})

    # ---- прошлый манифест: переиспользуем URL неизменных файлов ----
    prev = {}
    try:
        r = s.get(f"{API}/repos/{REPO}/releases/latest", timeout=30)
        if r.status_code == 200:
            for a in r.json().get("assets", []):
                if a["name"] == "manifest.json":
                    mf = requests.get(a["browser_download_url"], timeout=30).json()
                    prev = {f["sha1"]: f["url"] for f in mf.get("files", [])}
                    print(f"Прошлый манифест: {len(prev)} файлов для переиспользования")
    except Exception as e:
        print(f"(прошлый манифест не получен: {e})")

    # ---- создаём релиз ----
    rel = gh(s, "POST", f"{API}/repos/{REPO}/releases", json={
        "tag_name": args.tag, "name": f"Pack {args.tag}",
        "body": "Автопубликация сборки PokeTech Arcana", "make_latest": "true"})
    upload_url = rel["upload_url"].split("{")[0]
    print(f"Релиз создан: {rel['html_url']}")

    def upload(path: Path, name=None) -> str:
        name = name or path.name
        # GitHub не любит спецсимволы в имени ассета
        safe = "".join(c if c.isalnum() or c in "._-" else "." for c in name)
        with open(path, "rb") as f:
            r = s.post(f"{upload_url}?name={safe}", data=f,
                       headers={"Content-Type": "application/octet-stream"}, timeout=600)
        if r.status_code >= 300:
            sys.exit(f"Ошибка загрузки {name}: {r.status_code} {r.text[:200]}")
        return r.json()["browser_download_url"]

    # ---- моды ----
    files = []
    uploaded = reused = 0
    for i, jar in enumerate(mods, 1):
        h = sha1_of(jar)
        if h in prev:
            url = prev[h]; reused += 1
        else:
            print(f"[{i}/{len(mods)}] upload {jar.name}")
            url = upload(jar); uploaded += 1
        files.append({"path": f"mods/{jar.name}", "sha1": h,
                      "size": jar.stat().st_size, "url": url})
    print(f"Модов: загружено {uploaded}, переиспользовано {reused}")

    # ---- configs.zip ----
    cz_path = Path("configs.zip")
    with zipfile.ZipFile(cz_path, "w", zipfile.ZIP_DEFLATED) as z:
        for folder in CONFIG_FOLDERS:
            src = pack / folder
            if not src.exists():
                continue
            for p in src.rglob("*"):
                if p.is_file() and p.name not in CONFIG_EXCLUDE:
                    z.write(p, p.relative_to(pack))
    cz_sha = sha1_of(cz_path)
    cz_url = upload(cz_path)
    print(f"configs.zip загружен ({cz_path.stat().st_size // 1024} KB)")

    # ---- manifest ----
    manifest = {
        "pack_name": "PokeTech Arcana",
        "pack_version": args.pack_version or args.tag.replace("pack-v", ""),
        "minecraft": MINECRAFT_VERSION,
        "neoforge": args.neoforge,
        "server_address": args.server,
        "java_args": ["-XX:+UseG1GC"],
        "files": files,
        "config_zip": {"url": cz_url, "sha1": cz_sha},
    }
    mpath = Path("manifest.json")
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), "utf-8")
    upload(mpath)
    print("\nГОТОВО. Лаунчеры подхватят обновление автоматически.")
    print(f"Manifest: https://github.com/{REPO}/releases/latest/download/manifest.json")


if __name__ == "__main__":
    main()
