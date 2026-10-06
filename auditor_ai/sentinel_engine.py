"""
PyTorch residual-stream auditor for AI Homeostasis (Pillar I).

Implements the V50-S scale-invariant observer over latent activation
coordinates θ_t, producing the State Uncertainty Coordinate Ω_t and
enforcing Homeostatic / Metastable / Topological Veto phase gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Deque, Dict, List, Optional

import torch
import torch.nn as nn
from collections import deque

# Canonical V50-S phase gates (unit-less; shared with Engine.py).
TITRATION_CEILING: float = 1e-7
HOMEOSTATIC_MARGIN: float = 0.07
TOPOLOGICAL_VETO: float = 0.19
BASE_OMEGA: float = 0.05
DEFAULT_ROLLING_WINDOW: int = 30
DEFAULT_OMEGA_SCALE: float = 0.12


class PhaseState(str, Enum):
    """Invariant phase-space classification labels."""

    HOMEOSTATIC = "Homeostatic State (< 0.07 Ω)"
    METASTABLE = "Metastable State (0.07 to 0.19 Ω)"
    TOPOLOGICAL_VETO = "Topological Bifurcation (≥ 0.19 Ω)"


@dataclass(frozen=True)
class StepAuditResult:
    """Per-step audit payload returned by :meth:`SentinelActivationAuditor.forward`."""

    step_index: int
    theta: float
    velocity: float
    acceleration: float
    titration_breach: bool
    fatigue_coefficient: float
    omega_t: float
    phase_state: PhaseState
    topological_veto: bool


class SentinelActivationAuditor(nn.Module):
    """
    Stateless-per-call observer that tracks residual-stream activation
    trajectories through finite-difference kinetic acceleration.

    Mathematical pipeline
    ---------------------
    1. Velocity:        θ̇_t  = θ_t − θ_{t−1}
    2. Acceleration:    θ̈_t  = θ̇_t − θ̇_{t−1}   (= d²θ/dt² under Δt = 1)
    3. Titration:       |J_τ| = |θ̈_t|  >  ε      (ε = 1×10⁻⁷)
    4. Fatigue F_c:     rolling mean of |θ̈| over T steps
    5. State Ω_t:       Ω₀ + α · max|θ_k − θ₀| + β · F_c
    6. Phase gates:     Homeostatic / Metastable / Topological Veto
    """

    def __init__(
        self,
        rolling_window: int = DEFAULT_ROLLING_WINDOW,
        titration_ceiling: float = TITRATION_CEILING,
        homeostatic_margin: float = HOMEOSTATIC_MARGIN,
        topological_veto: float = TOPOLOGICAL_VETO,
        base_omega: float = BASE_OMEGA,
        omega_deviation_scale: float = DEFAULT_OMEGA_SCALE,
        fatigue_scale: float = 1.0,
    ) -> None:
        super().__init__()
        if rolling_window < 1:
            raise ValueError("rolling_window must be >= 1")

        self.rolling_window = int(rolling_window)
        self.titration_ceiling = float(titration_ceiling)
        self.homeostatic_margin = float(homeostatic_margin)
        self.topological_veto = float(topological_veto)
        self.base_omega = float(base_omega)
        self.omega_deviation_scale = float(omega_deviation_scale)
        self.fatigue_scale = float(fatigue_scale)

        # Trajectory buffers (not registered as parameters — audit state only).
        self._theta_history: List[float] = []
        self._abs_accel_window: Deque[float] = deque(maxlen=self.rolling_window)
        self._prev_theta: Optional[float] = None
        self._prev_velocity: Optional[float] = None
        self._theta_0: Optional[float] = None
        self._max_abs_deviation: float = 0.0
        self._step_index: int = 0

    def reset(self) -> None:
        """Clear all trajectory state for a fresh reasoning episode."""
        self._theta_history.clear()
        self._abs_accel_window.clear()
        self._prev_theta = None
        self._prev_velocity = None
        self._theta_0 = None
        self._max_abs_deviation = 0.0
        self._step_index = 0

    @staticmethod
    def _scalarize(theta: torch.Tensor) -> float:
        """Reduce a residual-stream tensor to a single coordinate θ."""
        if theta.ndim == 0:
            return float(theta.detach().float().item())
        # L2 norm of the flattened activation acts as the state variable.
        return float(torch.linalg.vector_norm(theta.detach().float()).item())

    def _classify(self, omega_t: float) -> PhaseState:
        if omega_t >= self.topological_veto:
            return PhaseState.TOPOLOGICAL_VETO
        if omega_t >= self.homeostatic_margin:
            return PhaseState.METASTABLE
        return PhaseState.HOMEOSTATIC

    def forward(self, residual_activation: torch.Tensor) -> StepAuditResult:
        """
        Ingest one residual-stream activation frame and return the audit result.

        Parameters
        ----------
        residual_activation:
            Activation tensor at the current reasoning step (any shape).
            Reduced to a scalar θ via L2 norm.

        Returns
        -------
        StepAuditResult
            Finite-difference kinematics, fatigue, Ω_t, and phase classification.
        """
        theta = self._scalarize(residual_activation)

        if self._theta_0 is None:
            self._theta_0 = theta

        # Finite differences (Δt = 1 between reasoning steps).
        if self._prev_theta is None:
            velocity = 0.0
            acceleration = 0.0
        else:
            velocity = theta - self._prev_theta
            if self._prev_velocity is None:
                acceleration = 0.0
            else:
                acceleration = velocity - self._prev_velocity

        abs_accel = abs(acceleration)
        titration_breach = abs_accel > self.titration_ceiling

        self._abs_accel_window.append(abs_accel)
        # Scale F_c once here; do not re-apply fatigue_scale inside Ω_t.
        fatigue_coefficient = (
            sum(self._abs_accel_window) / len(self._abs_accel_window)
        ) * self.fatigue_scale

        abs_deviation = abs(theta - self._theta_0)
        if abs_deviation > self._max_abs_deviation:
            self._max_abs_deviation = abs_deviation

        # Accumulated, trajectory-bound State Uncertainty Coordinate Ω_t.
        omega_t = (
            self.base_omega
            + (self._max_abs_deviation * self.omega_deviation_scale)
            + fatigue_coefficient
        )

        phase_state = self._classify(omega_t)
        topological_veto = phase_state == PhaseState.TOPOLOGICAL_VETO

        result = StepAuditResult(
            step_index=self._step_index,
            theta=theta,
            velocity=velocity,
            acceleration=acceleration,
            titration_breach=titration_breach,
            fatigue_coefficient=fatigue_coefficient,
            omega_t=omega_t,
            phase_state=phase_state,
            topological_veto=topological_veto,
        )

        self._theta_history.append(theta)
        self._prev_velocity = velocity
        self._prev_theta = theta
        self._step_index += 1
        return result

    def audit_summary(self) -> Dict[str, float | str | bool | int]:
        """Return a compact summary of the current accumulated trajectory."""
        if not self._theta_history:
            return {
                "steps": 0,
                "omega_t": self.base_omega,
                "phase_state": PhaseState.HOMEOSTATIC.value,
                "topological_veto": False,
            }

        # Recompute final Ω from retained state without mutating buffers.
        # Apply fatigue_scale once (same as forward()).
        fatigue = (
            (sum(self._abs_accel_window) / len(self._abs_accel_window)) * self.fatigue_scale
            if self._abs_accel_window
            else 0.0
        )
        omega_t = (
            self.base_omega
            + (self._max_abs_deviation * self.omega_deviation_scale)
            + fatigue
        )
        phase = self._classify(omega_t)
        return {
            "steps": self._step_index,
            "omega_t": omega_t,
            "fatigue_coefficient": fatigue,
            "max_abs_deviation": self._max_abs_deviation,
            "phase_state": phase.value,
            "topological_veto": phase == PhaseState.TOPOLOGICAL_VETO,
        }
