"""비밀번호 해싱과 로그인 토큰. 표준 라이브러리만 사용한다."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import AuthToken, User

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS).hex()
    return hmac.compare_digest(check, digest)  # 비교 시간을 일정하게 해 타이밍 공격을 막는다


def issue_token(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=settings.token_days)
    db.add(AuthToken(token=token, user_id=user.id, expires_at=expires))
    db.commit()
    return token


def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)) -> User:
    """'Authorization: Bearer <토큰>' 헤더로 로그인한 유저를 찾는다."""
    token = authorization.removeprefix("Bearer ").strip()
    row = db.get(AuthToken, token) if token else None
    if row is None or row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(401, "로그인이 필요합니다.")
    user = db.get(User, row.user_id)
    if user is None:
        raise HTTPException(401, "로그인이 필요합니다.")
    return user
