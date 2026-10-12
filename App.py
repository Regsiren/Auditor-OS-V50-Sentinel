import json
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

CRYPTO_COPY = (
    "Ed25519 Hardware-Ready Software Signature "
    "(HMAC/Ed25519 pure-Python & cryptography module fallback; "
    "cloud HSM key injection supported)."
)

BASELINE_OBSERVER = "Baseline Sentinel Observer (Static Genesis Anchor)"
ADAPTIVE_OBSERVER = "Adaptive Annealing Observer (Single-Anchor Dynamic Baseline)"
DUAL_HEAD_OBSERVER = "Dual-Head Governor (Stage I Prefill Audit + Stage II Decode Core)"

EARLY_WARNING_COPY = (
    "0-token prefill save and 1-3 token decode early-warning veto "
    "(demonstrated across synthetic residual shock benchmarks and pytest suites)."
)


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

    targets = ["logo.png", "logo.jpg", "logo.jpeg", "logo.png.jpg", "logo.png.jpeg", "assets/logo.png", "assets/logo.jpg", "assets/logo.jpeg", "assets/logo.png.jpg", "static/logo.png"]
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
    "ZONE-07-RESIDUAL_STREAM (AI Latent Activation & LLM Homeostasis)": "AI_HOMEOSTASIS",
}

# CSV sensor_id values (synthesizer / ingest) → profile preset
SENSOR_ID_PROFILE_MAP = {
    "ZONE-01-AMOC-CONVEYOR": "PLANETARY_INFRASTRUCTURE",
    "ZONE-02-JET-STREAM-ENVELOPE": "PLANETARY_INFRASTRUCTURE",
    "ZONE-03-CONTROL-BASELINE": "PLANETARY_INFRASTRUCTURE",
    "ZONE-07-RESIDUAL_STREAM": "AI_HOMEOSTASIS",
}

AI_HOMEOSTASIS_COLD_START = (
    "🧠 SYSTEM ARMED: AI LATENT ACTIVATION & LLM HOMEOSTASIS PROFILE\n\n"
    "Expecting transformer residual stream telemetry or hidden-state activation vectors.\n"
    "Tracks second-derivative kinetic acceleration (d²θ/dt²), sub-resolution titration "
    "firewall breaches (|J_tau| > 1e-7),\n"
    "and State Uncertainty Coordinates (Omega_t). Triggers Topological Veto at Omega >= 0.19.\n"
    "Veto events auto-mint Dual-Pillar schema v1.0 `.sent` attestation bags.\n\n"
    f"Early-warning envelope: {EARLY_WARNING_COPY}\n\n"
    f"Signing: {CRYPTO_COPY}"
)


def _analyze_zone(df_zone: pd.DataFrame, profile_name: str, ai_observer: str = BASELINE_OBSERVER) -> dict:
    """
    Route zone analysis to the AI residual auditor or the physical Engine kernel.

    AI_HOMEOSTASIS routes to Baseline, Adaptive Annealing, or Dual-Head Governor;
    soft-falls back to Engine if PyTorch / auditor_ai is unavailable on the host.
    """
    if profile_name != "AI_HOMEOSTASIS":
        return engine.analyze_systemic_solvency(df_zone, profile_name=profile_name)

    try:
        if ai_observer == DUAL_HEAD_OBSERVER:
            from auditor_ai.adaptive_engine import analyze_dual_head_dataframe

            return analyze_dual_head_dataframe(df_zone, profile_name=profile_name)
        if ai_observer == ADAPTIVE_OBSERVER:
            from auditor_ai.adaptive_engine import analyze_adaptive_dataframe

            return analyze_adaptive_dataframe(df_zone, profile_name=profile_name)
        from auditor_ai.sentinel_engine import analyze_activation_dataframe

        return analyze_activation_dataframe(df_zone, profile_name=profile_name)
    except ImportError:
        st.warning(
            "PyTorch AI auditor unavailable on this host — falling back to Engine.py "
            "finite-difference proxy for AI_HOMEOSTASIS."
        )
        report = engine.analyze_systemic_solvency(df_zone, profile_name="AI_HOMEOSTASIS")
        fallback = {
            DUAL_HEAD_OBSERVER: "dual_head_fallback",
            ADAPTIVE_OBSERVER: "adaptive_annealing_fallback",
        }.get(ai_observer, "baseline_sentinel_fallback")
        report.setdefault("v4_meta", {})["observer_mode"] = fallback
        return report


