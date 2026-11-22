from __future__ import annotations

import argparse
import sys

from gpu_fleet_assistant.config import VALID_PROVIDERS, load_app_config, resolve_llm_config
from gpu_fleet_assistant.db import GPURepository
from gpu_fleet_assistant.llm import OpenAICompatibleClient
from gpu_fleet_assistant.strategies import (
    AssistantStrategy,
    ChatMessage,
    PromptStuffingStrategy,
    ToolCallingStrategy,
)


def _build_strategy(
    strategy_name: str,
    repository: GPURepository,
    client: OpenAICompatibleClient,
) -> AssistantStrategy:
    if strategy_name == "tool_calling":
        return ToolCallingStrategy(repository, client)
    if strategy_name == "prompt_stuffing":
        return PromptStuffingStrategy(repository, client)
    raise ValueError(f"Unsupported strategy: {strategy_name!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gpu-fleet-assistant",
        description="Interactive CLI for the GPU Fleet AI Assistant.",
    )
    parser.add_argument(
        "--provider",
        choices=VALID_PROVIDERS,
        default=None,
        help="LLM provider override (defaults to LLM_PROVIDER from .env).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name override for the selected provider.",
    )
    parser.add_argument(
        "--strategy",
        choices=("tool_calling", "prompt_stuffing"),
        default="tool_calling",
        help="Assistant strategy to use (default: tool_calling).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    app_cfg = load_app_config()
    llm_cfg = resolve_llm_config(args.provider, model_override=args.model)

    repo = GPURepository(app_cfg.db_path)
    repo.initialize(seed=True)
    client = OpenAICompatibleClient(llm_cfg)
    assistant = _build_strategy(args.strategy, repo, client)

    print(
        f"GPU Fleet Assistant | strategy={assistant.name} | "
        f"provider={llm_cfg.provider} | model={llm_cfg.model}"
    )
    print("Digite sua pergunta (ou 'sair' para encerrar, '/limpar' para resetar histórico).\n")

    history: list[ChatMessage] = []
    while True:
        try:
            user_input = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"sair", "exit", "quit"}:
            print("Encerrando.")
            break
        if user_input.lower() in {"/limpar", "/clear"}:
            history.clear()
            print("Histórico limpo.\n")
            continue

        try:
            response = assistant.chat(user_input, history=history)
        except Exception as exc:
            print(f"[erro] Falha ao consultar o modelo: {exc}\n", file=sys.stderr)
            continue

        print(f"\nAssistente: {response.answer}")
        if response.tool_calls:
            formatted_tools = ", ".join(
                f"{tc.name}({tc.arguments})" for tc in response.tool_calls
            )
            print(f"  [tools: {formatted_tools}]")
        print(
            f"  [strategy={response.strategy} | model={response.model} | "
            f"calls={response.llm_calls} | {response.latency_ms:.0f}ms | "
            f"{response.total_tokens} tokens]\n"
        )
        history.append(ChatMessage(role="user", content=user_input))
        history.append(ChatMessage(role="assistant", content=response.answer))
