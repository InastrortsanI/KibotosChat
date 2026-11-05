# 키보토스 채팅

「블루 아카이브」 세계관에서 샬레의 선생님이 되어 학생들과 대화하는 AI 롤플레이 웹사이트입니다.
비상업 개인 포트폴리오용 팬 프로젝트이며, 저장소에는 게임의 이미지·로고·원문 대사가 들어 있지 않습니다.
학생 얼굴 아이콘은 팬 데이터베이스 [SchaleDB](https://schaledb.com)의 이미지를 링크로 불러와 표시합니다(GitHub Pages 버전만, 불러오지 못하면 이니셜 표시). 총학생회·NPC 학생 초상은 [BA-L10N-Viewer](https://github.com/BA-L10N-Viewer/viewer_site)의 공개 CDN을 링크합니다.
「블루 아카이브」와 모든 캐릭터 일러스트의 저작권은 NEXON Games / Yostar에 있습니다.

**바로 플레이: https://inastrortsani.github.io/KibotosChat/**
메뉴 아래쪽 'AI 설정'에 본인의 AI API 키(Gemini, Claude, OpenAI 중 하나)를 넣으면 시작할 수 있습니다.

## 기능
- **자유 모드**: 장소를 고르면 그곳에 있을 법한 학생이 자연스럽게 등장. 만난 학생 모두 호감도 반영
- **학생 1:1 대화**: 플레이어블 학생 140명 + 총학생회 임원 6명(린·모모카·아유무·아오이·카야·하이네) + 스토리 속 이름 있는 NPC 학생 10명(유키노·카구야·소라·아라타·아야메·스오우·아케미·코쿠리코·키키·나츠키). 싯딤의 상자의 아로나·프라나와도 1:1 대화 가능. 외부 콜라보 학생은 제외. 차림(수영복·새해 등)과 상황을 골라 시작
- **스토리 모드**: 시나리오 22종 + 자유 시나리오. 최대 6명이 함께 등장
- **메시지 삭제·입력 도우미**: 메시지를 눌러 삭제, `" "`·`* *`·`( )` 버튼으로 대사·행동·연출 지시 입력 (괄호 안은 인물들이 듣지 못하고 AI가 그대로 실행)
- **추천 답변**: 답장마다 선생님이 할 만한 말·행동 3개를 입력칸 위에 표시. 누르면 입력칸에 채워져 고쳐 보낼 수 있음 (설정에서 끄기 가능, 웹 버전 전용)
- **호감도·기억**: 학생별 호감도(헤일로 링으로 표시)가 방을 넘어 유지되고, 높을수록 부탁을 잘 들어주고 먼저 다가옴(서먹함→익숙함→신뢰→친밀→각별), 긴 대화는 자동 요약되어 기억으로 남음
- **계정·대화 저장**: 회원가입/로그인, 모든 대화 DB 저장, 다시 생성·되돌리기
- **AI 모델 교체**: Gemini / Claude / OpenAI / 테스트용 Mock 중 화면에서 선택

## 실행 방법 (Windows 기준)
```bash
cd KibotosChat
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload
```
브라우저에서 http://localhost:8000 을 엽니다.

API 키 없이도 `LLM_PROVIDER=mock` 상태로 화면과 DB 흐름을 모두 시험할 수 있습니다.
실제 대화를 하려면 `.env`에 키를 하나 이상 넣으세요. 키를 넣은 모델만 화면 목록에 나타납니다.
모델 이름(`GEMINI_MODEL` 등)은 각 회사 문서에서 최신 값을 확인해 바꿔 쓸 수 있습니다.

> `.env`와 `*.db`는 개인 정보(API 키, 계정)가 들어가므로 Git에 올리지 마세요. `.gitignore`에 이미 등록되어 있습니다.

## 웹 버전 (GitHub Pages / claude.ai)
Python 서버 없이 브라우저만으로 동작하는 한 장짜리 페이지(`index.html`)입니다. 같은 파일이 두 곳에서 동작합니다.

| | GitHub Pages | claude.ai 페이지 |
|---|---|---|
| AI 응답 | 방문자가 'AI 설정'에 넣은 API 키로 브라우저에서 직접 호출 | 보는 사람의 Claude 계정 (키 불필요) |
| 대화 저장 | 그 브라우저(localStorage)에만 저장 | claude.ai 계정의 개인 공간 |
| 모델 | Gemini / Claude / OpenAI 중 선택, 모델 이름 변경 가능 | Claude (기본/빠르게/깊이 있게) |

- API 키는 방문자의 브라우저에만 저장되고, 선택한 AI 회사 외에는 어디로도 보내지지 않습니다. 저장소에는 어떤 키도 들어 있지 않습니다.
- 데이터나 템플릿을 고친 뒤 아래 명령으로 다시 만들고 커밋하면 GitHub Pages에 반영됩니다.
  ```bash
  python tools/build_artifact.py   # artifact/template.html + data/*.json → index.html (+ claude.ai용 dist/)
  ```
- 서버 버전과 다른 점: 계정이 없고, 프롬프트·호감도·요약 로직은 `app/prompts.py`, `app/memory.py`를 JS로 옮긴 것입니다.
  자유 모드·메시지 삭제·장면 기록은 현재 웹 버전에만 있습니다.

## 폴더 구조
```
app/            서버 (FastAPI)
  main.py         진입점, 라우터·정적 파일 연결
  config.py       .env 설정
  db.py, models.py  DB 연결과 테이블
  security.py     비밀번호 해싱, 로그인 토큰
  schemas.py      API 입출력 형식
  lore.py         세계관 JSON 로딩
  prompts.py      LLM 시스템 프롬프트 조립 ← 대화 품질의 핵심
  memory.py       호감도 태그 처리, 대화 요약
  llm/            LLM 프로바이더 (공통 인터페이스 + 각 회사 구현)
  routers/        API 엔드포인트 (auth, catalog, chats)
data/           세계관·학교·학생·시나리오 데이터 (JSON)
frontend/       화면 (HTML/CSS/JS)
tools/          학생 명부 빌드 스크립트와 성격 원본
artifact/       웹 버전 템플릿 (index.html 의 원본)
index.html      빌드된 웹 버전 (GitHub Pages 첫 화면)
docs/           코드 학습 설명서
```

## 학생 데이터 고치기
- 성격·말투는 `tools/personas/*.json`에서 수정한 뒤 명부를 다시 빌드합니다.
  ```bash
  python tools/build_roster.py <SchaleDB students.json 경로>
  ```
  SchaleDB 데이터: https://github.com/lonqie/SchaleDB (data/kr/students.min.json)
- 성격·말투는 게임 한국어 데이터(학생 소개문·로비 대사)와 대조해 검토했습니다. 원문은 옮기지 않고 요약해 적습니다.
- 외모(머리색·눈·동물 귀/뿔/날개·헤일로)는 `tools/appearance.json`에 요약해 두었습니다(팬 위키 외모 항목을 참고해 직접 작성). 확인하지 못한 NPC는 `외모 미확인`으로 두어 AI가 지어내지 않게 합니다.
- 학생끼리 쓰는 말투(예: 미도리는 선생님에게 존댓말, 언니·아리스에게 반말)는 게임 시나리오 대사에서 집계합니다.
  ```bash
  python tools/build_peers.py <ba-data DB 폴더>   # → tools/peers.json, 그다음 build_roster.py 실행
  ```
  게임 데이터: https://github.com/electricgoat/ba-data (global 브랜치)
- `h`(선생님에게 쓰는 말투)는 `존댓말`·`반말` 외에 자유 문장도 됩니다. 예) 키사키 `예스러운 하게체`
- 외부 콜라보 학생(하츠네 미쿠, 미사카 미코토 등)과 일본 서버 전용 학생은 제외했습니다.

## API 문서
서버 실행 후 http://localhost:8000/docs 에서 모든 API를 직접 호출해 볼 수 있습니다.
