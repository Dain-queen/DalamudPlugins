#!/usr/bin/env python3
"""vnavmesh CN(AtmoOmen)의 새 버전을 확인해서, 버전 번호만 올린 사본을 이 저장소에 올린다.

왜: 원본 vnavmesh(veyn, 1.x)와 CN판(0.x)은 내부 이름이 둘 다 "vnavmesh"라서
    Dalamud가 버전이 높은 원본만 남기고 CN판을 지워버린다.
    그래서 CN판 버전 앞자리에 100을 더해(0.9.5.0 → 100.9.5.0) 항상 CN판이 남게 한다.
    플러그인 내용(dll)은 손대지 않고, zip 안의 매니페스트 버전만 바꾼다.

GitHub Actions(.github/workflows/vnavmesh-cn.yml)가 3시간마다 실행한다.
직접 실행: python3 scripts/vnavmesh_cn.py  (바뀌었으면 repo.json 과 plugins/vnavmesh/latest.zip 을 고침)
"""
import io
import json
import os
import sys
import time
import urllib.request
import zipfile

UPSTREAM = "https://raw.githubusercontent.com/AtmoOmen/DalamudPlugins/main/pluginmaster.json"
OWNER = "Dain-queen"
PUBLIC_REPO = "DalamudPlugins"
RAW = f"https://raw.githubusercontent.com/{OWNER}/{PUBLIC_REPO}/main"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERNAL = "vnavmesh"
BUMP = 100


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Dain-queen-DalamudPlugins"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def bump(version: str) -> str:
    parts = [int(p) for p in version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    parts[0] += BUMP
    return ".".join(str(p) for p in parts[:4])


def main() -> int:
    upstream = json.loads(fetch(UPSTREAM).decode("utf-8-sig"))
    src = next((e for e in upstream if e.get("InternalName") == INTERNAL), None)
    if src is None:
        print("!! AtmoOmen 저장소에 vnavmesh CN 항목이 없음", file=sys.stderr)
        return 1

    cn_version = src["AssemblyVersion"]
    version = bump(cn_version)

    repo_path = os.path.join(ROOT, "repo.json")
    with open(repo_path, encoding="utf-8-sig") as f:
        entries = json.load(f)

    current = next((e for e in entries if e.get("InternalName") == INTERNAL), None)
    zip_path = os.path.join(ROOT, "plugins", INTERNAL, "latest.zip")
    if current and current.get("CnVersion") == cn_version and os.path.exists(zip_path):
        print(f"변경 없음: vnavmesh CN {cn_version} (배포 {version})")
        return 0

    data = fetch(src["DownloadLinkInstall"])
    src_zip = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    found = False
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src_zip.infolist():
            content = src_zip.read(info.filename)
            name = info.filename
            if "/" not in name and name.endswith(".json") and not name.endswith(".deps.json"):
                try:
                    manifest = json.loads(content.decode("utf-8-sig"))
                except Exception:
                    manifest = None
                if isinstance(manifest, dict) and manifest.get("InternalName") == INTERNAL:
                    manifest["AssemblyVersion"] = version
                    content = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")
                    found = True
            dst.writestr(info, content)

    if not found:
        print("!! zip 안에서 vnavmesh 매니페스트를 찾지 못함", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with open(zip_path, "wb") as f:
        f.write(out.getvalue())

    link = f"{RAW}/plugins/{INTERNAL}/latest.zip"
    entry = {k: v for k, v in src.items() if k not in ("DownloadLinkInstall", "DownloadLinkUpdate", "DownloadLinkTesting")}
    entry.update({
        "Name": "vnavmesh CN",
        "AssemblyVersion": version,
        "TestingAssemblyVersion": version,
        "IsTestingExclusive": False,
        "Punchline": "vnavmesh CN (AtmoOmen) — 원본 vnavmesh에 지워지지 않게 버전 번호만 올린 사본",
        "Description": (src.get("Description") or "")
                       + f"\n\nAtmoOmen의 vnavmesh CN {cn_version}을 그대로 담고, 버전 번호만 {version}으로 올렸습니다."
                         "\nCN판이 업데이트되면 자동으로 따라 올라갑니다.",
        "DownloadLinkInstall": link,
        "DownloadLinkUpdate": link,
        "DownloadLinkTesting": link,
        "LastUpdate": int(time.time()),
        "CnVersion": cn_version,
    })

    if current:
        entries[entries.index(current)] = entry
    else:
        entries.append(entry)

    with open(repo_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"업데이트: vnavmesh CN {cn_version} → 배포 {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
