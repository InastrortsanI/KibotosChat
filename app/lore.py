"""data/ 폴더의 세계관 JSON을 한 번만 읽어 메모리에 들고 있는 모듈."""
import json
from functools import lru_cache

from .config import settings


def _load(name: str):
    with open(settings.data_dir / name, encoding="utf-8") as f:
        return json.load(f)


@lru_cache  # 처음 한 번만 파일을 읽고, 이후엔 결과를 재사용한다.
def world() -> dict:
    return _load("world.json")


@lru_cache
def schools() -> dict[str, dict]:
    return _load("schools.json")


@lru_cache
def students() -> dict[str, dict]:
    return {s["id"]: s for s in _load("students.json")}


@lru_cache
def scenarios() -> dict[str, dict]:
    return {s["id"]: s for s in _load("scenarios.json")}


def student(sid: str) -> dict | None:
    return students().get(sid)
