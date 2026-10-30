"""sentinel_mcp — open-core MCP Air-Gap Gatekeeper (stdio interceptor).

Transparent stdio bridge with kinematic Token-0 governance on ``tools/call``.
Commercial SentinelGate cloud SDK clients are intentionally out of scope.
"""

from __future__ import annotations

from sentinel_mcp.cli import VETO_OMEGA, main, run
from sentinel_mcp.proxy import mint_sentinel_bag

__all__ = [
    "VETO_OMEGA",
    "main",
    "mint_sentinel_bag",
    "run",
]

__version__ = "1.1.1"
