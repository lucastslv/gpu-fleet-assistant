#import "@preview/lambda-notes:0.1.1": *

#set text(lang: "pt", region: "BR")

#show: lambda-notes.with(
  title: "Relatório Técnico do Desafio",
  author: "Lucas Telles da Silva",
  date: "11/2026",
  subject: "Desafio de Estágio em Machine Learning / AI — Assistente Conversacional de GPUs",
  keywords: ("LLM", "Tool Calling", "Prompt Stuffing", "SQLite", "FastAPI", "Avaliação Empírica"),
  color: blue,
)

= Contexto e Objetivo

O objetivo deste projeto é implementar um *assistente conversacional de IA* capaz de responder perguntas sobre uma frota simulada de GPUs persistida em SQLite, garantindo que todas as respostas sejam estritamente ancoradas nos dados da aplicação (evitando alucinações sobre modelos, quantidades ou funcionalidades inexistentes).

== Frota Simulada (Seed SQLite)

Ao inicializar, o banco SQLite é populado de forma idempotente com os cinco modelos especificados no desafio:

#figure(
  table(
    columns: (auto, auto, auto, auto, auto),
    align: (left, right, right, right, right),
    [*Modelo de GPU*], [*Total*], [*Disponíveis*], [*VRAM / GPU (GB)*], [*VRAM Total (GB)*],
    [`NVIDIA A100`], [4], [4], [80], [320],
    [`NVIDIA L40S`], [6], [6], [48], [288],
    [`NVIDIA RTX 4090`], [3], [3], [24], [72],
    [`NVIDIA H100`], [2], [2], [80], [160],
    [`NVIDIA A40`], [4], [4], [48], [192],
    [*Total da Frota*], [*19*], [*19*], [—], [*1.032*],
  ),
  caption: [Inventário inicial da frota de GPUs persistido na tabela `gpus` em SQLite.],
)

Optou-se por manter o escopo de dados enxuto nesta etapa (sem tabela de reservas ou janelas futuras), mas rastreando separadamente `total_quantity` e `available_quantity` com restrições de integridade no banco (`0 <= available_quantity <= total_quantity`). Isso permite simular GPUs em uso em tempo real nos testes, nos benchmarks e na interface web.

= Arquitetura da Solução <arquitetura>

A aplicação foi estruturada em *quatro camadas desacopladas*, aplicando os padrões *Repository* (acesso a dados) e *Strategy* (estratégias de integração com LLMs). Essa separação permite que a interface web, a CLI interativa e a suite de avaliação consumam exatamente o mesmo núcleo sem acoplamento reverso.

#figure(
  image("../diagrams/architecture.svg", height: 15.8cm),
  caption: [Arquitetura de componentes do GPU Fleet Assistant, destacando o isolamento entre o painel administrativo (`/api/gpus`) e o acesso somente leitura do assistente (`/api/chat`).],
) <fig-arch>

== Decisões Técnicas Principais

1. *Separação entre Repositório e Tools (`db/repository.py` vs. `strategies/tool_calling.py`):*
   O `GPURepository` encapsula todo o SQL parametrizado e não conhece LLMs, JSON Schema ou HTTP. As *tools* expostas ao modelo funcionam como um adaptador fino estritamente *somente leitura* (`list_gpus`, `find_gpus`, `check_availability` e `get_fleet_summary`), aplicando o *princípio do menor privilégio*. Operações mutáveis (`set_available_quantity` e `reset_to_seed`) ficam restritas aos endpoints do painel web e aos testes.

2. *Desambiguação Explícita nas Consultas:*
   Durante a inspeção dos traces de avaliação, observou-se que buscas parciais ambíguas (como `"L4"` em um catálogo contendo `NVIDIA L4` e `NVIDIA L40S`) retornavam `found: false`, induzindo o LLM a afirmar que o modelo não existia. O retorno de `check_availability` foi estendido com `ambiguous: true` e a lista `matches`, permitindo que o modelo apresente as correspondências com precisão.

3. *Cliente LLM Agnóstico (`llm/client.py`):*
   Um wrapper fino sobre o SDK oficial `openai` (`OpenAICompatibleClient`) unifica a comunicação com modelos locais via *Ollama* e APIs comerciais (*DeepSeek*, *Mistral* ou endpoints customizados), coletando telemetria padronizada (`latency_ms`, `prompt_tokens`, `completion_tokens`, `total_tokens` e `tool_calls`). O cliente também trata nuances reais entre provedores, como a exigência de `top_p = 1.0` com `temperature = 0.0` na API da Mistral e a extração limpa de texto em modelos com blocos de raciocínio (*thinking* / tags `<think>`).

== Fluxo de Execução (*Tool Calling*)

