from __future__ import annotations

from pathlib import Path

import pytest

from gpu_fleet_assistant.db import GPURepository, SEED_GPUS


@pytest.fixture()
def repo() -> GPURepository:
    repository = GPURepository(":memory:")
    repository.initialize(seed=True)
    yield repository
    repository.close()


def test_initialize_seeds_exact_challenge_gpus(repo: GPURepository) -> None:
    gpus = repo.list_gpus()
    assert len(gpus) == 5
    assert [(g.name, g.total_quantity, g.available_quantity, g.memory_gb) for g in gpus] == [
        ("NVIDIA A100", 4, 4, 80),
        ("NVIDIA L40S", 6, 6, 48),
        ("NVIDIA RTX 4090", 3, 3, 24),
        ("NVIDIA H100", 2, 2, 80),
        ("NVIDIA A40", 4, 4, 48),
    ]


def test_initialize_is_idempotent_and_preserves_state(repo: GPURepository) -> None:
    repo.set_available_quantity("A100", 1)
    repo.initialize(seed=True)

    a100 = repo.get_gpu("NVIDIA A100")
    assert a100 is not None
    assert a100.available_quantity == 1
    assert len(repo.list_gpus()) == len(SEED_GPUS)


def test_reset_to_seed_restores_initial_quantities(repo: GPURepository) -> None:
    repo.set_available_quantity("H100", 0)
    repo.reset_to_seed()

    h100 = repo.get_gpu("H100")
    assert h100 is not None
    assert h100.available_quantity == 2


def test_get_gpu_supports_exact_and_unambiguous_partial_match(repo: GPURepository) -> None:
    assert repo.get_gpu("NVIDIA A100") is not None
    assert repo.get_gpu("nvidia a100") is not None
    assert repo.get_gpu("a100") is not None
    assert repo.get_gpu("4090").name == "NVIDIA RTX 4090"  # type: ignore[union-attr]
    # Ambiguous ("100" matches A100 and H100; "NVIDIA" matches all)
    assert repo.get_gpu("100") is None
    assert repo.get_gpu("NVIDIA") is None
    # Non-existent or empty
    assert repo.get_gpu("NVIDIA B200") is None
    assert repo.get_gpu("   ") is None


def test_find_gpus_filters_by_memory_availability_and_name(repo: GPURepository) -> None:
    high_vram = repo.find_gpus(min_memory_gb=80)
    assert [g.name for g in high_vram] == ["NVIDIA A100", "NVIDIA H100"]

    mid_or_high_with_four = repo.find_gpus(min_memory_gb=48, min_available=4)
    assert [g.name for g in mid_or_high_with_four] == [
        "NVIDIA A100",
        "NVIDIA L40S",
        "NVIDIA A40",
    ]

    hundred_series = repo.find_gpus(name_query="100")
    assert [g.name for g in hundred_series] == ["NVIDIA A100", "NVIDIA H100"]


def test_find_gpus_rejects_negative_filters(repo: GPURepository) -> None:
    with pytest.raises(ValueError, match="min_memory_gb"):
        repo.find_gpus(min_memory_gb=-1)

    with pytest.raises(ValueError, match="min_available"):
        repo.find_gpus(min_available=-1)


def test_check_availability_cases(repo: GPURepository) -> None:
    ok = repo.check_availability("A100", quantity=2)
    assert ok.found is True
    assert ok.is_available is True
    assert ok.gpu is not None
    assert ok.gpu.name == "NVIDIA A100"

    too_many = repo.check_availability("H100", quantity=3)
    assert too_many.found is True
    assert too_many.is_available is False

    missing = repo.check_availability("RTX 5090", quantity=1)
    assert missing.found is False
    assert missing.is_available is False
    assert missing.ambiguous is False
    assert missing.gpu is None
    assert missing.matches == ()

    ambiguous = repo.check_availability("100", quantity=2)
    assert ambiguous.found is False
    assert ambiguous.is_available is False
    assert ambiguous.ambiguous is True
    assert [m.name for m in ambiguous.matches] == ["NVIDIA A100", "NVIDIA H100"]

    with pytest.raises(ValueError, match="at least 1"):
        repo.check_availability("A100", quantity=0)


def test_list_gpus_only_available_and_set_available_quantity(repo: GPURepository) -> None:
    updated = repo.set_available_quantity("H100", 0)
    assert updated.available_quantity == 0
    assert updated.in_use_quantity == 2

    available_only = repo.list_gpus(only_available=True)
    assert [g.name for g in available_only] == [
        "NVIDIA A100",
        "NVIDIA L40S",
        "NVIDIA RTX 4090",
        "NVIDIA A40",
    ]

    with pytest.raises(ValueError, match="between 0 and 2"):
        repo.set_available_quantity("H100", 3)

    with pytest.raises(ValueError, match="between 0 and 2"):
        repo.set_available_quantity("H100", -1)

    with pytest.raises(LookupError):
        repo.set_available_quantity("B200", 1)


def test_get_fleet_summary(repo: GPURepository) -> None:
    repo.set_available_quantity("A100", 2)  # 2 in use -> 160 GB in use

    summary = repo.get_fleet_summary()
    assert summary.model_count == 5
    assert summary.total_gpus == 19  # 4 + 6 + 3 + 2 + 4
    assert summary.available_gpus == 17
    assert summary.in_use_gpus == 2
    # Total VRAM: 4*80 + 6*48 + 3*24 + 2*80 + 4*48 = 320 + 288 + 72 + 160 + 192 = 1032
    assert summary.total_memory_gb == 1032
    assert summary.available_memory_gb == 1032 - 160


def test_file_backed_sqlite_persistence(tmp_path: Path) -> None:
    db_file = tmp_path / "nested" / "fleet.db"
    repo1 = GPURepository(db_file)
    repo1.initialize(seed=True)
    repo1.set_available_quantity("L40S", 3)

    repo2 = GPURepository(db_file)
    l40s = repo2.get_gpu("L40S")
    assert l40s is not None
    assert l40s.available_quantity == 3
    assert l40s.in_use_quantity == 3
