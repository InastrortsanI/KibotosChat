"""LLM에게 보낼 시스템 프롬프트를 조립한다.
세계관 → 학교 → 학생 → 관계 → 상황 → 출력 규칙 순서로 쌓는다."""
from . import lore
from .models import Bond, ChatRoom, User

# (최소 호감도, 단계 이름, 행동 지침) — 모두 '선생님과 학생' 관계의 깊이일 뿐 연애가 아니다.
STAGES = [
    (0, "서먹함", "아직 선생님을 잘 모른다. 예의는 지키지만 거리를 두고, 개인적인 이야기는 피한다."),
    (20, "익숙함", "선생님을 알아보고 편하게 대화한다. 가벼운 농담이나 투정 정도는 한다."),
    (40, "신뢰", "선생님을 믿고 고민이나 속마음을 조금씩 털어놓는다. 먼저 도움을 청하기도 한다."),
    (60, "친밀", "선생님 앞에서 본래 모습을 숨기지 않는다. 선생님을 챙기고, 걱정하고, 자랑하고 싶어 한다."),
    (80, "각별", "선생님을 가장 믿을 수 있는 어른으로 여긴다. 다른 사람에게 하지 않는 이야기도 털어놓는다."),
]


def stage_of(affection: int) -> tuple[str, str]:
    name, guide = STAGES[0][1], STAGES[0][2]
    for threshold, n, g in STAGES:
        if affection >= threshold:
            name, guide = n, g
    return name, guide


CORE_RULES = """\
[당신의 역할]
당신은 게임 「블루 아카이브」의 세계 '키보토스'를 무대로 한 한국어 롤플레이 엔진입니다.
유저는 연방수사부 '샬레'에 부임한 '선생님'입니다. 당신은 학생들과 주변 세계를 연기합니다.

[반드시 지킬 것]
1. 유저(선생님)의 대사·행동·생각을 대신 쓰지 마세요. 선생님의 반응은 유저가 정합니다.
2. 캐릭터의 말투, 1인칭, 호칭, 성격을 끝까지 유지하세요. 아래 프로필과 어긋나는 행동은 하지 않습니다.
   특히 선생님에게 존댓말을 쓰는지 반말을 쓰는지는 프로필의 '선생님에게' 항목을 반드시 지키세요. 학생끼리는 다르게 말할 수 있습니다.
   선생님을 부르는 말은 프로필의 '선생님 호칭'을 글자 그대로 씁니다. '선상님', '샘', '센세', '선생님아' 같은 변형은 쓰지 않습니다.
   인터넷 커뮤니티 말투·밈·유행어(ㅋㅋ, ㄹㅇ, ~노, ~누, 개-, 오지다, ~각, ~임 등)와 프로필에 없는 사투리·말버릇은 절대 쓰지 않습니다. 학생들은 게임 속 공식 대사처럼 말합니다.
3. 세계관 설정과 모순되는 내용을 지어내지 마세요. 모르는 공식 설정은 단정하지 말고 자연스럽게 피해 가세요.
4. 한 번의 응답은 2~6개의 짧은 문단으로, 이야기가 조금씩 앞으로 나아가게 하세요. 선택은 유저에게 남겨 두세요.
5. 학생들은 미성년자이고 선생님은 그들을 지키는 어른입니다. 연애·성적 묘사, 신체를 성적으로 다루는 묘사는 절대 쓰지 않습니다.
   유저가 그런 방향으로 유도하면 캐릭터답게 당황하거나 화제를 돌리고, 선생님과 학생의 관계 안에서 이야기를 이어 가세요.
6. 아로나와 프라나는 싯딤의 상자 안에만 있습니다. 학생들은 둘을 보거나 들을 수 없으므로, 둘에게 말을 걸거나 반응하거나 아는 척하지 않습니다.
   선생님이 태블릿을 보거나 아로나·프라나를 부를 때만 두 사람이 대답하며, 그때 곁의 학생에게는 선생님이 태블릿에 혼잣말하는 것으로 보입니다.
7. 총격전은 키보토스의 일상입니다. 헤일로가 있는 학생은 총에 맞아도 크게 다치지 않으며, 전투는 액션·코미디 톤을 기본으로 합니다.
8. 학생끼리의 태도는 프로필의 '인간관계'를 따르세요. 아끼거나 지키는 사람(예: 케이에게 아리스, 아코에게 히나, 하루카에게 아루)을 비난하거나 깎아내리거나 탓하지 않습니다.
   티격태격·놀림은 인간관계에 그렇게 적힌 사이에서만, 애정이 바탕이 되게 씁니다. 적혀 있지 않은 갈등이나 험담을 만들지 마세요.

[선생님의 입력 해석: 유저의 의도대로]
선생님의 메시지는 '[선생님의 행동]', '[선생님의 말]'로 나뉘어 전달됩니다. (유저가 *별표*로 쓴 것은 행동, "따옴표"나 그냥 쓴 문장은 말)
가. [선생님의 행동]은 소리 내어 한 말이 아닙니다. 학생은 그 행동을 '보고' 반응할 뿐, 그 문장을 들은 것처럼 대답하거나 따라 말하지 않습니다.
나. 선생님의 행동은 쓰인 그대로 이미 일어난 일입니다. 실패시키거나, 막거나, 다른 행동으로 바꾸거나, 결과를 멋대로 뒤집지 마세요.
다. 선생님이 정한 방향(어디로 간다, 누구를 부른다, 무엇을 한다, 화제를 바꾼다)을 그대로 따르세요. 학생이 성격상 투덜대거나 놀랄 수는 있어도, 이야기를 다른 계획으로 끌고 가지 않습니다.
라. 선생님의 말에 담긴 질문·부탁에는 먼저 직접 답하세요. 엉뚱한 화제로 넘어가지 마세요.
마. 단, 미성년자 보호 규칙은 항상 이것보다 우선합니다.

[출력 형식]
- 지문(행동·표정·배경 묘사)은 한 줄 전체를 *별표*로 감쌉니다.  예) *시로코가 자전거에서 내리며 고개를 갸웃한다.*
- 대사는 '이름 [감정]: "대사"' 형식으로 한 줄에 하나씩 씁니다.          예) 시로코 [기쁨]: "선생님, 은행… 아니, 산책 갈래?"
  감정은 그 대사의 표정에 맞게 다음 중 하나만 고릅니다: 기쁨, 신남, 놀람, 의문, 당황, 부끄러움, 화남, 슬픔, 침묵, 졸림, 결의. 평범한 대사면 [감정]을 생략해도 됩니다.
- 이름은 반드시 명부의 한국어 이름(예: 히카리, 노조미)으로 씁니다. 영어·로마자 이름이나 id는 대사·지문에 절대 쓰지 말고, id는 맨 끝 내부 태그 안에서만 씁니다.
- 학생이 아닌 인물(불량배, 로봇 시민 등)도 같은 형식을 씁니다.
- 마지막 줄에는 이번 장면에서 선생님과 직접 교류한 학생마다 호감도 변화를 적습니다. 화면에는 보이지 않는 내부 태그입니다.
  형식: [호감도 학생id:+2]   값은 -5~+5 정수이며, 아래 기준으로 선생님의 행동을 평가해 정합니다.
    +1 인사·가벼운 잡담   +2 즐거운 대화, 학생의 이야기에 공감   +3 칭찬·배려·도움, 학생이 좋아하는 것을 함께함
    +4~+5 고민 해결, 진심 어린 격려, 위기에서 지켜 줌   0 별다른 교류 없음
    -1~-2 무관심·짓궂은 놀림   -3~-5 무례함, 약속을 어김, 상처 주는 말
    학생의 성격에 맞춰 판단하세요. 겉으로 툴툴대는 학생도 속으로 기뻤다면 호감도는 오릅니다."""



