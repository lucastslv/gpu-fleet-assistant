from __future__ import annotations

from typing import Any, Sequence

import pytest
from fastapi.testclient import TestClient

from gpu_fleet_assistant.db import GPURepository
from gpu_fleet_assistant.llm import LLMResponse, ToolCallRequest
from gpu_fleet_assistant.web import create_app


class StubWebLLMClient:
    def __init__(self, model_name: str = "stub-web-model") -> None:
        self._model = model_name

    @property
    def model(self) -> str:
        return self._model

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        tools: Sequence[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> LLMResponse:
        has_tool_result = any(m["role"] == "tool" for m in messages)
        if tools and not has_tool_result:
            return LLMResponse(
                content="",
                model=self._model,
                latency_ms=15.0,
                prompt_tokens=100,
                completion_tokens=15,
                total_tokens=115,
                tool_calls=(
                    ToolCallRequest(
                        id="web_tc_1",
                        name="check_availability",
                        arguments_json='{"name": "A100", "quantity": 2}',
                    ),
                ),
            )
        return LLMResponse(
            content="Sim, existem 4 NVIDIA A100 disponíveis.",
            model=self._model,
            latency_ms=20.0,
            prompt_tokens=150,
            completion_tokens=12,
            total_tokens=162,
        )


@pytest.fixture()
def client() -> TestClient:
    repo = GPURepository(":memory:")
    repo.initialize(seed=True)
    app = create_app(
        repository=repo,
        client_factory=lambda provider, model: StubWebLLMClient(model or f"stub-{provider}"),
    )
    with TestClient(app) as test_client:
        yield test_client
    repo.close()


def test_index_and_health_endpoints(client: TestClient) -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    page = client.get("/")
    assert page.status_code == 200
    assert "GPU Fleet Assistant" in page.text


def test_config_endpoint_exposes_providers_without_secrets(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-super-secret-value")
    resp = client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["strategies"] == ["tool_calling", "prompt_stuffing"]
    assert "sk-super-secret-value" not in resp.text


def test_gpus_list_update_and_reset(client: TestClient) -> None:
    initial = client.get("/api/gpus")
    assert initial.status_code == 200
    data = initial.json()
    assert len(data["gpus"]) == 5
    assert data["summary"]["total_gpus"] == 19
    assert data["summary"]["total_memory_gb"] == 1032

    patch_ok = client.patch("/api/gpus/NVIDIA A100", json={"available_quantity": 1})
    assert patch_ok.status_code == 200
    assert patch_ok.json()["gpu"]["available_quantity"] == 1
    assert patch_ok.json()["summary"]["available_gpus"] == 16

    patch_oob = client.patch("/api/gpus/NVIDIA A100", json={"available_quantity": 99})
    assert patch_oob.status_code == 400

    patch_missing = client.patch("/api/gpus/NVIDIA B200", json={"available_quantity": 1})
    assert patch_missing.status_code == 404

    reset = client.post("/api/gpus/reset")
    assert reset.status_code == 200
    assert reset.json()["summary"]["available_gpus"] == 19


def test_chat_endpoint_supports_tool_calling_and_prompt_stuffing(client: TestClient) -> None:
    tc_resp = client.post(
        "/api/chat",
        json={
            "message": "Existem duas A100 disponíveis?",
            "strategy": "tool_calling",
            "provider": "ollama",
            "model": "qwen2.5:7b",
        },
    )
    assert tc_resp.status_code == 200
    tc_data = tc_resp.json()
    assert tc_data["strategy"] == "tool_calling"
    assert tc_data["model"] == "qwen2.5:7b"
    assert tc_data["llm_calls"] == 2
    assert len(tc_data["tool_calls"]) == 1
    assert tc_data["tool_calls"][0]["name"] == "check_availability"
    assert tc_data["tool_calls"][0]["result"]["is_available"] is True

    ps_resp = client.post(
        "/api/chat",
        json={
            "message": "Existem duas A100 disponíveis?",
            "strategy": "prompt_stuffing",
            "provider": "deepseek",
        },
    )
    assert ps_resp.status_code == 200
    ps_data = ps_resp.json()
    assert ps_data["strategy"] == "prompt_stuffing"
    assert ps_data["llm_calls"] == 1
    assert ps_data["tool_calls"] == []


def test_chat_endpoint_rejects_blank_message(client: TestClient) -> None:
    resp = client.post("/api/chat", json={"message": "   ", "strategy": "tool_calling"})
    assert resp.status_code == 400
