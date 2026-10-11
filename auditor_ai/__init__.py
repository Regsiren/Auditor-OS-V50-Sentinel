"""
Auditor OS V50-S — AI Homeostasis package.

Provides PyTorch residual-stream activation auditing under the same
scale-invariant thermodynamic gates used by the physical telemetry kernel,
plus the ARIA adaptive alignment track.
"""

from auditor_ai.sentinel_engine import (
    HOMEOSTATIC_MARGIN,
    TITRATION_CEILING,
    TOPOLOGICAL_VETO,
    PhaseState,
    SentinelActivationAuditor,
    StepAuditResult,
    analyze_activation_dataframe,
)
from auditor_ai.adaptive_engine import (
    AdaptivePhaseState,
    AdaptiveStepResult,
    ScaledAdaptiveSentinelAuditor,
)

__all__ = [
    "HOMEOSTATIC_MARGIN",
    "TITRATION_CEILING",
    "TOPOLOGICAL_VETO",
    "PhaseState",
    "SentinelActivationAuditor",
    "StepAuditResult",
    "analyze_activation_dataframe",
    "AdaptivePhaseState",
    "AdaptiveStepResult",
    "ScaledAdaptiveSentinelAuditor",
]

__version__ = "0.2.0"
