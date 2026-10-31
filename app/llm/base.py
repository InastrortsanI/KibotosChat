"""모든 LLM 프로바이더가 따라야 하는 공통 규칙(인터페이스)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Turn:
    role: str      # "user" | "assistant"
    content: str


class LLMError(Exception):
    """API 키 누락, 네트워크 오류, 응답 형식 오류 등을 한 종류로 묶는다."""


class LLMProvider(ABC):
    key: str    # 내부 식별자 (예: "gemini")
    label: str  # 화면에 보일 이름

    @abstractmethod
    async def generate(self, system: str, turns: list[Turn], max_tokens: int = 1200) -> str:
        """시스템 프롬프트 + 대화 기록을 받아 다음 assistant 응답 텍스트를 돌려준다."""

    @staticmethod
    def normalize(turns: list[Turn]) -> list[Turn]:
        """대부분의 API는 '첫 메시지는 user', 'user/assistant 번갈아'를 요구한다.
        스토리 오프닝처럼 assistant로 시작하거나 같은 역할이 연속되면 맞춰 준다."""
        fixed: list[Turn] = []
        if turns and turns[0].role == "assistant":
            fixed.append(Turn("user", "(이야기를 시작해 주세요.)"))
        for t in turns:
            if fixed and fixed[-1].role == t.role:
                fixed[-1] = Turn(t.role, fixed[-1].content + "\n\n" + t.content)
            else:
                fixed.append(Turn(t.role, t.content))
        return fixed
