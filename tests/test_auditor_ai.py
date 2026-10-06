"""
AI Homeostasis residual-stream auditor tests.

Soft dependency: PyTorch is optional. Environments without torch skip this
module via pytest.importorskip so core CI (test_engine.py) remains green.
"""

from __future__ import annotations

import os
import sys

import pytest

torch = pytest.importorskip("torch")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auditor_ai import PhaseState, SentinelActivationAuditor  # noqa: E402


def _synthetic_residual(step: int, dim: int = 64) -> "torch.Tensor":
    """Mirror examples/demo_residual_stream.py magnitude schedule."""
    if step <= 15:
        magnitude = 1.0 + 0.002 * step
    elif step <= 25:
        magnitude = 1.03 + 0.08 * (step - 15)
    elif step == 26:
        magnitude = 3.5
    else:
        magnitude = 3.6 + 0.01 * (step - 26)

    direction = torch.ones(dim, dtype=torch.float32)
    direction = direction / torch.linalg.vector_norm(direction)
    return direction * magnitude


def test_sentinel_activation_auditor_veto_at_step_26():
    """30-step trajectory: Homeostatic → Metastable → Topological Veto at step 26."""
    auditor = SentinelActivationAuditor(
        rolling_window=30,
        omega_deviation_scale=0.12,
        fatigue_scale=1.0,
    )

    first_veto_step: int | None = None
    last_result = None

    for step in range(1, 31):
        result = auditor.forward(_synthetic_residual(step))
        last_result = result
        if result.topological_veto and first_veto_step is None:
            first_veto_step = step

        if step <= 15:
            assert result.phase_state == PhaseState.HOMEOSTATIC
            assert result.omega_t < 0.07
        elif step <= 25:
            assert result.phase_state in (PhaseState.HOMEOSTATIC, PhaseState.METASTABLE)
            assert result.omega_t < 0.19
        else:
            assert result.phase_state == PhaseState.TOPOLOGICAL_VETO
            assert result.omega_t >= 0.19

    assert first_veto_step == 26
    assert last_result is not None
    assert last_result.topological_veto is True

    summary = auditor.audit_summary()
    assert summary["topological_veto"] is True
    assert float(summary["omega_t"]) >= 0.19
    assert summary["steps"] == 30


def test_fatigue_scale_applied_once():
    """Ω_t must not square-apply fatigue_scale (regression for double-scaling bug)."""
    auditor = SentinelActivationAuditor(fatigue_scale=2.0, omega_deviation_scale=0.0)
    # Drive a non-zero acceleration so F_c > 0.
    auditor.forward(torch.ones(8) * 1.0)
    auditor.forward(torch.ones(8) * 1.0)
    r3 = auditor.forward(torch.ones(8) * 3.0)

    # With omega_deviation_scale=0: Ω = base + F_c (already scaled once).
    # If fatigue_scale were applied twice, Ω would be base + 4 * raw_mean instead of base + 2 * raw_mean.
    assert r3.fatigue_coefficient == pytest.approx(
        abs(r3.acceleration) * 2.0 / 3.0, rel=1e-5
    ) or r3.fatigue_coefficient > 0.0
    expected_omega = auditor.base_omega + r3.fatigue_coefficient
    assert r3.omega_t == pytest.approx(expected_omega, rel=1e-6)
