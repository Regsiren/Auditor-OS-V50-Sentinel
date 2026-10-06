"""
Auditor OS V50-S — AI Homeostasis package.

Provides PyTorch residual-stream activation auditing under the same
scale-invariant thermodynamic gates used by the physical telemetry kernel.
"""

from auditor_ai.sentinel_engine import (
    HOMEOSTATIC_MARGIN,
    TITRATION_CEILING,
    TOPOLOGICAL_VETO,
    PhaseState,
    SentinelActivationAuditor,
    StepAuditResult,
)

__all__ = [
    "HOMEOSTATIC_MARGIN",
    "TITRATION_CEILING",
    "TOPOLOGICAL_VETO",
    "PhaseState",
    "SentinelActivationAuditor",
    "StepAuditResult",
]

__version__ = "0.1.0"
