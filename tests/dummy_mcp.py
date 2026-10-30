"""Minimal stdio echo server for MCP proxy integration tests."""

from __future__ import annotations

import json
import sys

while True:
    line = sys.stdin.readline()
    if not line:
        break
    if not line.strip():
        continue
    payload = json.loads(line)
    payload["dummy_server_received"] = True
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()
