"""ARIA ScaledAdaptiveSentinelAuditor tests (soft-skip without torch)."""

from __future__ import annotations

import os
import sys

import pytest

torch = pytest.importorskip("torch")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from auditor_ai import ScaledAdaptiveSentinelAuditor


def _activation(step: int, d_model: int = 64, shock_step: int = 25) -> "torch.Tensor":
    v = torch.zeros(d_model, dtype=torch.float32)
    v[0] = 1.0 + 0.002 * step
    if step < shock_step:
        v[1] = 0.001 * step
    elif step == shock_step:
        v[1] = 2.5
    else:
        v[1] = 2.5 + 0.01 * (step - shock_step)
    return v


def test_epsilon_scales_with_sqrt_d_model():
    a = ScaledAdaptiveSentinelAuditor(d_model=100, base_epsilon=1e-7)
    assert a.epsilon_scaled == pytest.approx(1e-7 * 10.0)


def test_laminar_then_orthogonal_shock_veto_at_step_25():
    auditor = ScaledAdaptiveSentinelAuditor(d_model=64, rolling_window=30)
    first_veto = None
    freeze_step = None

    for step in range(1, 41):
        result = auditor.forward(_activation(step))
        if result.anchor_frozen and freeze_step is None:
            freeze_step = step
        if result.topological_veto and first_veto is None:
            first_veto = step
        if step < 25:
            assert result.omega_t < 0.07

    assert freeze_step == 25
    assert first_veto == 25
    assert auditor.audit_summary()["anchor_frozen"] is True
