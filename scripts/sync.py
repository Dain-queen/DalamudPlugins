#!/usr/bin/env python3
"""비공개 플러그인 저장소들의 최신 Releases zip 을 받아 plugins/ 에 넣고 repo.json 을 다시 만든다.

사용법 (gh 로그인 필요):  python3 scripts/sync.py
플러그인을 추가하려면 아래 PLUGINS 목록에 한 줄 추가한다.
"""
import io
import json
import os
import re
import subprocess
import sys
import time
import zipfile

OWNER = "Dain-queen"
PUBLIC_REPO = "DalamudPlugins"
RAW = f"https://raw.githubusercontent.com/{OWNER}/{PUBLIC_REPO}/main"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (비공개 저장소 이름, 인스톨러에 보일 이름 — None 이면 플러그인 원래 이름)
PLUGINS = [
    ("NoSolicitingKR", None),
    ("PartyFinderPresets", None),
    ("EnergyPackFlag", None),
    ("keybound_brawler_chat", None),
    ("Stylist-ilvl-KR", "Stylist (한글·아이템 레벨 제한)"),
    ("GatherBuddyReborn-KR", "GatherBuddy Reborn (한글)"),
    ("AutoMahjongKR", None),
]


def gh(*args, binary=False):
    out = subprocess.run(["gh", "api", *args], check=True, capture_output=True)
    return out.stdout if binary else out.stdout.decode("utf-8")


def changelog_from(body: str) -> str:
    body = (body or "").strip()
    return body[:3000]


def main():
    entries = []
    for repo, display_name in PLUGINS:
        try:
            rel = json.loads(gh(f"repos/{OWNER}/{repo}/releases/latest"))
        except subprocess.CalledProcessError:
            print(f"!! {repo}: 릴리스 없음, 건너뜀", file=sys.stderr)
            continue
        assets = [a for a in rel["assets"] if a["name"].endswith(".zip")]
        if not assets:
            print(f"!! {repo}: zip 없음, 건너뜀", file=sys.stderr)
            continue
        data = gh("-H", "Accept: application/octet-stream",
                  f"repos/{OWNER}/{repo}/releases/assets/{assets[0]['id']}", binary=True)

        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = [n for n in z.namelist() if "/" not in n and n.endswith(".json") and not n.endswith(".deps.json")]
            dlls = {n[:-4] for n in z.namelist() if "/" not in n and n.endswith(".dll")}
            manifest_name = next(n for n in names if n[:-5] in dlls)
            manifest = json.loads(z.read(manifest_name).decode("utf-8-sig"))

        internal = manifest["InternalName"]
        os.makedirs(os.path.join(ROOT, "plugins", internal), exist_ok=True)
        with open(os.path.join(ROOT, "plugins", internal, "latest.zip"), "wb") as f:
            f.write(data)

        link = f"{RAW}/plugins/{internal}/latest.zip"
        entry = dict(manifest)
        if display_name:
            entry["Name"] = display_name
        entry.update({
            "DownloadLinkInstall": link,
            "DownloadLinkUpdate": link,
            "DownloadLinkTesting": link,
            "TestingAssemblyVersion": manifest["AssemblyVersion"],
            "IsTestingExclusive": False,
            "LastUpdate": int(time.mktime(time.strptime(rel["published_at"], "%Y-%m-%dT%H:%M:%SZ"))),
            "Changelog": changelog_from(rel.get("body")),
            "AcceptsFeedback": False,
        })
        entries.append(entry)
        print(f"ok {repo}: {internal} {manifest['AssemblyVersion']}")

    with open(os.path.join(ROOT, "repo.json"), "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
