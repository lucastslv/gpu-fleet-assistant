from __future__ import annotations

from typing import Sequence

from gpu_fleet_assistant.db.repository import GPURepository
from gpu_fleet_assistant.llm.client import LLMClient
from gpu_fleet_assistant.strategies.base import AssistantResponse, ChatMessage

SYSTEM_PROMPT_TEMPLATE = """Você é um assistente de infraestrutura de GPUs para um time de IA.
Responda de forma clara, objetiva e em português (a menos que o usuário pergunte em outro idioma).

REGRAS OBRIGATÓRIAS:
1. Baseie-se EXCLUSIVAMENTE nos dados de infraestrutura listados abaixo.
2. NUNCA invente modelos de GPU, quantidades, memória ou disponibilidade que não estejam nos dados.
3. Se o usuário perguntar sobre uma GPU que não existe na lista, informe explicitamente que ela não faz parte da infraestrutura.
4. Se uma informação não puder ser respondida com os dados disponíveis (por exemplo, reservas futuras ou preços), diga claramente que o sistema não possui essa informação.

{fleet_snapshot}
"""


def format_fleet_snapshot(repository: GPURepository) -> str:
    """Serialize the current SQLite GPU inventory into a markdown block for prompt stuffing."""
    gpus = repository.list_gpus()
    summary = repository.get_fleet_summary()

    lines = [
        "DADOS ATUAIS DA INFRAESTRUTURA DE GPUs:",
        "| GPU | Total | Disponíveis | Em uso | Memória por GPU (GB) | Memória Disponível Total (GB) |",
        "|-----|------:|------------:|-------:|---------------------:|------------------------------:|",
    ]
    for gpu in gpus:
        lines.append(
            f"| {gpu.name} | {gpu.total_quantity} | {gpu.available_quantity} | "
            f"{gpu.in_use_quantity} | {gpu.memory_gb} | {gpu.available_memory_gb} |"
        )

    lines.extend(
        [
            "",
            "RESUMO DA FROTA:",
            f"- Modelos cadastrados: {summary.model_count}",
            f"- Total de GPUs: {summary.total_gpus} ({summary.available_gpus} disponíveis, {summary.in_use_gpus} em uso)",
            f"- Memória VRAM total: {summary.total_memory_gb} GB ({summary.available_memory_gb} GB disponíveis)",
        ]
    )
    return "\n".join(lines)


class PromptStuffingStrategy:
    """Baseline strategy that injects a full snapshot of the GPU table into the system prompt."""

    def __init__(self, repository: GPURepository, llm_client: LLMClient) -> None:
        self._repository = repository
        self._llm_client = llm_client

    @property
    def name(self) -> str:
        return "prompt_stuffing"

    def build_system_prompt(self) -> str:
        snapshot = format_fleet_snapshot(self._repository)
        return SYSTEM_PROMPT_TEMPLATE.format(fleet_snapshot=snapshot)

    def chat(
        self,
        message: str,
        history: Sequence[ChatMessage] | None = None,
    ) -> AssistantResponse:
        cleaned = message.strip()
        if not cleaned:
            raise ValueError("message must not be empty.")

        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.build_system_prompt()}
        ]
        if history:
            messages.extend(turn.to_openai_dict() for turn in history)
        messages.append({"role": "user", "content": cleaned})

        response = self._llm_client.complete(messages)
        return AssistantResponse(
            answer=response.content,
            strategy=self.name,
            model=response.model,
            latency_ms=response.latency_ms,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            llm_calls=1,
            tool_calls=(),
        )
