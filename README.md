# Dain-queen Dalamud 플러그인 저장소

FF14 한국 서버(Dalamud 15)용 플러그인 모음입니다. 플러그인 인스톨러에서 바로 설치하고 업데이트할 수 있습니다.

## 추가하는 법

1. 게임에서 `/xlsettings` → **실험적 기능** 탭을 엽니다.
2. **사용자 정의 플러그인 저장소**에 아래 주소를 붙여 넣고 **+** 를 누른 뒤, 체크 표시가 켜져 있는지 확인하고 **저장**합니다.

```
https://raw.githubusercontent.com/Dain-queen/DalamudPlugins/main/repo.json
```

3. `/xlplugins` → **모든 플러그인**에서 이름으로 검색해 설치합니다. 업데이트는 인스톨러의 **업데이트** 버튼으로 한 번에 됩니다.

## 들어 있는 플러그인

| 플러그인 | 설명 |
|---|---|
| NoSolicitingKR | 내가 정한 단어가 들어간 채팅 숨기기 |
| PartyFinderPresets | 파티 모집 양식 저장/불러오기 |
| EnergyPackFlag | 에너지 팩 X 표식 위치에 깃발 자동 찍기 |
| KeyboundBrawlerChat | 키바운드 브롤러 문구 자동 입력 |
| Stylist (한글·아이템 레벨 제한) | Stylist 한글판 + 직업별 아이템 레벨 범위 제한 |
| GatherBuddy Reborn (한글) | GatherBuddy Reborn UI 한국어 번역판 |

## 갱신 (관리용)

각 플러그인 비공개 저장소의 최신 Releases zip 을 받아 `plugins/` 와 `repo.json` 을 다시 만듭니다.

```
python3 scripts/sync.py
```
