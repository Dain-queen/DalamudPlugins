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
| AutoMahjongKR | 도마 마작 자동 타패·리치·쯔모 / 버릴 패 추천 |
| ItemBatchUse | 소지품 우클릭 → 일괄 사용 (상자 여러 개 한 번에 열기) |
| AutoDismount | 탈것을 탄 채 스킬을 쓰면 자동으로 내리고 그 스킬 사용 |
| InstantTeleport | 돌발·비상 임무·NPC·에테라이트로 이동, 자동 모드(자동 이동·돌발 자동 공격) |
| vnavmesh CN | AtmoOmen의 vnavmesh CN 사본 (아래 참고) |
| Questionable (vnavmesh CN 호환) | puni.sh Questionable에서 vnavmesh CN도 인식하게 한 곳만 고친 사본 (아래 참고) |

### vnavmesh CN

원본 vnavmesh(1.x)와 CN판(0.x)은 내부 이름이 같아서, Dalamud가 버전이 높은 원본만 남기고 CN판을 지웁니다.
그래서 CN판 내용은 그대로 두고 **버전 번호 앞자리에 100을 더한 사본**(예: 0.9.5.0 → 100.9.5.0)을 올립니다. 이러면 항상 CN판이 남습니다.
GitHub Actions(`vnavmesh CN 따라가기`)가 3시간마다 AtmoOmen 저장소를 확인해서, CN판이 업데이트되면 자동으로 따라 올립니다.
직접 확인하려면 `python3 scripts/vnavmesh_cn.py`를 실행합니다.

### Questionable (vnavmesh CN 호환)

Questionable은 vnavmesh를 **표시 이름**(`Name == "vnavmesh"`)으로 찾습니다. CN판은 표시 이름이 `vnavmesh CN`이라 못 찾고,
길찾기가 계속 "준비 안 됨"으로 남아 캐릭터가 움직이지 않습니다. (CN판 이름을 바꾸면 Daily Routines가 CN판을 못 알아봅니다.)
그래서 `IPCUtils.IPCSubscriber.Version()`의 비교식만 `(표시 이름 == name || 내부 이름 == name)`으로 고칩니다. 원래 조건을 포함하므로 다른 연동은 그대로입니다.
패치는 `tools/QstPatcher`(Mono.Cecil)가 하고, 버전은 vnavmesh CN 사본처럼 앞자리에 100을 더합니다 (15.756.3.64 → 115.756.3.64).
GitHub Actions(`Questionable CN 호환판 따라가기`)가 3시간마다 puni.sh를 확인해서 원본이 업데이트되면 자동으로 따라 올립니다.
원본 소스: https://github.com/PunishXIV/Questionable (AGPL-3.0). 패치 도구 소스는 이 저장소에 있습니다.

## 갱신 (관리용)

각 플러그인 비공개 저장소의 최신 Releases zip 을 받아 `plugins/` 와 `repo.json` 을 다시 만듭니다.
스크립트가 관리하지 않는 항목(vnavmesh CN, Questionable)과 이번에 릴리스를 못 읽은 항목은 기존 `repo.json` 내용을 그대로 남깁니다.

```
python3 scripts/sync.py
```
