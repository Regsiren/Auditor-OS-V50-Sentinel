import pandas as pd
import numpy as np
import Engine as engine
import Forensic_kernel as kernel

def test_early_return_integrity():
    """Validates that truncated inputs return consistent dictionary schemas to prevent UI execution failures."""
    df_short = pd.DataFrame({"observed_value": [35.0, 35.0]})
    report = engine.analyze_systemic_solvency(df_short)
    
    assert report["verdict"] == "PASS"
    assert "v4_meta" in report
    assert report["v4_meta"]["cumulative_entropy"] == engine.BASE_UNCERTAINTY_COEFFICIENT

def test_phase_gate_transitions():
    """Verifies that the engine correctly handles the 0.07 Margin Gate and 0.19 Veto Gate."""
    # Setup nominal baseline
    data = {
        "observed_value": np.full(100, 35.0),
        "power_matrix": np.full(100, 1000.0),
        "spatial_displacement": np.zeros(100)
    }
    df_nominal = pd.DataFrame(data)
    report_nominal = engine.analyze_systemic_solvency(df_nominal)
    assert report_nominal["v4_meta"]["phase_label"] == engine.STATUS_HOMEOSTATIC

    # Force immediate catastrophic displacement breach (Stage 2)
    data["spatial_displacement"] = np.full(100, 45.0)
    df_breach = pd.DataFrame(data)
    report_breach = engine.analyze_systemic_solvency(df_breach)
    assert report_breach["v4_meta"]["quench_kinetic_veto"] is True
    assert report_breach["v4_meta"]["phase_label"] == engine.STATUS_BIFURCATION_COLLAPSE

def test_unsigned_stream_firewall():
    """Confirms that verification loops correctly block datasets that lack cryptographic row hashes."""
    df_unsigned = pd.DataFrame({"observed_value": [35.0, 35.1, 35.2]})
    assert kernel.verify_telemetry_chain(df_unsigned) is False

def test_positive_cryptographic_chain_validation():
    """Validates that a correctly signed time-series sequence from the synthesizer loop passes verification."""
    raw_data = {
        "observed_value": [35.00000000, 34.99999988, 34.99999971],
        "power_matrix": [1000.0, 999.98, 999.96],
        "spatial_displacement": [0.0, 0.001, 0.002]
    }
    df_test = pd.DataFrame(raw_data)

    # Emulate Data_Synthesizer sequential pair-chain signing logic
    row_hashes = []
    for idx, row in df_test.iterrows():
        row_dict = row.to_dict()
        if row_hashes:
            row_dict["prev_hash"] = row_hashes[-1]
        row_hashes.append(kernel.generate_stateless_row_hash(row_dict))

    df_test["row_hash"] = row_hashes

    # Assert that the forensic validation kernel successfully verifies the chain
    assert kernel.verify_telemetry_chain(df_test) is True
