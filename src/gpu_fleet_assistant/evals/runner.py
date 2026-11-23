from __future__ import annotations

import argparse
import json
from pathlib import Path

from gpu_fleet_assistant.config import VALID_PROVIDERS, resolve_llm_config
from gpu_fleet_assistant.evals.dataset import load_eval_cases
from gpu_fleet_assistant.evals.evaluator import (
    STRATEGY_FACTORIES,
    format_markdown_report,
    run_eval,
    summarize_results,
)
from gpu_fleet_assistant.llm import OpenAICompatibleClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gpu-fleet-eval",
        description="Run comparative evaluations between prompt_stuffing and tool_calling.",
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
        help="Model name override (e.g. llama3.2:3b, deepseek-flash, mistral-large-4).",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        choices=tuple(STRATEGY_FACTORIES),
        default=["prompt_stuffing", "tool_calling"],
        help="Strategies to evaluate (default: both prompt_stuffing and tool_calling).",
    )
    parser.add_argument(
        "--scenario",
        choices=("default", "scaled", "all"),
        default="default",
        help="Dataset scenario: 'default' (5 GPUs), 'scaled' (50 nodes), or 'all'.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional path to save full JSON results.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=None,
        help="Optional path to save the Markdown report.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    llm_cfg = resolve_llm_config(args.provider, model_override=args.model)
    client = OpenAICompatibleClient(llm_cfg)
    cases = load_eval_cases(scenario=args.scenario)

    print(
        f"Running {len(cases)} eval cases | scenario={args.scenario} | "
        f"provider={llm_cfg.provider} | model={llm_cfg.model} | "
        f"strategies={', '.join(args.strategies)}\n"
    )

    results = run_eval(cases, args.strategies, client)
    summaries = summarize_results(results)
    markdown = format_markdown_report(results, summaries)
    print(markdown)

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "provider": llm_cfg.provider,
            "model": llm_cfg.model,
            "scenario": args.scenario,
            "summaries": [s.to_dict() for s in summaries],
            "results": [r.to_dict() for r in results],
        }
        args.output_json.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nSaved JSON report to {args.output_json}")

    if args.output_md is not None:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown + "\n", encoding="utf-8")
        print(f"Saved Markdown report to {args.output_md}")


if __name__ == "__main__":
    main()
