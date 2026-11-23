from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

ProviderName = Literal["ollama", "deepseek", "mistral", "custom"]

VALID_PROVIDERS: tuple[ProviderName, ...] = ("ollama", "deepseek", "mistral", "custom")


@dataclass(frozen=True, slots=True)
class LLMConfig:
    """Connection settings for an OpenAI-compatible LLM endpoint."""

    provider: ProviderName
    base_url: str
    model: str
    api_key: str
    temperature: float = 0.0
    timeout_seconds: float = 60.0


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Top-level application configuration."""

    db_path: Path
    default_provider: ProviderName
    temperature: float = 0.0
    timeout_seconds: float = 60.0


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value.strip() if value is not None else default


def resolve_llm_config(
    provider: str | None = None,
    *,
    model_override: str | None = None,
    temperature: float | None = None,
    timeout_seconds: float | None = None,
    load_env: bool = True,
) -> LLMConfig:
    """Build an LLMConfig for the requested provider from environment variables."""
    if load_env:
        load_dotenv()

    selected = (provider or _env("LLM_PROVIDER", "ollama")).lower()
    if selected not in VALID_PROVIDERS:
        allowed = ", ".join(VALID_PROVIDERS)
        raise ValueError(f"Unsupported LLM provider {selected!r}. Expected one of: {allowed}.")

    temp = (
        temperature
        if temperature is not None
        else float(_env("LLM_TEMPERATURE", "0.0"))
    )
    timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else float(_env("LLM_TIMEOUT_SECONDS", "60"))
    )

    if selected == "ollama":
        base_url = _env("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        model = model_override or _env("OLLAMA_MODEL", "qwen2.5:7b")
        api_key = _env("OLLAMA_API_KEY", "ollama")
    elif selected == "deepseek":
        base_url = _env("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        model = model_override or _env("DEEPSEEK_MODEL", "deepseek-flash")
        api_key = _env("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required when using the 'deepseek' provider.")
    elif selected == "mistral":
        base_url = _env("MISTRAL_BASE_URL", "https://api.mistral.ai/v1")
        model = model_override or _env("MISTRAL_MODEL", "mistral-small-latest")
        api_key = _env("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY is required when using the 'mistral' provider.")
    else:  # custom
        base_url = _env("LLM_BASE_URL")
        model = model_override or _env("LLM_MODEL")
        api_key = _env("LLM_API_KEY", "not-required")
        if not base_url or not model:
            raise ValueError(
                "LLM_BASE_URL and LLM_MODEL are required when using the 'custom' provider."
            )

    return LLMConfig(
        provider=selected,  # type: ignore[arg-type]
        base_url=base_url,
        model=model,
        api_key=api_key,
        temperature=temp,
        timeout_seconds=timeout,
    )


def load_app_config(*, load_env: bool = True) -> AppConfig:
    """Load application-level settings from environment variables."""
    if load_env:
        load_dotenv()

    provider = _env("LLM_PROVIDER", "ollama").lower()
    if provider not in VALID_PROVIDERS:
        allowed = ", ".join(VALID_PROVIDERS)
        raise ValueError(f"Unsupported LLM_PROVIDER {provider!r}. Expected one of: {allowed}.")

    return AppConfig(
        db_path=Path(_env("GPU_FLEET_DB_PATH", "data/gpu_fleet.db")),
        default_provider=provider,  # type: ignore[arg-type]
        temperature=float(_env("LLM_TEMPERATURE", "0.0")),
        timeout_seconds=float(_env("LLM_TIMEOUT_SECONDS", "60")),
    )
