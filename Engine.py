import numpy as np
import pandas as pd

# ==============================================================================
# AUDITOR OS V50 SENTINEL CORE: PHYSICAL CONSTANTS & CONFIGURATION
# ==============================================================================
MATH_BUFFER = 1e-7

# System Status Boundary Gates (Unit-less Phase Space Coordinate Flags)
MARGIN_CALL_THRESHOLD = 0.07        # Bound 1: Metastable Degradation Limit (Stage 1 Midpoint)
INSTITUTIONAL_BINARY_VETO_GATE = 0.19 # Bound 2: Topological Macro-Bifurcation Veto (Stage 2 Transition)

# Fixed Fiduciary Baseline Entropy
BASE_UNCERTAINTY_COEFFICIENT = 0.05   # Tier 5 Sovereign Gold Standard Baseline

# System State Narrative Labels (Section 3 Phase Nomenclature)
STATUS_HOMEOSTATIC = "Homeostatic State (< 0.07 Φ)"
STATUS_METASTABLE_IMPAIRMENT = "Metastable State (0.07 to 0.19 Φ)"
STATUS_BIFURCATION_COLLAPSE = "Topological Bifurcation (≥ 0.19 Φ)"

# ==============================================================================
# CORE KINETIC SENTINEL & T-30 MOMENTUM ENGINE
# ==============================================================================
def analyze_systemic_solvency(
    df_raw: pd.DataFrame, 
    val_col: str = "observed_value",
    power_col: str = "power_matrix",
    displacement_col: str = "spatial_displacement",
    rolling_window: int = 30
) -> dict:
    """
    Stateless Fiduciary Kernel for tracking complex multi-zone structural evolution.
    Combines real-time snapshot acceleration tracking with strategic T-30 time-travel momentum profiling.
    """
    df = df_raw.copy()
    total_rows = len(df)
    
    if total_rows < 3:
        return {
            "verdict": "PASS",
            "phi_current": BASE_UNCERTAINTY_COEFFICIENT,
            "fc_gradient": 0.0,
            "remaining_useful_life_steps": float('inf'),
            "system_phase": STATUS_HOMEOSTATIC,
            "v4_meta": {
                "cumulative_entropy": BASE_UNCERTAINTY_COEFFICIENT,
                "fatigue_gradient_fc": 0.0,
                "remaining_useful_life_periods": "NOMINAL / STABLE",
                "total_kinetic_breaches": 0,
                "max_observed_jitter": 0.0,
                "verdict": "PASS",
                "phase_label": STATUS_HOMEOSTATIC,
                "stalled_zone": False,
                "quench_kinetic_veto": False
            },
            "processed_df": df
        }

    # 1. Real-Time Snapshot Layer: Second Derivative Calculation (The Instantaneous Shiver)
    # dθ/dt — first temporal derivative (velocity of observable change)
    df["velocity"] = df[val_col].diff().fillna(0.0)
    # d²θ/dt² — kinetic acceleration (Section 3: second derivative of the observable)
    df["kinetic_acceleration"] = df["velocity"].diff().fillna(0.0)
    
    # Instantaneous forensic breaches where |kinetic_acceleration| exceeds the titration gate
    df["kinetic_breach"] = df["kinetic_acceleration"].abs() > MATH_BUFFER
    total_breaches = int(df["kinetic_breach"].sum())

    # 2. Strategic Layer: T-30 Momentum Integration (The Integral of Fatigue) [cite: 9, 13, 15]
    # Fc = ∫ |d²θ/dt²| * w(t) dt over rolling 30-period baseline window
    df["abs_kinetic_acceleration"] = df["kinetic_acceleration"].abs()
    df["fatigue_coefficient"] = df["abs_kinetic_acceleration"].rolling(window=rolling_window, min_periods=1).mean()
    
    # Fetch current decay gradient terminal state (Fc) [cite: 10]
    current_fc = float(df["fatigue_coefficient"].iloc[-1]) if total_rows >= rolling_window else 0.0

    # 3. Dynamic Uncertainty Coefficient Matrix (Pure Unit-less Entropy Vector Φ)
    # Compute rolling local micro-variance (Noise Floor Jitter Tracker J_t)
    df["jitter"] = df[val_col].rolling(window=10, min_periods=1).std().fillna(0.0)
    max_jitter = float(df["jitter"].max())

    # Build continuous entropy path accumulation
    cumulative_deviation = float((df[val_col] - df[val_col].iloc[0]).abs().max())
    
    # Calculate current system structural impairment coordinate (Φ)
    phi_current = BASE_UNCERTAINTY_COEFFICIENT + (cumulative_deviation * 0.05)
    
    # Force hard limits for macro structural failures (e.g., severe power drops or structural displacement shifts)
    power_drop_detected = False
    if total_rows > 1:
        initial_power = float(df[power_col].iloc[0])
        current_power = float(df[power_col].iloc[-1])
        # Systemic Dislocation Gate: Triggered if core power delta exceeds 10.0 MW limit
        if abs(initial_power - current_power) > 10.0:
            power_drop_detected = True
            
    max_displacement = float(df[displacement_col].max())
    if max_displacement > 1.0 or power_drop_detected:
        # Accelerate Φ calculation exponentially based on structural shear inputs
        phi_current = max(phi_current, MARGIN_CALL_THRESHOLD + (max_displacement * 0.01))

    # 4. Strategic Time-Travel Vector: Dynamic Remaining Useful Life (RUL) Prediction [cite: 11, 24]
    # Asks: Based on rolling momentum of micro-accelerations, when will system hit 0.19 Veto Gate? [cite: 12]
    if current_fc > 0.0 and phi_current < INSTITUTIONAL_BINARY_VETO_GATE:
        # Distance to absolute topological phase collapse divided by integrated decay rate
        remaining_useful_life = (INSTITUTIONAL_BINARY_VETO_GATE - phi_current) / (current_fc + 1e-12)
        # Limit to reasonable scale, protect against infinite step division boundaries
        remaining_useful_life_steps = max(0.0, float(remaining_useful_life))
    elif phi_current >= INSTITUTIONAL_BINARY_VETO_GATE:
        remaining_useful_life_steps = 0.0
    else:
        remaining_useful_life_steps = float('inf')

    # 5. Non-Linear Phase Portal Trajectory Categorization
    if phi_current >= INSTITUTIONAL_BINARY_VETO_GATE:
        system_phase = STATUS_BIFURCATION_COLLAPSE
        verdict = "FAIL"
    elif phi_current >= MARGIN_CALL_THRESHOLD:
        system_phase = STATUS_METASTABLE_IMPAIRMENT
        verdict = "FAIL"
    else:
        system_phase = STATUS_HOMEOSTATIC
        verdict = "PASS"

    # Export signed multi-zone validation metadata package
    v4_meta = {
        "cumulative_entropy": round(phi_current, 6),
        "fatigue_gradient_fc": round(current_fc, 8),
        "remaining_useful_life_periods": round(remaining_useful_life_steps, 2) if remaining_useful_life_steps != float('inf') else "NOMINAL / STABLE",
        "total_kinetic_breaches": total_breaches,
        "max_observed_jitter": round(max_jitter, 8),
        "verdict": verdict,
        "phase_label": system_phase,
        "stalled_zone": bool(phi_current >= MARGIN_CALL_THRESHOLD and phi_current < INSTITUTIONAL_BINARY_VETO_GATE),
        "quench_kinetic_veto": bool(phi_current >= INSTITUTIONAL_BINARY_VETO_GATE)
    }

    return {
        "verdict": verdict,
        "phi_current": phi_current,
        "fc_gradient": current_fc,
        "remaining_useful_life_steps": remaining_useful_life_steps,
        "system_phase": system_phase,
        "v4_meta": v4_meta,
        "processed_df": df
    }