A estratégia principal (`ToolCallingStrategy`) executa um loop controlado (`max_steps = 5`) com validação estrita dos argumentos JSON, recuperação graciosa de erros (retornando `{"error": ...}` ao modelo sem interromper o turno) e síntese final garantida caso o limite de passos seja atingido. A @fig-flow ilustra um turno completo para a pergunta de exemplo do desafio.

#figure(
  image("../diagrams/tool_calling_flow.svg", width: 100%),
  caption: [Fluxo detalhado de um turno de *Tool Calling*, do envio da pergunta na interface web até o retorno da consulta SQLite ao LLM e síntese da resposta final.],
) <fig-flow>

= Avaliação Empírica: `prompt_stuffing` vs. `tool_calling` <evals>

Uma pergunta natural diante de uma tabela de cinco linhas é: *por que não injetar todo o inventário diretamente no system prompt?* Para responder de forma empírica, sem adotar *Tool Calling* por puro dogma, implementou-se também a estratégia baseline `PromptStuffingStrategy` (snapshot completo da frota em 1 chamada ao LLM) e uma suite determinística em `src/gpu_fleet_assistant/evals/`.

== Metodologia do Benchmark

A suite executa *16 casos determinísticos*, cada um em um banco SQLite `:memory:` isolado (evitando interferência entre testes e preservando o banco real da aplicação):

- *12 casos na frota padrão (5 GPUs):* consultas básicas (3), limites e ocupação parcial mutada no SQLite (3), filtros e agregações não pré-calculadas como a soma de GPUs com `>= 48 GB` (3) e testes anti-alucinação / fora de escopo como `NVIDIA B200`, `A100 de 40 GB` e pedido de reserva futura (3).
- *4 casos no cenário escalado (`scaled`, 50 GPUs reais):* injeta 45 modelos reais adicionais de *NVIDIA, AMD e Intel* (de 8 GB a 192 GB) para estressar contexto e filtragem multi-fabricante (`H200` de 141 GB, filtro `>= 100 GB` retornando `H200`, `MI300X`, `MI250X` e `Intel Max 1550`, desambiguação `L4`/`L40`/`L40S` e filtro combinado `Intel >= 48 GB`).

As duas estratégias foram avaliadas em *5 modelos de diferentes portes* (locais e via API), totalizando *160 execuções* com zero erros de infraestrutura.

