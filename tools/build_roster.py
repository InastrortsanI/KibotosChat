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
]

# SchaleDB 이후 공개된 이격(뉴스 보도로 확인한 것만)
EXTRA_OUTFITS = {
    "kikyou": ["수영복"], "renge": ["수영복"], "yukari": ["수영복"], "seia": ["수영복"],
    "hasumi": ["수영복"], "nagisa": ["수영복"], "mika": ["수영복"], "ichika": ["수영복"],
    "kisaki": ["수영복"], "shun": ["수영복"],
}

PLACEHOLDER = "(공개 자료 부족)"


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
    return entry


def main(db_path: str) -> None:
    raw = json.loads(Path(db_path).read_text(encoding="utf-8"))
    personas = load_personas()

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
        entry = {"id": sid, "name": name, "full_name": full, "school": school, "club": club,
                 "birthday": birthday, "outfits": EXTRA_OUTFITS.get(sid, [])}
        roster.append(apply_persona(entry, personas.get(sid)))

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
