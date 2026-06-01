import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import pytz
from datetime import datetime
import Engine as engine
import Forensic_kernel as kernel

# Resolve Application Directories for Brand Ingestion
_APP_DIR = os.path.dirname(os.path.abspath(__file__))

def _logo_path():
    """Aggressively scans the script directory and working path for any variant of the brand asset."""
    _script_dir = os.path.abspath(_APP_DIR)
    _logo_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".npg", ".png.jpg", ".png.jpeg")
    try:
        for ent in sorted(os.scandir(_script_dir), key=lambda e: e.name.lower()):
            if not ent.is_file():
                continue
            nl = ent.name.lower()
            if not nl.startswith("logo"):
                continue
            if any(nl.endswith(ext) for ext in _logo_ext) or ".png.jpg" in nl or ".png.jpeg" in nl:
                return os.path.abspath(ent.path)
    except OSError:
        pass

    targets = ["logo.png", "logo.jpg", "logo.jpeg", "logo.png.jpg", "logo.png.jpeg", "assets/logo.png", "assets/logo.png.jpg", "static/logo.png"]
    roots = (_APP_DIR, os.getcwd(), os.path.abspath("."))
    for t in targets:
        if os.path.isfile(t):
            return os.path.abspath(t)
        for root in roots:
            p = os.path.join(root, t)
            if os.path.isfile(p):
                return os.path.abspath(p)
    return None

# Initialize Core Window Grid Configuration
st.set_page_config(page_title="Auditor OS V50-S", layout="wide")

# ==============================================================================
# SIDEBAR CONTROL ROOM: THOHAT LOGO & SOVEREIGN HASH CLOCK
# ==============================================================================
# 1. Core Brand Ingestion Block
_logo = _logo_path()
if _logo:
    st.sidebar.image(_logo, width="stretch")
else:
    st.sidebar.markdown("<h2 style='text-align: center; color: #7f8c8d;'>THOHAT VENTURES</h2>", unsafe_allow_html=True)

st.sidebar.markdown("---")

# 2. Live Sovereign Hash Clock Component
st.sidebar.subheader("⏳ Temporal Anchor")
tz_options = ["Europe/London", "America/New_York", "Asia/Tokyo", "UTC"]
_tz_for_clock = st.sidebar.selectbox("Site Timezone (IANA):", tz_options, index=0, key="site_tz_sel")

try:
    _clock_tz = pytz.timezone(_tz_for_clock)
except Exception:
    _clock_tz = pytz.timezone("Europe/London")

