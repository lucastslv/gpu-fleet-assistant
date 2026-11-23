from __future__ import annotations

from typing import Any, Sequence

import pytest

from gpu_fleet_assistant.evals import (
    EvalCase,
    build_repository_for_case,
    format_markdown_report,
    load_eval_cases,
    normalize_text,
    run_eval,
    score_answer,
    summarize_results,
)
from gpu_fleet_assistant.llm import LLMResponse, ToolCallRequest


class StubEvalLLMClient:
    """Mock LLM client that handles both prompt_stuffing and tool_calling eval runs."""

    def __init__(self, *, fail_on_substring: str | None = None) -> None:
        self._fail_on_substring = fail_on_substring

    @property
    def model(self) -> str:
        return "stub-eval-model"

    def complete(
        self,
        messages: Sequence[dict[str, Any]],
        *,
        tools: Sequence[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> LLMResponse:
        user_msg = next(m["content"] for m in reversed(messages) if m["role"] == "user")
        if self._fail_on_substring and self._fail_on_substring in user_msg:
            raise RuntimeError("simulated timeout")

        # If tools are enabled and we haven't called a tool yet, issue a check_availability call
        has_tool_result = any(m["role"] == "tool" for m in messages)
        if tools and not has_tool_result:
            return LLMResponse(
                content="",
                model=self.model,
                latency_ms=20.0,
                prompt_tokens=120,
                completion_tokens=15,
                total_tokens=135,
                tool_calls=(
                    ToolCallRequest(
                        id="tc_1",
                        name="list_gpus",
                        arguments_json="{}",
                    ),
                ),
            )

        return LLMResponse(
            content="Temos NVIDIA A100, NVIDIA L40S, NVIDIA RTX 4090, NVIDIA H100 e NVIDIA A40.",
            model=self.model,
            latency_ms=15.0,
            prompt_tokens=180,
            completion_tokens=20,
            total_tokens=200,
        )


def test_load_eval_cases_scenarios() -> None:
    default_cases = load_eval_cases("default")
    scaled_cases = load_eval_cases("scaled")
    all_cases = load_eval_cases("all")

    assert len(default_cases) == 12
    assert len(scaled_cases) == 4
    assert len(all_cases) == 16

    with pytest.raises(ValueError, match="Unsupported scenario"):
        load_eval_cases("invalid")


def test_build_repository_for_scaled_and_mutated_cases() -> None:
    cases = {c.id: c for c in load_eval_cases("all")}

    partial_repo = build_repository_for_case(cases["partial_usage_a100"])
    try:
        a100 = partial_repo.get_gpu("NVIDIA A100")
        assert a100 is not None
        assert a100.available_quantity == 1
    finally:
        partial_repo.close()

    scaled_repo = build_repository_for_case(cases["scaled_needle_h200"])
    try:
        all_gpus = scaled_repo.list_gpus()
        assert len(all_gpus) == 50
        assert any(g.name.startswith("AMD ") for g in all_gpus)
        assert any(g.name.startswith("Intel ") for g in all_gpus)

        h200 = scaled_repo.get_gpu("NVIDIA H200")
        assert h200 is not None
        assert h200.memory_gb == 141
        assert h200.available_quantity == 3

        ge_100 = [g.name for g in scaled_repo.find_gpus(min_memory_gb=100)]
        assert ge_100 == [
            "NVIDIA H200",
            "AMD Instinct MI300X",
            "AMD Instinct MI250X",
            "Intel Data Center GPU Max 1550",
        ]

        intel_ge_48 = [
            g.name for g in scaled_repo.find_gpus(name_query="Intel", min_memory_gb=48)
        ]
        assert intel_ge_48 == [
            "Intel Data Center GPU Max 1550",
            "Intel Data Center GPU Max 1100",
        ]
    finally:
        scaled_repo.close()


def test_score_answer_handles_accents_and_forbidden_terms() -> None:
    assert normalize_text("Não há GPUs disponíveis!") == "nao ha gpus disponiveis!"
    assert (
        normalize_text("Total: 1.032 GB ou 1,032 GB (12.5 ms)")
        == "total: 1032 gb ou 1032 gb (12.5 ms)"
    )

    case = EvalCase(
        id="sample",
        category="test",
        scenario="default",
        prompt="?",
        description="test",
        must_contain_all=("A100", "H100"),
        must_contain_any=("nao", "disponivel"),
        must_not_contain=("L40S",),
    )

    ok, reasons = score_answer(case, "A100 e H100 estão disponíveis.")
    assert ok is False  # 'disponiveis' != 'disponivel'
    assert len(reasons) == 1

    ok2, reasons2 = score_answer(case, "Não temos L40S, apenas A100 e H100.")
    assert ok2 is False
    assert any("forbidden" in r for r in reasons2)

    ok3, reasons3 = score_answer(case, "Não, apenas A100 e H100 atendem.")
    assert ok3 is True
    assert reasons3 == ()

    check_two_case = next(c for c in load_eval_cases("default") if c.id == "check_two_a100")
    ok_false_neg, _ = score_answer(
        check_two_case, "Não, há apenas 4 A100 disponíveis na infraestrutura."
    )
    assert ok_false_neg is False


def test_run_eval_summarizes_strategies_and_captures_exceptions() -> None:
    cases = [load_eval_cases("default")[0], load_eval_cases("default")[1]]
    client = StubEvalLLMClient(fail_on_substring="duas A100")

    results = run_eval(cases, ["prompt_stuffing", "tool_calling"], client)
    assert len(results) == 4

    summaries = summarize_results(results)
    by_strategy = {s.strategy: s for s in summaries}

    assert by_strategy["prompt_stuffing"].passed_cases == 1
    assert by_strategy["prompt_stuffing"].error_cases == 1
    assert by_strategy["prompt_stuffing"].tool_usage_rate_pct is None

    assert by_strategy["tool_calling"].passed_cases == 1
    assert by_strategy["tool_calling"].error_cases == 1
    assert by_strategy["tool_calling"].avg_llm_calls == 2.0
    assert by_strategy["tool_calling"].tool_usage_rate_pct == 50.0

    report = format_markdown_report(results, summaries)
    assert "## Resumo Comparativo" in report
    assert "`prompt_stuffing`" in report
    assert "`tool_calling`" in report
