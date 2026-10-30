#!/usr/bin/env python3
"""
ARIA adaptive-hook latency overhead benchmark (open-core).

Measures wall-clock cost of a synthetic **model forward** (large GEMM)
with and without an additional ``HardenedHomeostaticSentinelCore``
adaptive hook on the residual.  Public ARIA target: hook overhead
**< 1.2%** of the host forward under this workload.

Run from repository root::

    pip install -r requirements.txt -r requirements-ai.txt
    python evaluations/latency_overhead_bench.py
    # or
    pytest evaluations/latency_overhead_bench.py -q
"""

from __future__ import annotations

import os
import statistics
import sys
import time
from typing import List, Tuple

import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auditor_ai.adaptive_engine import (  # noqa: E402
    HardenedHomeostaticSentinelCore,
    PrefillSentinelAuditor,
)

D_MODEL = 64
VOCAB = 2048
TOP_K = 128
# Host GEMM FLOPs dominate: open-core hook must stay <1.2% of this forward.
# ~48 × 8192² ≈ 3.2e9 FMAs per step — representative of a mid-size residual block.
HIDDEN = 8192
BATCH = 48
WARMUP = 3
ITERS = 12
OVERHEAD_LIMIT = 0.012  # 1.2%
REPEATS = 5


def _seed_core() -> HardenedHomeostaticSentinelCore:
    prefill = PrefillSentinelAuditor(d_model=D_MODEL, n_centroids=4)
    prompt = torch.zeros(16, D_MODEL, dtype=torch.float32)
    prompt[:, 0] = 1.0
    stage1 = prefill.forward(prompt, surprisals=torch.full((16,), 0.25))
    assert not stage1.prefill_veto
    core = HardenedHomeostaticSentinelCore(
        d_model=D_MODEL,
        vocab_size=VOCAB,
        top_k=TOP_K,
        anchor_radius=2.5,
    )
    core.seed_from_prefill(stage1)
    return core


def _host_forward(hidden: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
    """Synthetic host model forward (dominant FLOPs)."""
    return hidden @ weight


def _time_loop(fn, n: int) -> float:
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    return time.perf_counter() - t0


def measure_overhead(seed: int = 7) -> dict:
    """Return timing stats and fractional overhead (hook / host-forward)."""
    g = torch.Generator().manual_seed(seed)
    hidden = torch.randn(BATCH, HIDDEN, generator=g, dtype=torch.float32)
    weight = torch.randn(HIDDEN, HIDDEN, generator=g, dtype=torch.float32)
    residual = torch.zeros(D_MODEL, dtype=torch.float32)
    residual[0] = 1.0
    logits = torch.randn(VOCAB, generator=g, dtype=torch.float32) * 0.05

    core = _seed_core()

    def baseline() -> None:
        out = _host_forward(hidden, weight)
        # Keep a tiny dependency so the compiler cannot DCE the GEMM.
        residual[0] = 1.0 + 1e-6 * float(out[0, 0].item())

    def hooked() -> None:
        out = _host_forward(hidden, weight)
        residual[0] = 1.0 + 1e-6 * float(out[0, 0].item())
        core.forward(residual, logits=logits, informational_content=1.0)

    # Warmup
    _time_loop(baseline, WARMUP)
    _time_loop(hooked, WARMUP)
    core = _seed_core()

    def hooked_fresh() -> None:
        out = _host_forward(hidden, weight)
        residual[0] = 1.0 + 1e-6 * float(out[0, 0].item())
        core.forward(residual, logits=logits, informational_content=1.0)

    baselines: List[float] = []
    hooked_times: List[float] = []
    for _ in range(REPEATS):
        baselines.append(_time_loop(baseline, ITERS))
        hooked_times.append(_time_loop(hooked_fresh, ITERS))

    base_med = statistics.median(baselines)
    hook_med = statistics.median(hooked_times)
    overhead = max(0.0, (hook_med - base_med) / max(base_med, 1e-12))
    return {
        "baseline_s": base_med,
        "hooked_s": hook_med,
        "overhead_fraction": overhead,
        "overhead_pct": overhead * 100.0,
        "limit_pct": OVERHEAD_LIMIT * 100.0,
        "iters": ITERS,
        "hidden": HIDDEN,
        "batch": BATCH,
        "d_model": D_MODEL,
        "top_k": TOP_K,
        "passes_limit": overhead <= OVERHEAD_LIMIT,
    }


def test_adaptive_hook_overhead_under_1_2_percent() -> None:
    stats = measure_overhead()
    assert stats["passes_limit"], (
        f"ARIA hook overhead {stats['overhead_pct']:.3f}% exceeds "
        f"{stats['limit_pct']:.1f}% public threshold; stats={stats}"
    )


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass
    print("=" * 72)
    print("  ARIA latency overhead bench — adaptive hook vs host GEMM forward")
    print("  Target: auditor_ai/adaptive_engine.py (HardenedHomeostaticSentinelCore)")
    print("=" * 72)
    stats = measure_overhead()
    print(
        f"baseline={stats['baseline_s']*1e3:.3f} ms  "
        f"hooked={stats['hooked_s']*1e3:.3f} ms  "
        f"overhead={stats['overhead_pct']:.3f}%  "
        f"(limit {stats['limit_pct']:.1f}%)"
    )
    if stats["passes_limit"]:
        print("[PASS] Overhead within public ARIA <1.2% threshold.")
        raise SystemExit(0)
    print("[FAIL] Overhead exceeded threshold.")
    raise SystemExit(1)
