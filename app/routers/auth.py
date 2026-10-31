from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import AuthToken, User
from ..schemas import AuthIn, AuthOut, ProfileIn, UserOut
from ..security import current_user, hash_password, issue_token, verify_password

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth/register", response_model=AuthOut)
def register(body: AuthIn, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == body.username)):
        raise HTTPException(409, "이미 사용 중인 아이디입니다.")
    user = User(username=body.username, password_hash=hash_password(body.password),
                sensei_name=body.sensei_name.strip())
    db.add(user)
    db.commit()
    return AuthOut(token=issue_token(db, user), user=UserOut.model_validate(user))


@router.post("/auth/login", response_model=AuthOut)
def login(body: AuthIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    # 아이디가 없는지, 비밀번호가 틀렸는지 구분해 알려 주지 않는다 (계정 존재 여부 노출 방지).
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "아이디 또는 비밀번호가 올바르지 않습니다.")
    return AuthOut(token=issue_token(db, user), user=UserOut.model_validate(user))


@router.post("/auth/logout")
def logout(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    db.execute(delete(AuthToken).where(AuthToken.token == authorization.removeprefix("Bearer ").strip()))
    db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    # current_user 와 이 함수는 같은 요청 안에서 같은 DB 세션을 공유하므로 바로 수정하면 된다.
    user.sensei_name = body.sensei_name.strip()
    db.commit()
    return user
