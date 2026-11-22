from __future__ import annotations

import json
from typing import Any, Sequence

import pytest

from gpu_fleet_assistant.db import GPURepository
from gpu_fleet_assistant.llm import LLMResponse, ToolCallRequest
from gpu_fleet_assistant.strategies import (
    TOOL_DEFINITIONS,
    ChatMessage,
    ToolCallingStrategy,
)


class ScriptedLLMClient:
    """Deterministic fake LLM client that replays a sequence of LLMResponse objects."""

    def __init__(self, responses: Sequence[LLMResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    @property
    def model(self) -> str:
        return "scripted-model"

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        tools: Sequence[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.calls.append(
            {
                "messages": list(messages),
                "tools": list(tools) if tools is not None else None,
                "tool_choice": tool_choice,
            }
        )
        return self._responses.pop(0)


@pytest.fixture()
def repo() -> GPURepository:
    repository = GPURepository(":memory:")
    repository.initialize(seed=True)
    yield repository
    repository.close()


def test_only_read_only_tools_are_exposed() -> None:
    tool_names = {tool["function"]["name"] for tool in TOOL_DEFINITIONS}
    assert tool_names == {
        "list_gpus",
        "find_gpus",
        "check_availability",
        "get_fleet_summary",
    }


def test_tool_calling_executes_check_availability_and_aggregates_telemetry(
    repo: GPURepository,
) -> None:
    repo.set_available_quantity("NVIDIA A100", 2)
    client = ScriptedLLMClient(
        [
            LLMResponse(
                content="",
                model="qwen2.5:7b",
                latency_ms=40.0,
                prompt_tokens=150,
                completion_tokens=20,
                total_tokens=170,
                tool_calls=(
                    ToolCallRequest(
                        id="call_1",
                        name="check_availability",
                        arguments_json='{"name": "A100", "quantity": 2}',
                    ),
                ),
            ),
            LLMResponse(
                content="Sim, existem 2 NVIDIA A100 disponíveis no momento.",
                model="qwen2.5:7b",
                latency_ms=35.5,
                prompt_tokens=220,
                completion_tokens=18,
                total_tokens=238,
            ),
        ]
    )

    strategy = ToolCallingStrategy(repo, client)
    result = strategy.chat("Existem duas A100 disponíveis?")

    assert result.strategy == "tool_calling"
    assert result.answer == "Sim, existem 2 NVIDIA A100 disponíveis no momento."
    assert result.llm_calls == 2
    assert result.latency_ms == 75.5
    assert result.prompt_tokens == 370
    assert result.completion_tokens == 38
    assert result.total_tokens == 408
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "check_availability"
    assert result.tool_calls[0].arguments == {"name": "A100", "quantity": 2}
    assert result.tool_calls[0].result["found"] is True
    assert result.tool_calls[0].result["is_available"] is True
    assert result.tool_calls[0].result["gpu"]["available_quantity"] == 2

    # Second LLM call must receive the serialized tool result message
    second_messages = client.calls[1]["messages"]
    tool_msg = second_messages[-1]
    assert tool_msg["role"] == "tool"
    assert tool_msg["tool_call_id"] == "call_1"
    payload = json.loads(tool_msg["content"])
    assert payload["is_available"] is True


def test_tool_calling_supports_multiple_tools_in_single_turn(repo: GPURepository) -> None:
    client = ScriptedLLMClient(
        [
            LLMResponse(
                content="",
                model="deepseek-chat",
                latency_ms=50.0,
                tool_calls=(
                    ToolCallRequest(
                        id="call_a",
                        name="find_gpus",
                        arguments_json='{"min_memory_gb": 80}',
                    ),
                    ToolCallRequest(
                        id="call_b",
                        name="get_fleet_summary",
                        arguments_json="{}",
                    ),
                ),
            ),
            LLMResponse(
                content="Temos A100 e H100 com 80 GB, dentro de 19 GPUs totais.",
                model="deepseek-chat",
                latency_ms=30.0,
            ),
        ]
    )

    strategy = ToolCallingStrategy(repo, client)
    result = strategy.chat("Quais GPUs têm 80 GB e quantas GPUs temos no total?")

    assert len(result.tool_calls) == 2
    assert [g["name"] for g in result.tool_calls[0].result["gpus"]] == [
        "NVIDIA A100",
        "NVIDIA H100",
    ]
    assert result.tool_calls[1].result["total_gpus"] == 19


def test_tool_calling_handles_invalid_json_unknown_tool_and_bad_args(
    repo: GPURepository,
) -> None:
    client = ScriptedLLMClient(
        [
            LLMResponse(
                content="",
                model="qwen2.5:7b",
                latency_ms=20.0,
                tool_calls=(
                    ToolCallRequest(
                        id="call_bad_json",
                        name="list_gpus",
                        arguments_json="{broken json",
                    ),
                    ToolCallRequest(
                        id="call_unknown",
                        name="delete_all_gpus",
                        arguments_json="{}",
                    ),
                    ToolCallRequest(
                        id="call_bad_qty",
                        name="check_availability",
                        arguments_json='{"name": "A100", "quantity": 0}',
                    ),
                ),
            ),
            LLMResponse(
                content="Não foi possível executar essa operação.",
                model="qwen2.5:7b",
                latency_ms=15.0,
            ),
        ]
    )

    strategy = ToolCallingStrategy(repo, client)
    result = strategy.chat("Teste de robustez")

    assert result.llm_calls == 2
    assert "Invalid JSON" in result.tool_calls[0].result["error"]
    assert "Unknown tool" in result.tool_calls[1].result["error"]
    assert "at least 1" in result.tool_calls[2].result["error"]


def test_tool_calling_enforces_max_steps_and_forces_final_answer(
    repo: GPURepository,
) -> None:
    loop_call = LLMResponse(
        content="",
        model="qwen2.5:7b",
        latency_ms=10.0,
        tool_calls=(
            ToolCallRequest(
                id="call_loop",
                name="list_gpus",
                arguments_json="{}",
            ),
        ),
    )
    final_answer = LLMResponse(
        content="Temos 5 modelos de GPU disponíveis.",
        model="qwen2.5:7b",
        latency_ms=12.0,
    )
    client = ScriptedLLMClient([loop_call, loop_call, final_answer])

    strategy = ToolCallingStrategy(repo, client, max_steps=2)
    result = strategy.chat("Quais GPUs temos?")

    assert result.llm_calls == 3
    assert result.answer == "Temos 5 modelos de GPU disponíveis."
    # The fallback call after max_steps must not pass tools
    assert client.calls[0]["tools"] is not None
    assert client.calls[1]["tools"] is not None
    assert client.calls[2]["tools"] is None


def test_tool_calling_preserves_history_and_rejects_empty_message(
    repo: GPURepository,
) -> None:
    client = ScriptedLLMClient(
        [LLMResponse(content="Resposta direta.", model="qwen2.5:7b", latency_ms=10.0)]
    )
    strategy = ToolCallingStrategy(repo, client)
    history = [
        ChatMessage(role="user", content="Oi"),
        ChatMessage(role="assistant", content="Olá! Como posso ajudar?"),
    ]

    strategy.chat("Obrigado", history=history)
    sent = client.calls[0]["messages"]
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]

    with pytest.raises(ValueError, match="empty"):
        strategy.chat("   ")
