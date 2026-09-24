import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "quest-development" / "release-1.6.0"
REPO = "NikitaF5/PokeTechArcana"
TAG = "pack-v1.6.0"


credential = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n", text=True, capture_output=True, check=True)
fields = dict(line.split("=", 1) for line in credential.stdout.splitlines() if "=" in line)
token = fields.get("password")
if not token:
    raise RuntimeError("Git Credential Manager did not return a GitHub token")
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "PokeTechArcana-release-publisher"}


def api(method, url, *, body=None, content_type="application/json"):
    request_headers = dict(headers)
    if body is not None:
        request_headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    with urllib.request.urlopen(request, timeout=600) as response:
        payload = response.read()
    return json.loads(payload) if payload else {}


payload = {"tag_name": TAG, "target_commitish": "main", "name": "PokeTech Arcana 1.6.0 — Occultism, EvilCraft и Forbidden & Arcanus", "body": "Добавлены три полные квестовые главы: Occultism, EvilCraft и Forbidden & Arcanus.", "make_latest": "true"}
try:
    release = api("POST", f"https://api.github.com/repos/{REPO}/releases", body=json.dumps(payload).encode("utf-8"))
except urllib.error.HTTPError as exc:
    if exc.code != 422:
        raise
    release = api("GET", f"https://api.github.com/repos/{REPO}/releases/tags/{TAG}")
upload_url = release["upload_url"].split("{")[0]
existing = {asset["name"]: asset for asset in release.get("assets", [])}
for path in (OUT / "configs.zip", OUT / "manifest.json"):
    if path.name in existing:
        api("DELETE", existing[path.name]["url"])
    query = urllib.parse.urlencode({"name": path.name})
    api("POST", f"{upload_url}?{query}", body=path.read_bytes(), content_type="application/octet-stream")
    print(f"uploaded {path.name} ({path.stat().st_size} bytes)")
print(release["html_url"])

