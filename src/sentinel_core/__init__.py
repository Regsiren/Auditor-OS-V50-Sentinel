"""sentinel_core — kinematic auditing, crypto, and RFC-001 data schemas."""

from .kinematics import KinematicAuditor, KinematicMetrics

__version__ = "1.1.1"

__all__ = [
    "KinematicAuditor",
    "KinematicMetrics",
    "__version__",
]
