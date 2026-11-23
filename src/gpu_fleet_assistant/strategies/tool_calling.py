from __future__ import annotations

import json
from typing import Any, Sequence

from gpu_fleet_assistant.db.repository import GPURepository
from gpu_fleet_assistant.llm.client import LLMClient
from gpu_fleet_assistant.strategies.base import (
    AssistantResponse,
    ChatMessage,
    ToolCallTrace,
)

TOOL_CALLING_SYSTEM_PROMPT = """Você é um assistente de infraestrutura de GPUs para um time de IA.
Responda de forma clara, objetiva e em português (a menos que o usuário pergunte em outro idioma).

REGRAS OBRIGATÓRIAS:
1. Você NÃO conhece os dados da frota de memória. Sempre consulte as ferramentas disponíveis antes de responder perguntas sobre modelos de GPU, quantidades, disponibilidade ou memória VRAM.
2. Baseie-se EXCLUSIVAMENTE nos dados retornados pelas consultas ao sistema.
3. NUNCA invente modelos de GPU, quantidades, memória ou disponibilidade.
4. Se a consulta indicar que uma GPU não existe na frota, informe explicitamente que ela não faz parte da infraestrutura. Se houver mais de um modelo compatível com o termo pesquisado, apresente os modelos encontrados de forma clara.
5. ESCOPO ESTRITO: Você responde EXCLUSIVAMENTE perguntas sobre a infraestrutura de GPUs do time (modelos, quantidades, disponibilidade e memória VRAM). Recuse educadamente qualquer pedido fora desse tema — como código/algoritmos gerais, matemática, traduções, curiosidades ou tarefas não relacionadas à frota de GPUs — explicando que você é um assistente dedicado apenas à consulta de recursos de GPU.
6. Para solicitações relacionadas a GPUs que o sistema não suporta (por exemplo, reservas futuras, agendamentos ou preços), diga claramente que o sistema não possui essa informação ou funcionalidade.
7. Responda sempre em linguagem natural voltada ao usuário final: NÃO mencione nomes de ferramentas/funções, parâmetros, campos JSON (como `found: false`, `ambiguous`, etc.) ou detalhes internos da consulta.
"""

TOOL_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "type": "function",
        "function": {
            "name": "list_gpus",
            "description": (
                "Lista todos os modelos de GPU cadastrados na infraestrutura com "
                "quantidade total, quantidade disponível, em uso e memória VRAM (GB)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "only_available": {
                        "type": "boolean",
                        "description": (
                            "Se true, retorna apenas GPUs com pelo menos 1 unidade disponível."
                        ),
                    }
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_gpus",
            "description": (
                "Filtra modelos de GPU por parte do nome, memória VRAM mínima (GB) "
                "e/ou quantidade mínima de unidades disponíveis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name_query": {
                        "type": "string",
                        "description": "Trecho do nome do modelo de GPU (ex.: 'A100', '100', 'RTX').",
                    },
                    "min_memory_gb": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Memória VRAM mínima por GPU em GB (ex.: 48, 80).",
                    },
                    "min_available": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Quantidade mínima de unidades disponíveis.",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": (
                "Verifica se existe um modelo específico de GPU na infraestrutura e se há "
                "pelo menos `quantity` unidades disponíveis no momento."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nome completo ou parcial do modelo (ex.: 'NVIDIA A100', 'A100', '4090').",
                    },
                    "quantity": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Quantidade de unidades desejadas (padrão: 1).",
                    },
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fleet_summary",
            "description": (
                "Retorna métricas agregadas da frota inteira: total de modelos, total de GPUs, "
                "GPUs disponíveis/em uso e memória VRAM total/disponível em GB."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    },
)


def _parse_arguments(arguments_json: str) -> tuple[dict[str, Any] | None, str | None]:
    if not arguments_json.strip():
        return {}, None
    try:
        parsed = json.loads(arguments_json)
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON arguments: {exc.msg}"
    if not isinstance(parsed, dict):
        return None, "Tool arguments must be a JSON object."
    return parsed, None


