#!/usr/bin/env python3
"""
Stage I Prefill + Stage II Decode Dual-Head Governor demo.

Pipeline
--------
  1. Stage I PrefillSentinelAuditor on a prompt — centroids + prefill pass/veto.
  2. Hand seed state to Stage II HardenedHomeostaticSentinelCore.
  3. Simulate 20 nominal decode steps (Ω < 0.07).
  4. Inject orthogonal shear shock at step 12; verify Fused Top-K steering
     and Topological Veto within ≤ 3 steps (1–3 token early warning).

Run from repository root:
  pip install -r requirements-ai.txt
  python examples/demo_stage1_stage2_pipeline.py
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

from auditor_ai import HardenedHomeostaticSentinelCore, PrefillSentinelAuditor


D_MODEL = 64
VOCAB = 1024
TOP_K = 512
TOTAL_DECODE = 20
SHOCK_STEP = 12
MAX_VETO_LAG = 3


def _benign_prompt(seq_len: int = 24, d_model: int = D_MODEL) -> torch.Tensor:
    """Smooth laminar prompt residuals across early/mid/late strata."""
    t = torch.linspace(0.0, 1.0, seq_len).unsqueeze(-1)
    base = torch.zeros(seq_len, d_model)
    base[:, 0] = 1.0 + 0.05 * t.squeeze()
    base[:, 1] = 0.02 * t.squeeze()
    return base


def _decode_activation(step: int, shock_step: int = SHOCK_STEP, d_model: int = D_MODEL) -> torch.Tensor:
    v = torch.zeros(d_model, dtype=torch.float32)
    v[0] = 1.0 + 0.002 * step
    if step < shock_step:
        v[1] = 0.001 * step
    elif step == shock_step:
        v[1] = 3.0  # orthogonal shear injection
    else:
        v[1] = 3.0 + 0.05 * (step - shock_step)
    return v


def run_demo() -> None:
    print("=" * 78)
    print("  THOHAT V50-S  |  Stage I Prefill + Stage II Decode Governor Demo")
    print("=" * 78)

    # --- Step 1: Stage I Prefill ---
    prefill = PrefillSentinelAuditor(d_model=D_MODEL, n_centroids=4)
    prompt = _benign_prompt()
    surprisals = torch.full((prompt.shape[0],), 0.4)
    stage1 = prefill.forward(prompt, surprisals=surprisals)

    print("\n[Stage I] Prefill audit")
    print(f"  Ω_prefill              = {stage1.omega_prefill:.4f}")
    print(f"  contraction_discordance = {stage1.contraction_discordance:.4f}")
    print(f"  centroids shape         = {tuple(stage1.centroids.shape)}")
    print(f"  phase                   = {stage1.phase_state.name}")
    print(f"  prefill_veto            = {stage1.prefill_veto}")
    assert not stage1.prefill_veto, "Benign prompt should pass prefill"
    assert stage1.centroids.shape == (4, D_MODEL)
    print("  [+] Prefill PASS — agency centroids extracted (0-token save not triggered)")

    # --- Step 2: Handover to Stage II ---
    core = HardenedHomeostaticSentinelCore(
        d_model=D_MODEL,
        vocab_size=VOCAB,
        top_k=TOP_K,
        anchor_radius=2.5,
    )
    core.seed_from_prefill(stage1)
    assert core.agency_centroids is not None
    print("\n[Stage II] Seeded from prefill centroids")
    print(f"  agency centroids        = {tuple(core.agency_centroids.shape)}")
    print(f"  top_k                   = {core.top_k}")

    # --- Steps 3–4: Decode loop ---
    print("\n[Decode] step telemetry")
    print(
        f"{'step':>4}  {'Ω_t':>8}  {'Δτ':>8}  {'a_orth':>10}  "
        f"{'ψ_sm':>8}  {'steer':>5}  phase"
    )
    print("-" * 78)

    first_veto: int | None = None
    first_steer: int | None = None
    gen = torch.Generator().manual_seed(7)

    for step in range(1, TOTAL_DECODE + 1):
        theta = _decode_activation(step)
        logits = torch.randn(VOCAB, generator=gen) * 0.1
        logits[0] += 1.0  # mild preference for token 0
        result = core.forward(theta, logits=logits, informational_content=1.0 + 0.01 * step)

        if result.actuation_applied and first_steer is None and step >= SHOCK_STEP:
            first_steer = step
        if result.topological_veto and first_veto is None:
            first_veto = step

        marker = ""
        if step == SHOCK_STEP:
            marker = "  ← ORTHOGONAL SHOCK"
        if result.topological_veto and first_veto == step:
            marker = "  ← TOPOLOGICAL VETO"

        print(
            f"{step:4d}  {result.omega_t:8.4f}  {result.delta_tau:8.4f}  "
            f"{result.a_orthogonal:10.4e}  {result.smoothed_psi:8.4f}  "
            f"{str(result.actuation_applied):>5}  {result.phase_state.name}{marker}"
        )

        if step < SHOCK_STEP:
            assert result.omega_t < 0.07, f"Nominal decode Ω breached at step {step}: {result.omega_t}"

    print("-" * 78)
    print(f"First fused Top-K steer @ shock window : {first_steer}")
    print(f"First topological veto                 : {first_veto}")
    print(f"Feedforward compensation (final)       : {core.last_actuation_compensation:.6f}")
    print("=" * 78)

    assert first_steer is not None and first_steer >= SHOCK_STEP
    assert first_veto is not None, "Expected topological veto after orthogonal shock"
    lag = first_veto - SHOCK_STEP
    assert 0 <= lag <= MAX_VETO_LAG, f"Veto lag {lag} exceeds 1–3 token early-warning window"
    print(
        f"[+] Demo assertions passed: nominal Ω < 0.07, fused Top-K steering on shock, "
        f"veto within {lag} token(s) (≤ {MAX_VETO_LAG})."
    )


if __name__ == "__main__":
    run_demo()
