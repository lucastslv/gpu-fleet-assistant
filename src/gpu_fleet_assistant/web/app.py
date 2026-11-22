from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable, Literal

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from gpu_fleet_assistant.config import (
    VALID_PROVIDERS,
    load_app_config,
    resolve_llm_config,
)
from gpu_fleet_assistant.db import GPURepository
from gpu_fleet_assistant.llm import LLMClient, OpenAICompatibleClient
from gpu_fleet_assistant.strategies import (
    ChatMessage,
    PromptStuffingStrategy,
    ToolCallingStrategy,
)

STATIC_DIR = Path(__file__).parent / "static"

ClientFactory = Callable[[str | None, str | None], LLMClient]


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[HistoryItem] = Field(default_factory=list)
    strategy: Literal["tool_calling", "prompt_stuffing"] = "tool_calling"
    provider: Literal["ollama", "deepseek", "mistral", "custom"] | None = None
    model: str | None = None


class UpdateAvailabilityRequest(BaseModel):
    available_quantity: int = Field(ge=0)


def _default_client_factory(provider: str | None, model: str | None) -> LLMClient:
    llm_cfg = resolve_llm_config(provider, model_override=model or None)
    return OpenAICompatibleClient(llm_cfg)


def _inspect_providers() -> list[dict[str, Any]]:
    """Return provider availability metadata without exposing secret API keys."""
    providers: list[dict[str, Any]] = []
    for name in VALID_PROVIDERS:
        try:
            cfg = resolve_llm_config(name)
            providers.append(
                {
                    "name": name,
                    "configured": True,
                    "default_model": cfg.model,
                    "base_url": cfg.base_url,
                }
            )
        except ValueError:
            providers.append(
                {
                    "name": name,
                    "configured": False,
                    "default_model": "",
                    "base_url": "",
                }
            )
    return providers


def create_app(
    *,
    repository: GPURepository | None = None,
    client_factory: ClientFactory | None = None,
) -> FastAPI:
    """Create and configure the FastAPI web application."""
    app_cfg = load_app_config()
    repo = repository or GPURepository(app_cfg.db_path)
    repo.initialize(seed=True)
    make_client = client_factory or _default_client_factory

    app = FastAPI(
        title="GPU Fleet Assistant",
        description="Assistente conversacional de IA para consulta de recursos de GPU.",
        version="0.1.0",
    )

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/config")
    def get_config() -> dict[str, Any]:
        cfg = load_app_config()
        return {
            "default_provider": cfg.default_provider,
            "default_strategy": "tool_calling",
            "strategies": ["tool_calling", "prompt_stuffing"],
            "providers": _inspect_providers(),
        }

    @app.get("/api/gpus")
    def list_gpus() -> dict[str, Any]:
        gpus = repo.list_gpus()
        summary = repo.get_fleet_summary()
        return {
            "gpus": [gpu.to_dict() for gpu in gpus],
            "summary": summary.to_dict(),
        }

    @app.patch("/api/gpus/{gpu_name:path}")
    def update_gpu_availability(
        gpu_name: str,
        payload: UpdateAvailabilityRequest,
    ) -> dict[str, Any]:
        try:
            updated = repo.set_available_quantity(gpu_name, payload.available_quantity)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "gpu": updated.to_dict(),
            "summary": repo.get_fleet_summary().to_dict(),
        }

    @app.post("/api/gpus/reset")
    def reset_gpus() -> dict[str, Any]:
        repo.reset_to_seed()
        return {
            "gpus": [gpu.to_dict() for gpu in repo.list_gpus()],
            "summary": repo.get_fleet_summary().to_dict(),
        }

    @app.post("/api/chat")
    def chat(payload: ChatRequest) -> dict[str, Any]:
        cleaned_message = payload.message.strip()
        if not cleaned_message:
            raise HTTPException(status_code=400, detail="message must not be empty.")

        try:
            client = make_client(payload.provider, payload.model)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        strategy = (
            ToolCallingStrategy(repo, client)
            if payload.strategy == "tool_calling"
            else PromptStuffingStrategy(repo, client)
        )

        history = [
            ChatMessage(role=item.role, content=item.content)
            for item in payload.history
        ]

        try:
            response = strategy.chat(cleaned_message, history=history)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Falha ao consultar o provedor LLM: {exc}",
            ) from exc

        return response.to_dict()

    return app


app = create_app()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="gpu-fleet-web",
        description="Run the GPU Fleet Assistant web UI (FastAPI + HTML/CSS/JS).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000).")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development.")
    args = parser.parse_args(argv)

    uvicorn.run(
        "gpu_fleet_assistant.web.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