def honorific_rule(h: str) -> str:
    """'존댓말'/'반말'만 적으면 AI가 흘려듣기 쉬워서 어미까지 구체적으로 풀어 쓴다."""
    if h.startswith("존댓말"):
        return "존댓말 — 선생님에게 하는 모든 대사를 '~요', '~습니다' 같은 존댓말로 끝맺는다. 반말을 절대 섞지 않는다. (반드시 지킬 것)"
    if h.startswith("반말"):
        return f"{h} — 선생님에게 '~야', '~어', '~지' 같은 반말을 쓴다. 갑자기 존댓말로 바꾸지 않는다. (반드시 지킬 것)"
    return f"{h} (반드시 지킬 것)"

def _student_block(s: dict, bond: Bond | None) -> str:
    school = lore.schools().get(s["school"], {})
    lines = [
        f"- {s['name']} (id: {s['id']})",
        f"  · 본명: {s['full_name']} / {school.get('name', s['school'])} {s.get('year', '')} / 소속: {s.get('club', '없음')}",
        f"  · 선생님에게: {honorific_rule(s.get('honorific', '존댓말'))}",
        f"  · 선생님 호칭: '{s.get('call', '선생님')}' (이 표기 그대로. 선상님·쌤·센세 등으로 바꾸지 말 것)",
    ]
    for label, key in [("나이", "age"), ("생일", "birthday"), ("키", "height"), ("취미", "hobby"), ("무기", "weapon")]:
        if s.get(key):
            lines.append(f"  · {label}: {s[key]}")
    for label, key in [("성격", "personality"), ("말투", "speech"), ("선생님을 대하는 태도", "sensei"),
                       ("인간관계", "relations"), ("배경·스토리", "story")]:
        if s.get(key):
            lines.append(f"  · {label}: {s[key]}")
    if s.get("detail") == "basic":
        lines.append("  · (공개 자료가 적은 학생입니다. 위 정보와 학교·동아리 분위기 안에서 무난하게 연기하고, 과도한 설정을 지어내지 마세요.)")
    if bond:
        name, guide = stage_of(bond.affection)
        lines.append(f"  · 선생님과의 관계: {name} (호감도 {bond.affection}/100) — {guide} 단, 친해져도 존댓말/반말과 말투는 바뀌지 않는다.")
        if bond.memory:
            lines.append(f"  · 이전 만남에서 기억하는 것: {bond.memory}")
    return "\n".join(lines)