== Resultados Consolidados

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (auto, auto, auto, auto, auto, auto, auto),
      inset: (x: 4.5pt, y: 4.5pt),
      align: (left, left, left, center, center, right, right),
      [*Modelo*], [*Perfil*], [*Estratégia*], [*Acurácia*], [*50 GPUs*], [*Latência*], [*Tokens*],
      [#box[`llama3.2:3b`]], [Local 3B], [#box[`prompt_stuffing`]], [10/16 (62,5%)], [1/4], [841 ms], [734],
      [#box[`llama3.2:3b`]], [Local 3B], [#box[`tool_calling`]], [11/16 (68,8%)], [*3/4*], [1.193 ms], [1.427],
      [#box[`qwen3.5:4b`]], [Local 4B (think)], [#box[`prompt_stuffing`]], [14/16 (87,5%)], [4/4], [21.512 ms], [1.718],
      [#box[`qwen3.5:4b`]], [Local 4B (think)], [#box[`tool_calling`]], [*16/16 (100%)*], [*4/4*], [*7.587 ms*], [2.361],
      [#box[`mistral-small-2603`]], [API compacto], [#box[`prompt_stuffing`]], [16/16 (100%)], [4/4], [1.003 ms], [840],
      [#box[`mistral-small-2603`]], [API compacto], [#box[`tool_calling`]], [*16/16 (100%)*], [*4/4*], [*1.487 ms*], [1.894],
      [#box[`deepseek-flash`]], [API médio], [#box[`prompt_stuffing`]], [16/16 (100%)], [4/4], [2.025 ms], [893],
      [#box[`deepseek-flash`]], [API médio], [#box[`tool_calling`]], [*16/16 (100%)*], [*4/4*], [3.212 ms], [2.614],
      [#box[`mistral-large-4`]], [API grande (think)], [#box[`prompt_stuffing`]], [15/16 (93,8%)\*], [3/4\*], [3.795 ms], [956],
      [#box[`mistral-large-4`]], [API grande (think)], [#box[`tool_calling`]], [*16/16 (100%)*], [*4/4*], [5.348 ms], [2.040],
    )
  },
  caption: [Comparativo empírico entre `prompt_stuffing` e `tool_calling` nos 5 modelos avaliados (160 execuções, 0 erros). Relatórios completos e traces JSON disponíveis em `docs/evals/`.],
)

#callout(title: "Achado Principal — Ganho em Modelos Locais Pequenos", color: green)[
  No `llama3.2:3b`, o uso de `tool_calling` *triplicou a acurácia no cenário de 50 GPUs reais* (de 25% para 75%), eliminando alucinações no filtro multi-vendor `>= 100 GB`. Já no `qwen3.5:4b` (modelo local de 4B com *thinking* nativo), `tool_calling` não apenas elevou a acurácia para *100% (16/16)*, como foi *2,8 vezes mais rápido* que `prompt_stuffing` (7,6 s vs. 21,5 s), pois delegar filtros ao SQLite reduziu em cerca de 3 vezes os tokens gastos em raciocínio interno.
]

#note[
  *Notas metodológicas:* (1) `qwen3.5:4b` e `mistral-large-4` operaram com *thinking* nativo ativo por padrão, elevando latência e `completion_tokens` em comparação aos modelos sem *thinking*; (2) a revisão manual dos traces confirmou que a única falha heurística do `mistral-large-4` em `prompt_stuffing` (`scaled_intel_ge_48gb`) foi um falso negativo da regra `must_not_contain`, pois o modelo acertou o filtro e citou os modelos menores da Intel apenas para justificar sua exclusão.
]

== Análise de Trade-offs e Escolha Arquitetural

Os dados confirmam que não existe uma solução única ideal para todos os cenários, mas apontam claramente a arquitetura mais adequada para evolução em produção:

- *Quando `prompt_stuffing` é competitivo:* em catálogos pequenos e estáticos com modelos modernos via API (`mistral-small-2603` e `deepseek-flash`), oferece 100% de acerto com 1 única chamada, cerca de 1,5x menor latência e 2--3x menos tokens (pois não envia os schemas das 4 tools nem executa o segundo *round-trip*).
- *Por que `tool_calling` foi escolhido como padrão da aplicação:* garante filtragem determinística via SQL, mantém o tamanho de contexto estável conforme a frota cresce, isola permissões (somente leitura) e prepara a base para futuras ações transacionais (como reservas). Além disso, os números mostram que um modelo rápido sem *thinking* (`deepseek-flash` ou `mistral-small-2603`) aliado a *tool calling* entrega os mesmos 100% de precisão que um modelo *reasoning* grande (`mistral-large-4`), com latência muito inferior.

= Interface Web, Testes e Reprodutibilidade

== Interface Web (FastAPI + HTML/CSS/JS)

Para a demonstração interativa, construiu-se uma interface web leve sem etapa de build, servida diretamente pelo FastAPI (`uv run gpu-fleet-web`), configurada na arquitetura principal (*DeepSeek Flash + Tool Calling*):

- *Painel da frota em tempo real:* exibe KPIs agregados (GPUs e VRAM disponíveis) e cartões individuais por modelo com botões `-` / `+` e *Resetar frota*, atualizando diretamente o SQLite via `PATCH /api/gpus/{name}` para testar a resposta do assistente sob mudanças ao vivo de disponibilidade.
- *Chat com observabilidade:* renderização segura de Markdown/tabelas, barra de telemetria por turno (modelo, chamadas ao LLM, latência e tokens) e *inspetor expansível de tool calls* mostrando os argumentos enviados e o JSON retornado pelo repositório.

== Testes Automatizados e Execução

Toda a base é validada por *35 testes unitários determinísticos* (`tests/`), executados em cerca de 1,6 segundos usando SQLite `:memory:` e clientes LLM mockados (sem dependência de rede ou modelo ativo). O ambiente é gerenciado via `uv` (Python `>= 3.14`):

```bash
# Instalar dependências e configurar variáveis de ambiente
uv sync
cp .env.example .env

# Rodar todos os 35 testes unitários
uv run pytest -v

# Iniciar a interface web (http://127.0.0.1:8000)
uv run gpu-fleet-web

# Iniciar a CLI interativa ou reproduzir a suite de evals
uv run gpu-fleet-assistant --strategy tool_calling --provider deepseek
uv run gpu-fleet-eval --provider deepseek --scenario all
```

= Conclusão

Apesar de partir de um problema conceitualmente simples, consultar um inventário pequeno de GPUs compartilhadas, o desafio se mostrou muito bem desenhado por abrir espaço para investigar decisões reais de engenharia com LLMs sem depender de um domínio artificialmente complexo.

Ao longo do desenvolvimento, embora a avaliação dos modelos em si não fosse o foco do desafio, testar `prompt_stuffing` e `tool_calling` em modelos locais pequenos e APIs de diferentes portes trouxe excelentes insights sobre o comportamento das estratégias. Os resultados evidenciaram o quanto cada abordagem depende do tamanho do contexto, do porte do modelo e de detalhes práticos de integração, como o tratamento de ambiguidades nas consultas, diferenças de protocolo entre provedores e o impacto do *thinking* sobre latência e consumo de tokens.

Por fim, o recorte enxuto do enunciado permitiu equilibrar simplicidade e rigor experimental: manter o sistema fácil de executar e testar, apoiando cada escolha arquitetural em evidência empírica reproduzível.
