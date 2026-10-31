# 키보토스 채팅

「블루 아카이브」 세계관에서 샬레의 선생님이 되어 학생들과 대화하는 AI 롤플레이 웹사이트입니다.
비상업 개인 포트폴리오용 팬 프로젝트이며, 게임의 이미지·로고·원문 대사는 포함하지 않습니다.

**바로 플레이: https://inastrortsani.github.io/KibotosChat/**
메뉴 아래쪽 'AI 설정'에 본인의 AI API 키(Gemini, Claude, OpenAI 중 하나)를 넣으면 시작할 수 있습니다.

## 기능
- **자유 모드**: 장소를 고르면 그곳에 있을 법한 학생이 자연스럽게 등장. 만난 학생 모두 호감도 반영
- **학생 1:1 대화**: 플레이어블 학생 140명. 차림(수영복·새해 등)과 상황을 골라 시작
- **스토리 모드**: 시나리오 11종 + 자유 시나리오. 최대 6명이 함께 등장
- **메시지 삭제·입력 도우미**: 메시지를 눌러 삭제, `" "`·`* *` 버튼으로 대사·행동 입력
- **호감도·기억**: 학생별 호감도(헤일로 링으로 표시)가 방을 넘어 유지되고, 긴 대화는 자동 요약되어 기억으로 남음
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
- `"(공개 자료 부족)"`으로 남은 24명은 화면에 '자료 보강 중'으로 표시됩니다. 말투(`s`)를 채우면 표시가 사라집니다.
- 외부 콜라보 학생(하츠네 미쿠, 미사카 미코토 등)과 일본 서버 전용 학생은 제외했습니다.

## API 문서
서버 실행 후 http://localhost:8000/docs 에서 모든 API를 직접 호출해 볼 수 있습니다.
