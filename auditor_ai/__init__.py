"""
Auditor OS V50-S — AI Homeostasis package.

Provides PyTorch residual-stream activation auditing under the same
scale-invariant thermodynamic gates used by the physical telemetry kernel,
plus the ARIA adaptive alignment track (Stage I Prefill + Stage II Decode).
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
    DecodeStepResult,
    HardenedHomeostaticSentinelCore,
    PrefillAuditResult,
    PrefillSeedState,
    PrefillSentinelAuditor,
    ScaledAdaptiveSentinelAuditor,
    analyze_adaptive_dataframe,
    analyze_dual_head_dataframe,
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
    "analyze_adaptive_dataframe",
    "analyze_dual_head_dataframe",
    "PrefillSentinelAuditor",
    "PrefillAuditResult",
    "PrefillSeedState",
    "HardenedHomeostaticSentinelCore",
    "DecodeStepResult",
]

__version__ = "0.3.0"
