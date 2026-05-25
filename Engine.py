import numpy as np
import pandas as pd

# ==============================================================================
# AUDITOR OS V50 SENTINEL CORE: PHYSICAL CONSTANTS & CONFIGURATION
# ==============================================================================
MATH_BUFFER = 1e-7

# System Status Boundary Gates (Unit-less Phase Space Coordinate Flags)
MARGIN_CALL_THRESHOLD = 0.07
INSTITUTIONAL_BINARY_VETO_GATE = 0.19

# Fixed Fiduciary Baseline Entropy
BASE_UNCERTAINTY_COEFFICIENT = 0.05

# System State Narrative Labels (Section 3 Phase Nomenclature)
STATUS_HOMEOSTATIC = "Homeostatic State (< 0.07 Φ)"
STATUS_METASTABLE_IMPAIRMENT = "Metastable State (0.07 to 0.19 Φ)"
STATUS_BIFURCATION_COLLAPSE = "Topological Bifurcation (≥ 0.19 Φ)"

# =====================================================================
# STANDARD DOMAIN CONFIGURATION PRESETS
# =====================================================================
DOMAIN_PROFILES = {
    "PLANETARY_INFRASTRUCTURE": {
        "titration_ceiling": 1e-7,
        "metastable_margin": 0.07,
        "collapse_veto": 0.19,
        "base_uncertainty": 0.05,
        "primary_multiplier": 0.05,
        "shear_limit": 1.0,
        "energy_delta_limit": 10.0,
    },
    "BIOMETRIC_SENTINEL": {
        "titration_ceiling": 1e-7,
        "metastable_margin": 0.07,
        "collapse_veto": 0.19,
        "base_uncertainty": 0.05,
        "primary_multiplier": 0.12,
        "shear_limit": 0.05,
        "energy_delta_limit": 2.5,
    },
    "QUANTUM_COHERENCE": {
        "titration_ceiling": 1e-8,
        "metastable_margin": 0.07,
        "collapse_veto": 0.19,
        "base_uncertainty": 0.05,
        "primary_multiplier": 0.01,
        "shear_limit": 0.002,
        "energy_delta_limit": 0.05,
    },
}


def _preset_to_cfg(preset: dict, profile_name: str) -> dict:
    """Map a DOMAIN_PROFILES preset into the internal engine configuration keys."""
    return {
        "domain_id": profile_name,
        "math_buffer": preset["titration_ceiling"],
        "margin_call_threshold": preset["metastable_margin"],
        "institutional_binary_veto_gate": preset["collapse_veto"],
        "base_uncertainty_coefficient": preset.get("base_uncertainty", BASE_UNCERTAINTY_COEFFICIENT),
        "rolling_window": 30,
        "jitter_window": 10,
        "phi_deviation_scale": preset["primary_multiplier"],
        "power_drop_threshold": preset["energy_delta_limit"],
        "displacement_trigger": preset["shear_limit"],
        "displacement_phi_scale": 0.01,
        "val_col": "observed_value",
        "power_col": "power_matrix",
        "displacement_col": "spatial_displacement",
        "status_homeostatic": STATUS_HOMEOSTATIC,
        "status_metastable": STATUS_METASTABLE_IMPAIRMENT,
        "status_bifurcation": STATUS_BIFURCATION_COLLAPSE,
    }


def _resolve_cfg(profile_name: str = "PLANETARY_INFRASTRUCTURE", domain_profile: dict = None) -> dict:
    preset = DOMAIN_PROFILES.get(profile_name, DOMAIN_PROFILES["PLANETARY_INFRASTRUCTURE"])
    cfg = _preset_to_cfg(preset, profile_name)
    if domain_profile:
        cfg.update(domain_profile)
    return cfg


