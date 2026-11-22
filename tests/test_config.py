from __future__ import annotations

import pytest

from gpu_fleet_assistant.config import load_app_config, resolve_llm_config


def test_resolve_ollama_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "LLM_PROVIDER",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "OLLAMA_API_KEY",
        "LLM_TEMPERATURE",
        "LLM_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(key, raising=False)

    cfg = resolve_llm_config("ollama", load_env=False)
    assert cfg.provider == "ollama"
    assert cfg.base_url == "http://localhost:11434/v1"
    assert cfg.model == "qwen2.5:7b"
    assert cfg.api_key == "ollama"
    assert cfg.temperature == 0.0


def test_resolve_deepseek_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        resolve_llm_config("deepseek", load_env=False)

    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-deepseek")
    cfg = resolve_llm_config("deepseek", model_override="deepseek-reasoner", load_env=False)
    assert cfg.provider == "deepseek"
    assert cfg.base_url == "https://api.deepseek.com/v1"
    assert cfg.model == "deepseek-reasoner"
    assert cfg.api_key == "sk-test-deepseek"


def test_resolve_mistral_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MISTRAL_API_KEY", "mistral-key")
    monkeypatch.setenv("MISTRAL_MODEL", "mistral-large-latest")

    cfg = resolve_llm_config("mistral", load_env=False)
    assert cfg.provider == "mistral"
    assert cfg.base_url == "https://api.mistral.ai/v1"
    assert cfg.model == "mistral-large-latest"
    assert cfg.api_key == "mistral-key"


def test_resolve_invalid_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        resolve_llm_config("unknown-provider", load_env=False)


def test_load_app_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GPU_FLEET_DB_PATH", "tmp/custom.db")
    monkeypatch.setenv("LLM_PROVIDER", "mistral")

    app_cfg = load_app_config(load_env=False)
    assert str(app_cfg.db_path) == "tmp/custom.db"
    assert app_cfg.default_provider == "mistral"
