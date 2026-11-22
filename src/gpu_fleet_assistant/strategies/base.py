from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol, Sequence

MessageRole = Literal["user", "assistant"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Single conversational turn exchanged between user and assistant."""

    role: MessageRole
    content: str

    def to_openai_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True, slots=True)
class ToolCallTrace:
    """Observability record of a tool invocation executed during a turn."""

    name: str
    arguments: dict[str, Any]
    result: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "arguments": self.arguments,
            "result": self.result,
        }


@dataclass(frozen=True, slots=True)
class AssistantResponse:
    """Standardized output returned by every assistant strategy."""

    answer: str
    strategy: str
    model: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    llm_calls: int = 1
    tool_calls: tuple[ToolCallTrace, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "strategy": self.strategy,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_calls,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
        }


class AssistantStrategy(Protocol):
    """Common interface implemented by Prompt Stuffing, Tool Calling, etc."""

    @property
    def name(self) -> str: ...

    def chat(
        self,
        message: str,
        history: Sequence[ChatMessage] | None = None,
    ) -> AssistantResponse: ...
