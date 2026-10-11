"""
ARIA Adaptive Alignment Engine — ScaledAdaptiveSentinelAuditor.

Implements dimension-scaled titration, orthogonal shear decomposition,
dynamic baseline annealing, and dual-scale State Uncertainty Coordinate Ω_t
for the ARIA research track (Pillar I).
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque, Dict, List, Optional

import torch
import torch.nn as nn

from auditor_ai.sentinel_engine import (
    BASE_OMEGA,
    HOMEOSTATIC_MARGIN,
    TITRATION_CEILING,
    TOPOLOGICAL_VETO,
)

DEFAULT_ROLLING_WINDOW: int = 30
DEFAULT_LOCAL_SCALE: float = 0.08
DEFAULT_MACRO_SCALE: float = 0.10
DEFAULT_ANNEAL_RATE: float = 0.05


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
