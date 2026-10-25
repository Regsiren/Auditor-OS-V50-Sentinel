"""The physics engine (Δτ, v_t, a_⊥).

Finite-difference velocity, shear decomposition, and Ω coordinate.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from typing import Deque, List, Optional, Sequence, Union

EPS: float = 1e-7
DELTA_TAU_MIN: float = 0.01
DELTA_TAU_MAX: float = 5.0
WINDOW: int = 30

# Ω_t = 0.05 + α·D_geo + β·‖a_⊥‖² + γ·F_c
ALPHA: float = 0.12
BETA: float = 0.08
GAMMA: float = 0.02
OMEGA_FLOOR: float = 0.05
RECALIBRATE_OMEGA: float = 0.07
VETO_OMEGA: float = 0.19
D_MACRO_MAX: float = 3.5


@dataclass(frozen=True)
class KinematicMetrics:
    """Live kinematic observables for one auditor step."""

    omega_t: float
    j_tau: float  # orthogonal shear magnitude ‖a_⊥‖
    f_c: float  # rolling fatigue coefficient
    epsilon: float
    d_geo: float
    d_macro: float
    delta_tau: float
    phase: str  # NOMINAL | RECALIBRATE | VETO
    entropy_resonance: bool


class KinematicAuditor:
    """Rolling kinematic auditor over successive state vectors θ_t."""

    def __init__(
        self,
        profile: Union[str, None] = "standard",
        *,
        window: int = WINDOW,
        veto_omega: float = VETO_OMEGA,
        recalibrate_omega: float = RECALIBRATE_OMEGA,
        epsilon: float = EPS,
    ) -> None:
        self.profile = profile or "standard"
        self.window = int(window)
        self.veto_omega = float(veto_omega)
        self.recalibrate_omega = float(recalibrate_omega)
        self.epsilon = float(epsilon)
        self._states: Deque[List[float]] = deque(maxlen=self.window)
        self._velocities: Deque[List[float]] = deque(maxlen=self.window)
        self._delta_taus: Deque[float] = deque(maxlen=self.window)
        self._shear_norms: Deque[float] = deque(maxlen=self.window)
        self._theta0: Optional[List[float]] = None
        self._steps = 0
        self.last: Optional[KinematicMetrics] = None

        # Named profiles adjust phase thresholds only (public baseline).
        if self.profile in ("high-security", "high_security"):
            self.recalibrate_omega = 0.05
            self.veto_omega = 0.15
        elif self.profile in ("high-frequency", "high_frequency"):
            self.recalibrate_omega = 0.10
            self.veto_omega = 0.22

    def step(self, theta: Sequence[float]) -> KinematicMetrics:
        """Advance the auditor with θ_t; return live kinematic metrics."""
        state = [float(x) for x in theta]
        if not state:
            raise ValueError("theta must be a non-empty sequence")
        if any(not math.isfinite(x) for x in state):
            raise ValueError("theta components must be finite")

        if self._theta0 is None:
            self._theta0 = list(state)

        if self._states and len(state) != len(self._states[-1]):
            raise ValueError(
                f"theta dimensionality changed: {len(self._states[-1])} -> {len(state)}"
            )

        if not self._states:
            # First observation: floor Δτ, zero velocity/acceleration.
            delta_tau = DELTA_TAU_MIN
            velocity = [0.0] * len(state)
            a_perp_norm = 0.0
            entropy_resonance = False
            d_geo = 0.0
        else:
            prev = self._states[-1]
            d_geo = _l2(state, prev)
            # Surprisal-coupled informational interval: Δτ = clamp(D_geo).
            delta_tau = min(DELTA_TAU_MAX, max(DELTA_TAU_MIN, d_geo))
            velocity = [(state[i] - prev[i]) / delta_tau for i in range(len(state))]
            prev_v = self._velocities[-1]
            prev_dt = self._delta_taus[-1]
            denom = delta_tau + prev_dt
            accel = [
                2.0 * (velocity[i] - prev_v[i]) / denom for i in range(len(state))
            ]
            a_parallel, a_perp = _decompose_shear(accel, velocity, self.epsilon)
            a_perp_norm = _norm(a_perp)
            entropy_resonance = a_perp_norm > self.epsilon
            _ = a_parallel  # retained for completeness of the shear split

        self._states.append(state)
        self._velocities.append(velocity)
        self._delta_taus.append(delta_tau)
        self._shear_norms.append(a_perp_norm)
        self._steps += 1

        f_c = sum(self._shear_norms) / len(self._shear_norms)
        d_macro = _norm(
            [state[i] - self._theta0[i] for i in range(len(state))]
        )
        omega_t = (
            OMEGA_FLOOR
            + ALPHA * d_geo
            + BETA * (a_perp_norm ** 2)
            + GAMMA * f_c
        )
        phase = self._classify(omega_t, d_macro)

        metrics = KinematicMetrics(
            omega_t=float(omega_t),
            j_tau=float(a_perp_norm),
            f_c=float(f_c),
            epsilon=float(self.epsilon),
            d_geo=float(d_geo),
            d_macro=float(d_macro),
            delta_tau=float(delta_tau),
            phase=phase,
            entropy_resonance=bool(entropy_resonance),
        )
        self.last = metrics
        return metrics

    def _classify(self, omega_t: float, d_macro: float) -> str:
        if omega_t >= self.veto_omega or d_macro > D_MACRO_MAX:
            return "VETO"
        if omega_t >= self.recalibrate_omega:
            return "RECALIBRATE"
        return "NOMINAL"

    def reset(self) -> None:
        self._states.clear()
        self._velocities.clear()
        self._delta_taus.clear()
        self._shear_norms.clear()
        self._theta0 = None
        self._steps = 0
        self.last = None

    def __len__(self) -> int:
        return self._steps


def _norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in vector))


def _l2(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(len(a))))


def _decompose_shear(
    accel: Sequence[float],
    velocity: Sequence[float],
    epsilon: float,
) -> tuple[List[float], List[float]]:
    """Split acceleration into parallel / perpendicular components."""
    v_norm_sq = sum(v * v for v in velocity)
    if v_norm_sq <= epsilon:
        return [0.0] * len(accel), list(accel)
    scale = sum(accel[i] * velocity[i] for i in range(len(accel))) / (v_norm_sq + epsilon)
    a_parallel = [scale * velocity[i] for i in range(len(velocity))]
    a_perp = [accel[i] - a_parallel[i] for i in range(len(accel))]
    return a_parallel, a_perp
