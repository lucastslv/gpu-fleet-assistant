# Relatórios Empíricos de Avaliação (`evals/`)

Esta pasta contém os relatórios gerados por `uv run gpu-fleet-eval --scenario all` comparando `prompt_stuffing` (baseline) vs. `tool_calling` (arquitetura principal) em **16 casos determinísticos**:

- **12 casos `default`:** frota oficial do desafio (5 modelos de GPU).
- **4 casos `scaled`:** frota heterogênea de estresse com **50 modelos reais** (NVIDIA, AMD e Intel).

## Índice de Relatórios (5 modelos · 160 execuções)

| Modelo | Ambiente / Tipo | Relatório Markdown | Traces JSON |
| :--- | :--- | :---: | :---: |
| `llama3.2:3b` | Local 3B (Ollama) | [eval_llama32.md](eval_llama32.md) | [eval_llama32.json](eval_llama32.json) |
| `qwen3.5:4b` | Local 4B (*thinking*, Ollama) | [eval_qwen35_4b.md](eval_qwen35_4b.md) | [eval_qwen35_4b.json](eval_qwen35_4b.json) |
| `mistral-small-2603` | API compacto (Mistral) | [eval_mistral_small.md](eval_mistral_small.md) | [eval_mistral_small.json](eval_mistral_small.json) |
| `deepseek-flash` | API médio (DeepSeek) | [eval_deepseek.md](eval_deepseek.md) | [eval_deepseek.json](eval_deepseek.json) |
| `mistral-large-4` | API grande (*thinking*, Mistral) | [eval_mistral_large.md](eval_mistral_large.md) | [eval_mistral_large.json](eval_mistral_large.json) |

## Como reproduzir

```bash
uv run gpu-fleet-eval --provider deepseek --model deepseek-flash --scenario all \
  --output-md docs/evals/eval_deepseek.md --output-json docs/evals/eval_deepseek.json
```
