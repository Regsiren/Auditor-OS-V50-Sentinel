"""Regression: commercial denylist basenames must never appear in this repo."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_commercial_ip_denylist_absent() -> None:
    script = ROOT / "scripts" / "check_ip_denylist.py"
    spec = importlib.util.spec_from_file_location("check_ip_denylist", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
    assert mod.iter_violations(ROOT) == []
