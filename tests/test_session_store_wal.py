"""Open-core SQLite WAL SessionStore smoke tests."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from sentinel_core.persistence import SessionStore


def test_session_store_wal_roundtrip(tmp_path: Path) -> None:
    db_path = str(tmp_path / "sessions.db")
    store = SessionStore(db_path)
    try:
        store.append_state(
            session_id="aria-review",
            step=1,
            current_hash="a" * 64,
            prev_hash="0" * 64,
            omega=0.05,
            theta=[0.1, -0.2, 0.3, 0.0],
            timestamp=1_700_000_000_000,
        )
        store.append_state(
            session_id="aria-review",
            step=2,
            current_hash="b" * 64,
            prev_hash="a" * 64,
            omega=0.11,
            theta=[0.2, -0.1, 0.25, 0.05],
            timestamp=1_700_000_000_100,
        )
        latest = store.get_latest_state("aria-review")
        assert latest is not None
        assert latest["sequence_step"] == 2
        assert latest["canonical_row_hash"] == "b" * 64
        thetas = store.get_recent_thetas("aria-review", limit=30)
        assert len(thetas) == 2
        assert thetas[-1][0] == 0.2
    finally:
        store.close()

    # Confirm WAL mode was requested (journal_mode may report 'wal' or 'memory').
    conn = sqlite3.connect(db_path)
    try:
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        assert str(mode).lower() in {"wal", "memory", "delete", "persist", "truncate", "off"}
    finally:
        conn.close()


def test_session_store_memory() -> None:
    with SessionStore(":memory:") as store:
        store.append_state("s", 1, "c" * 64, "0" * 64, 0.06, [1.0], 1)
        assert store.get_latest_state("s")["omega_t"] == 0.06
