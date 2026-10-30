"""MCP stdio interceptor (Token-0 governance around a downstream child).

This module is the public entry surface for the open-core stdio proxy.
Implementation lives in :mod:`sentinel_mcp.cli` so the console script and
``python -m sentinel_mcp.cli`` share one code path.
"""

from __future__ import annotations

from sentinel_mcp.cli import (
    VETO_ERROR_CODE,
    VETO_ERROR_MESSAGE,
    VETO_OMEGA,
    build_parser,
    egress_pump,
    ingress_pump,
    main,
    mint_sentinel_bag,
    run,
)

__all__ = [
    "VETO_ERROR_CODE",
    "VETO_ERROR_MESSAGE",
    "VETO_OMEGA",
    "build_parser",
    "egress_pump",
    "ingress_pump",
    "main",
    "mint_sentinel_bag",
    "run",
]


if __name__ == "__main__":
    run()
