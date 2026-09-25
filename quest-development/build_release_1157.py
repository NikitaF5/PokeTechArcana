"""Build launcher overlay for the approved ATM-style quest layouts."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEST = ROOT / "quest-development"
PACK = ROOT / "skyblock-update" / "pack"
OUT = QUEST / "release-1.15.7"
PREVIOUS_MANIFEST = QUEST / "release-1.15.6" / "manifest.json"


def sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def add_tree(archive: zipfile.ZipFile, base: Path, roots: tuple[str, ...]) -> None:
    for name in roots:
        source = base / name
        if not source.exists():
            continue
        for path in sorted(source.rglob("*")):
            if path.is_file() and path.name not in {"options.txt", "servers.dat"} and not path.name.endswith(".tar.gz"):
                archive.write(path, path.relative_to(base).as_posix())


OUT.mkdir(parents=True, exist_ok=True)
configs = OUT / "configs.zip"
with zipfile.ZipFile(configs, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    add_tree(archive, PACK, ("config", "kubejs", "resourcepacks", "defaultconfigs"))

manifest = json.loads(PREVIOUS_MANIFEST.read_text("utf-8"))
manifest["pack_version"] = "1.15.7"
manifest["config_zip"] = {
    "url": "https://github.com/NikitaF5/PokeTechArcana/releases/download/pack-v1.15.7/configs.zip",
    "sha1": sha1(configs),
}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")
print(f"configs.zip {configs.stat().st_size} {sha1(configs)}")
print(f"manifest files {len(manifest['files'])}")
