"""
ISO 20022 clearing bridge for Dual-Pillar `.sent` evidence bags.

Maps canonical_row_hash into pacs.008 MsgId and camt.053 EndToEndId fields,
and executes an autonomous dividend kill-switch when Ω ≥ 0.19.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any
from xml.dom import minidom

VETO_THRESHOLD = 0.19


def _require_bag_fields(bag: dict[str, Any]) -> tuple[str, float]:
    try:
        canonical = bag["cryptographic_attestation"]["canonical_row_hash"]
        omega = float(bag["thermodynamic_state_vector"]["state_coordinate_omega"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Bag missing Dual-Pillar v1.0 hash / Ω fields") from exc
    if not isinstance(canonical, str) or len(canonical) != 64:
        raise ValueError("canonical_row_hash must be a 64-char hex digest")
    return canonical, omega


def dividend_kill_switch(omega: float, threshold: float = VETO_THRESHOLD) -> dict[str, Any]:
    """
    Autonomous dividend kill-switch.

    When Ω ≥ 0.19, clearing instructions must halt dividend / credit-transfer
    release pending human override.
    """
    armed = float(omega) >= float(threshold)
    return {
        "kill_switch_armed": armed,
        "omega": float(omega),
        "threshold": float(threshold),
        "action": "HALT_DIVIDEND_AND_CREDIT_TRANSFER" if armed else "CLEAR_TO_PROCEED",
        "rationale": (
            "Topological Veto: State Uncertainty Coordinate crossed institutional gate."
            if armed
            else "Nominal / Metastable: clearing path remains open under policy."
        ),
    }


def map_sent_to_pacs008(bag: dict[str, Any]) -> str:
    """
    Build a minimal pacs.008 XML snippet with MsgId = canonical_row_hash.

    Path: Document/FIToFICstmrCdtTrf/GrpHdr/MsgId
    """
    canonical, omega = _require_bag_fields(bag)
    ns = "urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08"
    document = ET.Element("Document", xmlns=ns)
    root = ET.SubElement(document, "FIToFICstmrCdtTrf")
    grp = ET.SubElement(root, "GrpHdr")
    ET.SubElement(grp, "MsgId").text = canonical
    ET.SubElement(grp, "NbOfTxs").text = "1"
    ET.SubElement(grp, "CtrlSum").text = "0"
    cdt = ET.SubElement(root, "CdtTrfTxInf")
    ET.SubElement(cdt, "AccptncDtTm").text = str(
        bag["attestation_header"].get("timestamp_utc_ms", 0)
    )
    ET.SubElement(cdt, "KillSwitch").text = (
        "ARMED" if omega >= VETO_THRESHOLD else "CLEAR"
    )
    return _pretty_xml(document)


def map_sent_to_camt053(bag: dict[str, Any]) -> str:
    """
    Build a minimal camt.053 XML snippet with EndToEndId = canonical_row_hash.

    Path: Stmt/Entry/NtryDtls/TxDtls/Refs/EndToEndId
    (wrapped under Document/BkToCstmrStmt for well-formedness)
    """
    canonical, omega = _require_bag_fields(bag)
    ns = "urn:iso:std:iso:20022:tech:xsd:camt.053.001.08"
    document = ET.Element("Document", xmlns=ns)
    stmt_wrap = ET.SubElement(document, "BkToCstmrStmt")
    stmt = ET.SubElement(stmt_wrap, "Stmt")
    ET.SubElement(stmt, "Id").text = f"SENT-{canonical[:16]}"
    entry = ET.SubElement(stmt, "Ntry")
    details = ET.SubElement(entry, "NtryDtls")
    tx = ET.SubElement(details, "TxDtls")
    refs = ET.SubElement(tx, "Refs")
    ET.SubElement(refs, "EndToEndId").text = canonical
    ET.SubElement(tx, "KillSwitch").text = (
        "ARMED" if omega >= VETO_THRESHOLD else "CLEAR"
    )
    return _pretty_xml(document)


def map_sent_to_iso20022_json(bag: dict[str, Any]) -> dict[str, Any]:
    """JSON companion payload for pacs.008 / camt.053 hash injection + kill-switch."""
    canonical, omega = _require_bag_fields(bag)
    switch = dividend_kill_switch(omega)
    return {
        "pacs008": {
            "Document": {
                "FIToFICstmrCdtTrf": {
                    "GrpHdr": {"MsgId": canonical},
                }
            }
        },
        "camt053": {
            "Stmt": {
                "Ntry": {
                    "NtryDtls": {
                        "TxDtls": {
                            "Refs": {"EndToEndId": canonical},
                        }
                    }
                }
            }
        },
        "dividend_kill_switch": switch,
        "canonical_row_hash": canonical,
        "state_coordinate_omega": omega,
    }


def bridge_sent_bag(bag: dict[str, Any] | str) -> dict[str, Any]:
    """Full bridge: accept dict or JSON string; return XML snippets + JSON map + kill-switch."""
    if isinstance(bag, str):
        bag = json.loads(bag)
    if not isinstance(bag, dict):
        raise TypeError("bag must be a dict or JSON string")
    return {
        "pacs008_xml": map_sent_to_pacs008(bag),
        "camt053_xml": map_sent_to_camt053(bag),
        "iso20022_json": map_sent_to_iso20022_json(bag),
        "dividend_kill_switch": dividend_kill_switch(
            float(bag["thermodynamic_state_vector"]["state_coordinate_omega"])
        ),
    }


def _pretty_xml(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="utf-8")
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent="  ")
