from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS gpus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    total_quantity INTEGER NOT NULL CHECK (total_quantity >= 0),
    available_quantity INTEGER NOT NULL CHECK (
        available_quantity >= 0 AND available_quantity <= total_quantity
    ),
    memory_gb INTEGER NOT NULL CHECK (memory_gb > 0)
);
"""

# Initial fleet specification from Desafio_2026.md: (name, total_quantity, memory_gb)
SEED_GPUS: tuple[tuple[str, int, int], ...] = (
    ("NVIDIA A100", 4, 80),
    ("NVIDIA L40S", 6, 48),
    ("NVIDIA RTX 4090", 3, 24),
    ("NVIDIA H100", 2, 80),
    ("NVIDIA A40", 4, 48),
)


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection configured with Row factory and foreign keys."""
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create database tables if they do not exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def seed_gpus(conn: sqlite3.Connection, *, force_reset: bool = False) -> None:
    """Populate the gpus table with the challenge's default fleet.

    When force_reset is False (default), inserts are idempotent via INSERT OR IGNORE
    so existing state (e.g. modified available_quantity) is preserved.
    """
    if force_reset:
        conn.execute("DELETE FROM gpus;")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'gpus';")

    conn.executemany(
        """
        INSERT OR IGNORE INTO gpus (name, total_quantity, available_quantity, memory_gb)
        VALUES (?, ?, ?, ?);
        """,
        [(name, qty, qty, mem) for name, qty, mem in SEED_GPUS],
    )
    conn.commit()
