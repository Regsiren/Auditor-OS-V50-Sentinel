"""
ARIA Adaptive Alignment Engine — ScaledAdaptiveSentinelAuditor plus
Consolidated Stage I (Prefill) / Stage II (Decode) Dual-Head Governor.

Implements dimension-scaled titration, orthogonal shear decomposition,
dynamic baseline annealing, dual-scale State Uncertainty Coordinate Ω_t,
agency-preserving centroids, Informational Metric Interval kinematics,
and Fused Top-K logit steering for the ARIA research track (Pillar I).
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple, TYPE_CHECKING

import torch
import torch.nn as nn
import torch.nn.functional as F

from auditor_ai.sentinel_engine import (
    BASE_OMEGA,
    HOMEOSTATIC_MARGIN,
    TITRATION_CEILING,
    TOPOLOGICAL_VETO,
)


def _mint_veto_sent_bag(
    *,
    omega: float,
    j_tau: float,
    fc: float,
    phase_boundary_state: str,
    sequence_step: int,
    model_identifier: str,
    zone_or_session_id: str = "ZONE-07-RESIDUAL_STREAM",
    layer_depth_index: int = 0,
) -> Dict[str, Any]:
    """Mint a Dual-Pillar schema v1.0 `.sent` bag on Topological Veto."""
    import Forensic_kernel as kernel

    return kernel.mint_sentinel_v10_bag(
        state_coordinate_omega=float(omega),
        sub_resolution_jitter_j_tau=max(0.0, float(j_tau)),
        rolling_fatigue_fc=max(0.0, float(fc)),
        phase_boundary_state=phase_boundary_state,
        sequence_step=int(max(0, sequence_step)),
        model_identifier=model_identifier,
        layer_depth_index=int(layer_depth_index),
        zone_or_session_id=zone_or_session_id,
    )

if TYPE_CHECKING:
    import pandas as pd

DEFAULT_ROLLING_WINDOW: int = 30
DEFAULT_LOCAL_SCALE: float = 0.08
DEFAULT_MACRO_SCALE: float = 0.10
DEFAULT_ANNEAL_RATE: float = 0.05
DEFAULT_TOP_K: int = 512
DEFAULT_N_CENTROIDS: int = 4
DEFAULT_ANCHOR_RADIUS: float = 2.5
DEFAULT_DELTA_MIN: float = 1e-3
DEFAULT_I0: float = 1.0
DEFAULT_SOFTMIN_TEMP: float = 0.35
DEFAULT_PID_KP: float = 0.45
DEFAULT_PID_KI: float = 0.08
DEFAULT_PID_KD: float = 0.12
DEFAULT_PSI_SMOOTH: float = 0.65


class AdaptivePhaseState(str, Enum):
    """Tri-phase boundary labels for the adaptive alignment track."""

    NOMINAL = "Nominal / Homeostatic (< 0.07 Ω)"
    METASTABLE = "Metastable Impairment (0.07 to 0.19 Ω)"
    VETO = "Topological Veto (≥ 0.19 Ω)"


@dataclass(frozen=True)
class AdaptiveStepResult:
    """Per-step adaptive audit telemetry."""

    step_index: int
    theta_norm: float
    velocity_norm: float
    acceleration_norm: float
    a_tangential: float
    a_orthogonal: float
    epsilon_scaled: float
    titration_breach: bool
    lambda_t: float
    anchor_frozen: bool
    local_divergence: float
    macro_migration: float
    fatigue_coefficient: float
    omega_t: float
    phase_state: AdaptivePhaseState
    topological_veto: bool


class ScaledAdaptiveSentinelAuditor(nn.Module):
    """
    ARIA-scaled residual-stream auditor with orthogonal shear decomposition
    and dynamic baseline annealing.

    Pipeline
    --------
    1. Dimension-scaled firewall: ε_d = ε · √d_model
    2. Finite-difference kinematics on residual vector θ_t
    3. Orthogonal Shear Decomposition: a = a_∥ + a_⊥ relative to velocity
    4. Dynamic baseline annealing: λ_t ← (1−η)·λ_{t−1} + η·θ_t when |a_⊥| is
       laminar; freeze λ_t when orthogonal shock exceeds ε_d
    5. Dual-scale Ω_t = Ω₀ + α·local_div + β·macro_mig + F_c
    6. Tri-phase gates: Nominal < 0.07 ≤ Metastable < 0.19 ≤ Veto
    """

    def __init__(
        self,
        d_model: int = 64,
        rolling_window: int = DEFAULT_ROLLING_WINDOW,
        base_epsilon: float = TITRATION_CEILING,
        homeostatic_margin: float = HOMEOSTATIC_MARGIN,
        topological_veto: float = TOPOLOGICAL_VETO,
        base_omega: float = BASE_OMEGA,
        local_scale: float = DEFAULT_LOCAL_SCALE,
        macro_scale: float = DEFAULT_MACRO_SCALE,
        anneal_rate: float = DEFAULT_ANNEAL_RATE,
    ) -> None:
        super().__init__()
        if d_model < 1:
            raise ValueError("d_model must be >= 1")
        if rolling_window < 1:
            raise ValueError("rolling_window must be >= 1")

        self.d_model = int(d_model)
        self.rolling_window = int(rolling_window)
        self.base_epsilon = float(base_epsilon)
        self.epsilon_scaled = float(base_epsilon) * math.sqrt(float(d_model))
        self.homeostatic_margin = float(homeostatic_margin)
        self.topological_veto = float(topological_veto)
        self.base_omega = float(base_omega)
        self.local_scale = float(local_scale)
        self.macro_scale = float(macro_scale)
        self.anneal_rate = float(anneal_rate)

        self._prev_theta: Optional[torch.Tensor] = None
        self._prev_velocity: Optional[torch.Tensor] = None
        self._anchor: Optional[torch.Tensor] = None
        self._lambda_t: float = 1.0
        self._anchor_frozen: bool = False
        self._abs_accel_window: Deque[float] = deque(maxlen=self.rolling_window)
        self._step_index: int = 0

    def reset(self) -> None:
        """Clear trajectory / annealing state for a new episode."""
        self._prev_theta = None
        self._prev_velocity = None
        self._anchor = None
        self._lambda_t = 1.0
        self._anchor_frozen = False
        self._abs_accel_window.clear()
        self._step_index = 0

    @staticmethod
    def _as_vector(activation: torch.Tensor, d_model: int) -> torch.Tensor:
        v = activation.detach().float().reshape(-1)
        if v.numel() == 0:
            return torch.zeros(d_model, dtype=torch.float32)
        if v.numel() == d_model:
            return v
        if v.numel() == 1:
            # Broadcast scalar activation into a synthetic residual direction.
            out = torch.zeros(d_model, dtype=torch.float32)
            out[0] = v.item()
            return out
        # Truncate / pad to d_model for mixed-shape hooks.
        out = torch.zeros(d_model, dtype=torch.float32)
        n = min(d_model, v.numel())
        out[:n] = v[:n]
        return out

    def _classify(self, omega_t: float) -> AdaptivePhaseState:
        if omega_t >= self.topological_veto:
            return AdaptivePhaseState.VETO
        if omega_t >= self.homeostatic_margin:
            return AdaptivePhaseState.METASTABLE
        return AdaptivePhaseState.NOMINAL

    def forward(self, residual_activation: torch.Tensor) -> AdaptiveStepResult:
        """
        Ingest one residual-stream frame and return adaptive alignment telemetry.
        """
        theta = self._as_vector(residual_activation, self.d_model)
        theta_norm = float(torch.linalg.vector_norm(theta).item())

        if self._anchor is None:
            self._anchor = theta.clone()

        if self._prev_theta is None:
            velocity = torch.zeros_like(theta)
            acceleration = torch.zeros_like(theta)
        else:
            velocity = theta - self._prev_theta
            if self._prev_velocity is None:
                acceleration = torch.zeros_like(theta)
            else:
                acceleration = velocity - self._prev_velocity

        velocity_norm = float(torch.linalg.vector_norm(velocity).item())
        acceleration_norm = float(torch.linalg.vector_norm(acceleration).item())

        # Orthogonal Shear Decomposition relative to velocity direction.
        if velocity_norm > 1e-12:
            v_hat = velocity / velocity_norm
            a_tangential = float(torch.dot(acceleration, v_hat).item())
            a_parallel_vec = a_tangential * v_hat
            a_orth_vec = acceleration - a_parallel_vec
            a_orthogonal = float(torch.linalg.vector_norm(a_orth_vec).item())
        else:
            a_tangential = 0.0
            a_orthogonal = acceleration_norm

        titration_breach = a_orthogonal > self.epsilon_scaled or acceleration_norm > self.epsilon_scaled

        # Dynamic baseline annealing — freeze on orthogonal shock.
        if a_orthogonal > self.epsilon_scaled * 1e3 or a_orthogonal > 0.5:
            self._anchor_frozen = True
        if not self._anchor_frozen:
            eta = self.anneal_rate
            self._anchor = (1.0 - eta) * self._anchor + eta * theta
            self._lambda_t = (1.0 - eta) * self._lambda_t + eta * 1.0
        # else: λ_t and anchor held (freeze)

        local_divergence = abs(a_orthogonal)
        macro_migration = float(torch.linalg.vector_norm(theta - self._anchor).item())

        self._abs_accel_window.append(acceleration_norm)
        fatigue_coefficient = sum(self._abs_accel_window) / len(self._abs_accel_window)

        omega_t = (
            self.base_omega
            + self.local_scale * local_divergence
            + self.macro_scale * macro_migration
            + fatigue_coefficient
        )

        phase_state = self._classify(omega_t)
        topological_veto = phase_state == AdaptivePhaseState.VETO

        result = AdaptiveStepResult(
            step_index=self._step_index,
            theta_norm=theta_norm,
            velocity_norm=velocity_norm,
            acceleration_norm=acceleration_norm,
            a_tangential=a_tangential,
            a_orthogonal=a_orthogonal,
            epsilon_scaled=self.epsilon_scaled,
            titration_breach=titration_breach,
            lambda_t=self._lambda_t,
            anchor_frozen=self._anchor_frozen,
            local_divergence=local_divergence,
            macro_migration=macro_migration,
            fatigue_coefficient=fatigue_coefficient,
            omega_t=omega_t,
            phase_state=phase_state,
            topological_veto=topological_veto,
        )

        self._prev_velocity = velocity
        self._prev_theta = theta
        self._step_index += 1
        return result

    def audit_summary(self) -> Dict[str, float | str | bool | int]:
        """Compact summary of the accumulated adaptive trajectory."""
        fatigue = (
            sum(self._abs_accel_window) / len(self._abs_accel_window)
            if self._abs_accel_window
            else 0.0
        )
        return {
            "steps": self._step_index,
            "lambda_t": self._lambda_t,
            "anchor_frozen": self._anchor_frozen,
            "epsilon_scaled": self.epsilon_scaled,
            "fatigue_coefficient": fatigue,
            "d_model": self.d_model,
        }


def analyze_adaptive_dataframe(
    df_raw: "pd.DataFrame",
    *,
    value_col: str = "observed_value",
    profile_name: str = "AI_HOMEOSTASIS",
    d_model: int = 64,
    rolling_window: int = DEFAULT_ROLLING_WINDOW,
) -> dict:
    """
    Run :class:`ScaledAdaptiveSentinelAuditor` over a tabular activation stream.

    Returns an Engine-compatible report dict so Streamlit and Dual-Pillar `.sent`
    minting can reuse the same display / attestation path as the baseline auditor.
    """
    import pandas as pd  # local import keeps module import light for torch-only hosts

    if value_col not in df_raw.columns:
        raise ValueError(f"Activation stream missing required column '{value_col}'")

    df = df_raw.copy().reset_index(drop=True)
    auditor = ScaledAdaptiveSentinelAuditor(d_model=d_model, rolling_window=rolling_window)

    accelerations: List[float] = []
    fatigues: List[float] = []
    omegas: List[float] = []
    breaches: List[bool] = []
    a_orthogonals: List[float] = []
    a_tangentials: List[float] = []
    lambda_ts: List[float] = []
    frozen_flags: List[bool] = []
    last_result: Optional[AdaptiveStepResult] = None

    for raw in df[value_col].tolist():
        tensor = torch.tensor([float(raw)], dtype=torch.float32)
        result = auditor.forward(tensor)
        accelerations.append(result.acceleration_norm)
        fatigues.append(result.fatigue_coefficient)
        omegas.append(result.omega_t)
        breaches.append(result.titration_breach)
        a_orthogonals.append(result.a_orthogonal)
        a_tangentials.append(result.a_tangential)
        lambda_ts.append(result.lambda_t)
        frozen_flags.append(result.anchor_frozen)
        last_result = result

    df["kinetic_acceleration"] = accelerations
    df["fatigue_coefficient"] = fatigues
    df["omega_t"] = omegas
    df["kinetic_breach"] = breaches
    df["a_orthogonal"] = a_orthogonals
    df["a_tangential"] = a_tangentials
    df["lambda_t"] = lambda_ts
    df["anchor_frozen"] = frozen_flags

    if last_result is None:
        omega_final = BASE_OMEGA
        fc_final = 0.0
        phase = AdaptivePhaseState.NOMINAL
        breach_count = 0
        veto = False
        max_jitter = 0.0
        anchor_frozen = False
    else:
        omega_final = float(last_result.omega_t)
        fc_final = float(last_result.fatigue_coefficient)
        phase = last_result.phase_state
        breach_count = int(sum(breaches))
        veto = bool(last_result.topological_veto)
        max_jitter = float(max(a_orthogonals) if a_orthogonals else 0.0)
        anchor_frozen = bool(last_result.anchor_frozen)

    metastable = phase == AdaptivePhaseState.METASTABLE
    if omega_final >= TOPOLOGICAL_VETO and fc_final > 0.0:
        rul_steps = 0.0
    elif fc_final > 0.0 and omega_final < TOPOLOGICAL_VETO:
        rul_steps = max(0.0, (TOPOLOGICAL_VETO - omega_final) / (fc_final + 1e-12))
    else:
        rul_steps = float("inf")

    verdict = "FAIL" if veto else "PASS"
    v4_meta = {
        "cumulative_entropy": round(omega_final, 6),
        "fatigue_gradient_fc": round(fc_final, 8),
        "remaining_useful_life_periods": round(rul_steps, 2)
        if rul_steps != float("inf")
        else "NOMINAL / STABLE",
        "total_kinetic_breaches": breach_count,
        "max_observed_jitter": round(max_jitter, 8),
        "verdict": verdict,
        "phase_label": phase.value,
        "stalled_zone": metastable,
        "quench_kinetic_veto": veto,
        "domain_id": profile_name,
        "profile_name": profile_name,
        "state_coordinate": "Omega_t",
        "observer_mode": "aria_adaptive",
        "anchor_frozen": anchor_frozen,
        "epsilon_scaled": auditor.epsilon_scaled,
        "d_model": d_model,
    }

    return {
        "verdict": verdict,
        "phi_current": omega_final,
        "fc_gradient": fc_final,
        "remaining_useful_life_steps": rul_steps,
        "system_phase": phase.value,
        "v4_meta": v4_meta,
        "processed_df": df,
    }


# =============================================================================
# Stage I — Prefill Sentinel Auditor
# =============================================================================


@dataclass(frozen=True)
class PrefillAuditResult:
    """Stage I prefill audit telemetry and agency-preserving seed state."""

    omega_prefill: float
    phase_state: AdaptivePhaseState
    prefill_veto: bool
    surprisal_scaled_derivative: float
    contraction_discordance: float
    dist_early_mid: float
    dist_mid_late: float
    centroids: torch.Tensor  # (n_centroids, d_model)
    stratum_means: Dict[str, torch.Tensor]
    sequence_length: int
    d_model: int
    tokens_saved: int  # 0-token save when prefill veto fires
    sent_bag: Optional[Dict[str, Any]] = None  # Dual-Pillar v1.0 bag when veto


class PrefillSentinelAuditor(nn.Module):
    """
    Stage I Prefill Auditor — parallel stratum audit before decode begins.

    Audits prompt residual tensors across [early, mid, late] strata, scales
    spatial sequence derivatives by prompt surprisals, evaluates inter-layer
    contraction discordance, and extracts agency-optimized subspace centroids
    ``c_k`` that seed Stage II without collapsing agentic freedom.

    Input tensor expectations
    -------------------------
    * Preferred: ``[3, seq_len, d_model]`` — true layer strata (early, mid, late).
    * Fallback: ``[seq_len, d_model]`` — a single residual stream; the engine
      automatically partitions the sequence into temporal thirds.
    * Also accepted: ``[batch, seq_len, d_model]`` (batch-mean then temporal thirds).

    On ``Omega_prefill >= 0.19`` (``prefill_veto``), automatically mints a Dual-Pillar
    schema v1.0 `.sent` bag via ``mint_sentinel_v10_bag`` (returned on ``sent_bag``).
    """

    def __init__(
        self,
        d_model: int = 64,
        n_centroids: int = DEFAULT_N_CENTROIDS,
        homeostatic_margin: float = HOMEOSTATIC_MARGIN,
        topological_veto: float = TOPOLOGICAL_VETO,
        base_omega: float = BASE_OMEGA,
        discordance_scale: float = 0.12,
        surprisal_scale: float = 0.08,
    ) -> None:
        super().__init__()
        if d_model < 1:
            raise ValueError("d_model must be >= 1")
        if n_centroids < 1:
            raise ValueError("n_centroids must be >= 1")
        self.d_model = int(d_model)
        self.n_centroids = int(n_centroids)
        self.homeostatic_margin = float(homeostatic_margin)
        self.topological_veto = float(topological_veto)
        self.base_omega = float(base_omega)
        self.discordance_scale = float(discordance_scale)
        self.surprisal_scale = float(surprisal_scale)

    @staticmethod
    def _normalize_prompt(
        prompt_residuals: torch.Tensor,
        d_model: int,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Normalize prompt residuals into early/mid/late stratum tensors.

        Preferred input: ``[3, seq_len, d_model]`` true layer strata.
        Fallback: ``[seq_len, d_model]`` is partitioned into temporal thirds.
        """
        x = prompt_residuals.detach().float()
        if x.ndim == 2:
            # Fallback: single residual stream — partition into temporal thirds.
            seq, dim = x.shape
            if dim != d_model:
                # Pad / truncate feature dim.
                padded = torch.zeros(seq, d_model, dtype=torch.float32)
                n = min(dim, d_model)
                padded[:, :n] = x[:, :n]
                x = padded
            cuts = [0, max(1, seq // 3), max(2, (2 * seq) // 3), seq]
            early = x[cuts[0] : cuts[1]]
            mid = x[cuts[1] : cuts[2]]
            late = x[cuts[2] : cuts[3]]
            if early.numel() == 0:
                early = x[:1]
            if mid.numel() == 0:
                mid = x[min(1, seq - 1) : min(2, seq)]
            if late.numel() == 0:
                late = x[-1:]
            return early, mid, late

        if x.ndim == 3 and x.shape[0] == 3:
            # Explicit [early, mid, late] layer stack.
            strata = []
            for i in range(3):
                layer = x[i]
                if layer.shape[-1] != d_model:
                    padded = torch.zeros(layer.shape[0], d_model, dtype=torch.float32)
                    n = min(layer.shape[-1], d_model)
                    padded[:, :n] = layer[:, :n]
                    layer = padded
                strata.append(layer)
            return strata[0], strata[1], strata[2]

        if x.ndim == 3:
            # (batch, seq, d) — mean over batch then temporal thirds.
            return PrefillSentinelAuditor._normalize_prompt(x.mean(dim=0), d_model)

        raise ValueError(
            "prompt_residuals must be shaped (seq, d), (3, seq, d), or (batch, seq, d)"
        )

    @staticmethod
    def _mean_vec(tokens: torch.Tensor, d_model: int) -> torch.Tensor:
        if tokens.numel() == 0:
            return torch.zeros(d_model, dtype=torch.float32)
        return tokens.reshape(-1, tokens.shape[-1]).mean(dim=0)

    def _extract_agency_centroids(
        self,
        early: torch.Tensor,
        mid: torch.Tensor,
        late: torch.Tensor,
    ) -> torch.Tensor:
        """
        Agency-optimized subspace centroids from prompt clusters.

        Uses stratified means plus farthest-point sampling over pooled tokens so
        Stage II softmin routing preserves multiple agentic basins (not a single
        collapse-to-mean anchor).
        """
        pooled = torch.cat([early, mid, late], dim=0)
        if pooled.shape[0] == 0:
            return torch.zeros(self.n_centroids, self.d_model, dtype=torch.float32)

        seeds = [
            self._mean_vec(early, self.d_model),
            self._mean_vec(mid, self.d_model),
            self._mean_vec(late, self.d_model),
        ]
        centroids: List[torch.Tensor] = [s.clone() for s in seeds[: self.n_centroids]]

        # Farthest-point fill for remaining centroid slots.
        while len(centroids) < self.n_centroids:
            stacked = torch.stack(centroids, dim=0)
            dists = torch.cdist(pooled, stacked).min(dim=1).values
            idx = int(torch.argmax(dists).item())
            centroids.append(pooled[idx].clone())

        # One Lloyd-style refinement iteration (agency-preserving; no hard collapse).
        stacked = torch.stack(centroids[: self.n_centroids], dim=0)
        assign = torch.argmin(torch.cdist(pooled, stacked), dim=1)
        refined = []
        for k in range(self.n_centroids):
            mask = assign == k
            if bool(mask.any()):
                refined.append(pooled[mask].mean(dim=0))
            else:
                refined.append(stacked[k])
        return torch.stack(refined, dim=0)

    def _spatial_surprisal_derivative(
        self,
        early: torch.Tensor,
        mid: torch.Tensor,
        late: torch.Tensor,
        surprisals: Optional[torch.Tensor],
    ) -> float:
        """Spatial sequence derivative scaled by prompt surprisals."""
        mu_e = self._mean_vec(early, self.d_model)
        mu_m = self._mean_vec(mid, self.d_model)
        mu_l = self._mean_vec(late, self.d_model)
        d1 = torch.linalg.vector_norm(mu_m - mu_e)
        d2 = torch.linalg.vector_norm(mu_l - mu_m)
        raw = float((d1 + d2).item())

        if surprisals is None:
            # Proxy surprisal: mean token energy deviation across sequence.
            pooled = torch.cat([early, mid, late], dim=0)
            energies = torch.linalg.vector_norm(pooled, dim=-1)
            surprisal_weight = float(energies.std(unbiased=False).item()) + 1.0
        else:
            s = surprisals.detach().float().reshape(-1)
            surprisal_weight = float(s.mean().item()) + 1.0
        return raw * surprisal_weight

    def forward(
        self,
        prompt_residuals: torch.Tensor,
        surprisals: Optional[torch.Tensor] = None,
        *,
        zone_or_session_id: str = "ZONE-07-RESIDUAL_STREAM",
        auto_mint_sent: bool = True,
    ) -> PrefillAuditResult:
        """
        Audit a prompt residual sequence and return Stage I seed state.

        Parameters
        ----------
        prompt_residuals:
            Preferred ``[3, seq_len, d_model]`` true layer strata (early, mid, late).
            Fallback ``[seq_len, d_model]`` is auto-partitioned into temporal thirds.
            Also ``[batch, seq_len, d_model]`` (batch-mean then temporal thirds).
        surprisals:
            Optional per-token surprisal / NLL vector for derivative scaling.
        zone_or_session_id:
            Zone tag embedded in auto-minted `.sent` bags on veto.
        auto_mint_sent:
            When True (default), mint Dual-Pillar schema v1.0 on prefill veto.
        """
        early, mid, late = self._normalize_prompt(prompt_residuals, self.d_model)
        mu_e = self._mean_vec(early, self.d_model)
        mu_m = self._mean_vec(mid, self.d_model)
        mu_l = self._mean_vec(late, self.d_model)

        dist_early_mid = float(torch.linalg.vector_norm(mu_m - mu_e).item())
        dist_mid_late = float(torch.linalg.vector_norm(mu_l - mu_m).item())
        # Contraction discordance: mid→late stretch relative to early→mid.
        contraction_discordance = dist_mid_late / max(dist_early_mid, 1e-8)

        surprisal_deriv = self._spatial_surprisal_derivative(early, mid, late, surprisals)
        centroids = self._extract_agency_centroids(early, mid, late)

        omega_prefill = (
            self.base_omega
            + self.surprisal_scale * surprisal_deriv
            + self.discordance_scale * max(0.0, contraction_discordance - 1.0)
        )

        if omega_prefill >= self.topological_veto:
            phase = AdaptivePhaseState.VETO
        elif omega_prefill >= self.homeostatic_margin:
            phase = AdaptivePhaseState.METASTABLE
        else:
            phase = AdaptivePhaseState.NOMINAL

        veto = phase == AdaptivePhaseState.VETO
        seq_len = int(early.shape[0] + mid.shape[0] + late.shape[0])
        sent_bag: Optional[Dict[str, Any]] = None
        if veto and auto_mint_sent:
            sent_bag = _mint_veto_sent_bag(
                omega=omega_prefill,
                j_tau=surprisal_deriv,
                fc=0.0,
                phase_boundary_state=phase.value,
                sequence_step=max(0, seq_len - 1),
                model_identifier="aria-stage1-prefill-auditor",
                zone_or_session_id=zone_or_session_id,
                layer_depth_index=0,
            )
        return PrefillAuditResult(
            omega_prefill=float(omega_prefill),
            phase_state=phase,
            prefill_veto=veto,
            surprisal_scaled_derivative=float(surprisal_deriv),
            contraction_discordance=float(contraction_discordance),
            dist_early_mid=dist_early_mid,
            dist_mid_late=dist_mid_late,
            centroids=centroids,
            stratum_means={"early": mu_e, "mid": mu_m, "late": mu_l},
            sequence_length=seq_len,
            d_model=self.d_model,
            tokens_saved=0 if veto else -1,  # 0-token save on veto; -1 = decode proceeds
            sent_bag=sent_bag,
        )


# =============================================================================
# Stage II — Hardened Homeostatic Sentinel Core (Decode Governor)
# =============================================================================


@dataclass
class DecodeStepResult:
    """Per-token Stage II decode governor telemetry."""

    step_index: int
    delta_tau: float
    informational_content: float
    a_parallel: float
    a_orthogonal: float
    softmin_weights: torch.Tensor
    tether_radius_breach: bool
    raw_psi: float
    smoothed_psi: float
    feedforward_compensation: float
    steered_logits: Optional[torch.Tensor]
    top_k_indices: Optional[torch.Tensor]
    omega_t: float
    phase_state: AdaptivePhaseState
    topological_veto: bool
    actuation_applied: bool
    sent_bag: Optional[Dict[str, Any]] = None  # Dual-Pillar v1.0 bag when veto


@dataclass
class PrefillSeedState:
    """Handover packet from Stage I → Stage II."""

    centroids: torch.Tensor
    omega_prefill: float
    d_model: int


class HardenedHomeostaticSentinelCore(nn.Module):
    """
    Stage II Decode Core — closed-loop governor with agency-preserving centroids.

    Features
    --------
    * Informational Metric Interval: Δτ_t = max(δ_min, I(w_t) / I_0)
    * Orthogonal shear on information-time kinematics
    * Softmin relativistic routing vs prefill-seeded agency centroids with
      elastic tether radius R
    * Closed-loop PID actuation (smoothed_ψ) + feedforward compensation
    * Fused Top-K directional logit steering (K=512) at O(K · d_model) GEMV cost

    Input tensor expectations
    -------------------------
    * ``residual_activation``: vector broadcastable to ``d_model`` (scalar, ``[d]``,
      or padded/truncated residual frame) per decode step.
    * Prefill seed centroids must match ``d_model`` (from Stage I
      ``[3, seq_len, d_model]`` preferred strata, or temporal-thirds fallback).

    On ``Omega_t >= 0.19`` (``topological_veto``), automatically mints a Dual-Pillar
    schema v1.0 `.sent` bag via ``mint_sentinel_v10_bag`` (returned on ``sent_bag``).
    """

    def __init__(
        self,
        d_model: int = 64,
        vocab_size: int = 1024,
        top_k: int = DEFAULT_TOP_K,
        anchor_radius: float = DEFAULT_ANCHOR_RADIUS,
        delta_min: float = DEFAULT_DELTA_MIN,
        i0: float = DEFAULT_I0,
        softmin_temp: float = DEFAULT_SOFTMIN_TEMP,
        pid_kp: float = DEFAULT_PID_KP,
        pid_ki: float = DEFAULT_PID_KI,
        pid_kd: float = DEFAULT_PID_KD,
        psi_smooth: float = DEFAULT_PSI_SMOOTH,
        homeostatic_margin: float = HOMEOSTATIC_MARGIN,
        topological_veto: float = TOPOLOGICAL_VETO,
        base_omega: float = BASE_OMEGA,
        local_scale: float = DEFAULT_LOCAL_SCALE,
        macro_scale: float = DEFAULT_MACRO_SCALE,
        rolling_window: int = DEFAULT_ROLLING_WINDOW,
        embedding_table: Optional[torch.Tensor] = None,
    ) -> None:
        super().__init__()
        if d_model < 1:
            raise ValueError("d_model must be >= 1")
        self.d_model = int(d_model)
        self.vocab_size = int(vocab_size)
        self.top_k = int(min(top_k, vocab_size))
        self.anchor_radius = float(anchor_radius)
        self.delta_min = float(delta_min)
        self.i0 = float(i0)
        self.softmin_temp = float(softmin_temp)
        self.pid_kp = float(pid_kp)
        self.pid_ki = float(pid_ki)
        self.pid_kd = float(pid_kd)
        self.psi_smooth = float(psi_smooth)
        self.homeostatic_margin = float(homeostatic_margin)
        self.topological_veto = float(topological_veto)
        self.base_omega = float(base_omega)
        self.local_scale = float(local_scale)
        self.macro_scale = float(macro_scale)
        self.rolling_window = int(rolling_window)

        if embedding_table is None:
            # Deterministic synthetic embedding basis for unit tests / demos.
            gen = torch.Generator().manual_seed(50)
            emb = torch.randn(self.vocab_size, self.d_model, generator=gen)
            emb = F.normalize(emb, dim=-1)
        else:
            emb = embedding_table.detach().float()
            if emb.shape != (self.vocab_size, self.d_model):
                raise ValueError(
                    f"embedding_table must be ({self.vocab_size}, {self.d_model}), got {tuple(emb.shape)}"
                )
        self.register_buffer("embedding_table", emb)

        self._centroids: Optional[torch.Tensor] = None
        self._prev_theta: Optional[torch.Tensor] = None
        self._prev_velocity_tau: Optional[torch.Tensor] = None
        self._integral_error: float = 0.0
        self._prev_error: float = 0.0
        self._smoothed_psi: float = 0.0
        self._last_actuation_compensation: float = 0.0
        self._abs_accel_window: Deque[float] = deque(maxlen=self.rolling_window)
        self._step_index: int = 0
        self._seeded_omega: float = self.base_omega
        self._zone_or_session_id: str = "ZONE-07-RESIDUAL_STREAM"
        self._auto_mint_sent: bool = True
        self._veto_bag_emitted: bool = False

    def reset(self) -> None:
        """Clear decode trajectory / control state."""
        self._centroids = None
        self._prev_theta = None
        self._prev_velocity_tau = None
        self._integral_error = 0.0
        self._prev_error = 0.0
        self._smoothed_psi = 0.0
        self._last_actuation_compensation = 0.0
        self._abs_accel_window.clear()
        self._step_index = 0
        self._seeded_omega = self.base_omega
        self._veto_bag_emitted = False

    def seed_from_prefill(
        self,
        prefill: PrefillAuditResult | PrefillSeedState,
        *,
        zone_or_session_id: str = "ZONE-07-RESIDUAL_STREAM",
        auto_mint_sent: bool = True,
    ) -> None:
        """Hand over Stage I agency centroids and prefill Ω into the decode core."""
        self.reset()
        self._zone_or_session_id = zone_or_session_id
        self._auto_mint_sent = auto_mint_sent
        if isinstance(prefill, PrefillAuditResult):
            if prefill.prefill_veto:
                raise ValueError("Cannot seed Stage II from a vetoed prefill (0-token save).")
            self._centroids = prefill.centroids.detach().float().clone()
            self._seeded_omega = float(prefill.omega_prefill)
            if prefill.d_model != self.d_model:
                raise ValueError(
                    f"Prefill d_model {prefill.d_model} != Stage II d_model {self.d_model}"
                )
        else:
            self._centroids = prefill.centroids.detach().float().clone()
            self._seeded_omega = float(prefill.omega_prefill)
            if prefill.d_model != self.d_model:
                raise ValueError(
                    f"Seed d_model {prefill.d_model} != Stage II d_model {self.d_model}"
                )

    @property
    def agency_centroids(self) -> Optional[torch.Tensor]:
        return self._centroids

    @property
    def last_actuation_compensation(self) -> float:
        return self._last_actuation_compensation

    @property
    def smoothed_psi(self) -> float:
        return self._smoothed_psi

    def informational_metric_interval(self, informational_content: float) -> float:
        """Δτ_t = max(δ_min, I(w_t) / I_0)."""
        return max(self.delta_min, float(informational_content) / max(self.i0, 1e-12))

    def _softmin_routing(self, theta: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, bool]:
        """Softmin weights against agency centroids with elastic tether radius R."""
        if self._centroids is None:
            self._centroids = theta.unsqueeze(0).clone()
        dists = torch.linalg.vector_norm(self._centroids - theta.unsqueeze(0), dim=-1)
        # Softmin: lower distance → higher weight.
        weights = torch.softmax(-dists / max(self.softmin_temp, 1e-6), dim=0)
        routed_anchor = (weights.unsqueeze(-1) * self._centroids).sum(dim=0)
        min_dist = float(dists.min().item())
        tether_breach = min_dist > self.anchor_radius
        # Elastic pull toward routed anchor when outside radius.
        if tether_breach:
            pull = (routed_anchor - theta)
            pull_norm = float(torch.linalg.vector_norm(pull).item())
            if pull_norm > 1e-12:
                excess = min_dist - self.anchor_radius
                theta = theta + pull * (excess / pull_norm) * 0.35
        return weights, routed_anchor, tether_breach

    def _pid_actuation(self, error: float) -> Tuple[float, float]:
        """
        Closed-loop PID with smoothed ψ and feedforward compensation.

        Returns (smoothed_psi, feedforward_compensation).
        """
        self._integral_error += error
        derivative = error - self._prev_error
        raw_psi = (
            self.pid_kp * error
            + self.pid_ki * self._integral_error
            + self.pid_kd * derivative
        )
        # Feedforward cancels last actuation to prevent control chatter.
        compensated = raw_psi - self._last_actuation_compensation
        smoothed = (
            self.psi_smooth * self._smoothed_psi
            + (1.0 - self.psi_smooth) * compensated
        )
        self._prev_error = error
        self._smoothed_psi = float(smoothed)
        self._last_actuation_compensation = float(0.5 * smoothed)
        return float(smoothed), float(self._last_actuation_compensation)

    def fused_top_k_logit_steering(
        self,
        logits: torch.Tensor,
        steering_direction: torch.Tensor,
        psi: float,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Fused Top-K directional logit steering.

        Complexity: O(K · d_model) GEMV over the top-K candidate embeddings
        rather than full-vocab projection.
        """
        flat = logits.detach().float().reshape(-1)
        if flat.numel() != self.vocab_size:
            # Resize / pad to vocab for demo/test flexibility.
            padded = torch.zeros(self.vocab_size, dtype=torch.float32)
            n = min(self.vocab_size, flat.numel())
            padded[:n] = flat[:n]
            flat = padded

        k = min(self.top_k, self.vocab_size)
        top_vals, top_idx = torch.topk(flat, k=k, largest=True, sorted=False)
        # GEMV: steer scores += ψ · <e_i, steering_direction>
        emb_k = self.embedding_table[top_idx]  # (K, d)
        direction = steering_direction.detach().float().reshape(-1)
        if direction.numel() != self.d_model:
            dpad = torch.zeros(self.d_model, dtype=torch.float32)
            n = min(self.d_model, direction.numel())
            dpad[:n] = direction[:n]
            direction = dpad
        direction = F.normalize(direction, dim=0)
        delta = psi * torch.matmul(emb_k, direction)  # (K,)
        steered_slice = top_vals + delta

        steered = flat.clone()
        steered[top_idx] = steered_slice
        return steered, top_idx

    def _classify(self, omega_t: float) -> AdaptivePhaseState:
        if omega_t >= self.topological_veto:
            return AdaptivePhaseState.VETO
        if omega_t >= self.homeostatic_margin:
            return AdaptivePhaseState.METASTABLE
        return AdaptivePhaseState.NOMINAL

    def forward(
        self,
        residual_activation: torch.Tensor,
        *,
        logits: Optional[torch.Tensor] = None,
        informational_content: Optional[float] = None,
    ) -> DecodeStepResult:
        """
        Ingest one decode-step residual (and optional logits) and govern.

        Parameters
        ----------
        residual_activation:
            Hidden / residual vector θ_t.
        logits:
            Optional vocabulary logits for Fused Top-K steering.
        informational_content:
            Optional I(w_t); defaults to ‖θ_t‖₂ as a content proxy.
        """
        theta = ScaledAdaptiveSentinelAuditor._as_vector(residual_activation, self.d_model)
        info = (
            float(informational_content)
            if informational_content is not None
            else float(torch.linalg.vector_norm(theta).item())
        )
        delta_tau = self.informational_metric_interval(info)

        weights, routed_anchor, tether_breach = self._softmin_routing(theta)

        if self._prev_theta is None:
            velocity_tau = torch.zeros_like(theta)
            acceleration_tau = torch.zeros_like(theta)
        else:
            # Invariant kinematics over informational time: dθ/dτ ≈ Δθ / Δτ
            velocity_tau = (theta - self._prev_theta) / delta_tau
            if self._prev_velocity_tau is None:
                acceleration_tau = torch.zeros_like(theta)
            else:
                acceleration_tau = (velocity_tau - self._prev_velocity_tau) / delta_tau

        vel_norm = float(torch.linalg.vector_norm(velocity_tau).item())
        if vel_norm > 1e-12:
            v_hat = velocity_tau / vel_norm
            a_parallel = float(torch.dot(acceleration_tau, v_hat).item())
            a_orth_vec = acceleration_tau - a_parallel * v_hat
            a_orthogonal = float(torch.linalg.vector_norm(a_orth_vec).item())
        else:
            a_parallel = 0.0
            a_orthogonal = float(torch.linalg.vector_norm(acceleration_tau).item())

        macro_migration = float(torch.linalg.vector_norm(theta - routed_anchor).item())
        self._abs_accel_window.append(a_orthogonal)
        fatigue = sum(self._abs_accel_window) / len(self._abs_accel_window)

        omega_t = (
            max(self.base_omega, self._seeded_omega)
            + self.local_scale * a_orthogonal
            + self.macro_scale * macro_migration
            + fatigue
        )
        if tether_breach:
            omega_t += 0.04

        # Control error: pull orthogonal shear + tether excess toward homeostatic floor.
        error = (omega_t - self.homeostatic_margin) + a_orthogonal
        smoothed_psi, ff_comp = self._pid_actuation(error)
        raw_psi = smoothed_psi + ff_comp  # pre-smooth equivalent for telemetry

        steered_logits: Optional[torch.Tensor] = None
        top_k_indices: Optional[torch.Tensor] = None
        actuation_applied = False
        if logits is not None and abs(smoothed_psi) > 1e-8:
            # Steer opposite orthogonal shear direction toward routed agency centroid.
            steer_dir = routed_anchor - theta
            steered_logits, top_k_indices = self.fused_top_k_logit_steering(
                logits, steer_dir, -smoothed_psi
            )
            actuation_applied = True

        phase = self._classify(omega_t)
        veto = phase == AdaptivePhaseState.VETO

        sent_bag: Optional[Dict[str, Any]] = None
        if veto and self._auto_mint_sent and not self._veto_bag_emitted:
            sent_bag = _mint_veto_sent_bag(
                omega=omega_t,
                j_tau=a_orthogonal,
                fc=fatigue,
                phase_boundary_state=phase.value,
                sequence_step=self._step_index,
                model_identifier="aria-stage2-decode-core",
                zone_or_session_id=self._zone_or_session_id,
                layer_depth_index=0,
            )
            self._veto_bag_emitted = True

        result = DecodeStepResult(
            step_index=self._step_index,
            delta_tau=delta_tau,
            informational_content=info,
            a_parallel=a_parallel,
            a_orthogonal=a_orthogonal,
            softmin_weights=weights.detach().clone(),
            tether_radius_breach=tether_breach,
            raw_psi=raw_psi,
            smoothed_psi=smoothed_psi,
            feedforward_compensation=ff_comp,
            steered_logits=steered_logits,
            top_k_indices=top_k_indices,
            omega_t=float(omega_t),
            phase_state=phase,
            topological_veto=veto,
            actuation_applied=actuation_applied,
            sent_bag=sent_bag,
        )

        self._prev_velocity_tau = velocity_tau
        self._prev_theta = theta
        self._step_index += 1
        return result


def analyze_dual_head_dataframe(
    df_raw: "pd.DataFrame",
    *,
    value_col: str = "observed_value",
    profile_name: str = "AI_HOMEOSTASIS",
    d_model: int = 64,
    prefill_fraction: float = 0.35,
    zone_or_session_id: str = "ZONE-07-RESIDUAL_STREAM",
) -> dict:
    """
    Run Stage I Prefill → Stage II Decode over a tabular activation stream.

    The leading ``prefill_fraction`` of rows form the prompt residual sequence
    (temporal-thirds fallback unless the caller supplies multi-layer tensors
    elsewhere). Remaining rows are decode steps seeded by agency centroids.

    Returns an Engine-compatible report with ``omega_prefill`` / ``omega_decode``
    in ``v4_meta``, plus any auto-minted Dual-Pillar ``sent_bag`` on veto.
    """
    import pandas as pd

    if value_col not in df_raw.columns:
        raise ValueError(f"Activation stream missing required column '{value_col}'")

    df = df_raw.copy().reset_index(drop=True)
    n = len(df)
    if n < 2:
        raise ValueError("Dual-Head analysis requires at least 2 activation rows")

    prefill_n = max(3, min(n - 1, int(math.ceil(n * prefill_fraction))))
    values = [float(v) for v in df[value_col].tolist()]

    # Build (seq, d_model) prompt residuals — temporal-thirds fallback path.
    prompt = torch.zeros(prefill_n, d_model, dtype=torch.float32)
    for i, val in enumerate(values[:prefill_n]):
        prompt[i, 0] = val
        prompt[i, 1] = 0.01 * i

    stage1 = PrefillSentinelAuditor(d_model=d_model)
    prefill = stage1.forward(prompt, zone_or_session_id=zone_or_session_id)

    omegas: List[float] = []
    fatigues: List[float] = []
    accelerations: List[float] = []
    breaches: List[bool] = []
    a_orthogonals: List[float] = []
    decode_results: List[DecodeStepResult] = []
    sent_bag: Optional[Dict[str, Any]] = prefill.sent_bag
    omega_decode = float(prefill.omega_prefill)
    veto = bool(prefill.prefill_veto)
    phase = prefill.phase_state
    fc_final = 0.0
    max_jitter = float(prefill.surprisal_scaled_derivative)

    if not prefill.prefill_veto:
        core = HardenedHomeostaticSentinelCore(d_model=d_model, vocab_size=256, top_k=64)
        core.seed_from_prefill(prefill, zone_or_session_id=zone_or_session_id)
        for i, val in enumerate(values[prefill_n:]):
            theta = torch.zeros(d_model, dtype=torch.float32)
            theta[0] = val
            # Mild lateral component so decode kinematics are non-degenerate.
            theta[1] = 0.001 * (prefill_n + i)
            step = core.forward(theta, informational_content=abs(val) + 1.0)
            decode_results.append(step)
            omegas.append(step.omega_t)
            fatigues.append(step.smoothed_psi)  # placeholder column; overwrite below
            accelerations.append(step.a_orthogonal)
            breaches.append(step.tether_radius_breach or step.topological_veto)
            a_orthogonals.append(step.a_orthogonal)
            if step.sent_bag is not None and sent_bag is None:
                sent_bag = step.sent_bag
            if step.topological_veto:
                veto = True
                phase = step.phase_state
                omega_decode = step.omega_t
                fc_final = (
                    sum(a_orthogonals[-DEFAULT_ROLLING_WINDOW:]) / max(1, len(a_orthogonals[-DEFAULT_ROLLING_WINDOW:]))
                )
                break
        if decode_results:
            last = decode_results[-1]
            omega_decode = float(last.omega_t)
            phase = last.phase_state
            veto = veto or bool(last.topological_veto)
            fc_final = (
                sum(a_orthogonals[-DEFAULT_ROLLING_WINDOW:]) / max(1, len(a_orthogonals[-DEFAULT_ROLLING_WINDOW:]))
                if a_orthogonals
                else 0.0
            )
            max_jitter = max(max_jitter, max(a_orthogonals) if a_orthogonals else 0.0)

    # Align processed_df length with input for plotting.
    df["kinetic_acceleration"] = 0.0
    df["fatigue_coefficient"] = 0.0
    df["omega_t"] = float(prefill.omega_prefill)
    df["kinetic_breach"] = False
    if decode_results:
        for offset, step in enumerate(decode_results):
            idx = prefill_n + offset
            if idx >= len(df):
                break
            df.at[idx, "kinetic_acceleration"] = step.a_orthogonal
            df.at[idx, "fatigue_coefficient"] = abs(step.smoothed_psi)
            df.at[idx, "omega_t"] = step.omega_t
            df.at[idx, "kinetic_breach"] = step.topological_veto or step.tether_radius_breach
        # Forward-fill prefill region with prefill omega for cinema continuity.
        df.loc[: prefill_n - 1, "omega_t"] = float(prefill.omega_prefill)

    omega_final = float(omega_decode if decode_results or not prefill.prefill_veto else prefill.omega_prefill)
    if prefill.prefill_veto:
        omega_final = float(prefill.omega_prefill)

    metastable = phase == AdaptivePhaseState.METASTABLE
    if omega_final >= TOPOLOGICAL_VETO and fc_final > 0.0:
        rul_steps = 0.0
    elif fc_final > 0.0 and omega_final < TOPOLOGICAL_VETO:
        rul_steps = max(0.0, (TOPOLOGICAL_VETO - omega_final) / (fc_final + 1e-12))
    else:
        rul_steps = float("inf")

    verdict = "FAIL" if veto else "PASS"
    v4_meta = {
        "cumulative_entropy": round(omega_final, 6),
        "fatigue_gradient_fc": round(fc_final, 8),
        "remaining_useful_life_periods": round(rul_steps, 2)
        if rul_steps != float("inf")
        else "NOMINAL / STABLE",
        "total_kinetic_breaches": int(sum(breaches)) + (1 if prefill.prefill_veto else 0),
        "max_observed_jitter": round(max_jitter, 8),
        "verdict": verdict,
        "phase_label": phase.value,
        "stalled_zone": metastable,
        "quench_kinetic_veto": veto,
        "domain_id": profile_name,
        "profile_name": profile_name,
        "state_coordinate": "Omega_t",
        "observer_mode": "dual_head_governor",
        "omega_prefill": round(float(prefill.omega_prefill), 6),
        "omega_decode": round(float(omega_decode), 6),
        "prefill_veto": bool(prefill.prefill_veto),
        "prefill_rows": prefill_n,
        "decode_steps": len(decode_results),
        "contraction_discordance": round(float(prefill.contraction_discordance), 6),
        "sent_bag": sent_bag,
    }

    return {
        "verdict": verdict,
        "phi_current": omega_final,
        "fc_gradient": fc_final,
        "remaining_useful_life_steps": rul_steps,
        "system_phase": phase.value,
        "v4_meta": v4_meta,
        "processed_df": df,
        "sent_bag": sent_bag,
        "prefill_result": prefill,
    }
