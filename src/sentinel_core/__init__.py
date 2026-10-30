"""sentinel_core — kinematic auditing, crypto, and RFC-001 data schemas."""

from .crypto import StateChainer
from .kinematics import KinematicAuditor, KinematicMetrics
from .persistence import SessionStore

__version__ = "1.1.1"

__all__ = [
    "KinematicAuditor",
    "KinematicMetrics",
    "SessionStore",
    "StateChainer",
    "__version__",
]
