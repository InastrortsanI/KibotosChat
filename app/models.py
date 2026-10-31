"""DB 테이블 정의 (SQLAlchemy ORM)."""
from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    # 학생들이 부르는 선생님 이름 (비우면 그냥 '선생님')
    sensei_name: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[datetime] = mapped_column(default=now)


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime]


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(10))            # "single" | "story"
    title: Mapped[str] = mapped_column(String(80))
    student_ids: Mapped[str] = mapped_column(String(400))    # 쉼표로 구분: "hoshino,shiroko"
    outfit: Mapped[str] = mapped_column(String(40), default="")
    scenario_id: Mapped[str] = mapped_column(String(40), default="")
    situation: Mapped[str] = mapped_column(Text, default="")  # 유저가 직접 적은 상황 설정
    summary: Mapped[str] = mapped_column(Text, default="")    # 오래된 대화를 압축한 기억
    summarized_count: Mapped[int] = mapped_column(default=0)  # 요약에 흡수된 메시지 수
    created_at: Mapped[datetime] = mapped_column(default=now)
    updated_at: Mapped[datetime] = mapped_column(default=now, onupdate=now)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="room", cascade="all, delete-orphan", order_by="Message.id"
    )

    @property
    def student_list(self) -> list[str]:
        return [s for s in self.student_ids.split(",") if s]


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("chat_rooms.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(10))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    # 이 응답으로 바뀐 호감도 {"hoshino": 1} — 재생성·되돌리기 때 원상복구하려고 저장한다.
    affection: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=now)

    room: Mapped[ChatRoom] = relationship(back_populates="messages")


class Bond(Base):
    """선생님과 학생 한 명 사이의 관계. 채팅방이 달라도 공유된다."""
    __tablename__ = "bonds"
    __table_args__ = (UniqueConstraint("user_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[str] = mapped_column(String(40))
    affection: Mapped[int] = mapped_column(default=20)   # 0~100, 20 = '익숙함'(원작처럼 이미 아는 사이)
    memory: Mapped[str] = mapped_column(Text, default="")  # 방을 넘어 기억할 핵심 사실
