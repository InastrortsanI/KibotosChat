"""세계관·학생·시나리오 목록과 유저의 관계(호감도) 조회."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import lore
from ..config import settings
from ..db import get_db
from ..llm import available_providers
from ..models import Bond, User
from ..prompts import stage_of
from ..schemas import BondOut
from ..security import current_user

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/catalog")
def catalog():
    """로그인 없이도 볼 수 있는 공개 정보. 화면이 처음 열릴 때 한 번 받아 간다."""
    w = lore.world()
    providers = available_providers()
    default = settings.llm_provider if settings.llm_provider in providers else "mock"
    return {
        "world": {"sections": w["sections"], "outfits": list(w["outfit_contexts"].keys())},
        "schools": lore.schools(),
        "students": list(lore.students().values()),
        "scenarios": list(lore.scenarios().values()),
        "providers": [{"key": p.key, "label": p.label} for p in providers.values()],
        "default_provider": default,
    }


@router.get("/bonds", response_model=list[BondOut])
def my_bonds(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Bond).where(Bond.user_id == user.id)).all()
    return [to_bond_out(b) for b in rows]


def to_bond_out(b: Bond) -> BondOut:
    return BondOut(student_id=b.student_id, affection=b.affection, memory=b.memory, stage=stage_of(b.affection)[0])
