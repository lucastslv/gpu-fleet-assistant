from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GPUResource:
    """Represents a GPU model available in the shared infrastructure."""

    id: int
    name: str
    total_quantity: int
    available_quantity: int
    memory_gb: int

    @property
    def in_use_quantity(self) -> int:
        return self.total_quantity - self.available_quantity

    @property
    def total_memory_gb(self) -> int:
        return self.total_quantity * self.memory_gb

    @property
    def available_memory_gb(self) -> int:
        return self.available_quantity * self.memory_gb

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "total_quantity": self.total_quantity,
            "available_quantity": self.available_quantity,
            "in_use_quantity": self.in_use_quantity,
            "memory_gb": self.memory_gb,
            "total_memory_gb": self.total_memory_gb,
            "available_memory_gb": self.available_memory_gb,
        }


@dataclass(frozen=True, slots=True)
class AvailabilityCheck:
    """Structured result of checking whether N units of a GPU are available."""

    query: str
    requested_quantity: int
    found: bool
    is_available: bool
    gpu: GPUResource | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "requested_quantity": self.requested_quantity,
            "found": self.found,
            "is_available": self.is_available,
            "gpu": self.gpu.to_dict() if self.gpu is not None else None,
        }


@dataclass(frozen=True, slots=True)
class FleetSummary:
    """Aggregate metrics across all GPU models in the fleet."""

    model_count: int
    total_gpus: int
    available_gpus: int
    in_use_gpus: int
    total_memory_gb: int
    available_memory_gb: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_count": self.model_count,
            "total_gpus": self.total_gpus,
            "available_gpus": self.available_gpus,
            "in_use_gpus": self.in_use_gpus,
            "total_memory_gb": self.total_memory_gb,
            "available_memory_gb": self.available_memory_gb,
        }
