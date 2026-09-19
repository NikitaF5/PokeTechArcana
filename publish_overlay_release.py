"""Publish a non-destructive PokeTech Arcana client update.

The old pack manifest is kept as the base.  Only verified jars in --mods-dir
are added or updated.  GitHub release assets are never deleted.  A replacement
is removed from a player's mods directory only when it is named explicitly in
replacements.json and the new jar has passed SHA-1 validation in the launcher.
"""
import argparse
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import requests


REPO = "NikitaF5/PokeTechArcana"
API = "https://api.github.com"


def sha1_of(path):
    digest = hashlib.sha1()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_safe_jar_name(name):
    path = Path(name)
    if path.name != name or path.suffix.lower() != ".jar":
        raise ValueError(f"Unsafe jar name: {name!r}")


def api(session, method, url, **kwargs):
    response = session.request(method, url, timeout=600, **kwargs)
    if response.status_code >= 300:
        raise RuntimeError(f"GitHub API {method} {url}: {response.status_code} {response.text[:500]}")
    return response.json() if response.text else {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, help="current complete manifest.json")
    parser.add_argument("--mods-dir", required=True, help="directory containing only staged update jars")
    parser.add_argument("--tag", required=True, help="new tag, for example pack-v1.2.0")
    parser.add_argument("--server", required=True, help="current host:port for auto-connect")
    parser.add_argument("--neoforge", default="21.1.234")
    parser.add_argument("--replacements", default="replacements.json")
    parser.add_argument("--exclude", default="client-exclude.json")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GITHUB_TOKEN with repository write access before publishing.")

    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    replaces = json.loads(Path(args.replacements).read_text(encoding="utf-8"))
    excluded = set(json.loads(Path(args.exclude).read_text(encoding="utf-8")))
    for new_name, old_names in replaces.items():
        require_safe_jar_name(new_name)
        for old_name in old_names:
            require_safe_jar_name(old_name)

    staged = []
    for jar in sorted(Path(args.mods_dir).glob("*.jar")):
        if jar.name in excluded:
            print(f"Skipping server-only jar: {jar.name}")
            continue
        # Stop before publication if a download is not a real jar archive.
        with zipfile.ZipFile(jar) as archive:
            archive.namelist()
        staged.append(jar)
    if not staged:
        sys.exit("No client jars to publish.")

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    release = api(session, "POST", f"{API}/repos/{REPO}/releases", json={
        "tag_name": args.tag,
        "name": f"Pack {args.tag}",
        "body": "Cobblemon 1.8 client update. Existing release assets are retained.",
        "make_latest": "true",
    })
    upload_url = release["upload_url"].split("{")[0]

    def upload(path):
        safe_name = "".join(c if c.isalnum() or c in "._-+" else "." for c in path.name)
        with open(path, "rb") as stream:
            response = session.post(f"{upload_url}?name={safe_name}", data=stream,
                                    headers={"Content-Type": "application/octet-stream"}, timeout=600)
        if response.status_code >= 300:
            raise RuntimeError(f"Upload {path.name}: {response.status_code} {response.text[:500]}")
        return response.json()["browser_download_url"]

    files_by_name = {Path(item["path"]).name: dict(item) for item in baseline["files"]}
    predecessors = {old for old_names in replaces.values() for old in old_names}
    for old_name in predecessors:
        files_by_name.pop(old_name, None)

    for jar in staged:
        digest = sha1_of(jar)
        old = files_by_name.get(jar.name)
        if old and old.get("sha1") == digest:
            print(f"Keeping existing asset: {jar.name}")
            continue
        print(f"Uploading: {jar.name}")
        item = {
            "path": f"mods/{jar.name}", "sha1": digest,
            "size": jar.stat().st_size, "url": upload(jar),
        }
        if jar.name in replaces:
            item["replaces"] = replaces[jar.name]
        files_by_name[jar.name] = item

    manifest = dict(baseline)
    manifest.update({
        "pack_version": args.tag.removeprefix("pack-v"),
        "minecraft": "1.21.1",
        "neoforge": args.neoforge,
        "server_address": args.server,
        "files": [files_by_name[name] for name in sorted(files_by_name, key=str.lower)],
    })
    output = Path("manifest.json")
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    upload(output)
    print(f"Published {release['html_url']}")
    print(f"Files in complete manifest: {len(manifest['files'])}")


if __name__ == "__main__":
    main()
