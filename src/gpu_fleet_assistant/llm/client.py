from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from openai import OpenAI

from gpu_fleet_assistant.config import LLMConfig


@dataclass(frozen=True, slots=True)
class ToolCallRequest:
    """A single tool/function call requested by the LLM."""

    id: str
    name: str
    arguments_json: str


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Normalized response from a chat completion call, including telemetry."""

    content: str
    model: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tool_calls: tuple[ToolCallRequest, ...] = ()


class LLMClient(Protocol):
    """Protocol for chat-completion clients (allows easy mocking in tests)."""

    @property
    def model(self) -> str: ...

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        tools: Sequence[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> LLMResponse: ...


class OpenAICompatibleClient:
    """Thin wrapper over the OpenAI SDK for Ollama, DeepSeek, Mistral, and similar APIs."""

    def __init__(self, config: LLMConfig, *, sdk_client: Any | None = None) -> None:
        self.config = config
        self._client = sdk_client or OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout_seconds,
        )

    @property
    def model(self) -> str:
        return self.config.model

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        tools: Sequence[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": list(messages),
            "temperature": self.config.temperature,
        }
        if tools:
            kwargs["tools"] = list(tools)
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice

        start = time.perf_counter()
        completion = self._client.chat.completions.create(**kwargs)
        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)

        choice = completion.choices[0]
        message = choice.message
        content = (message.content or "").strip()

        raw_tool_calls = getattr(message, "tool_calls", None) or []
        parsed_tool_calls = tuple(
            ToolCallRequest(
                id=str(tc.id),
                name=str(tc.function.name),
                arguments_json=str(tc.function.arguments or "{}"),
            )
            for tc in raw_tool_calls
        )

        usage = getattr(completion, "usage", None)
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        total_tokens = int(
            getattr(usage, "total_tokens", 0) or (prompt_tokens + completion_tokens)
        )

        return LLMResponse(
            content=content,
            model=str(getattr(completion, "model", None) or self.config.model),
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            tool_calls=parsed_tool_calls,
        )