class ToolCallingStrategy:
    """Primary strategy that exposes read-only typed tools over GPURepository."""

    def __init__(
        self,
        repository: GPURepository,
        llm_client: LLMClient,
        *,
        max_steps: int = 5,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1.")
        self._repository = repository
        self._llm_client = llm_client
        self._max_steps = max_steps

    @property
    def name(self) -> str:
        return "tool_calling"

    def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            if tool_name == "list_gpus":
                allowed = {"only_available"}
                unknown = set(arguments) - allowed
                if unknown:
                    return {"error": f"Unexpected arguments for list_gpus: {sorted(unknown)}"}
                only_available = bool(arguments.get("only_available", False))
                gpus = self._repository.list_gpus(only_available=only_available)
                return {"count": len(gpus), "gpus": [gpu.to_dict() for gpu in gpus]}

            if tool_name == "find_gpus":
                allowed = {"name_query", "min_memory_gb", "min_available"}
                unknown = set(arguments) - allowed
                if unknown:
                    return {"error": f"Unexpected arguments for find_gpus: {sorted(unknown)}"}
                gpus = self._repository.find_gpus(
                    name_query=arguments.get("name_query"),
                    min_memory_gb=arguments.get("min_memory_gb"),
                    min_available=arguments.get("min_available"),
                )
                return {"count": len(gpus), "gpus": [gpu.to_dict() for gpu in gpus]}

            if tool_name == "check_availability":
                allowed = {"name", "quantity"}
                unknown = set(arguments) - allowed
                if unknown:
                    return {
                        "error": f"Unexpected arguments for check_availability: {sorted(unknown)}"
                    }
                gpu_name = arguments.get("name")
                if not isinstance(gpu_name, str) or not gpu_name.strip():
                    return {"error": "Argument 'name' must be a non-empty string."}
                quantity = arguments.get("quantity", 1)
                if not isinstance(quantity, int) or isinstance(quantity, bool):
                    return {"error": "Argument 'quantity' must be an integer."}
                check = self._repository.check_availability(gpu_name, quantity=quantity)
                return check.to_dict()

            if tool_name == "get_fleet_summary":
                if arguments:
                    return {
                        "error": f"Unexpected arguments for get_fleet_summary: {sorted(arguments)}"
                    }
                return self._repository.get_fleet_summary().to_dict()

            return {"error": f"Unknown tool: {tool_name!r}"}
        except (TypeError, ValueError) as exc:
            return {"error": str(exc)}

    def chat(
        self,
        message: str,
        history: Sequence[ChatMessage] | None = None,
    ) -> AssistantResponse:
        cleaned = message.strip()
        if not cleaned:
            raise ValueError("message must not be empty.")

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": TOOL_CALLING_SYSTEM_PROMPT}
        ]
        if history:
            messages.extend(turn.to_openai_dict() for turn in history)
        messages.append({"role": "user", "content": cleaned})

        total_latency_ms = 0.0
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        llm_calls = 0
        model_name = self._llm_client.model
        traces: list[ToolCallTrace] = []

        for _ in range(self._max_steps):
            response = self._llm_client.complete(
                messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
            llm_calls += 1
            model_name = response.model
            total_latency_ms += response.latency_ms
            prompt_tokens += response.prompt_tokens
            completion_tokens += response.completion_tokens
            total_tokens += response.total_tokens

            if not response.tool_calls:
                return AssistantResponse(
                    answer=response.content,
                    strategy=self.name,
                    model=model_name,
                    latency_ms=round(total_latency_ms, 2),
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    llm_calls=llm_calls,
                    tool_calls=tuple(traces),
                )

            messages.append(
                {
                    "role": "assistant",
                    "content": response.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": tc.arguments_json,
                            },
                        }
                        for tc in response.tool_calls
                    ],
                }
            )

            for tc in response.tool_calls:
                parsed_args, parse_error = _parse_arguments(tc.arguments_json)
                if parse_error is not None or parsed_args is None:
                    result: dict[str, Any] = {"error": parse_error or "Invalid arguments."}
                    recorded_args: dict[str, Any] = {"_raw": tc.arguments_json}
                else:
                    result = self._execute_tool(tc.name, parsed_args)
                    recorded_args = parsed_args

                traces.append(
                    ToolCallTrace(
                        name=tc.name,
                        arguments=recorded_args,
                        result=result,
                    )
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        # Safeguard: max_steps reached while the model still requested tools.
        # Ask for one final synthesis call without tools so the user gets an answer.
        final_response = self._llm_client.complete(messages)
        llm_calls += 1
        model_name = final_response.model
        total_latency_ms += final_response.latency_ms
        prompt_tokens += final_response.prompt_tokens
        completion_tokens += final_response.completion_tokens
        total_tokens += final_response.total_tokens

        return AssistantResponse(
            answer=final_response.content,
            strategy=self.name,
            model=model_name,
            latency_ms=round(total_latency_ms, 2),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            llm_calls=llm_calls,
            tool_calls=tuple(traces),
        )
