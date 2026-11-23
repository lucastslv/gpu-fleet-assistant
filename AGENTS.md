# AGENTS.md

Guia de contexto, arquitetura e convenções para agentes e colaboradores neste repositório.

## Objetivo do Projeto

Assistente conversacional de IA para consultar recursos de GPU compartilhados de um time de ML/AI, desenvolvido para o desafio em `Desafio_2026.md`.

Frota simulada (seed obrigatório em SQLite):
- `NVIDIA A100` — 4 unidades, 80 GB
- `NVIDIA L40S` — 6 unidades, 48 GB
- `NVIDIA RTX 4090` — 3 unidades, 24 GB
- `NVIDIA H100` — 2 unidades, 80 GB
- `NVIDIA A40` — 4 unidades, 48 GB

O diferencial do projeto é **implementar e comparar empiricamente** estratégias de integração com LLMs (ex.: `prompt_stuffing` como baseline vs. `tool_calling` como arquitetura principal) usando modelos de portes diferentes:
- **Modelo local pequeno**: Ollama (ex.: `qwen2.5:7b`)
- **Modelo maior via API**: DeepSeek ou Mistral (ambos via endpoint OpenAI-compatible)

## Decisões de Arquitetura

1. **Separação em 4 camadas desacopladas**:
   - `db/` (**Repository pattern**): camada pura de acesso ao SQLite (`GPURepository`, `GPUResource`, `AvailabilityCheck`, `FleetSummary`). Não conhece LLMs, prompts, JSON Schema ou HTTP.
   - `llm/`: wrapper fino (`OpenAICompatibleClient`) sobre o SDK `openai` com telemetria padronizada (`latency_ms`, tokens e `tool_calls`).
   - `strategies/` (**Strategy pattern**): todas as abordagens implementam `AssistantStrategy.chat(message, history) -> AssistantResponse`.
     - As **tools** do LLM ficam na estratégia `tool_calling`, atuando como adaptador fino sobre `GPURepository` e expondo apenas consultas de leitura (princípio do menor privilégio).
   - Interfaces (`cli.py` e futuro `FastAPI + HTML/CSS/JS`) + `evals/`.
2. **Escopo de dados atual**:
   - Sem tabela de reservas por enquanto; o banco rastreia `total_quantity` e `available_quantity` (permitindo simular GPUs em uso via `set_available_quantity` em testes, evals e UI).
3. **Anti-alucinação**:
   - O assistente deve responder apenas com base nos dados do SQLite, recusando inventar modelos, quantidades ou informações fora do escopo.

## Estrutura Atual e Roadmap

```text
src/gpu_fleet_assistant/
├── config.py                  # Resolução multi-provider (.env: ollama, deepseek, mistral, custom)
├── cli.py                     # CLI interativa (`uv run gpu-fleet-assistant`)
├── db/
│   ├── models.py              # Dataclasses: GPUResource, AvailabilityCheck, FleetSummary
│   ├── schema.py              # Schema SQLite + SEED_GPUS idempotente
│   └── repository.py          # GPURepository (queries determinísticas)
├── llm/
│   └── client.py              # OpenAICompatibleClient + LLMClient Protocol
├── strategies/
│   ├── base.py                # AssistantStrategy, ChatMessage, ToolCallTrace, AssistantResponse
│   ├── prompt_stuffing.py     # Baseline: snapshot do SQLite no system prompt
│   └── tool_calling.py        # Principal: tools tipadas de leitura sobre GPURepository + loop controlado
├── evals/
│   ├── dataset.json           # 16 casos (12 frota padrão + 4 estresse com 50 GPUs reais NVIDIA/AMD/Intel)
│   ├── dataset.py             # Loader de casos + frota de estresse de 50 GPUs reais em memória
│   ├── evaluator.py           # Scoring determinístico, agregação e relatório Markdown
│   └── runner.py              # CLI `uv run gpu-fleet-eval`
└── web/
    ├── app.py                 # FastAPI (`/api/gpus`, `/api/chat`, `/api/config`) + `uv run gpu-fleet-web`
    └── static/                # Frontend HTML/CSS/JS puro (painel SQLite + chat + inspetor de tools)
```

**Progresso:**
- [x] **Passo 1**: Domínio + SQLite + seed das 5 GPUs + testes unitários (`tests/test_repository.py`).
- [x] **Passo 2**: Configuração multi-provider + `OpenAICompatibleClient` + `PromptStuffingStrategy` + CLI interativa + testes (`tests/test_config.py`, `tests/test_prompt_stuffing.py`).
- [x] **Passo 3**: `ToolCallingStrategy` (schemas JSON/tools tipadas sobre `GPURepository` + loop controlado de execução + `--strategy tool_calling` na CLI + testes mockados em `tests/test_tool_calling.py`).
- [x] **Passo 4**: Suite de `evals/` (`dataset.json`, `evaluator.py`, `runner.py` / `uv run gpu-fleet-eval`, testes em `tests/test_evals.py`) comparando `prompt_stuffing` vs. `tool_calling` nos cenários padrão (5 GPUs) e escalado (50 GPUs reais NVIDIA/AMD/Intel) em 5 modelos (`docs/evals/`).
- [x] **Passo 5 (UI)**: Frontend em **FastAPI + HTML/CSS/JS** (`web/`, `uv run gpu-fleet-web`, testes em `tests/test_web.py`).
- [x] **Passo 5 (Docs)**: `README.md` final com arquitetura, decisões técnicas, instruções e resultados empíricos dos 5 modelos.

## Comandos Úteis

- Ambiente/Python: gerenciado via `uv` (Python `>=3.14`).
- Rodar testes unitários (não dependem de rede nem LLM rodando):
  ```bash
  uv run pytest -v
  ```
- Rodar interface web (FastAPI + HTML/CSS/JS):
  ```bash
  uv run gpu-fleet-web
  ```
- Rodar CLI interativa:
  ```bash
  uv run gpu-fleet-assistant
  uv run gpu-fleet-assistant --provider deepseek
  uv run gpu-fleet-assistant --provider ollama --model qwen2.5:7b
  ```
- Rodar suite comparativa de evals:
  ```bash
  uv run gpu-fleet-eval --provider deepseek --scenario all
  uv run gpu-fleet-eval --provider ollama --model llama3.2:3b --scenario all
  ```
- Configuração local: copiar `.env.example` para `.env`.

## Convenções de Código e Git

- **Tipagem e simplicidade**: usar `from __future__ import annotations`, `dataclass(frozen=True, slots=True)` e `Protocol` para facilitar mocks.
- **Testes**: toda nova camada deve ter testes unitários determinísticos em `tests/` usando SQLite `:memory:` e clientes LLM mockados.
- **Segurança**: nunca commitar `.env`, chaves de API ou bancos locais (`data/`, `*.db`).
- **Commits**: usar Conventional Commits em uma única linha (ex.: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `chore: ...`).
