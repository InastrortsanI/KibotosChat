"""실제 LLM API 구현체들. 각 회사의 REST API를 httpx로 직접 호출한다."""
import random
import re

import httpx

from .base import LLMError, LLMProvider, Turn

TIMEOUT = httpx.Timeout(90.0)


async def _post(url: str, headers: dict, body: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            res = await client.post(url, headers=headers, json=body)
    except httpx.HTTPError as e:
        raise LLMError(f"API 서버에 연결하지 못했습니다: {e}") from e
    if res.status_code != 200:
        raise LLMError(f"API 오류 {res.status_code}: {res.text[:300]}")
    return res.json()


class GeminiProvider(LLMProvider):
    key, label = "gemini", "Gemini"

    def __init__(self, api_key: str, model: str):
        self.api_key, self.model = api_key, model

    async def generate(self, system, turns, max_tokens=1200):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [
                # Gemini는 assistant 역할을 "model"이라고 부른다.
                {"role": "model" if t.role == "assistant" else "user", "parts": [{"text": t.content}]}
                for t in self.normalize(turns)
            ],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.9},
        }
        data = await _post(url, {"x-goog-api-key": self.api_key}, body)
        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts).strip()
        except (KeyError, IndexError) as e:
            raise LLMError(f"Gemini 응답을 해석하지 못했습니다: {str(data)[:300]}") from e


class ClaudeProvider(LLMProvider):
    key, label = "claude", "Claude"

    def __init__(self, api_key: str, model: str):
        self.api_key, self.model = api_key, model

    async def generate(self, system, turns, max_tokens=1200):
        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": t.role, "content": t.content} for t in self.normalize(turns)],
        }
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
        data = await _post("https://api.anthropic.com/v1/messages", headers, body)
        try:
            return "".join(b["text"] for b in data["content"] if b.get("type") == "text").strip()
        except KeyError as e:
            raise LLMError(f"Claude 응답을 해석하지 못했습니다: {str(data)[:300]}") from e


class OpenAIProvider(LLMProvider):
    key, label = "openai", "OpenAI"

    def __init__(self, api_key: str, model: str):
        self.api_key, self.model = api_key, model

    async def generate(self, system, turns, max_tokens=1200):
        messages = [{"role": "system", "content": system}]
        messages += [{"role": t.role, "content": t.content} for t in self.normalize(turns)]
        body = {"model": self.model, "messages": messages, "max_completion_tokens": max_tokens}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = await _post("https://api.openai.com/v1/chat/completions", headers, body)
        try:
            return (data["choices"][0]["message"]["content"] or "").strip()
        except (KeyError, IndexError) as e:
            raise LLMError(f"OpenAI 응답을 해석하지 못했습니다: {str(data)[:300]}") from e


class MockProvider(LLMProvider):
    """API 키 없이 전체 흐름을 테스트하기 위한 가짜 응답기.
    프롬프트의 [등장 학생] 목록을 읽어 형식만 맞춘 답을 만든다."""
    key, label = "mock", "테스트용 (Mock)"

    async def generate(self, system, turns, max_tokens=1200):
        if "[요약 작업]" in system:
            return '{"room_summary": "테스트 요약입니다.", "student_memories": {}}'
        speakers = re.findall(r"^- (.+?) \(id: ([\w*]+)\)", system, re.M) or [("학생", "unknown")]
        last = next((t.content for t in reversed(turns) if t.role == "user"), "")
        lines = [f"*{speakers[0][0]}이(가) 선생님의 말을 듣고 잠시 생각에 잠긴다.*"]
        for name, sid in speakers[:3]:
            lines.append(f'{name}: "선생님, 방금 \'{last[:20]}\'라고 하셨죠? 이건 테스트 응답이에요."')
        lines.append(f"[호감도 {speakers[0][1]}:{random.choice(['+1', '0'])}]")
        return "\n\n".join(lines)
