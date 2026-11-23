from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from gpu_fleet_assistant.db import GPURepository

ScenarioName = Literal["default", "scaled"]

# 45 real NVIDIA, AMD, and Intel GPU models added to the 5 challenge GPUs
# (total = 50 distinct models) for the scaled stress-test scenario.
# Tuple format: (name, total_quantity, available_quantity, memory_gb)
SCALED_EXTRA_GPUS: tuple[tuple[str, int, int, int], ...] = (
    # NVIDIA (27 models)
    ("NVIDIA H200", 4, 3, 141),
    ("NVIDIA L40", 4, 2, 48),
    ("NVIDIA L4", 4, 0, 24),
    ("NVIDIA A30", 4, 3, 24),
    ("NVIDIA A16", 6, 4, 64),
    ("NVIDIA A10", 8, 5, 24),
    ("NVIDIA A10G", 6, 3, 24),
    ("NVIDIA A2", 8, 6, 16),
    ("NVIDIA T4", 12, 7, 16),
    ("NVIDIA V100", 8, 4, 32),
    ("NVIDIA P100", 4, 1, 16),
    ("NVIDIA P40", 4, 2, 24),
    ("NVIDIA Tesla K80", 4, 0, 24),
    ("NVIDIA RTX 6000 Ada", 4, 2, 48),
    ("NVIDIA RTX 5000 Ada", 4, 3, 32),
    ("NVIDIA RTX 4000 Ada", 6, 4, 20),
    ("NVIDIA RTX A6000", 4, 2, 48),
    ("NVIDIA RTX A5000", 6, 3, 24),
    ("NVIDIA RTX A4000", 6, 5, 16),
    ("NVIDIA Quadro RTX 8000", 2, 1, 48),
    ("NVIDIA Quadro GV100", 2, 1, 32),
    ("NVIDIA Titan RTX", 2, 1, 24),
    ("NVIDIA RTX 4080", 4, 2, 16),
    ("NVIDIA RTX 4070 Ti", 4, 3, 12),
    ("NVIDIA RTX 3090", 6, 4, 24),
    ("NVIDIA RTX 3080", 6, 2, 10),
    ("NVIDIA RTX 3060", 8, 5, 12),
    # AMD (11 models)
    ("AMD Instinct MI300X", 4, 2, 192),
    ("AMD Instinct MI250X", 4, 3, 128),
    ("AMD Instinct MI210", 4, 2, 64),
    ("AMD Instinct MI100", 4, 1, 32),
    ("AMD Radeon PRO W7900", 4, 3, 48),
    ("AMD Radeon PRO W7800", 4, 2, 32),
    ("AMD Radeon PRO W6800", 4, 2, 32),
    ("AMD Radeon RX 7900 XTX", 6, 4, 24),
    ("AMD Radeon RX 7900 XT", 6, 3, 20),
    ("AMD Radeon RX 6950 XT", 4, 2, 16),
    ("AMD Radeon RX 6800 XT", 4, 1, 16),
    # Intel (7 models)
    ("Intel Data Center GPU Max 1550", 2, 2, 128),
    ("Intel Data Center GPU Max 1100", 4, 3, 48),
    ("Intel Data Center GPU Flex 170", 6, 4, 16),
    ("Intel Data Center GPU Flex 140", 6, 3, 12),
    ("Intel Arc Pro A60", 4, 2, 12),
    ("Intel Arc A770", 6, 4, 16),
    ("Intel Arc A750", 6, 5, 8),
)


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
        _seed_scaled_gpus(repo)

    for gpu_name, available_qty in case.setup_available.items():
        repo.set_available_quantity(gpu_name, available_qty)

    return repo


def _seed_scaled_gpus(repo: GPURepository) -> None:
    """Insert 45 real NVIDIA/AMD/Intel GPU models (total 50 rows) for the scaled stress test."""
    with repo._connection() as conn:  # noqa: SLF001 - intentional internal setup for eval stress test
        conn.executemany(
            """
            INSERT OR IGNORE INTO gpus (name, total_quantity, available_quantity, memory_gb)
            VALUES (?, ?, ?, ?);
            """,
            SCALED_EXTRA_GPUS,
        )
        conn.commit()
