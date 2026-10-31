"""API가 주고받는 데이터 모양 (Pydantic). 잘못된 입력은 여기서 자동으로 걸러진다."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AuthIn(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=100)
    sensei_name: str = Field(default="", max_length=20)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # ORM 객체를 바로 변환할 수 있게
    id: int
    username: str
    sensei_name: str


class AuthOut(BaseModel):
    token: str
    user: UserOut


class ProfileIn(BaseModel):
    sensei_name: str = Field(max_length=20)


class BondOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    student_id: str
    affection: int
    memory: str
    stage: str = ""


class RoomCreate(BaseModel):
    mode: Literal["single", "story"]
    student_ids: list[str] = Field(min_length=1, max_length=6)
    outfit: str = Field(default="", max_length=40)
    scenario_id: str = Field(default="", max_length=40)
    situation: str = Field(default="", max_length=1000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    affection: dict
    created_at: datetime


class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    mode: str
    title: str
    student_list: list[str]
    outfit: str
    scenario_id: str
    situation: str
    summary: str
    updated_at: datetime


class RoomDetail(RoomOut):
    messages: list[MessageOut]


class SendIn(BaseModel):
    content: str = Field(default="", max_length=2000)
    provider: str | None = None


class TurnOut(BaseModel):
    messages: list[MessageOut]   # 이번 요청으로 새로 생긴 메시지들
    bonds: list[BondOut]         # 변화가 반영된 관계 상태
    summarized: bool
