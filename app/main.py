"""서버 진입점. 실행: uvicorn app.main:app --reload"""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import Base, engine
from .routers import auth, catalog, chats

Base.metadata.create_all(engine)  # 테이블이 없으면 만든다 (처음 실행할 때)

app = FastAPI(title="키보토스 채팅", version="1.0")
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(chats.router)

app.mount("/static", StaticFiles(directory=settings.frontend_dir), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(settings.frontend_dir / "index.html")
