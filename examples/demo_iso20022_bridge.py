#!/usr/bin/env python3
"""
Demo: mint a Dual-Pillar .sent v1.0 bag and map it into ISO 20022 pacs.008 / camt.053.

Run from repository root:
  python examples/demo_iso20022_bridge.py
"""

from __future__ import annotations

import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import Forensic_kernel as kernel
from spec.iso20022_mapper import bridge_sent_bag


def main() -> None:
    # Simulate a Topological Veto bag (Ω ≥ 0.19) to exercise the kill-switch.
    bag = kernel.mint_sentinel_v10_bag(
        state_coordinate_omega=0.21,
        sub_resolution_jitter_j_tau=1.5,
        rolling_fatigue_fc=0.08,
        sequence_step=25,
        model_identifier="aria-adaptive-demo",
        layer_depth_index=5,
        zone_or_session_id="ZONE-07-RESIDUAL_STREAM",
    )

    print("=" * 72)
    print("  THOHAT V50-S  |  ISO 20022 Clearing Bridge Demo")
    print("=" * 72)
    print("Minted .sent v1.0 bag (truncated):")
    print(json.dumps(bag, indent=2)[:800], "...\n")

    bridged = bridge_sent_bag(bag)
    print("Dividend kill-switch:", bridged["dividend_kill_switch"])
    print("\n--- pacs.008 MsgId injection ---")
    print(bridged["pacs008_xml"][:600])
    print("\n--- camt.053 EndToEndId injection ---")
    print(bridged["camt053_xml"][:600])

    assert bridged["dividend_kill_switch"]["kill_switch_armed"] is True
    msg_id = bridged["iso20022_json"]["pacs008"]["Document"]["FIToFICstmrCdtTrf"]["GrpHdr"]["MsgId"]
    assert len(msg_id) <= 35 and msg_id.startswith("SG-") and "=" not in msg_id
    assert msg_id in bridged["pacs008_xml"]
    assert msg_id in bridged["camt053_xml"]
    print("\n[+] Bridge assertions passed (kill-switch armed, Max35Text ID injected).")


if __name__ == "__main__":
    main()