def _mint_v10_bag(report: dict, zone_name: str) -> dict:
    """Mint a Dual-Pillar schema v1.0 bag from an analysis report (or reuse governor bag)."""
    existing = report.get("sent_bag") or (report.get("v4_meta") or {}).get("sent_bag")
    if isinstance(existing, dict) and "attestation_header" in existing:
        return existing
    return kernel.mint_sentinel_v10_from_report(report, zone_name)


def _veto_cache_key(zone: str, report: dict, ai_observer: str) -> str:
    meta = report.get("v4_meta", {}) or {}
    return (
        f"{zone}|{ai_observer}|{report.get('phi_current')}|{report.get('fc_gradient')}|"
        f"{meta.get('total_kinetic_breaches')}|{meta.get('observer_mode')}"
    )


selected_zone_label = st.sidebar.selectbox(
    "Select Target Monitoring Zone:",
    options=list(ZONE_REGISTRY.keys()),
)
resolved_profile = ZONE_REGISTRY[selected_zone_label]
st.sidebar.info(f"Active Physics Blueprint: **{resolved_profile}**")

ai_observer = BASELINE_OBSERVER
if resolved_profile == "AI_HOMEOSTASIS":
    ai_observer = st.sidebar.radio(
        "AI Observer Mode:",
        [BASELINE_OBSERVER, ADAPTIVE_OBSERVER, DUAL_HEAD_OBSERVER],
        key="ai_observer_mode",
        help=EARLY_WARNING_COPY,
    )
    if ai_observer == DUAL_HEAD_OBSERVER:
        st.sidebar.success("Dual-Head Governor armed (Stage I Prefill + Stage II Decode).")
        st.sidebar.caption(EARLY_WARNING_COPY)
    elif ai_observer == ADAPTIVE_OBSERVER:
        st.sidebar.success("Adaptive Annealing observer armed (single-anchor dynamic baseline / Ω_t).")
    else:
        st.sidebar.success("Baseline Sentinel observer armed (static genesis anchor / Ω_t).")

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

    # Strict Schema Guardrail Check (AI profile only requires the activation coordinate)
    if resolved_profile == "AI_HOMEOSTASIS":
        required_headers = {"observed_value"}
    else:
        required_headers = {"observed_value", "power_matrix", "spatial_displacement"}
    missing_headers = required_headers - set(df_stream.columns)

    if missing_headers:
        st.error(f"❌ INVALID TELEMETRY STREAM SCHEMA: Missing required structural columns: {list(missing_headers)}")
        st.info("Ensure your input data strictly complies with the specification manifest displayed below.")
        st.stop()

    # Pad optional physical columns for AI streams so shared plot / mint paths stay robust.
    if resolved_profile == "AI_HOMEOSTASIS":
        if "power_matrix" not in df_stream.columns:
            df_stream["power_matrix"] = 0.0
        if "spatial_displacement" not in df_stream.columns:
            df_stream["spatial_displacement"] = 0.0

    st.success(f"Telemetry ingested — workspace target: {selected_zone_label} (`{resolved_profile}`)")

    # Active chain of custody validation check
    is_chain_valid = None
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
        zone_labels = ["ZONE-07-RESIDUAL_STREAM" if resolved_profile == "AI_HOMEOSTASIS" else "Main"]
        df_stream["sensor_id"] = zone_labels[0]
        
    all_reports = {}
    entropy_max = 0.0
    auto_veto_bags: dict[str, dict] = {}

    if "auto_veto_bags" not in st.session_state:
        st.session_state.auto_veto_bags = {}
    if "auto_veto_keys" not in st.session_state:
        st.session_state.auto_veto_keys = {}
    
    for zone in zone_labels:
        df_zone = df_stream[df_stream["sensor_id"] == zone]
        zone_profile = SENSOR_ID_PROFILE_MAP.get(zone, resolved_profile)
        report = _analyze_zone(df_zone, zone_profile, ai_observer=ai_observer)
        all_reports[zone] = report
        entropy_max = max(entropy_max, report["phi_current"])

        # Prefer governor-minted Dual-Pillar v1.0 bag; otherwise mint on veto.
        governor_bag = report.get("sent_bag") or (report.get("v4_meta") or {}).get("sent_bag")
        if isinstance(governor_bag, dict) and "attestation_header" in governor_bag:
            st.session_state.auto_veto_bags[str(zone)] = governor_bag
            st.session_state.auto_veto_keys[str(zone)] = _veto_cache_key(str(zone), report, ai_observer)
            auto_veto_bags[str(zone)] = governor_bag
        elif report.get("v4_meta", {}).get("quench_kinetic_veto") or float(report.get("phi_current", 0.0)) >= 0.19:
            cache_key = _veto_cache_key(str(zone), report, ai_observer)
            prior_key = st.session_state.auto_veto_keys.get(str(zone))
            if prior_key != cache_key or str(zone) not in st.session_state.auto_veto_bags:
                bag = _mint_v10_bag(report, str(zone))
                st.session_state.auto_veto_bags[str(zone)] = bag
                st.session_state.auto_veto_keys[str(zone)] = cache_key
            auto_veto_bags[str(zone)] = st.session_state.auto_veto_bags[str(zone)]
        
    # Boundary Check State Routing for Master Status Ribbon
    quench_zones = [k for k, v in all_reports.items() if v["v4_meta"]["quench_kinetic_veto"]]
    impairment_zones = [k for k, v in all_reports.items() if v["v4_meta"]["stalled_zone"]]

    active_zone = max(all_reports.keys(), key=lambda k: all_reports[k]["phi_current"])
    target_report = all_reports[active_zone]
    banner_text = target_report["system_phase"]

    if target_report["v4_meta"]["quench_kinetic_veto"]:
        banner_color = "#c0392b"
        if quench_zones:
            banner_text = f"{banner_text} — zones: {', '.join(quench_zones)}"
    elif target_report["v4_meta"]["stalled_zone"]:
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

    if auto_veto_bags:
        st.warning(
            f"Topological Veto attested — auto-minted Dual-Pillar schema v1.0 `.sent` bag(s) for: "
            f"{', '.join(auto_veto_bags.keys())}"
        )

    tab1, tab2 = st.tabs(["📊 Systemic Phase Space Tracker", "🗂️ Attestation Summary Bag"])
    
    with tab1:
        st.subheader("Localized Dimensional Analysis")
        selected_zone = st.selectbox("Select Target Observation Node:", zone_labels)
        
        target_report = all_reports[selected_zone]
        df_plot = target_report["processed_df"]
        meta = target_report["v4_meta"]
        is_ai_profile = (meta.get("profile_name") or resolved_profile) == "AI_HOMEOSTASIS"
        
        rul_val = meta['remaining_useful_life_periods']

        is_dual_head = meta.get("observer_mode") == "dual_head_governor" or ai_observer == DUAL_HEAD_OBSERVER
        if is_dual_head and "omega_prefill" in meta:
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric(
                "Ω_prefill (Stage I)",
                f"{float(meta['omega_prefill']):.4f}",
                help="Stage I PrefillSentinelAuditor state uncertainty. " + EARLY_WARNING_COPY,
            )
            c2.metric(
                "Ω_decode (Stage II)",
                f"{float(meta.get('omega_decode', meta['cumulative_entropy'])):.4f}",
                help="Stage II HardenedHomeostaticSentinelCore decode uncertainty.",
            )
            c3.metric("Fleet Max (Ω)", f"{entropy_max:.4f}")
            c4.metric("Decay Gradient (Fc)", f"{meta['fatigue_gradient_fc']:.8f}")
            c5.metric("Remaining Useful Life", str(rul_val))
            c6.metric("Kinetic Breaches", str(meta['total_kinetic_breaches']))
        else:
            col1, col2, col3, col4, col5 = st.columns(5)
            entropy_label = "State Uncertainty (Ω)" if is_ai_profile else "Node Entropy (Φ)"
            fleet_label = "Fleet Max (Ω)" if is_ai_profile else "Fleet Max Entropy (Φ)"
            col1.metric(entropy_label, f"{meta['cumulative_entropy']:.4f}")
            col2.metric(fleet_label, f"{entropy_max:.4f}", help="Highest uncertainty vector currently observed across all monitored zones. Drives the top Status Ribbon.")
            col3.metric("Decay Gradient (Fc)", f"{meta['fatigue_gradient_fc']:.8f}")
            col4.metric("Remaining Useful Life", str(rul_val))
            col5.metric("Kinetic Breaches", str(meta['total_kinetic_breaches']), help="Total threshold anomalies. Note: A stable control zone can accumulate baseline noise breaches without causing an upward shift in Phase Gates or Φ/Ω.")

        profile_label = meta.get("profile_name") or meta.get("domain_id") or resolved_profile
        observer_label = meta.get("observer_mode") or ("physical_telemetry" if not is_ai_profile else "baseline_sentinel")
        st.markdown(
            f"**Current Node Phase Status:** `{meta['phase_label']}` | "
            f"**Verification Verdict:** `{meta['verdict']}` | "
            f"**Physics Blueprint:** `{profile_label}` | "
            f"**Observer:** `{observer_label}`"
        )
        if is_dual_head:
            st.caption(EARLY_WARNING_COPY)

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
        st.markdown(
            "Select a node to mint an immutable **Dual-Pillar schema v1.0** `.sent` Attestation Evidence Bag "
            "with exactly four blocks: "
            "`attestation_header`, `thermodynamic_state_vector`, `execution_context`, "
            "`cryptographic_attestation`."
        )
        st.caption(CRYPTO_COPY)
        
        target_zone_bag = st.selectbox("Select Node for Export:", zone_labels, key="bag_export_sel")
        selected_report = all_reports[target_zone_bag]

        # Prefer the auto-minted veto bag when present so export matches the veto artifact.
        if str(target_zone_bag) in auto_veto_bags:
            bag = auto_veto_bags[str(target_zone_bag)]
            st.info("Exporting the auto-minted Topological Veto attestation for this node.")
        else:
            bag = _mint_v10_bag(selected_report, str(target_zone_bag))

        thermo = bag["thermodynamic_state_vector"]
        crypto = bag["cryptographic_attestation"]
        hdr = bag["attestation_header"]

        st.markdown("##### Schema v1.0 metadata preview")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("state_coordinate_omega", f"{thermo['state_coordinate_omega']:.6f}")
        m2.metric("sub_resolution_jitter_j_tau", f"{thermo['sub_resolution_jitter_j_tau']:.8f}")
        m3.metric("rolling_fatigue_fc (fc)", f"{thermo['rolling_fatigue_fc']:.8f}")
        m4.metric("sequence_step", str(hdr["sequence_step"]))
        st.markdown(
            f"**phase_boundary_state:** `{thermo['phase_boundary_state']}` · "
            f"**signature_algorithm:** `{crypto['signature_algorithm']}` · "
            f"**canonical_row_hash:** `{crypto['canonical_row_hash'][:16]}…`"
        )
        if is_chain_valid is not None:
            st.caption(
                f"Upstream CSV row-hash chain: "
                f"{'VERIFIED' if is_chain_valid else 'COMPROMISED / UNSIGNED'}"
            )

        evidence_string = json.dumps(bag, indent=4)
        
        st.text_area(
            "Signed Dual-Pillar `.sent` Evidence Block (schema v1.0):",
            evidence_string,
            height=350,
        )
        
        st.download_button(
            label=f"Export {target_zone_bag}.sent Evidence Bag (schema v1.0)",
            data=evidence_string,
            file_name=f"{str(target_zone_bag).lower()}.sent",
            mime="application/json",
        )
        
else:
    if resolved_profile == "AI_HOMEOSTASIS":
        st.info(AI_HOMEOSTASIS_COLD_START)
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
