#!/usr/bin/env python3
"""
Demo: PyTorch residual-stream AI Homeostasis audit over 30 reasoning steps.

Trajectory schedule
-------------------
  Steps  1–15 : Nominal homeostatic processing (stable residual norm).
  Steps 16–25 : Goal-drift recalibration (sustained latent deviation ramp).
  Step     26 : Acute acceleration spike → Topological Veto (Ω ≥ 0.19).
  Steps 27–30 : Post-veto frames (Ω remains above veto gate).

Run from repository root:
  pip install torch
  python examples/demo_residual_stream.py
"""

from __future__ import annotations

import os
import sys

import torch

# Shipped phase labels / Greek symbols; force UTF-8 on narrow Windows consoles.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# Allow `python examples/demo_residual_stream.py` from repo root.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auditor_ai import PhaseState, SentinelActivationAuditor


def _synthetic_residual(step: int, dim: int = 64) -> torch.Tensor:
    """
    Construct a synthetic residual-stream vector whose L2 norm encodes θ_t.

    The schedule is deterministic so reviewers can reproduce the veto at step 26.
    """
    # Base homeostatic activation magnitude.
    if step <= 15:
        magnitude = 1.0 + 0.002 * step
    elif step <= 25:
        # Goal-drift recalibration: smooth ramp away from genesis baseline.
        magnitude = 1.03 + 0.08 * (step - 15)
    elif step == 26:
        # Acute acceleration: discontinuous jump that spikes θ̈ and lifts Ω.
        magnitude = 3.5
    else:
        # Post-veto elevated plateau (trajectory remains non-homeostatic).
        magnitude = 3.6 + 0.01 * (step - 26)

    direction = torch.ones(dim, dtype=torch.float32)
    direction = direction / torch.linalg.vector_norm(direction)
    return direction * magnitude


def run_demo(total_steps: int = 30) -> None:
    auditor = SentinelActivationAuditor(
        rolling_window=30,
        omega_deviation_scale=0.12,
        fatigue_scale=1.0,
    )

    print("=" * 72)
    print("  THOHAT V50-S  |  Residual-Stream AI Homeostasis Demo")
    print("=" * 72)
    print(f"{'step':>4}  {'θ':>8}  {'θ̈':>10}  {'F_c':>10}  {'Ω_t':>8}  phase")
    print("-" * 72)

    veto_step: int | None = None

    for step in range(1, total_steps + 1):
        residual = _synthetic_residual(step)
        result = auditor.forward(residual)

        marker = ""
        if result.topological_veto and veto_step is None:
            veto_step = result.step_index + 1  # 1-indexed display
            marker = "  ← TOPOLOGICAL VETO"

        print(
            f"{step:4d}  {result.theta:8.4f}  {result.acceleration:10.4e}  "
            f"{result.fatigue_coefficient:10.4e}  {result.omega_t:8.4f}  "
            f"{result.phase_state.name}{marker}"
        )

    summary = auditor.audit_summary()
    print("-" * 72)
    print(f"Final Ω_t     : {summary['omega_t']:.4f}")
    print(f"Phase state   : {summary['phase_state']}")
    print(f"Veto asserted : {summary['topological_veto']}")
    if veto_step is not None:
        print(f"First veto at : step {veto_step}")
    print("=" * 72)

    # Hard assertions for CI / reviewer reproducibility.
    assert veto_step == 26, f"Expected Topological Veto at step 26, got {veto_step}"
    assert summary["topological_veto"] is True
    assert float(summary["omega_t"]) >= 0.19
    print("[+] Demo assertions passed: Topological Veto at step 26 (Ω >= 0.19).")


if __name__ == "__main__":
    run_demo()
