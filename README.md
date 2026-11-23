# GPU Fleet Assistant

Assistente conversacional de IA para consultar recursos compartilhados de GPU (persistidos em SQLite), desenvolvido para o [desafio](Desafio_2026.md).

A solução principal combina **FastAPI + HTML/CSS/JS**, **SQLite** e **Tool Calling** (tools somente leitura sobre um repositório desacoplado), acompanhada de uma baseline em **Prompt Stuffing** e uma suite reproduzível de avaliação (`evals/`) executada em 5 modelos locais e via API.

## Documentação e Demo

- **Demo ao vivo:** [gpu-fleet-assistant.onrender.com](https://gpu-fleet-assistant.onrender.com/) *(plano gratuito: o primeiro acesso pode levar ~30s para acordar a instância)*
- **Enunciado do desafio:** [Desafio_2026.md](Desafio_2026.md)
- **Relatório técnico completo (decisões, trade-offs e avaliação empírica):** [docs/report/main.pdf](docs/report/main.pdf) *(fonte Typst em [docs/report/main.typ](docs/report/main.typ))*
- **Relatórios e traces dos evals (5 modelos, 160 execuções):** [docs/evals/README.md](docs/evals/README.md)
- **Diagramas de arquitetura (D2):** [docs/diagrams/](docs/diagrams/)

## Visão Geral da Arquitetura

![Arquitetura de Componentes](docs/diagrams/architecture.svg)

- `db/`: schema SQLite, seed idempotente das 5 GPUs do desafio (`A100`, `L40S`, `RTX 4090`, `H100`, `A40`) e `GPURepository`.
- `llm/`: cliente OpenAI-compatible (`ollama`, `deepseek`, `mistral` ou `custom`) com telemetria de latência, tokens e *tool calls*.
- `strategies/`: `ToolCallingStrategy` (4 tools somente leitura em loop controlado) e `PromptStuffingStrategy` (baseline).
- `web/` e `cli.py`: interface web (painel SQLite em tempo real + chat + inspetor de *tool calls*) e CLI interativa.
- `evals/`: 16 casos determinísticos (frota padrão de 5 GPUs + cenário de estresse com 50 GPUs reais NVIDIA/AMD/Intel).

## Como Executar

### Pré-requisitos
- Python `>= 3.14` e [`uv`](https://docs.astral.sh/uv/)
- Chave de API (DeepSeek / Mistral) **ou** Ollama rodando localmente.

### 1. Instalar e configurar ambiente
```bash
uv sync
cp .env.example .env
```
Preencha as variáveis desejadas no `.env` (para a interface web, configure `DEEPSEEK_API_KEY`; para uso local na CLI/evals, basta apontar `OLLAMA_BASE_URL` e `OLLAMA_MODEL`).

### 2. Interface Web (FastAPI + HTML/CSS/JS)
```bash
uv run gpu-fleet-web
```
Acesse `http://127.0.0.1:8000` (Swagger da API em `http://127.0.0.1:8000/docs`).

### 3. CLI Interativa
```bash
uv run gpu-fleet-assistant --strategy tool_calling --provider deepseek
uv run gpu-fleet-assistant --strategy prompt_stuffing --provider ollama --model llama3.2:3b
```

### 4. Suite de Evals
```bash
uv run gpu-fleet-eval --provider deepseek --scenario all
uv run gpu-fleet-eval --provider ollama --model qwen3.5:4b --scenario all
```
