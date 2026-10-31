"""웹 버전(한 장짜리 페이지)을 만드는 스크립트.

Python 서버 버전과 같은 data/*.json 을 artifact/template.html 의 DATA 자리에 넣어
저장소 맨 위의 index.html 을 만든다. 이 파일 하나가 두 곳에서 그대로 동작한다.
  - GitHub Pages: 방문자가 'AI 설정'에 자기 API 키를 넣어 사용
  - claude.ai 페이지: 보는 사람의 Claude 계정으로 사용 (키 불필요)
데이터나 템플릿을 고친 뒤 이 스크립트를 실행하고 커밋하면 GitHub Pages에 반영된다.

사용법:  python tools/build_artifact.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "artifact" / "template.html"
OUT = ROOT / "index.html"                        # GitHub Pages용: 완전한 HTML 문서
OUT_CLAUDE = ROOT / "dist" / "kivotos-chat.html"  # claude.ai 게시용: 머리 부분은 claude.ai가 씌워 준다 (Git에는 올리지 않음)

# GitHub Pages에서는 문서 머리를 직접 붙여야 한다. 특히 viewport가 없으면 휴대폰에서 화면이 축소되어 보인다.
HEAD = (
    '<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    '<meta name="description" content="블루 아카이브 세계관에서 샬레의 선생님이 되어 학생들과 대화하는 AI 롤플레이 채팅 (팬 프로젝트)">\n'
    '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
    'img{max-width:100%}[hidden]{display:none!important}</style>\n'
)
TAIL = "\n</body>\n</html>\n"
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

    page = template.replace(PLACEHOLDER, payload)
    # 템플릿 앞부분(<title>, 글꼴, <style>)은 <head>로, 화면 본문(<div id="app"> 부터)은 <body>로
    head_part, body_part = page.split('<div id="app"', 1)
    OUT.write_text(HEAD + head_part + "</head>\n<body>\n" + '<div id="app"' + body_part + TAIL, encoding="utf-8")
    OUT_CLAUDE.parent.mkdir(exist_ok=True)
    OUT_CLAUDE.write_text(page, encoding="utf-8")
    print(f"저장 → {OUT.name} (GitHub Pages), {OUT_CLAUDE.relative_to(ROOT)} (claude.ai)  "
          f"{OUT.stat().st_size / 1024:.0f} KB, 학생 {len(data['students'])}명")


if __name__ == "__main__":
    main()