sovereign_ts = datetime.now(_clock_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
st.sidebar.markdown(f"**Sovereign Telemetry Clock:** `{sovereign_ts}`")

st.sidebar.markdown("---")

# =====================================================================
# Sentinel Domain Workspace: zone labels → physics profile presets
# =====================================================================
st.sidebar.header("🛡️ Sentinel Domain Workspace")

ZONE_REGISTRY = {
    "ZONE-01-AMOC (Planetary Ocean Conveyor)": "PLANETARY_INFRASTRUCTURE",
    "ZONE-02-JETSTREAM (Atmospheric Multi-Zone Jet)": "PLANETARY_INFRASTRUCTURE",
    "ZONE-03-CALDERA (Subterranean Magma Kinetics)": "PLANETARY_INFRASTRUCTURE",
    "ZONE-04-METABOLIC (Continuous Biometric Ingestion)": "BIOMETRIC_SENTINEL",
    "ZONE-05-AUTONOMIC (High-Frequency HRV Cadence)": "BIOMETRIC_SENTINEL",
    "ZONE-06-QUBIT (Quantum Cryogenic Noise Floor)": "QUANTUM_COHERENCE",
}

# CSV sensor_id values (synthesizer / ingest) → profile preset
SENSOR_ID_PROFILE_MAP = {
    "ZONE-01-AMOC-CONVEYOR": "PLANETARY_INFRASTRUCTURE",
    "ZONE-02-JET-STREAM-ENVELOPE": "PLANETARY_INFRASTRUCTURE",
    "ZONE-03-CONTROL-BASELINE": "PLANETARY_INFRASTRUCTURE",
}

selected_zone_label = st.sidebar.selectbox(
    "Select Target Monitoring Zone:",
    options=list(ZONE_REGISTRY.keys()),
)
resolved_profile = ZONE_REGISTRY[selected_zone_label]
st.sidebar.info(f"Active Physics Blueprint: **{resolved_profile}**")

st.sidebar.markdown("---")

# 3. File Ingestion Pipeline
st.sidebar.header("Data Ingestion Pipeline")
uploaded_file = st.sidebar.file_uploader("Upload Telemetry Stream (.csv)", type=["csv"])

st.sidebar.markdown("---")
st.sidebar.subheader("📖 Operations Room Guide")

with st.sidebar.expander("🔬 Core Metric Explainers", expanded=False):
    st.markdown(r"""
    **The Instantaneous Shiver ($d^2\theta/dt^2$):** Computes raw Kinetic Acceleration across continuous steps. Any spike above $1 \times 10^{-7}$ flags a structural breach.
    
    **Decay Gradient ($F_c$):** In reference software, the continuous integral is evaluated as a uniform 30-step rolling mean of $|\ddot{\theta}|$ — a discretization that preserves the long-term strategic decay signal with minimal compute overhead.
    
    **Remaining Useful Life (RUL):** A linear heuristic countdown estimating the step periods remaining before the system crosses into a phase transition. It is an operational triage indicator, not a validated probabilistic survival model.
    """)

with st.sidebar.expander("📜 V50-S Technical Manual", expanded=False):
    st.markdown(r"""
    ### Protocol SOP Manual
    **1. Homeostatic State (< 0.07 Φ)**
    System operates in pristine thermodynamic balance. Native negative feedback loops actively suppress internal frictions.
    
    **2. Metastable State (0.07 to 0.19 Φ)**
    The Autonomous Margin Boundary is breached. Micro-dislocations are actively compounding. The system is entering a pre-collapse state.
    
    **3. Topological Bifurcation (≥ 0.19 Φ)**
    The Absolute Structural Veto Gate is tripped. Complete macro-collapse of the boundary layer occurs.
    """)
    
    # Provide a clean, text-based manual download to prevent library bloat
    manual_text = "AUDITOR OS V50-S MANUAL\n\n1. TITRATION CEILING: 1e-7\n2. METASTABLE MARGIN GATE: 0.07\n3. CRITICAL COLLAPSE VETO: 0.19\n"
    st.download_button(
        label="📥 Download V50-S User Manual (.txt)",
        data=manual_text,
        file_name="Auditor_OS_V50S_User_Manual.txt",
        mime="text/plain",
        key="manual_dl_sidebar"
    )

# Main Application Master Header Layout
st.markdown("""
    <h1 style='text-align: center; color: #2c3e50;'>AUDITOR OS V50 SENTINEL</h1>
    <h3 style='text-align: center; color: #7f8c8d;'>Macro-System Phase Space Tracker & Boundary Oracle</h3>
    <hr/>
""", unsafe_allow_html=True)

if uploaded_file is not None:
    df_stream = pd.read_csv(uploaded_file)

    # Strict Schema Guardrail Check
    required_headers = {"observed_value", "power_matrix", "spatial_displacement"}
    missing_headers = required_headers - set(df_stream.columns)

    if missing_headers:
        st.error(f"❌ INVALID TELEMETRY STREAM SCHEMA: Missing required structural columns: {list(missing_headers)}")
        st.info("Ensure your input data strictly complies with the specification manifest displayed below.")
        st.stop()

    st.success(f"Telemetry ingested — workspace target: {selected_zone_label} (`{resolved_profile}`)")

    # Active chain of custody validation check
    with st.sidebar:
        if "row_hash" in df_stream.columns:
            if "sensor_id" in df_stream.columns:
                is_chain_valid = all(
                    kernel.verify_telemetry_chain(
                        df_stream[df_stream["sensor_id"] == z].reset_index(drop=True)
                    )
                    for z in df_stream["sensor_id"].unique()
                )
            else:
                is_chain_valid = kernel.verify_telemetry_chain(df_stream.reset_index(drop=True))
            if is_chain_valid:
                st.success("🔒 Telemetry Chain of Custody: VERIFIED")
            else:
                st.error("❌ Telemetry Chain of Custody: COMPROMISED / ALTERED")
        else:
            st.warning("⚠️ Unsigned Stream: No Cryptographic Row Hashes Present")
    
    if "sensor_id" in df_stream.columns:
        zone_labels = df_stream["sensor_id"].unique()
    else:
        zone_labels = ["Main"]
        df_stream["sensor_id"] = "Main"
        
    all_reports = {}
    entropy_max = 0.0
    
    for zone in zone_labels:
        df_zone = df_stream[df_stream["sensor_id"] == zone]
        zone_profile = SENSOR_ID_PROFILE_MAP.get(zone, resolved_profile)
        report = engine.analyze_systemic_solvency(df_zone, profile_name=zone_profile)
        all_reports[zone] = report
        entropy_max = max(entropy_max, report["phi_current"])
        
    # Boundary Check State Routing for Master Status Ribbon
    quench_zones = [k for k, v in all_reports.items() if v["v4_meta"]["quench_kinetic_veto"]]
    impairment_zones = [k for k, v in all_reports.items() if v["v4_meta"]["stalled_zone"]]

    active_zone = max(all_reports.keys(), key=lambda k: all_reports[k]["phi_current"])
    target_report = all_reports[active_zone]
    banner_text = target_report["system_phase"]

    if target_report["system_phase"] == engine.STATUS_BIFURCATION_COLLAPSE:
        banner_color = "#c0392b"
        if quench_zones:
            banner_text = f"{banner_text} — zones: {', '.join(quench_zones)}"
    elif target_report["system_phase"] == engine.STATUS_METASTABLE_IMPAIRMENT:
        banner_color = "#FFBF00"
        if impairment_zones:
            banner_text = f"{banner_text} — zones: {', '.join(impairment_zones)}"
    else:
        banner_color = "#27ae60"

    st.markdown(f"""
        <div style='background-color: {banner_color}; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 25px;'>
            <h3 style='color: white; margin: 0;'>{banner_text}</h3>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 Systemic Phase Space Tracker", "🗂️ Attestation Summary Bag"])
    
    with tab1:
        st.subheader("Localized Dimensional Analysis")
        selected_zone = st.selectbox("Select Target Observation Node:", zone_labels)
        
        target_report = all_reports[selected_zone]
        df_plot = target_report["processed_df"]
        meta = target_report["v4_meta"]
        
        rul_val = meta['remaining_useful_life_periods']

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Node Entropy (Φ)", f"{meta['cumulative_entropy']:.4f}")
        col2.metric("Fleet Max Entropy (Φ)", f"{entropy_max:.4f}", help="Highest entropy vector currently observed across all monitored zones. Drives the top Status Ribbon.")
        col3.metric("Decay Gradient (Fc)", f"{meta['fatigue_gradient_fc']:.8f}")
        col4.metric("Remaining Useful Life", str(rul_val))
        col5.metric("Kinetic Breaches", str(meta['total_kinetic_breaches']), help="Total threshold anomalies. Note: A stable control zone can accumulate baseline noise breaches without causing an upward shift in Phase Gates or Φ.")

        profile_label = meta.get("profile_name") or meta.get("domain_id") or resolved_profile
        st.markdown(
            f"**Current Node Phase Status:** `{meta['phase_label']}` | "
            f"**Verification Verdict:** `{meta['verdict']}` | "
            f"**Physics Blueprint:** `{profile_label}`"
        )

        st.markdown("---")
        
        st.subheader("Kinetic Trajectory Cinema")
        fig, ax1 = plt.subplots(figsize=(12, 5))
        
        if "timestamp" in df_plot.columns:
            x_axis = pd.to_datetime(df_plot["timestamp"])
            x_label = "Observation Timeline (Calendar Date)"
        else:
            x_axis = df_plot.index
            x_label = "Temporal Intervals (Steps)"
        
        ax1.plot(x_axis, df_plot["observed_value"], color="#3498db", label="Observed Variable (θ)", alpha=0.8)
        ax1.set_xlabel(x_label)
        ax1.set_ylabel("Observable Coordinate Value", color="#3498db")
        ax1.tick_params(axis='y', labelcolor='#3498db')
        
        ax2 = ax1.twinx()
        ax2.plot(x_axis, df_plot["fatigue_coefficient"], color="#e67e22", label="Integrated Fatigue (Fc)", linestyle="--", alpha=0.9)
        ax2.set_ylabel("T-30 Structural Decay Gradient (Fc)", color="#e67e22")
        ax2.tick_params(axis='y', labelcolor='#e67e22')
        
        if "timestamp" in df_plot.columns:
            fig.autofmt_xdate()
        
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)
        
    with tab2:
        st.subheader("Cryptographic Audit Attestation Seals")
        st.markdown("Select a node to mint an immutable, standalone verification metadata package:")
        
        target_zone_bag = st.selectbox("Select Node for Export:", zone_labels, key="bag_export_sel")
        selected_report = all_reports[target_zone_bag]
        
        evidence_string = kernel.mint_sentinel_evidence_bag(selected_report, target_zone_bag)
        
        st.text_area("Signed `.sent` Evidence Block Content:", evidence_string, height=350)
        
        st.download_button(
            label=f"Export {target_zone_bag}.sent Evidence Bag",
            data=evidence_string,
            file_name=f"{target_zone_bag.lower()}.sent",
            mime="application/json"
        )
        
else:
    st.info(
        f"🌐 SYSTEM READY FOR TELEMETRY INGESTION\n\n"
        f"Sidebar workspace: **{selected_zone_label}** → `{resolved_profile}`\n\n"
        "Upload a validated CSV (sample: `data/MACRO_SYSTEM_PLANETARY_STREAM.csv`) with these column headers:\n"
        "* **observed_value**: High-resolution material titration or physical boundary coordinate decimals.\n"
        "* **power_matrix**: Localized kinetic pump output or thermal energy transport delta (MW).\n"
        "* **spatial_displacement**: Multi-dimensional boundary or structural shear vector drift (km).\n"
        "* **sensor_id** (optional): Per-node identifier; known IDs auto-resolve to domain presets."
    )
