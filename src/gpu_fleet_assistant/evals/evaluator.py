from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from gpu_fleet_assistant.db import GPURepository
from gpu_fleet_assistant.evals.dataset import EvalCase, build_repository_for_case
from gpu_fleet_assistant.llm import LLMClient
from gpu_fleet_assistant.strategies import (
    AssistantStrategy,
    PromptStuffingStrategy,
    ToolCallingStrategy,
)


def normalize_text(text: str) -> str:
    """Lowercase and strip diacritics for accent-insensitive Portuguese matching."""
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(stripped.lower().split())


@dataclass(frozen=True, slots=True)
class CaseResult:
    """Outcome of running a single EvalCase against one strategy."""

    case_id: str
    category: str
    scenario: str
    strategy: str
    model: str
    passed: bool
    answer: str
    failure_reasons: tuple[str, ...]
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    llm_calls: int
    tool_names: tuple[str, ...]
    expected_tool_hit: bool | None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "scenario": self.scenario,
            "strategy": self.strategy,
            "model": self.model,
            "passed": self.passed,
            "answer": self.answer,
            "failure_reasons": list(self.failure_reasons),
            "latency_ms": self.latency_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_calls,
            "tool_names": list(self.tool_names),
            "expected_tool_hit": self.expected_tool_hit,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class StrategySummary:
    """Aggregated benchmark metrics for a single strategy across a set of cases."""

    strategy: str
    model: str
    total_cases: int
    passed_cases: int
    error_cases: int
    accuracy_pct: float
    avg_latency_ms: float
    avg_prompt_tokens: float
    avg_total_tokens: float
    avg_llm_calls: float
    tool_usage_rate_pct: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "model": self.model,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "error_cases": self.error_cases,
            "accuracy_pct": self.accuracy_pct,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_prompt_tokens": self.avg_prompt_tokens,
            "avg_total_tokens": self.avg_total_tokens,
            "avg_llm_calls": self.avg_llm_calls,
            "tool_usage_rate_pct": self.tool_usage_rate_pct,
        }


def score_answer(case: EvalCase, answer: str) -> tuple[bool, tuple[str, ...]]:
    """Evaluate an assistant answer deterministically against the case assertions."""
    normalized = normalize_text(answer)
    reasons: list[str] = []

    if not normalized:
        reasons.append("empty answer")
        return False, tuple(reasons)

    for required in case.must_contain_all:
        if normalize_text(required) not in normalized:
            reasons.append(f"missing required term {required!r}")

    if case.must_contain_any:
        if not any(normalize_text(term) in normalized for term in case.must_contain_any):
            reasons.append(f"missing any of {list(case.must_contain_any)!r}")

    for forbidden in case.must_not_contain:
        if normalize_text(forbidden) in normalized:
            reasons.append(f"contained forbidden term {forbidden!r}")

    return len(reasons) == 0, tuple(reasons)


StrategyFactory = Callable[[GPURepository, LLMClient], AssistantStrategy]

STRATEGY_FACTORIES: dict[str, StrategyFactory] = {
    "prompt_stuffing": lambda repo, client: PromptStuffingStrategy(repo, client),
    "tool_calling": lambda repo, client: ToolCallingStrategy(repo, client),
}


