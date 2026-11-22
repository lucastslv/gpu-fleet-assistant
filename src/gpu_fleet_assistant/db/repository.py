from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from gpu_fleet_assistant.db.models import AvailabilityCheck, FleetSummary, GPUResource
from gpu_fleet_assistant.db.schema import connect, init_schema, seed_gpus


def _row_to_gpu(row: sqlite3.Row) -> GPUResource:
    return GPUResource(
        id=int(row["id"]),
        name=str(row["name"]),
        total_quantity=int(row["total_quantity"]),
        available_quantity=int(row["available_quantity"]),
        memory_gb=int(row["memory_gb"]),
    )


class GPURepository:
    """SQLite-backed repository for querying and managing simulated GPU resources."""

    def __init__(self, db_path: str | Path = "data/gpu_fleet.db") -> None:
        self.db_path = Path(db_path) if str(db_path) != ":memory:" else db_path
        self._memory_conn: sqlite3.Connection | None = (
            connect(":memory:") if str(db_path) == ":memory:" else None
        )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if self._memory_conn is not None:
            yield self._memory_conn
            return

        conn = connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def close(self) -> None:
        """Close the persistent connection when using an in-memory SQLite database."""
        if self._memory_conn is not None:
            self._memory_conn.close()
            self._memory_conn = None

    def initialize(self, *, seed: bool = True) -> None:
        """Ensure schema exists and optionally seed the initial GPU fleet."""
        with self._connection() as conn:
            init_schema(conn)
            if seed:
                seed_gpus(conn, force_reset=False)

    def reset_to_seed(self) -> None:
        """Reset the database to the initial seeded state."""
        with self._connection() as conn:
            init_schema(conn)
            seed_gpus(conn, force_reset=True)

    def list_gpus(self, *, only_available: bool = False) -> list[GPUResource]:
        """Return all GPU models ordered by id."""
        sql = "SELECT id, name, total_quantity, available_quantity, memory_gb FROM gpus"
        if only_available:
            sql += " WHERE available_quantity > 0"
        sql += " ORDER BY id ASC;"

        with self._connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [_row_to_gpu(row) for row in rows]

    def find_gpus(
        self,
        *,
        name_query: str | None = None,
        min_memory_gb: int | None = None,
        min_available: int | None = None,
    ) -> list[GPUResource]:
        """Filter GPUs by optional name substring, minimum VRAM (GB), and minimum availability."""
        clauses: list[str] = []
        params: list[object] = []

        if name_query is not None and name_query.strip():
            clauses.append("LOWER(name) LIKE ?")
            params.append(f"%{name_query.strip().lower()}%")

        if min_memory_gb is not None:
            if min_memory_gb < 0:
                raise ValueError("min_memory_gb must be non-negative.")
            clauses.append("memory_gb >= ?")
            params.append(min_memory_gb)

        if min_available is not None:
            if min_available < 0:
                raise ValueError("min_available must be non-negative.")
            clauses.append("available_quantity >= ?")
            params.append(min_available)

        sql = "SELECT id, name, total_quantity, available_quantity, memory_gb FROM gpus"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id ASC;"

        with self._connection() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_row_to_gpu(row) for row in rows]

    def get_gpu(self, name: str) -> GPUResource | None:
        """Look up a single GPU by exact name (case-insensitive) or unambiguous substring.

        Examples:
            - "NVIDIA A100" -> NVIDIA A100
            - "a100" -> NVIDIA A100
            - "4090" -> NVIDIA RTX 4090
            - "100" -> None (ambiguous: matches A100 and H100)
            - "B200" -> None (not found)
        """
        cleaned = name.strip()
        if not cleaned:
            return None

        with self._connection() as conn:
            exact = conn.execute(
                """
                SELECT id, name, total_quantity, available_quantity, memory_gb
                FROM gpus
                WHERE LOWER(name) = LOWER(?);
                """,
                (cleaned,),
            ).fetchone()
            if exact is not None:
                return _row_to_gpu(exact)

            partial = conn.execute(
                """
                SELECT id, name, total_quantity, available_quantity, memory_gb
                FROM gpus
                WHERE LOWER(name) LIKE ?
                ORDER BY id ASC;
                """,
                (f"%{cleaned.lower()}%",),
            ).fetchall()

        if len(partial) == 1:
            return _row_to_gpu(partial[0])
        return None

    def check_availability(self, name: str, quantity: int = 1) -> AvailabilityCheck:
        """Check whether at least `quantity` units of the requested GPU are available."""
        if quantity < 1:
            raise ValueError("quantity must be at least 1.")

        gpu = self.get_gpu(name)
        if gpu is None:
            partial_matches = self.find_gpus(name_query=name) if name.strip() else []
            if len(partial_matches) > 1:
                return AvailabilityCheck(
                    query=name,
                    requested_quantity=quantity,
                    found=False,
                    is_available=False,
                    gpu=None,
                    ambiguous=True,
                    matches=tuple(partial_matches),
                )
            return AvailabilityCheck(
                query=name,
                requested_quantity=quantity,
                found=False,
                is_available=False,
                gpu=None,
            )

        return AvailabilityCheck(
            query=name,
            requested_quantity=quantity,
            found=True,
            is_available=gpu.available_quantity >= quantity,
            gpu=gpu,
        )

    def get_fleet_summary(self) -> FleetSummary:
        """Compute aggregate statistics across all GPU models."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS model_count,
                    COALESCE(SUM(total_quantity), 0) AS total_gpus,
                    COALESCE(SUM(available_quantity), 0) AS available_gpus,
                    COALESCE(SUM(total_quantity * memory_gb), 0) AS total_memory_gb,
                    COALESCE(SUM(available_quantity * memory_gb), 0) AS available_memory_gb
                FROM gpus;
                """
            ).fetchone()

        total_gpus = int(row["total_gpus"])
        available_gpus = int(row["available_gpus"])
        return FleetSummary(
            model_count=int(row["model_count"]),
            total_gpus=total_gpus,
            available_gpus=available_gpus,
            in_use_gpus=total_gpus - available_gpus,
            total_memory_gb=int(row["total_memory_gb"]),
            available_memory_gb=int(row["available_memory_gb"]),
        )

    def set_available_quantity(self, name: str, available_quantity: int) -> GPUResource:
        """Update the available quantity for a GPU model (useful for demos and tests)."""
        gpu = self.get_gpu(name)
        if gpu is None:
            raise LookupError(f"GPU not found or ambiguous: {name!r}")

        if not (0 <= available_quantity <= gpu.total_quantity):
            raise ValueError(
                f"available_quantity must be between 0 and {gpu.total_quantity}, "
                f"got {available_quantity}."
            )

        with self._connection() as conn:
            conn.execute(
                "UPDATE gpus SET available_quantity = ? WHERE id = ?;",
                (available_quantity, gpu.id),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT id, name, total_quantity, available_quantity, memory_gb FROM gpus WHERE id = ?;",
                (gpu.id,),
            ).fetchone()

        return _row_to_gpu(updated)
