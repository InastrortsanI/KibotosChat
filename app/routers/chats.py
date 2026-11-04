"""채팅방 생성·조회와 대화 진행."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import lore
from ..db import get_db
from ..llm import LLMError, Turn, get_provider
from ..memory import apply_affection, get_bonds, history_turns, maybe_summarize, split_affection
from ..models import ChatRoom, Message, User, now
from ..prompts import OBEY_NOTE, build_cast_reminder, build_system_prompt
from ..schemas import MessageOut, RoomCreate, RoomDetail, RoomOut, SendIn, TurnOut
from ..security import current_user
from .catalog import to_bond_out

router = APIRouter(prefix="/api/rooms", tags=["chat"])


def _own_room(db: Session, user: User, room_id: int) -> ChatRoom:
    room = db.get(ChatRoom, room_id)
    if room is None or room.user_id != user.id:  # 남의 방은 '없는 방'으로 취급
        raise HTTPException(404, "대화방을 찾을 수 없습니다.")
    return room


@router.get("", response_model=list[RoomOut])
def list_rooms(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(ChatRoom).where(ChatRoom.user_id == user.id).order_by(ChatRoom.updated_at.desc())
    return db.scalars(q).all()


@router.post("", response_model=RoomDetail)
def create_room(body: RoomCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    unknown = [s for s in body.student_ids if not lore.student(s)]
    if unknown:
        raise HTTPException(400, f"없는 학생입니다: {', '.join(unknown)}")
    if body.mode == "single" and len(body.student_ids) != 1:
        raise HTTPException(400, "1:1 대화는 학생 한 명만 선택할 수 있습니다.")

    first = lore.student(body.student_ids[0])
    scenario = lore.scenarios().get(body.scenario_id) if body.scenario_id else None
    if body.mode == "story":
        title = scenario["title"] if scenario else "자유 스토리"
    else:
        title = first["name"] + (f" ({body.outfit})" if body.outfit else "")

    room = ChatRoom(user_id=user.id, mode=body.mode, title=title, student_ids=",".join(body.student_ids),
                    outfit=body.outfit, scenario_id=body.scenario_id, situation=body.situation.strip())
    db.add(room)
    if scenario and scenario.get("opening"):
        # 스토리 오프닝은 미리 써 둔 글로 시작한다 (LLM 호출 없이 즉시 표시).
        room.messages.append(Message(role="assistant", content=scenario["opening"]))
    get_bonds(db, user.id, body.student_ids)
    db.commit()
    return room


@router.get("/{room_id}", response_model=RoomDetail)
def get_room(room_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return _own_room(db, user, room_id)


@router.delete("/{room_id}")
def delete_room(room_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(_own_room(db, user, room_id))
    db.commit()
    return {"ok": True}


async def _generate(db: Session, user: User, room: ChatRoom, provider_key: str | None) -> TurnOut:
    """현재 대화 기록으로 다음 응답을 만들고, 호감도·요약까지 처리한다."""
    try:
        provider = get_provider(provider_key)
    except LLMError as e:
        raise HTTPException(400, str(e))

    bonds = get_bonds(db, user.id, room.student_list)
    turns = history_turns(room)
    teacher_spoke = bool(turns) and turns[-1].role == "user"
    if not teacher_spoke:
        # 유저 입력 없이 '이어서 진행'할 때: 모델이 다음 장면을 쓰도록 짧은 지시를 덧붙인다.
        turns.append(Turn("user", "(선생님은 잠시 지켜본다. 장면을 자연스럽게 이어 주세요.)"))
    memo = build_cast_reminder(room)
    if teacher_spoke:
        # 모델은 메시지 맨 끝을 가장 강하게 따르므로, 인물 메모를 앞에 두고 선생님의 입력을 맨 뒤에 놓는다.
        turns[-1] = Turn("user", (memo + "\n\n" if memo else "") + "[이번 선생님의 입력 — 이번 응답에서 가장 먼저, 쓰인 그대로 따를 것]\n"
                         + turns[-1].content + "\n\n" + OBEY_NOTE)
    elif memo:
        turns[-1] = Turn(turns[-1].role, turns[-1].content + "\n\n" + memo)

    try:
        raw = await provider.generate(build_system_prompt(user, room, bonds), turns)
    except LLMError as e:
        db.rollback()
        raise HTTPException(502, str(e))

    text, changes = split_affection(raw)
    applied = apply_affection(bonds, changes)
    reply = Message(role="assistant", content=text or "*(응답이 비어 있습니다. 다시 생성해 보세요.)*", affection=applied)
    room.messages.append(reply)
    summarized = await maybe_summarize(room, bonds, provider)
    room.updated_at = now()  # 메시지만 추가되면 방 행은 안 바뀌므로 직접 갱신
    db.commit()
    return TurnOut(messages=[MessageOut.model_validate(reply)],
                   bonds=[to_bond_out(b) for b in bonds.values()], summarized=summarized)


@router.post("/{room_id}/messages", response_model=TurnOut)
async def send_message(room_id: int, body: SendIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    room = _own_room(db, user, room_id)
    if not body.content.strip():
        raise HTTPException(400, "메시지를 입력하세요.")
    mine = Message(role="user", content=body.content.strip())
    room.messages.append(mine)
    db.flush()  # id를 받기 위해 DB에 먼저 반영 (commit은 응답까지 끝난 뒤에)
    out = await _generate(db, user, room, body.provider)
    out.messages.insert(0, MessageOut.model_validate(mine))
    return out


@router.post("/{room_id}/continue", response_model=TurnOut)
async def continue_story(room_id: int, body: SendIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return await _generate(db, user, _own_room(db, user, room_id), body.provider)


def _revert(room: ChatRoom, bonds: dict, msg: Message) -> None:
    for sid, delta in (msg.affection or {}).items():
        if sid in bonds:
            bonds[sid].affection = max(0, min(100, bonds[sid].affection - delta))
    room.messages.remove(msg)


@router.post("/{room_id}/regenerate", response_model=TurnOut)
async def regenerate(room_id: int, body: SendIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    room = _own_room(db, user, room_id)
    last = room.messages[-1] if room.messages else None
    if last is None or last.role != "assistant" or len(room.messages) <= room.summarized_count:
        raise HTTPException(400, "다시 생성할 응답이 없습니다.")
    _revert(room, get_bonds(db, user.id, room.student_list), last)
    db.flush()
    return await _generate(db, user, room, body.provider)


@router.delete("/{room_id}/messages/last", response_model=RoomDetail)
def undo(room_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    """마지막 '선생님 입력 + 그에 대한 응답'을 통째로 되돌린다."""
    room = _own_room(db, user, room_id)
    bonds = get_bonds(db, user.id, room.student_list)
    while room.messages and len(room.messages) > room.summarized_count:
        msg = room.messages[-1]
        _revert(room, bonds, msg)
        if msg.role == "user":
            break
    db.commit()
    return room
