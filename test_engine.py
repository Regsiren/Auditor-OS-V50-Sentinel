import pandas as pd
import numpy as np
import Engine as engine
import Forensic_kernel as kernel


def test_early_return_integrity():
    df_short = pd.DataFrame({"observed_value": [35.0, 35.0]})
    report = engine.analyze_systemic_solvency(df_short)
    assert report["verdict"] == "PASS"
    assert "v4_meta" in report
    assert report["v4_meta"]["cumulative_entropy"] == engine.BASE_UNCERTAINTY_COEFFICIENT


def test_phase_gate_transitions():
    data = {
        "observed_value": np.full(100, 35.0),
        "power_matrix": np.full(100, 1000.0),
        "spatial_displacement": np.zeros(100),
    }
    report_nominal = engine.analyze_systemic_solvency(pd.DataFrame(data))
    assert report_nominal["v4_meta"]["phase_label"] == engine.STATUS_HOMEOSTATIC
    data["spatial_displacement"] = np.full(100, 45.0)
    report_breach = engine.analyze_systemic_solvency(pd.DataFrame(data))
    assert report_breach["v4_meta"]["quench_kinetic_veto"] is True
    assert report_breach["v4_meta"]["phase_label"] == engine.STATUS_BIFURCATION_COLLAPSE


def test_unsigned_stream_firewall():
    df_unsigned = pd.DataFrame({"observed_value": [35.0, 35.1, 35.2]})
    assert kernel.verify_telemetry_chain(df_unsigned) is False


def test_positive_cryptographic_chain_validation():
    raw_data = {
        "timestamp": ["2026-05-20 00:00:00", "2026-05-27 00:00:00", "2026-06-03 00:00:00"],
        "sensor_id": ["ZONE-TEST", "ZONE-TEST", "ZONE-TEST"],
        "observed_value": [35.00000000, 34.99999988, 34.99999971],
        "power_matrix": [1000.0, 999.98, 999.96],
        "spatial_displacement": [0.0, 0.001, 0.002],
    }
    df_test = pd.DataFrame(raw_data)
    prev_hash = kernel.genesis_hash("ZONE-TEST")
    row_hashes = []
    for idx in range(len(df_test)):
        current_hash = kernel.generate_stateless_row_hash(df_test.iloc[idx].to_dict(), prev_hash)
        row_hashes.append(current_hash)
        prev_hash = current_hash
    df_test["row_hash"] = row_hashes
    assert kernel.verify_telemetry_chain(df_test) is True


def test_tampered_chain_detection():
    raw_data = {
        "timestamp": ["2026-05-20 00:00:00", "2026-05-27 00:00:00", "2026-06-03 00:00:00"],
        "sensor_id": ["ZONE-TEST", "ZONE-TEST", "ZONE-TEST"],
        "observed_value": [35.00000000, 34.99999988, 34.99999971],
        "power_matrix": [1000.0, 999.98, 999.96],
        "spatial_displacement": [0.0, 0.001, 0.002],
    }
    df_test = pd.DataFrame(raw_data)
    prev_hash = kernel.genesis_hash("ZONE-TEST")
    row_hashes = []
    for idx in range(len(df_test)):
        current_hash = kernel.generate_stateless_row_hash(df_test.iloc[idx].to_dict(), prev_hash)
        row_hashes.append(current_hash)
        prev_hash = current_hash
    df_test["row_hash"] = row_hashes
    df_test.loc[1, "observed_value"] = 40.0
    assert kernel.verify_telemetry_chain(df_test) is False


def test_domain_profile_preset():
    data = {
        "observed_value": np.full(100, 35.0),
        "power_matrix": np.full(100, 1000.0),
        "spatial_displacement": np.zeros(100),
    }
    report = engine.analyze_systemic_solvency(pd.DataFrame(data), profile_name="BIOMETRIC_SENTINEL")
    assert report["v4_meta"]["profile_name"] == "BIOMETRIC_SENTINEL"
    assert report["v4_meta"]["domain_id"] == "BIOMETRIC_SENTINEL"
    assert report["verdict"] == "PASS"


def test_planetary_preset_matches_legacy_gates():
    cfg = engine._preset_to_cfg(
        engine.DOMAIN_PROFILES["PLANETARY_INFRASTRUCTURE"], "PLANETARY_INFRASTRUCTURE"
    )
    assert cfg["power_drop_threshold"] == 10.0
    assert cfg["displacement_trigger"] == 1.0
    assert cfg["math_buffer"] == 1e-7