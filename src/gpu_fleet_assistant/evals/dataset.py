from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from gpu_fleet_assistant.db import GPURepository

ScenarioName = Literal["default", "scaled"]


@dataclass(frozen=True, slots=True)
class EvalCase:
    """Single deterministic evaluation case for comparing assistant strategies."""

    id: str
    category: str
    scenario: ScenarioName
    prompt: str
    description: str
    setup_available: dict[str, int] = field(default_factory=dict)
    must_contain_all: tuple[str, ...] = ()
    must_contain_any: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()
    expected_tools_any: tuple[str, ...] = ()


def load_eval_cases(scenario: str = "default") -> list[EvalCase]:
    """Load evaluation cases from dataset.json filtered by scenario ('default', 'scaled', or 'all')."""
    if scenario not in {"default", "scaled", "all"}:
        raise ValueError(f"Unsupported scenario {scenario!r}. Expected 'default', 'scaled', or 'all'.")

    dataset_path = Path(__file__).parent / "dataset.json"
    raw_cases: list[dict[str, Any]] = json.loads(dataset_path.read_text(encoding="utf-8"))

    cases: list[EvalCase] = []
    for item in raw_cases:
        if scenario != "all" and item["scenario"] != scenario:
            continue
        cases.append(
            EvalCase(
                id=str(item["id"]),
                category=str(item["category"]),
                scenario=item["scenario"],
                prompt=str(item["prompt"]),
                description=str(item["description"]),
                setup_available=dict(item.get("setup_available", {})),
                must_contain_all=tuple(item.get("must_contain_all", ())),
                must_contain_any=tuple(item.get("must_contain_any", ())),
                must_not_contain=tuple(item.get("must_not_contain", ())),
                expected_tools_any=tuple(item.get("expected_tools_any", ())),
            )
        )
    return cases


def build_repository_for_case(case: EvalCase) -> GPURepository:
    """Create an isolated in-memory SQLite repository seeded for the given eval case."""
    repo = GPURepository(":memory:")
    repo.initialize(seed=True)

    if case.scenario == "scaled":
        _seed_scaled_nodes(repo)

    for gpu_name, available_qty in case.setup_available.items():
        repo.set_available_quantity(gpu_name, available_qty)

    return repo


def _seed_scaled_nodes(repo: GPURepository) -> None:
    """Insert 45 synthetic cluster nodes (total 50 rows) to stress-test context size and filtering."""
    synthetic_rows: list[tuple[str, int, int, int]] = []
    for idx in range(1, 46):
        if idx == 37:
            synthetic_rows.append(("Cluster Node 37 (NVIDIA H200)", 4, 3, 141))
        elif idx == 42:
            synthetic_rows.append(("Cluster Node 42 (NVIDIA L4)", 4, 0, 24))
        elif idx % 2 == 0:
            synthetic_rows.append((f"Cluster Node {idx:02d} (NVIDIA V100)", 4, 2, 32))
        else:
            synthetic_rows.append((f"Cluster Node {idx:02d} (NVIDIA T4)", 8, 4, 16))

    with repo._connection() as conn:  # noqa: SLF001 - intentional internal setup for eval stress test
        conn.executemany(
            """
            INSERT OR IGNORE INTO gpus (name, total_quantity, available_quantity, memory_gb)
            VALUES (?, ?, ?, ?);
            """,
            synthetic_rows,
        )
        conn.commit()
