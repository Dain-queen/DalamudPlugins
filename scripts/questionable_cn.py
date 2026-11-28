#!/usr/bin/env python3
"""Questionable(puni.sh)의 새 버전을 받아, vnavmesh CN을 인식하게 패치한 사본을 이 저장소에 올린다.

왜: Questionable은 vnavmesh를 표시 이름(Name == "vnavmesh")으로 찾는다.
    vnavmesh CN은 표시 이름이 "vnavmesh CN"이라 못 찾고, 길찾기가 "준비 안 됨"으로 남아
    캐릭터가 움직이지 않는다. (CN판 이름을 바꾸면 Daily Routines가 CN판을 못 알아본다.)
    그래서 Questionable.dll에서 그 비교식 한 곳만 (표시 이름 또는 내부 이름)으로 고친다.
    → tools/QstPatcher 참고

    원본 Questionable과 내부 이름이 같으므로 vnavmesh CN 사본처럼 버전 앞자리에 100을 더한다.
    (15.756.3.64 → 115.756.3.64)

GitHub Actions(.github/workflows/questionable-cn.yml)가 3시간마다 실행한다. .NET 8 SDK가 필요하다.
직접 실행: python3 scripts/questionable_cn.py
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

UPSTREAM = "https://love.puni.sh/ment.json"
OWNER = "Dain-queen"
PUBLIC_REPO = "DalamudPlugins"
RAW = f"https://raw.githubusercontent.com/{OWNER}/{PUBLIC_REPO}/main"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERNAL = "Questionable"
BUMP = 100
# 패치 내용을 바꾸면 이 숫자를 올린다 → 같은 원본 버전이라도 다시 만든다
PATCH_REV = 1


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Dain-queen-DalamudPlugins"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def bump(version: str) -> str:
    parts = [int(p) for p in version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    parts[0] += BUMP
    return ".".join(str(p) for p in parts[:4])


def patch_dll(data: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "in.dll")
        dst = os.path.join(tmp, "out.dll")
        with open(src, "wb") as f:
            f.write(data)
        project = os.path.join(ROOT, "tools", "QstPatcher")
        subprocess.run(["dotnet", "run", "-c", "Release", "--project", project, "--", src, dst], check=True)
        with open(dst, "rb") as f:
            return f.read()


def main() -> int:
    upstream = json.loads(fetch(UPSTREAM).decode("utf-8-sig"))
    src = next((e for e in upstream if e.get("InternalName") == INTERNAL), None)
    if src is None:
        print("!! puni.sh 저장소에 Questionable 항목이 없음", file=sys.stderr)
        return 1

    up_version = src["AssemblyVersion"]
    version = bump(up_version)

    repo_path = os.path.join(ROOT, "repo.json")
    with open(repo_path, encoding="utf-8-sig") as f:
        entries = json.load(f)

    current = next((e for e in entries if e.get("InternalName") == INTERNAL), None)
    zip_path = os.path.join(ROOT, "plugins", INTERNAL, "latest.zip")
    if (current and current.get("UpstreamVersion") == up_version
            and current.get("PatchRev") == PATCH_REV and os.path.exists(zip_path)):
        print(f"변경 없음: Questionable {up_version} (배포 {version})")
        return 0

    data = fetch(src["DownloadLinkInstall"])
    src_zip = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    found_manifest = False
    found_dll = False
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
                    found_manifest = True
            elif name == "Questionable.dll":
                content = patch_dll(content)
                found_dll = True
            dst.writestr(info, content)

    if not (found_manifest and found_dll):
        print(f"!! zip 안에서 매니페스트({found_manifest}) 또는 Questionable.dll({found_dll})을 찾지 못함", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with open(zip_path, "wb") as f:
        f.write(out.getvalue())

    link = f"{RAW}/plugins/{INTERNAL}/latest.zip"
    entry = {k: v for k, v in src.items() if k not in ("DownloadLinkInstall", "DownloadLinkUpdate", "DownloadLinkTesting")}
    entry.update({
        "Name": "Questionable (vnavmesh CN 호환)",
        "AssemblyVersion": version,
        "TestingAssemblyVersion": version,
        "IsTestingExclusive": False,
        "Punchline": "Questionable — vnavmesh CN에서도 움직이게 고친 사본",
        "Description": (src.get("Description") or "")
                       + f"\n\npuni.sh의 Questionable {up_version}에서 vnavmesh를 찾는 비교식 한 곳만 고쳐"
                         f" vnavmesh CN도 인식하게 했고, 버전 번호를 {version}으로 올렸습니다."
                       + "\n원본이 업데이트되면 자동으로 따라 올라갑니다. 원본 소스: https://github.com/PunishXIV/Questionable (AGPL-3.0)",
        "DownloadLinkInstall": link,
        "DownloadLinkUpdate": link,
        "DownloadLinkTesting": link,
        "LastUpdate": int(time.time()),
        "UpstreamVersion": up_version,
        "PatchRev": PATCH_REV,
    })

    if current:
        entries[entries.index(current)] = entry
    else:
        entries.append(entry)

    with open(repo_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"업데이트: Questionable {up_version} → 배포 {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