# ==============================================================================
# CORE KINETIC SENTINEL & T-30 MOMENTUM ENGINE
# ==============================================================================
def analyze_systemic_solvency(
    df_raw: pd.DataFrame,
    profile_name: str = "PLANETARY_INFRASTRUCTURE",
    domain_profile: dict = None,
    val_col: str = "observed_value",
    power_col: str = "power_matrix",
    displacement_col: str = "spatial_displacement",
    rolling_window: int = 30,
) -> dict:
    """
    Stateless universal solvency engine for tracking multi-zone structural evolution.
    Applies scale-invariant second-derivative calculus across dynamic physical profiles.

    profile_name: Key in DOMAIN_PROFILES (PLANETARY_INFRASTRUCTURE, BIOMETRIC_SENTINEL, QUANTUM_COHERENCE).
    domain_profile: Optional dict merged over the selected preset for fine-grained overrides.
    """
    cfg = _resolve_cfg(profile_name, domain_profile)

    if val_col != "observed_value":
        cfg["val_col"] = val_col
    if power_col != "power_matrix":
        cfg["power_col"] = power_col
    if displacement_col != "spatial_displacement":
        cfg["displacement_col"] = displacement_col
    if rolling_window != 30:
        cfg["rolling_window"] = rolling_window

    math_buffer = float(cfg["math_buffer"])
    margin_threshold = float(cfg["margin_call_threshold"])
    veto_gate = float(cfg["institutional_binary_veto_gate"])
    base_phi = float(cfg["base_uncertainty_coefficient"])
    jitter_window = int(cfg["jitter_window"])
    phi_deviation_scale = float(cfg["phi_deviation_scale"])
    power_drop_threshold = float(cfg["power_drop_threshold"])
    displacement_trigger = float(cfg["displacement_trigger"])
    displacement_phi_scale = float(cfg["displacement_phi_scale"])
    rolling_window = int(cfg["rolling_window"])
    val_col = cfg["val_col"]
    power_col = cfg["power_col"]
    displacement_col = cfg["displacement_col"]

    status_homeostatic = cfg["status_homeostatic"]
    status_metastable = cfg["status_metastable"]
    status_bifurcation = cfg["status_bifurcation"]

    df = df_raw.copy()
    total_rows = len(df)

    if total_rows < 3:
        return {
            "verdict": "PASS",
            "phi_current": base_phi,
            "fc_gradient": 0.0,
            "remaining_useful_life_steps": float("inf"),
            "system_phase": status_homeostatic,
            "v4_meta": {
                "cumulative_entropy": base_phi,
                "fatigue_gradient_fc": 0.0,
                "remaining_useful_life_periods": "NOMINAL / STABLE",
                "total_kinetic_breaches": 0,
                "max_observed_jitter": 0.0,
                "verdict": "PASS",
                "phase_label": status_homeostatic,
                "stalled_zone": False,
                "quench_kinetic_veto": False,
                "domain_id": cfg.get("domain_id"),
                "profile_name": profile_name,
            },
            "processed_df": df,
        }

    # 1. Real-Time Snapshot Layer: Second Derivative Calculation (Universal Acceleration)
    df["velocity"] = df[val_col].diff().fillna(0.0)
    df["kinetic_acceleration"] = df["velocity"].diff().fillna(0.0)
    df["kinetic_breach"] = df["kinetic_acceleration"].abs() > math_buffer
    total_breaches = int(df["kinetic_breach"].sum())

    # 2. Strategic Layer: T-30 Momentum Integration (The Integral of Fatigue)
    df["abs_kinetic_acceleration"] = df["kinetic_acceleration"].abs()
    df["fatigue_coefficient"] = df["abs_kinetic_acceleration"].rolling(
        window=rolling_window, min_periods=1
    ).mean()
    current_fc = float(df["fatigue_coefficient"].iloc[-1]) if total_rows >= rolling_window else 0.0

    # 3. Dynamic Uncertainty Coefficient Matrix (Unit-less Entropy Vector Φ)
    df["jitter"] = df[val_col].rolling(window=jitter_window, min_periods=1).std().fillna(0.0)
    max_jitter = float(df["jitter"].max())

    cumulative_deviation = float((df[val_col] - df[val_col].iloc[0]).abs().max())
    phi_current = base_phi + (cumulative_deviation * phi_deviation_scale)

    energy_anomaly_detected = False
    if total_rows > 1 and power_col in df.columns:
        initial_energy = float(df[power_col].iloc[0])
        current_energy = float(df[power_col].iloc[-1])
        if abs(initial_energy - current_energy) > power_drop_threshold:
            energy_anomaly_detected = True

    max_shear = 0.0
    if displacement_col in df.columns:
        max_shear = float(df[displacement_col].max())

    if max_shear > displacement_trigger or energy_anomaly_detected:
        phi_current = max(phi_current, margin_threshold + (max_shear * displacement_phi_scale))

    # 4. Strategic Time-Travel Vector: Dynamic Remaining Useful Life (RUL) Prediction
    if current_fc > 0.0 and phi_current < veto_gate:
        remaining_useful_life = (veto_gate - phi_current) / (current_fc + 1e-12)
        remaining_useful_life_steps = max(0.0, float(remaining_useful_life))
    elif phi_current >= veto_gate:
        remaining_useful_life_steps = 0.0
    else:
        remaining_useful_life_steps = float("inf")

    # 5. Invariant Boundary Threshold Classification
    if phi_current >= veto_gate:
        system_phase = status_bifurcation
        verdict = "FAIL"
    elif phi_current >= margin_threshold:
        system_phase = status_metastable
        verdict = "FAIL"
    else:
        system_phase = status_homeostatic
        verdict = "PASS"

    v4_meta = {
        "cumulative_entropy": round(phi_current, 6),
        "fatigue_gradient_fc": round(current_fc, 8),
        "remaining_useful_life_periods": round(remaining_useful_life_steps, 2)
        if remaining_useful_life_steps != float("inf")
        else "NOMINAL / STABLE",
        "total_kinetic_breaches": total_breaches,
        "max_observed_jitter": round(max_jitter, 8),
        "verdict": verdict,
        "phase_label": system_phase,
        "stalled_zone": bool(phi_current >= margin_threshold and phi_current < veto_gate),
        "quench_kinetic_veto": bool(phi_current >= veto_gate),
        "domain_id": cfg.get("domain_id"),
        "profile_name": profile_name,
    }

    return {
        "verdict": verdict,
        "phi_current": phi_current,
        "fc_gradient": current_fc,
        "remaining_useful_life_steps": remaining_useful_life_steps,
        "system_phase": system_phase,
        "v4_meta": v4_meta,
        "processed_df": df,
    }
