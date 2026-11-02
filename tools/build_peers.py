"""학생끼리 쓰는 말투(반말/존댓말)와 부르는 말을 게임 시나리오에서 집계해 tools/peers.json 으로 저장한다.

선생님에게 존댓말을 쓰는 학생도 친구에게는 반말을 쓰는 경우가 많다(예: 미도리 → 언니·아리스·유즈에게 반말).
프로필에는 '선생님에게' 말투만 있어서 AI가 학생끼리도 존댓말을 쓰게 되는 문제를 막기 위한 자료다.

방법: 대사가 '상대 이름(+쨩/선배/씨…)' 또는 '언니/부장/위원장님…' 같은 부름말로 시작하면
      그 상대에게 직접 하는 말로 보고, 문장 끝(~요/~습니다 → 존댓말, 그 밖 → 반말)을 센다.
      선생님이 함께 언급된 대사는 섞일 수 있어 뺀다.

사용법:  python tools/build_peers.py <ba-data DB 폴더>
         (ba-data: https://github.com/electricgoat/ba-data 의 global 브랜치, ScenarioScriptExcelTable*.json)
"""
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "peers.json"

SUFFIX = r"(?:\s?(?:쨩|짱|선배님|선배|님|씨|양|부장님|부장|회장님|회장|위원장님|위원장|반장|대장|소대장|실장님|실장))?"
TITLE = re.compile(r"^(언니|선배님|선배|위원장님|회장님|부장님|부장|반장|대장님|실장님|단장님)\s*[,!?…~.]")
POLITE = re.compile(r"(요|니다|니까|세요|죠|십시오|십니까|습니까|에요|예요)[\s.!?…~♪)]*$")


def main(db_dir: str) -> None:
    students = json.loads((ROOT / "data" / "students.json").read_text(encoding="utf-8"))
    by_name = {s["name"]: s["id"] for s in students if s["school"] != "Shittim"}
    # 딕셔너리 컴프리헨션으로 이름마다 '이름으로 부르며 시작하는 대사' 정규식을 미리 만들어 둔다
    calls = {n: re.compile("^(" + re.escape(n) + SUFFIX + r")\s*[,!?…~.]") for n in by_name}

    # stats[말하는 학생][상대] = [반말 수, 존댓말 수, 부른 말 Counter]
    stats = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, collections.Counter()]))
    for f in sorted(Path(db_dir).glob("ScenarioScriptExcelTable*.json")):
        rows = json.loads(f.read_text(encoding="utf-8"))
        rows = rows if isinstance(rows, list) else rows.get("DataList", [])
        for row in rows:
            m = re.match(r"^\d;([^;]+);\d+;(.*)", row.get("ScriptKr") or "", re.S)
            if not m:
                continue
            speaker = m.group(1).split(" ")[0]  # '히마리 방한복' → '히마리'
            if speaker not in by_name:
                continue
            text = re.sub(r"#.*", "", m.group(2)).replace("\n", " ")
            text = re.sub(r"\[/?[a-z]+[^\]]*\]", "", text).strip()
            if not text or "선생님" in text:
                continue
            target, hit = None, None
            for name, rx in calls.items():
                if name != speaker and (hit := rx.match(text)):  # := (바다코끼리 연산자): 대입과 검사를 한 번에
                    target = by_name[name]
                    break
            if not target and (hit := TITLE.match(text)):
                target = "#" + hit.group(1)
            if not target:
                continue
            rest = text[hit.end():].strip()
            if len(rest) < 3:
                continue
            cell = stats[by_name[speaker]][target]
            cell[1 if POLITE.search(rest) else 0] += 1
            cell[2][hit.group(1)] += 1

    out = {}
    for sid, targets in stats.items():
        rows = []
        for tid, (casual, polite, forms) in targets.items():
            n = casual + polite
            if n < 2:  # 한 번뿐인 건 우연일 수 있어 뺀다
                continue
            reg = "반말" if casual >= polite * 2 else "존댓말" if polite >= casual * 2 else "섞음"
            if reg == "섞음" and n < 4:
                continue
            rows.append([tid, reg, forms.most_common(1)[0][0], n])
        if rows:
            out[sid] = sorted(rows, key=lambda r: -r[3])
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"학생 {len(out)}명의 학생 간 말투 저장 → {OUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
