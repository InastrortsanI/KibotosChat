"""학생 명부(data/students.json)를 만드는 스크립트.

- 사실 정보(이름·학년·나이·생일·키·무기·취미): SchaleDB 공개 데이터에서 가져온다.
- 성격·말투·관계: tools/personas/*.json 에 직접 작성한 내용을 합친다.
- SchaleDB에 아직 없는 신규 학생: 아래 NEW_STUDENTS 에 사실 정보를 직접 적는다.

사용법:  python tools/build_roster.py <SchaleDB students.json 경로>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PERSONA_DIR = ROOT / "tools" / "personas"
OUT = ROOT / "data" / "students.json"

COLLAB = {"Hatsune_Miku", "Misaka_Mikoto", "Shokuhou_Misaki", "Saten_Ruiko"}  # 외부 IP 콜라보는 제외
WEAPON = {"SR": "저격소총", "SG": "샷건", "AR": "돌격소총", "MG": "기관총", "SMG": "기관단총", "HG": "권총",
          "GL": "유탄발사기", "RL": "로켓런처", "MT": "박격포", "RG": "레일건", "FT": "화염방사기"}
CLUB = {"Kohshinjo68": "흥신소 68", "Justice": "정의실현부", "CleanNClearing": "C&C", "BookClub": "도서부",
        "Countermeasure": "대책위원회", "Engineer": "엔지니어부", "FoodService": "급양부", "Fuuki": "선도부",
        "GourmetClub": "미식연구회", "HoukagoDessert": "방과후 디저트부", "KnightsHospitaller": "구호기사단",
        "MatsuriOffice": "마츠리부", "Meihuayuan": "매화원", "Onmyobu": "음양부", "RemedialClass": "보충수업부",
        "SPTF": "초현상특무부", "Shugyobu": "수행부", "Endanbou": "연단방", "TheSeminar": "세미나",
        "TrainingClub": "트레이닝부", "TrinityVigilance": "트리니티 자경단", "Veritas": "베리타스",
        "NinpoKenkyubu": "인법연구부", "GameDev": "게임개발부", "RedwinterSecretary": "사무국",
        "anzenkyoku": "생활안전국", "SisterHood": "시스터후드", "Class227": "227호 특별반",
        "Emergentology": "응급의학부", "RabbitPlatoon": "RABBIT 소대", "PandemoniumSociety": "만마전",
        "AriusSqud": "아리우스 스쿼드", "HotSpringsDepartment": "온천개발부", "TeaParty": "티파티",
        "PublicPeaceBureau": "공안국", "BlackTortoisePromenade": "현무상회", "Genryumon": "현룡문",
        "LaborParty": "용역부", "KnowledgeLiberationFront": "지식해방전선",
        "Hyakkayouran": "백화요란 분쟁조정위원회", "ShinySparkleSociety": "반짝반짝부",
        "AbydosStudentCouncil": "아비도스 학생회", "EmptyClub": "무소속"}

# SchaleDB 스냅숏 이후 추가된 학생 (한국 서버 기준 플레이어블). 출처: 학생 명부 위키(2026-10-30 갱신)
NEW_STUDENTS = [
    ("niya", "니야", "아마치 니야", "Hyakkiyako", "음양부", "1월 1일"),
    ("erika", "에리카", "하타미 에리카", "Gehenna", "반짝반짝부", "2월 1일"),
    ("reijo", "레이죠", "카야마 레이죠", "Shanhaijing", "현무상회", "3월 3일"),
    ("ritsu", "리츠", "우스바 리츠", "WildHunt", "특수교역부", "3월 6일"),
    ("subaru", "스바루", "카케하시 스바루", "Arius", "니코메디아", "3월 9일"),
    ("niko", "니코", "요시노 니코", "SRT", "FOX 소대", "2월 11일"),
    ("kisaki", "키사키", "류우게 키사키", "Shanhaijing", "현룡문", "2월 19일"),
    ("satsuki", "사츠키", "쿄고쿠 사츠키", "Gehenna", "만마전", "4월 10일"),
    ("rabu", "라브", "코마카제 라브", "Trinity", "헬멧단", "5월 6일"),
    ("yakumo", "야쿠모", "아라마키 야쿠모", "RedWinter", "출판부", "5월 18일"),
    ("otogi", "오토기", "텐진야마 오토기", "SRT", "FOX 소대", "5월 20일"),
    ("rio", "리오", "츠카츠키 리오", "Millennium", "세미나", "6월 6일"),
    ("hikari", "히카리", "타치바나 히카리", "Highlander", "CCC", "6월 14일"),
    ("nozomi", "노조미", "타치바나 노조미", "Highlander", "CCC", "6월 14일"),
    ("takane", "타카네", "미요시 타카네", "RedWinter", "출판부", "6월 18일"),
    ("aoba", "아오바", "우츠미 아오바", "Highlander", "화물운송관리부", "7월 19일"),
    ("rei", "레이", "노마사 레이", "Millennium", "트레이닝부", "8월 9일"),
    ("konoka", "코노카", "시마 코노카", "Valkyrie", "공안국", "8월 19일"),
    ("miyo", "미요", "사쿠라이 미요", "WildHunt", "특수교역부", "8월 24일"),
    ("fuyu", "후유", "와카사 후유", "WildHunt", "특수교역부", "9월 5일"),
    ("rena", "레나", "키누이 레나", "WildHunt", "오컬트연구회", "9월 21일"),
    ("chiaki", "치아키", "모토미야 치아키", "Gehenna", "만마전", "9월 22일"),
    ("seia", "세이아", "유리조노 세이아", "Trinity", "티파티", "9월 29일"),
    ("kurumi", "쿠루미", "타카쿠라 쿠루미", "SRT", "FOX 소대", "9월 30일"),
    ("eri", "에리", "시라오 에리", "WildHunt", "오컬트연구회", "10월 31일"),
    ("kanoe", "카노에", "이타가키 카노에", "WildHunt", "오컬트연구회", "11월 2일"),
    ("nagusa", "나구사", "고료 나구사", "Hyakkiyako", "백화요란 분쟁조정위원회", "12월 7일"),
    ("kei", "케이", "텐도 케이", "Millennium", "초현상특무부", "3월 25일"),
    # 총학생회 임원 (플레이어블이 아닌 NPC. 생일 등 미공개 정보는 비워 둔다)
    ("rin", "린", "나나가미 린", "GSC", "수석행정관", ""),
    ("momoka", "모모카", "유라기 모모카", "GSC", "교통실", ""),
    ("ayumu", "아유무", "이와비츠 아유무", "GSC", "조정실", ""),
    ("aoi", "아오이", "오키 아오이", "GSC", "재무실장", ""),
    ("kaya", "카야", "시라누이 카야", "GSC", "방위실장", ""),
    ("haine", "하이네", "하이네", "GSC", "체육실장", ""),
    # 이름 있는 NPC 학생 (게임 스토리 등장인물. 생일 등 미공개 정보는 비워 둔다)
    ("yukino", "유키노", "유키노", "SRT", "FOX 소대", ""),
    ("kaguya", "카구야", "우루시바라 카구야", "Shanhaijing", "경극부", ""),
    ("sora", "소라", "소라", "Etc", "엔젤 24 점원", ""),
    ("arata", "아라타", "시가라키 아라타", "Hyakkiyako", "길거리 망량즈", ""),
    ("ayame", "아야메", "아야메", "Hyakkiyako", "백화요란 분쟁조정위원회 (선대 부장)", ""),
    ("suou", "스오우", "스오우", "Highlander", "감리실", ""),
    ("akemi", "아케미", "쿠리하마 아케미", "Etc", "불량배", ""),
    ("kokuriko", "코쿠리코", "코쿠리코", "Hyakkiyako", "화조풍월부", ""),
    ("kiki", "키키", "키키", "Shanhaijing", "매화원 원생", ""),
    ("natsuki", "나츠키", "아사쿠사 나츠키", "Hyakkiyako", "인력거부", ""),
    # 싯딤의 상자 OS (학생이 아님. 학생들은 둘을 인식하지 못한다)
    ("arona", "아로나", "아로나", "Shittim", "메인 OS", ""),
    ("plana", "프라나", "프라나", "Shittim", "서브 OS", ""),
]

# 신규 학생의 게임 내 캐릭터 Id (SchaleDB 이미지 주소용). 게임 데이터 CharacterExcelTable 기준.
NEW_ART = {
    "niya": 20046, "erika": 20058, "reijo": 10104, "ritsu": 20050, "subaru": 10130, "niko": 10139,
    "kisaki": 10145, "satsuki": 20040, "rabu": 16018, "yakumo": 20052, "otogi": 16020, "rio": 10133,
    "hikari": 10117, "nozomi": 10118, "takane": 10131, "aoba": 16017, "rei": 10115, "konoka": 10137,
    "miyo": 10127, "fuyu": 10128, "rena": 10138, "chiaki": 10107, "seia": 10110, "kurumi": 10140,
    "eri": 10125, "kanoe": 10126, "nagusa": 10119, "kei": 10135,
}
# NPC 초상 (SchaleDB에 없음). 게임 데이터의 NPC_Portrait 이름 기준, BA-L10N-Viewer 공개 CDN.
NPC_ART = {sid: f"https://ba-l10n-r2.cnfast.top/ba/01_01_Character/npc_portrait_{name}.png" for sid, name in {
    "rin": "rin", "momoka": "momoka", "ayumu": "np0013", "aoi": "np0032", "kaya": "np0015", "haine": "np0033",
    "kaguya": "np0242", "sora": "sora", "ayame": "np0206", "kiki": "np0216", "natsuki": "np0182",
    "arona": "arona", "plana": "np0035",
}.items()}
# 적 유닛·이벤트용 학생 초상(Student_Portrait)이 있는 NPC는 그쪽을 쓴다 (플레이어블 아이콘과 같은 화풍).
NPC_ART.update({sid: f"https://ba-l10n-r2.cnfast.top/ba/01_01_Character/student_portrait_{code}.png" for sid, code in {
    "yukino": "ch0171", "arata": "ch0236", "suou": "ch0244", "akemi": "ch0265", "kokuriko": "ch0226",
}.items()})
# 글로벌 데이터에 기본 의상 없이 이격만 있는 학생(키사키=수영복, 리오=특수 슈트)은 기본 의상 초상으로 덮어쓴다.
BASE_ART = {sid: f"https://ba-l10n-r2.cnfast.top/ba/01_01_Character/student_portrait_{code}.png" for sid, code in {
    "kisaki": "ch0139", "rio": "ch0158",
}.items()}

# SchaleDB 이후 공개된 이격(뉴스 보도로 확인한 것만)
EXTRA_OUTFITS = {
    "kikyou": ["수영복"], "renge": ["수영복"], "yukari": ["수영복"], "seia": ["수영복"],
    "hasumi": ["수영복"], "nagisa": ["수영복"], "mika": ["수영복"], "ichika": ["수영복"],
    "kisaki": ["수영복"], "shun": ["수영복"],
}

PLACEHOLDER = "(공개 자료 부족)"

APPEARANCE = ROOT / "tools" / "appearance.json"  # 외모 요약 (직접 작성)
PEERS = ROOT / "tools" / "peers.json"            # 학생 간 말투 (tools/build_peers.py 가 시나리오에서 집계)
# 부름말만으로는 누군지 알 수 없는 경우와, 집계에 잡히지 않았지만 대사로 확인한 경우를 손으로 보충한다.
TITLE_WHO = {("midori", "#언니"): "모모이", ("momoi", "#언니"): None}
# 표시 이름 바꾸기: SchaleDB의 '시로코*테러'는 별표(*)가 '행동' 표시와 겹쳐 대사·입력이 잘못 나뉜다. 게임 시나리오 표기('시로코 테러')로 쓴다.
NAME_OVERRIDE = {"shiroko_terror": ("시로코 테러", "스나오오카미 시로코(테러)")}
# 유저나 AI가 부를 수 있는 다른 이름. 이 이름으로 불러도 그 학생으로 알아본다.
ALIASES = {"shiroko_terror": ["시로코*테러", "시로코＊테러", "시로코테러", "테러 시로코", "큰 시로코", "어른 시로코", "다른 세계의 시로코"]}
PEER_EXTRA = {"midori": [["kei", "반말", "케이 쨩", 9]],  # '케이 쨩도 너무 화내지 말아 줘'
              "momoi": [["yuzu", "반말", "유즈", 9]]}     # '유즈는 어떻게 생각해?' ('유즈!'처럼 부름말만 있는 대사가 많아 집계에서 빠짐)


def load_personas() -> dict:
    merged = {}
    for f in sorted(PERSONA_DIR.glob("*.json")):
        merged.update(json.loads(f.read_text(encoding="utf-8")))
    return merged


def apply_persona(entry: dict, persona: dict | None) -> dict:
    persona = persona or {}
    for short, key in [("p", "personality"), ("s", "speech"), ("t", "sensei"), ("r", "relations"), ("st", "story")]:
        value = persona.get(short, "")
        if value and value != PLACEHOLDER:
            entry[key] = value
    # 말투가 비어 있으면 자료가 부족한 학생으로 표시 → 프롬프트에서 '지어내지 말라'는 안내가 붙는다.
    entry["detail"] = "full" if entry.get("speech") else "basic"
    # 선생님에게 쓰는 높임. 자료가 없으면 더 안전한 존댓말을 기본값으로 둔다.
    entry["honorific"] = persona.get("h", "존댓말")
    # 선생님을 부르는 호칭 (게임 대사 기준). 대부분 '선생님'이고, 예외만 페르소나의 "c"에 적는다.
    entry["call"] = persona.get("c", "선생님")
    # 두 번에 나눠 외치는 대사 (예: 케이 '이번에야말로!!' → 다음 응답 '선생님을 죽이고!! 저도 죽겠어요!!')
    if persona.get("cs"):
        entry["catch_split"] = persona["cs"]
    return entry


def peer_text(sid: str, rows: list, names: dict) -> str:
    """[['aris','반말','아리스 쨩',15], ...] → "반말: 아리스('아리스 쨩'), … / 존댓말: …" """
    groups: dict[str, list[str]] = {}
    for tid, reg, form, _n in rows:
        if tid.startswith("#"):
            who = TITLE_WHO.get((sid, tid), "")
            if who is None:
                continue
            label = f"'{form}'" + (f"({who})" if who else "이라 부르는 상대")
        else:
            label = f"{names.get(tid, tid)}('{form}')"
        groups.setdefault(reg, []).append(label)
    order = [("반말", "반말"), ("존댓말", "존댓말"), ("섞음", "반말·존댓말 섞음")]
    return " / ".join(f"{title}: {', '.join(groups[k])}" for k, title in order if k in groups)


def main(db_path: str) -> None:
    raw = json.loads(Path(db_path).read_text(encoding="utf-8"))
    personas = load_personas()
    looks = json.loads(APPEARANCE.read_text(encoding="utf-8"))
    peers = json.loads(PEERS.read_text(encoding="utf-8")) if PEERS.exists() else {}

    outfits: dict[str, list[str]] = {}
    for s in raw:  # '아루(새해)' → 아루의 의상 목록에 '새해' 추가
        if "(" in s["Name"]:
            base_name, outfit = s["Name"].rstrip(")").split("(", 1)
            outfits.setdefault(base_name, [])
            if outfit not in outfits[base_name]:
                outfits[base_name].append(outfit)

    roster = []
    for s in raw:
        if "(" in s["Name"] or s["PathName"] in COLLAB:
            continue
        sid = s["PathName"].lower()
        entry = {
            "id": sid,
            "art": s["Id"],
            "name": s["Name"],
            "full_name": f"{s['FamilyName']} {s['PersonalName']}" if s["FamilyName"] else s["Name"],
            "school": s["School"],
            "club": CLUB.get(s["Club"], s["Club"]),
            "year": s["SchoolYear"],
            "age": s["CharacterAge"],
            "birthday": s["Birthday"],
            "height": s["CharHeightMetric"],
            "hobby": s["Hobby"],
            "weapon": WEAPON.get(s["WeaponType"], s["WeaponType"]),
            "outfits": outfits.get(s["Name"], []) + EXTRA_OUTFITS.get(sid, []),
        }
        roster.append(apply_persona(entry, personas.get(sid)))

    known = {e["id"] for e in roster}
    for sid, name, full, school, club, birthday in NEW_STUDENTS:
        if sid in known:
            continue
        entry = {"id": sid, "art": NEW_ART.get(sid), "art_url": NPC_ART.get(sid) or BASE_ART.get(sid), "name": name, "full_name": full, "school": school, "club": club,
                 "birthday": birthday, "outfits": EXTRA_OUTFITS.get(sid, [])}
        roster.append(apply_persona(entry, personas.get(sid)))

    for e in roster:
        if e["id"] in NAME_OVERRIDE:
            e["name"], e["full_name"] = NAME_OVERRIDE[e["id"]]
        if e["id"] in ALIASES:
            e["aliases"] = ALIASES[e["id"]]
    names = {e["id"]: e["name"] for e in roster}
    for e in roster:
        if looks.get(e["id"]):
            e["appearance"] = looks[e["id"]]
        rows = peers.get(e["id"], []) + PEER_EXTRA.get(e["id"], [])
        if rows:
            e["peers"] = peer_text(e["id"], rows, names)

    missing = [e["id"] for e in roster if e["id"] not in personas]
    unused = sorted(set(personas) - {e["id"] for e in roster})
    roster.sort(key=lambda e: (e["school"], e["name"]))
    OUT.write_text(json.dumps(roster, ensure_ascii=False, indent=1), encoding="utf-8")

    basic = sum(e["detail"] == "basic" for e in roster)
    print(f"학생 {len(roster)}명 저장 → {OUT}  (상세 {len(roster) - basic} / 자료 부족 {basic})")
    if missing:
        print("페르소나 없음:", missing)
    if unused:
        print("명부에 없는 페르소나 id:", unused)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