def run_eval(
    cases: Sequence[EvalCase],
    strategies: Sequence[str],
    client: LLMClient,
) -> list[CaseResult]:
    """Execute all evaluation cases across the requested strategies."""
    for strategy_name in strategies:
        if strategy_name not in STRATEGY_FACTORIES:
            allowed = ", ".join(STRATEGY_FACTORIES)
            raise ValueError(f"Unsupported strategy {strategy_name!r}. Expected one of: {allowed}.")

    results: list[CaseResult] = []
    for strategy_name in strategies:
        factory = STRATEGY_FACTORIES[strategy_name]
        for case in cases:
            repo = build_repository_for_case(case)
            try:
                strategy = factory(repo, client)
                response = strategy.chat(case.prompt)
                passed, reasons = score_answer(case, response.answer)
                tool_names = tuple(tc.name for tc in response.tool_calls)

                expected_tool_hit: bool | None = None
                if strategy_name == "tool_calling" and case.expected_tools_any:
                    expected_tool_hit = any(
                        name in case.expected_tools_any for name in tool_names
                    )

                results.append(
                    CaseResult(
                        case_id=case.id,
                        category=case.category,
                        scenario=case.scenario,
                        strategy=strategy_name,
                        model=response.model,
                        passed=passed,
                        answer=response.answer,
                        failure_reasons=reasons,
                        latency_ms=response.latency_ms,
                        prompt_tokens=response.prompt_tokens,
                        completion_tokens=response.completion_tokens,
                        total_tokens=response.total_tokens,
                        llm_calls=response.llm_calls,
                        tool_names=tool_names,
                        expected_tool_hit=expected_tool_hit,
                    )
                )
            except Exception as exc:
                results.append(
                    CaseResult(
                        case_id=case.id,
                        category=case.category,
                        scenario=case.scenario,
                        strategy=strategy_name,
                        model=client.model,
                        passed=False,
                        answer="",
                        failure_reasons=(f"exception: {exc}",),
                        latency_ms=0.0,
                        prompt_tokens=0,
                        completion_tokens=0,
                        total_tokens=0,
                        llm_calls=0,
                        tool_names=(),
                        expected_tool_hit=False if (strategy_name == "tool_calling" and case.expected_tools_any) else None,
                        error=str(exc),
                    )
                )
            finally:
                repo.close()

    return results


def summarize_results(results: Sequence[CaseResult]) -> list[StrategySummary]:
    """Compute per-strategy summary statistics."""
    grouped: dict[str, list[CaseResult]] = {}
    for res in results:
        grouped.setdefault(res.strategy, []).append(res)

    summaries: list[StrategySummary] = []
    for strategy_name, items in grouped.items():
        total = len(items)
        passed = sum(1 for item in items if item.passed)
        errors = sum(1 for item in items if item.error is not None)
        valid = [item for item in items if item.error is None]
        denom = len(valid) or 1

        tool_checks = [item.expected_tool_hit for item in items if item.expected_tool_hit is not None]
        tool_rate = (
            round(100.0 * sum(1 for hit in tool_checks if hit) / len(tool_checks), 1)
            if tool_checks
            else None
        )

        summaries.append(
            StrategySummary(
                strategy=strategy_name,
                model=items[0].model if items else "",
                total_cases=total,
                passed_cases=passed,
                error_cases=errors,
                accuracy_pct=round(100.0 * passed / total, 1) if total else 0.0,
                avg_latency_ms=round(sum(i.latency_ms for i in valid) / denom, 1),
                avg_prompt_tokens=round(sum(i.prompt_tokens for i in valid) / denom, 1),
                avg_total_tokens=round(sum(i.total_tokens for i in valid) / denom, 1),
                avg_llm_calls=round(sum(i.llm_calls for i in valid) / denom, 2),
                tool_usage_rate_pct=tool_rate,
            )
        )

    return summaries


def format_markdown_report(
    results: Sequence[CaseResult],
    summaries: Sequence[StrategySummary],
) -> str:
    """Render a GitHub-flavored Markdown comparison table ready for README.md."""
    lines = [
        "## Resumo Comparativo",
        "",
        "| Estratégia | Modelo | Acurácia | Erros | Latência Média (ms) | Prompt Tokens (média) | Total Tokens (média) | Chamadas LLM | Uso de Tool Esperada |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for s in summaries:
        tool_col = f"{s.tool_usage_rate_pct:.1f}%" if s.tool_usage_rate_pct is not None else "—"
        lines.append(
            f"| `{s.strategy}` | `{s.model}` | {s.passed_cases}/{s.total_cases} ({s.accuracy_pct:.1f}%) | "
            f"{s.error_cases} | {s.avg_latency_ms:.1f} | {s.avg_prompt_tokens:.1f} | "
            f"{s.avg_total_tokens:.1f} | {s.avg_llm_calls:.2f} | {tool_col} |"
        )

    lines.extend(
        [
            "",
            "## Detalhamento por Caso",
            "",
            "| Caso | Categoria | Estratégia | Status | Latência (ms) | Tokens | Tools | Motivo (se falhou) |",
            "| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |",
        ]
    )
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        tools = ", ".join(r.tool_names) if r.tool_names else "—"
        reason = "; ".join(r.failure_reasons) if r.failure_reasons else "—"
        lines.append(
            f"| `{r.case_id}` | `{r.category}` | `{r.strategy}` | {status} | "
            f"{r.latency_ms:.0f} | {r.total_tokens} | {tools} | {reason} |"
        )

    return "\n".join(lines)
