#!/usr/bin/env python3
"""Fail if commercial IP-denylist basenames appear in the public tree.

Denylisted modules must permanently remain in Auditor_Sovereign_Sandbox:

  - generate_scada.py
  - ingestion_spline.py
  - thermodynamic_calculus.py
  - phase_space_gating.py
  - rfc001_packaging.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DENIED_BASENAMES = frozenset(
    {
        "generate_scada.py",
        "ingestion_spline.py",
        "thermodynamic_calculus.py",
        "phase_space_gating.py",
        "rfc001_packaging.py",
    }
)

SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".eggs",
        "dist",
        "build",
    }
)


def iter_violations(root: Path) -> list[Path]:
    hits: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.name in DENIED_BASENAMES:
            hits.append(path)
    return sorted(hits)


def main() -> int:
    violations = iter_violations(ROOT)
    if violations:
        print("IP DENYLIST VIOLATION — remove these from the public repo:", file=sys.stderr)
        for path in violations:
            print(f"  {path.relative_to(ROOT).as_posix()}", file=sys.stderr)
        print(
            "Canonical home: Auditor_Sovereign_Sandbox only.",
            file=sys.stderr,
        )
        return 1
    print("IP denylist check passed (0 commercial denylist files present).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
