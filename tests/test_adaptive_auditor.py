"""ARIA ScaledAdaptiveSentinelAuditor tests (soft-skip without torch)."""

from __future__ import annotations

import json
import os
import sys

import pytest

torch = pytest.importorskip("torch")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import Forensic_kernel as kernel
from auditor_ai import (
    HardenedHomeostaticSentinelCore,
    PrefillSentinelAuditor,
    ScaledAdaptiveSentinelAuditor,
    analyze_adaptive_dataframe,
    analyze_dual_head_dataframe,
)

SCHEMA_PATH = os.path.join(ROOT, "spec", "sent_attestation.json")


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


def test_analyze_adaptive_dataframe_veto_mints_schema_v10_bag():
    """Portal ARIA path: adaptive report → auto-mint Dual-Pillar v1.0 bag."""
    import pandas as pd

    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)

    rows = []
    for step in range(1, 31):
        v = _activation(step)
        rows.append({"observed_value": float(v[0].item() + v[1].item()), "sensor_id": "ZONE-07-RESIDUAL_STREAM"})
    # Strong orthogonal-style shock via scalar spike so Ω crosses veto.
    for step in range(31, 41):
        rows.append({"observed_value": 50.0 + step, "sensor_id": "ZONE-07-RESIDUAL_STREAM"})

    df = pd.DataFrame(rows)
    report = analyze_adaptive_dataframe(df, profile_name="AI_HOMEOSTASIS", d_model=64)
    assert report["v4_meta"]["observer_mode"] == "aria_adaptive"

    bag = kernel.mint_sentinel_v10_from_report(
        report,
        "ZONE-07-RESIDUAL_STREAM",
        private_key_bytes=bytes(range(32)),
        hmac_key=b"unit-test-hmac-key",
    )
    assert set(bag.keys()) == {
        "attestation_header",
        "thermodynamic_state_vector",
        "execution_context",
        "cryptographic_attestation",
    }
    assert "flags" not in bag
    jsonschema.validate(instance=bag, schema=schema)

    if report["v4_meta"]["quench_kinetic_veto"] or report["phi_current"] >= 0.19:
        assert bag["thermodynamic_state_vector"]["state_coordinate_omega"] >= 0.19


def _benign_prompt(seq_len: int = 24, d_model: int = 64) -> "torch.Tensor":
    t = torch.linspace(0.0, 1.0, seq_len).unsqueeze(-1)
    base = torch.zeros(seq_len, d_model)
    base[:, 0] = 1.0 + 0.05 * t.squeeze()
    base[:, 1] = 0.02 * t.squeeze()
    return base


def _injected_prompt(seq_len: int = 24, d_model: int = 64) -> "torch.Tensor":
    """Prompt with severe mid→late contraction discordance (injection-like)."""
    x = _benign_prompt(seq_len, d_model)
    # Blow up the late third off-manifold to force discordance + surprisal derivative.
    late0 = max(2, (2 * seq_len) // 3)
    x[late0:, 0] = 8.0
    x[late0:, 2] = 12.0
    x[late0:, 5] = -9.0
    return x


def test_prefill_sentinel_pass_extracts_agency_centroids():
    auditor = PrefillSentinelAuditor(d_model=64, n_centroids=4)
    result = auditor.forward(_benign_prompt(), surprisals=torch.full((24,), 0.3))
    assert result.prefill_veto is False
    assert result.omega_prefill < 0.19
    assert result.centroids.shape == (4, 64)
    assert result.contraction_discordance > 0.0
    assert result.tokens_saved == -1  # decode may proceed


def test_prefill_sentinel_prompt_injection_veto():
    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)

    auditor = PrefillSentinelAuditor(d_model=64, n_centroids=4, surprisal_scale=0.15, discordance_scale=0.2)
    result = auditor.forward(_injected_prompt(), surprisals=torch.full((24,), 2.5))
    assert result.prefill_veto is True
    assert result.omega_prefill >= 0.19
    assert result.tokens_saved == 0  # 0-token prefill save
    assert result.sent_bag is not None
    assert set(result.sent_bag.keys()) == {
        "attestation_header",
        "thermodynamic_state_vector",
        "execution_context",
        "cryptographic_attestation",
    }
    jsonschema.validate(instance=result.sent_bag, schema=schema)


