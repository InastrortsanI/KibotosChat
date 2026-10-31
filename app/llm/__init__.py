"""설정에 따라 사용할 수 있는 프로바이더를 만들어 주는 곳 (팩토리)."""
from ..config import settings
from .base import LLMError, LLMProvider, Turn
from .providers import ClaudeProvider, GeminiProvider, MockProvider, OpenAIProvider


def available_providers() -> dict[str, LLMProvider]:
    """API 키가 있는 프로바이더만 등록한다. mock은 항상 사용 가능."""
    found: dict[str, LLMProvider] = {}
    if settings.gemini_api_key:
        found["gemini"] = GeminiProvider(settings.gemini_api_key, settings.gemini_model)
    if settings.anthropic_api_key:
        found["claude"] = ClaudeProvider(settings.anthropic_api_key, settings.claude_model)
    if settings.openai_api_key:
        found["openai"] = OpenAIProvider(settings.openai_api_key, settings.openai_model)
    found["mock"] = MockProvider()
    return found


def get_provider(key: str | None = None) -> LLMProvider:
    providers = available_providers()
    key = key or settings.llm_provider
    if key not in providers:
        raise LLMError(f"'{key}' 프로바이더를 쓸 수 없습니다. .env에 API 키가 있는지 확인하세요.")
    return providers[key]


__all__ = ["LLMError", "LLMProvider", "Turn", "available_providers", "get_provider"]
