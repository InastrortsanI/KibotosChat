"""호감도 태그 처리와 대화 요약(기억) 처리."""
import json
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import lore
from .config import settings
from .llm import LLMError, LLMProvider, Turn
from .models import Bond, ChatRoom
from .prompts import build_summary_prompt

AFFECTION_TAG = re.compile(r"\[호감도\s+([\w*]+)\s*:\s*([+-]?\d+)\]")


def split_affection(text: str) -> tuple[str, dict[str, int]]:
    """응답에서 [호감도 id:+1] 태그를 떼어 내고, {학생id: 변화량}을 돌려준다."""
    changes: dict[str, int] = {}
    for sid, delta in AFFECTION_TAG.findall(text):
        changes[sid] = max(-5, min(5, int(delta)))  # 모델이 과하게 줘도 ±5로 자른다
    return AFFECTION_TAG.sub("", text).strip(), changes


def get_bonds(db: Session, user_id: int, student_ids: list[str]) -> dict[str, Bond]:
    """학생별 Bond 행을 가져오고, 없으면 새로 만든다."""
    rows = db.scalars(select(Bond).where(Bond.user_id == user_id, Bond.student_id.in_(student_ids))).all()
    bonds = {b.student_id: b for b in rows}
    for sid in student_ids:
        if sid not in bonds and lore.student(sid):
            bonds[sid] = Bond(user_id=user_id, student_id=sid)
            db.add(bonds[sid])
    return bonds


def apply_affection(bonds: dict[str, Bond], changes: dict[str, int]) -> dict[str, int]:
    applied = {}
    for sid, delta in changes.items():
        if sid in bonds:  # 방에 없는 학생 id를 모델이 지어내면 무시
            b = bonds[sid]
            b.affection = max(0, min(100, b.affection + delta))
            applied[sid] = delta
    return applied


USER_PART = re.compile(r'\*([^*]+)(?:\*|$)|["“]([^"”]*)(?:["”]|$)|[(（]([^)）]*)(?:[)）]|$)|([^*"“”(（]+)')


def label_user_input(text: str) -> str:
    """선생님 입력을 '행동'(*별표*)과 '말'로 나눠 이름표를 붙인다. 표시가 없으면 그대로 둔다."""
    if not re.search(r'[*"“”(（]', text):
        return text
    out = []
    for act, said, ooc, rest in USER_PART.findall(text):
        if act.strip():
            out.append(f"[선생님의 행동 — 이미 일어난 일] {act.strip()}")
        elif ooc.strip():
            out.append(f"[연출 지시 — 이야기 밖에서 유저가 내린 지시. 아무도 듣지 못함. 이번 응답에 반드시 반영] {ooc.strip()}")
        elif (said or rest).strip():
            out.append(f'[선생님의 말] "{(said or rest).strip()}"')
    return "\n".join(out) or text


def history_turns(room: ChatRoom) -> list[Turn]:
    """요약에 아직 흡수되지 않은 최근 대화만 LLM에 보낸다."""
    return [Turn(m.role, label_user_input(m.content) if m.role == "user" else m.content)
            for m in room.messages[room.summarized_count:]]


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


async def maybe_summarize(room: ChatRoom, bonds: dict[str, Bond], provider: LLMProvider) -> bool:
    """대화가 길어지면 오래된 부분을 요약해 room.summary 와 Bond.memory 로 옮긴다."""
    pending = room.messages[room.summarized_count:]
    if len(pending) <= settings.summary_trigger:
        return False

    chunk = pending[: len(pending) - settings.keep_recent]
    transcript = "\n".join(f"{'선생님' if m.role == 'user' else '이야기'}: {m.content}" for m in chunk)
    memories = "\n".join(f"- {sid}: {b.memory or '(없음)'}" for sid, b in bonds.items())
    system = build_summary_prompt(room) + f"\n학생별 기존 기억:\n{memories}"

    try:
        data = _parse_json(await provider.generate(system, [Turn("user", transcript)], max_tokens=800))
    except (LLMError, ValueError):
        return False  # 요약 실패는 치명적이지 않다. 다음 메시지 때 다시 시도한다.

    room.summary = str(data.get("room_summary", room.summary))[:2000]
    for sid, mem in (data.get("student_memories") or {}).items():
        if sid in bonds and mem:
            bonds[sid].memory = str(mem)[:400]
    room.summarized_count += len(chunk)
    return True