def test_stage2_agency_centroid_init_and_delta_tau():
    prefill = PrefillSentinelAuditor(d_model=64, n_centroids=4).forward(_benign_prompt())
    core = HardenedHomeostaticSentinelCore(d_model=64, vocab_size=256, top_k=64)
    core.seed_from_prefill(prefill)
    assert core.agency_centroids is not None
    assert core.agency_centroids.shape == (4, 64)

    assert core.informational_metric_interval(0.0) == pytest.approx(core.delta_min)
    assert core.informational_metric_interval(2.0) == pytest.approx(2.0 / core.i0)

    theta = torch.zeros(64)
    theta[0] = 1.0
    step = core.forward(theta, informational_content=2.0)
    assert step.delta_tau == pytest.approx(2.0 / core.i0)
    assert step.omega_t < 0.19


def test_stage2_fused_top_k_steering_and_feedforward_compensation():
    prefill = PrefillSentinelAuditor(d_model=64, n_centroids=4).forward(_benign_prompt())
    core = HardenedHomeostaticSentinelCore(d_model=64, vocab_size=256, top_k=64)
    core.seed_from_prefill(prefill)

    # Warm up one laminar step so PID / velocity state exist.
    warm = torch.zeros(64)
    warm[0] = 1.0
    core.forward(warm, logits=torch.zeros(256), informational_content=1.0)

    shock = torch.zeros(64)
    shock[0] = 1.0
    shock[1] = 4.0
    logits = torch.randn(256)
    result = core.forward(shock, logits=logits, informational_content=1.2)

    assert result.actuation_applied is True
    assert result.steered_logits is not None
    assert result.top_k_indices is not None
    assert result.top_k_indices.numel() == 64
    assert result.steered_logits.shape == (256,)
    # Feedforward compensation should be non-trivial after actuation.
    assert abs(result.feedforward_compensation) > 0.0 or abs(result.smoothed_psi) > 0.0
    assert abs(core.last_actuation_compensation) >= 0.0


def test_stage2_orthogonal_shock_vetoes_within_three_tokens():
    jsonschema = pytest.importorskip("jsonschema")
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)

    prefill = PrefillSentinelAuditor(d_model=64, n_centroids=4).forward(_benign_prompt())
    core = HardenedHomeostaticSentinelCore(d_model=64, vocab_size=256, top_k=64, anchor_radius=2.0)
    core.seed_from_prefill(prefill)

    shock_step = 12
    first_veto = None
    veto_bag = None
    for step in range(1, 21):
        v = torch.zeros(64)
        v[0] = 1.0 + 0.002 * step
        if step < shock_step:
            v[1] = 0.001 * step
        elif step == shock_step:
            v[1] = 3.0
        else:
            v[1] = 3.0 + 0.05 * (step - shock_step)
        result = core.forward(v, logits=torch.randn(256), informational_content=1.0)
        if step < shock_step:
            assert result.omega_t < 0.07
        if result.topological_veto and first_veto is None:
            first_veto = step
            veto_bag = result.sent_bag

    assert first_veto is not None
    assert 0 <= (first_veto - shock_step) <= 3
    assert veto_bag is not None
    jsonschema.validate(instance=veto_bag, schema=schema)


def test_analyze_dual_head_dataframe_exposes_stage_omegas():
    import pandas as pd

    rows = [{"observed_value": 1.0 + 0.01 * i, "sensor_id": "ZONE-07-RESIDUAL_STREAM"} for i in range(40)]
    # Late decode shock via elevated observed_value after prefill window.
    for i in range(40, 55):
        rows.append({"observed_value": 20.0 + i, "sensor_id": "ZONE-07-RESIDUAL_STREAM"})
    df = pd.DataFrame(rows)
    report = analyze_dual_head_dataframe(df, profile_name="AI_HOMEOSTASIS", d_model=64)
    assert report["v4_meta"]["observer_mode"] == "dual_head_governor"
    assert "omega_prefill" in report["v4_meta"]
    assert "omega_decode" in report["v4_meta"]
    if report["v4_meta"]["quench_kinetic_veto"]:
        assert report.get("sent_bag") is not None or report["v4_meta"].get("sent_bag") is not None
