"""Persistence & Session State Engine (RFC-001 Section 7).

SQLite (WAL) session store for kinematic / attestation chain continuity
across process restarts and concurrent readers.
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class SessionStore:
    """WAL-backed SQLite store for per-session kinematic chain history."""

    def __init__(self, db_path: str) -> None:
        parent = os.path.dirname(os.path.abspath(db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # Concurrent readers see committed writes immediately under WAL.
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_history (
                session_id TEXT,
                sequence_step INTEGER,
                canonical_row_hash TEXT,
                prev_bag_hash TEXT,
                omega_t REAL,
                theta_json TEXT,
                timestamp_ms INTEGER,
                PRIMARY KEY (session_id, sequence_step)
            )
            """
        )
        self.conn.commit()

    def append_state(
        self,
        session_id: str,
        step: int,
        current_hash: str,
        prev_hash: str,
        omega: float,
        theta: list[float],
        timestamp: int,
    ) -> None:
        """Insert one attested kinematic step and commit immediately."""
        self.conn.execute(
            """
            INSERT INTO session_history (
                session_id,
                sequence_step,
                canonical_row_hash,
                prev_bag_hash,
                omega_t,
                theta_json,
                timestamp_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                int(step),
                current_hash,
                prev_hash,
                float(omega),
                json.dumps(list(theta)),
                int(timestamp),
            ),
        )
        self.conn.commit()

    def get_latest_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return the highest-``sequence_step`` row for ``session_id``, or None."""
        cursor = self.conn.execute(
            """
            SELECT
                session_id,
                sequence_step,
                canonical_row_hash,
                prev_bag_hash,
                omega_t,
                theta_json,
                timestamp_ms
            FROM session_history
            WHERE session_id = ?
            ORDER BY sequence_step DESC
            LIMIT 1
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        payload = dict(row)
        # Decode θ for callers that restore the auditor ring buffer.
        try:
            payload["theta"] = json.loads(payload["theta_json"])
        except (TypeError, json.JSONDecodeError):
            payload["theta"] = []
        return payload

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "SessionStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
