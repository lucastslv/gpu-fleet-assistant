from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Sequence

import pytest

from gpu_fleet_assistant.config import LLMConfig
from gpu_fleet_assistant.db import GPURepository
from gpu_fleet_assistant.llm import LLMResponse, OpenAICompatibleClient
from gpu_fleet_assistant.strategies import ChatMessage, PromptStuffingStrategy


class FakeLLMClient:
    def __init__(self, reply: str = "Sim, existem 4 NVIDIA A100 disponíveis.") -> None:
        self.reply = reply
        self.calls: list[list[dict[str, Any]]] = []

    @property
    def model(self) -> str:
        return "fake-model"

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        tools: Sequence[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.calls.append(list(messages))
        return LLMResponse(
            content=self.reply,
            model=self.model,
            latency_ms=12.5,
            prompt_tokens=200,
            completion_tokens=20,
            total_tokens=220,
        )


@pytest.fixture()
def repo() -> GPURepository:
    repository = GPURepository(":memory:")
    repository.initialize(seed=True)
    yield repository
    repository.close()


def test_prompt_stuffing_injects_live_sqlite_snapshot(repo: GPURepository) -> None:
    repo.set_available_quantity("NVIDIA A100", 2)
    fake_llm = FakeLLMClient()
    strategy = PromptStuffingStrategy(repo, fake_llm)

    result = strategy.chat("Existem duas A100 disponíveis?")

    assert result.strategy == "prompt_stuffing"
    assert result.answer == "Sim, existem 4 NVIDIA A100 disponíveis."
    assert result.model == "fake-model"
    assert result.llm_calls == 1
    assert result.tool_calls == ()
    assert result.total_tokens == 220

    sent_messages = fake_llm.calls[0]
    assert sent_messages[0]["role"] == "system"
    system_prompt = sent_messages[0]["content"]
    assert "| NVIDIA A100 | 4 | 2 | 2 | 80 | 160 |" in system_prompt
    assert "NVIDIA H100" in system_prompt
    assert "NVIDIA RTX 4090" in system_prompt
    assert sent_messages[-1] == {"role": "user", "content": "Existem duas A100 disponíveis?"}


def test_prompt_stuffing_preserves_conversation_history(repo: GPURepository) -> None:
    fake_llm = FakeLLMClient(reply="Cada uma tem 80 GB.")
    strategy = PromptStuffingStrategy(repo, fake_llm)
    history = [
        ChatMessage(role="user", content="Quais GPUs temos?"),
        ChatMessage(role="assistant", content="Temos A100, L40S, RTX 4090, H100 e A40."),
    ]

    strategy.chat("Qual a memória da A100?", history=history)

    sent_messages = fake_llm.calls[0]
    assert [m["role"] for m in sent_messages] == ["system", "user", "assistant", "user"]
    assert sent_messages[1]["content"] == "Quais GPUs temos?"
    assert sent_messages[2]["content"] == "Temos A100, L40S, RTX 4090, H100 e A40."
    assert sent_messages[3]["content"] == "Qual a memória da A100?"


def test_prompt_stuffing_rejects_empty_message(repo: GPURepository) -> None:
    strategy = PromptStuffingStrategy(repo, FakeLLMClient())
    with pytest.raises(ValueError, match="empty"):
        strategy.chat("   ")


def test_openai_compatible_client_parses_content_usage_and_tool_calls() -> None:
    fake_completion = SimpleNamespace(
        model="qwen2.5:7b",
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="Consultando ferramentas...",
                    tool_calls=[
                        SimpleNamespace(
                            id="call_1",
                            function=SimpleNamespace(
                                name="check_availability",
                                arguments='{"name": "A100", "quantity": 2}',
                            ),
                        )
                    ],
                )
            )
        ],
        usage=SimpleNamespace(prompt_tokens=100, completion_tokens=25, total_tokens=125),
    )

    captured_kwargs: dict[str, Any] = {}

    def fake_create(**kwargs: Any) -> Any:
        captured_kwargs.update(kwargs)
        return fake_completion

    fake_sdk = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
    )
    client = OpenAICompatibleClient(
        LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434/v1",
            model="qwen2.5:7b",
            api_key="ollama",
        ),
        sdk_client=fake_sdk,
    )

    resp = client.complete(
        [{"role": "user", "content": "Tem A100?"}],
        tools=[{"type": "function", "function": {"name": "check_availability"}}],
        tool_choice="auto",
    )

    assert captured_kwargs["model"] == "qwen2.5:7b"
    assert captured_kwargs["tool_choice"] == "auto"
    assert resp.content == "Consultando ferramentas..."
    assert resp.prompt_tokens == 100
    assert resp.completion_tokens == 25
    assert resp.total_tokens == 125
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "check_availability"
    assert resp.tool_calls[0].arguments_json == '{"name": "A100", "quantity": 2}'