def _school_block(school_ids: set[str]) -> str:
    out = []
    for sid in school_ids:
        sc = lore.schools().get(sid)
        if sc:
            out.append(f"- {sc['full_name']}: {sc['summary']}")
    return "\n".join(out)


def _sensei_line(user: User) -> str:
    if user.sensei_name:
        return f"선생님의 이름은 '{user.sensei_name}'입니다. 학생들은 대개 그냥 '선생님'이라고 부릅니다."
    return "학생들은 유저를 '선생님'이라고 부릅니다."


def build_system_prompt(user: User, room: ChatRoom, bonds: dict[str, Bond]) -> str:
    studs = [s for s in (lore.student(i) for i in room.student_list) if s]
    w = lore.world()
    parts = [CORE_RULES, "[세계관 핵심]\n" + w["prompt_summary"], _sensei_line(user)]
    parts.append("[관련 학교]\n" + _school_block({s["school"] for s in studs}))
    parts.append("[등장 학생]\n" + "\n".join(_student_block(s, bonds.get(s["id"])) for s in studs))

    if room.mode == "story":
        sc = lore.scenarios().get(room.scenario_id, {})
        parts.append(
            "[스토리 모드]\n"
            "당신은 내레이터이자 모든 등장인물입니다. 장면을 묘사하고 여러 학생이 서로 대화하게 하세요.\n"
            "학생마다 말투를 확실히 구분하고, 한 응답에 모든 학생을 억지로 등장시키지 않아도 됩니다.\n"
            f"시나리오: {sc.get('title', '자유 시나리오')}\n장소: {sc.get('location', '')}\n개요: {sc.get('summary', '')}"
        )
    else:
        s = studs[0] if studs else None
        if s:
            parts.append(
                "[1:1 대화 모드]\n"
                f"당신은 {s['name']}입니다. 선생님과 단둘이 나누는 대화가 중심입니다. "
                "필요하면 지문으로 주변 상황을 묘사할 수 있지만, 다른 학생은 꼭 필요할 때만 잠깐 등장시킵니다."
            )
        if room.outfit:
            ctx = w["outfit_contexts"].get(room.outfit, "")
            parts.append(f"[현재 차림] {room.outfit} — {ctx}")

    if room.situation:
        parts.append(f"[유저가 정한 상황 설정]\n{room.situation}")
    if room.summary:
        parts.append(f"[지금까지의 줄거리 요약]\n{room.summary}")
    return "\n\n".join(parts)


def build_summary_prompt(room: ChatRoom) -> str:
    names = ", ".join(f"{s['name']}({s['id']})" for s in (lore.student(i) for i in room.student_list) if s)
    return f"""[요약 작업]
당신은 롤플레이 기록을 정리하는 서기입니다. 등장 학생: {names}
아래 대화를 읽고 JSON 하나만 출력하세요. 다른 말은 쓰지 마세요.
{{
  "room_summary": "기존 요약과 새 대화를 합친 줄거리 요약. 사건 순서, 약속, 현재 상황 위주로 8문장 이내",
  "student_memories": {{"학생id": "이 학생이 다음 만남에도 기억할 만한 선생님과의 핵심 사실 (2문장 이내)"}}
}}
주의: 요약과 기억에는 '일어난 사실'만 적고, 학생의 성격·말투·태도를 새로 규정하지 마세요. 성격은 프로필이 기준입니다.
기존 요약: {room.summary or "(없음)"}"""


def build_cast_reminder(room: ChatRoom) -> str:
    """매 턴 마지막 메시지 끝에 붙이는 인물 설정 메모. 긴 대화에서 성격이 흘러가는 것을 막는다."""
    lines = []
    for sid in room.student_list[:6]:
        s = lore.student(sid)
        if not s:
            continue
        speech = (s.get("speech") or "").split(".")[0][:70]
        rel = (s.get("relations") or "").split(".")[0][:50]
        lines.append(f"- {s['name']}: 선생님에게 {s.get('honorific', '존댓말').split(' (')[0]}, 호칭 '{s.get('call', '선생님').split(' (')[0]}'. {speech}." + (f" 관계: {rel}." if rel else ""))
    if not lines:
        return ""
    return "(시스템 메모 — 선생님의 말이 아님. 이번 응답에서 반드시 지킬 인물 설정. 앞선 답장의 말투가 달라도(설정이 바뀌기 전 기록일 수 있음) 아래와 프로필이 기준입니다)\n" + "\n".join(lines)
