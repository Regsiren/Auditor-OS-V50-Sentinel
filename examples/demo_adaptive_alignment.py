#!/usr/bin/env python3
"""
ARIA Adaptive Alignment demo — laminar semantic drift then orthogonal shock.

Schedule (40 steps)
-------------------
  Steps  1–24 : Laminar semantic drift (Ω kept < 0.07).
  Step     25 : Orthogonal acceleration injection → anchor freeze + Ω ≥ 0.19 veto.
  Steps 26–40 : Post-veto elevated orthogonal residual.

Run from repository root:
  pip install -r requirements-ai.txt
  python examples/demo_adaptive_alignment.py
"""

from __future__ import annotations

import os
import sys

import torch

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auditor_ai import ScaledAdaptiveSentinelAuditor


D_MODEL = 64
TOTAL_STEPS = 40
SHOCK_STEP = 25


def _activation(step: int, d_model: int = D_MODEL) -> torch.Tensor:
    """
    Construct a residual vector with controlled tangential vs orthogonal content.

    Laminar steps advance mostly along e_0 (tangential semantic drift).
    Shock at step 25 injects a large e_1 component (orthogonal shear).
    """
    v = torch.zeros(d_model, dtype=torch.float32)
    # Slow laminar drift along primary semantic axis.
    v[0] = 1.0 + 0.002 * step
    if step < SHOCK_STEP:
        v[1] = 0.001 * step  # tiny orthogonal component (below freeze threshold)
    elif step == SHOCK_STEP:
        v[1] = 2.5  # orthogonal acceleration injection
    else:
        v[1] = 2.5 + 0.01 * (step - SHOCK_STEP)
    return v


def run_demo() -> None:
    auditor = ScaledAdaptiveSentinelAuditor(d_model=D_MODEL, rolling_window=30)
    print("=" * 78)
    print("  THOHAT V50-S  |  ARIA Adaptive Alignment Demo")
    print("=" * 78)
    print(
        f"{'step':>4}  {'Ω_t':>8}  {'a_orth':>10}  {'λ_t':>6}  "
        f"{'freeze':>6}  phase"
    )
    print("-" * 78)

    first_veto: int | None = None
    freeze_step: int | None = None

    for step in range(1, TOTAL_STEPS + 1):
        result = auditor.forward(_activation(step))
        marker = ""
        if result.anchor_frozen and freeze_step is None:
            freeze_step = step
            marker = "  ← ANCHOR FREEZE"
        if result.topological_veto and first_veto is None:
            first_veto = step
            marker = "  ← TOPOLOGICAL VETO"

        print(
            f"{step:4d}  {result.omega_t:8.4f}  {result.a_orthogonal:10.4e}  "
            f"{result.lambda_t:6.3f}  {str(result.anchor_frozen):>6}  "
            f"{result.phase_state.name}{marker}"
        )

        if step < SHOCK_STEP:
            assert result.omega_t < 0.07, f"Laminar Ω breached early at step {step}: {result.omega_t}"

    print("-" * 78)
    print(f"Summary: {auditor.audit_summary()}")
    print(f"First freeze at : {freeze_step}")
    print(f"First veto at   : {first_veto}")
    print("=" * 78)

    assert freeze_step == SHOCK_STEP, f"Expected freeze at {SHOCK_STEP}, got {freeze_step}"
    assert first_veto == SHOCK_STEP, f"Expected veto at {SHOCK_STEP}, got {first_veto}"
    print(f"[+] Demo assertions passed: freeze + veto at step {SHOCK_STEP}.")


if __name__ == "__main__":
    run_demo()
