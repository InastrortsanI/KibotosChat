"""DB 연결과 세션 관리."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# SQLite는 기본적으로 한 스레드에서만 쓰도록 막혀 있어서, 웹 서버용으로 풀어 준다.
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """요청 하나마다 세션을 열고, 끝나면 반드시 닫는다 (FastAPI 의존성)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
