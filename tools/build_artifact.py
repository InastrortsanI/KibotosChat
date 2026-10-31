"""모바일용 claude.ai 페이지를 만드는 스크립트.

Python 서버 버전과 같은 data/*.json 을 artifact/template.html 의 DATA 자리에 넣어
한 장짜리 HTML(dist/kivotos-chat.html)을 만든다. 데이터를 고치면 이 스크립트만 다시 실행하면 된다.

사용법:  python tools/build_artifact.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "artifact" / "template.html"
OUT = ROOT / "dist" / "kivotos-chat.html"
PLACEHOLDER = "/*__DATA__*/null"


def load(name: str):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def main() -> None:
    data = {
        "world": load("world.json"),
        "schools": load("schools.json"),
        "students": load("students.json"),
        "scenarios": load("scenarios.json"),
    }
    # <script> 안에 JSON을 넣을 때 "</" 가 있으면 태그가 닫혀 버리므로 "<\/" 로 바꾼다.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    template = TEMPLATE.read_text(encoding="utf-8")
    if template.count(PLACEHOLDER) != 1:
        raise SystemExit(f"템플릿에 {PLACEHOLDER} 자리가 정확히 한 번 있어야 합니다.")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(template.replace(PLACEHOLDER, payload), encoding="utf-8")
    print(f"저장 → {OUT}  ({OUT.stat().st_size / 1024:.0f} KB, 학생 {len(data['students'])}명)")


if __name__ == "__main__":
    main()
