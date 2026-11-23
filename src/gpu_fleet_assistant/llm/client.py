from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from openai import OpenAI

from gpu_fleet_assistant.config import LLMConfig

_THINK_TAG_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


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


def _extract_text_content(raw_content: Any) -> str:
    """Normalize string or structured content-block lists to clean user-facing text."""
    if raw_content is None:
        return ""
    if isinstance(raw_content, str):
        return _THINK_TAG_RE.sub("", raw_content).strip()
    if isinstance(raw_content, list):
        parts: list[str] = []
        for block in raw_content:
            if isinstance(block, str):
                cleaned = _THINK_TAG_RE.sub("", block).strip()
                if cleaned:
                    parts.append(cleaned)
                continue
            block_type = (
                block.get("type")
                if isinstance(block, dict)
                else getattr(block, "type", None)
            )
            if block_type == "text":
                text = (
                    block.get("text")
                    if isinstance(block, dict)
                    else getattr(block, "text", None)
                )
                if isinstance(text, str):
                    cleaned = _THINK_TAG_RE.sub("", text).strip()
                    if cleaned:
                        parts.append(cleaned)
        return "\n".join(parts).strip()
    return _THINK_TAG_RE.sub("", str(raw_content)).strip()


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
        if self.config.temperature == 0.0:
            # Required by providers like Mistral when using greedy sampling (temperature=0).
            kwargs["top_p"] = 1.0
        if tools:
            kwargs["tools"] = list(tools)
            if tool_choice is not None:
                kwargs["tool_choice"] = tool_choice

        start = time.perf_counter()
        completion = self._client.chat.completions.create(**kwargs)
        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)

        choice = completion.choices[0]
        message = choice.message
        content = _extract_text_content(message.content)

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
