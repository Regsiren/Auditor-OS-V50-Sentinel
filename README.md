# The Sentinel Protocol (Auditor OS V50-S Core)

> **Scale-Invariant Thermodynamic Attribution: Mapping Non-Linear Phase Transitions in Macro-Systems via Stateless Telemetry Auditing**

This repository contains the reference implementation framework for the **V50 Sentinel (V50-S) Core**, a stateless, hardware-agnostic telemetry cross-examination engine designed to monitor structural and environmental stability boundaries.

**Live Operations Portal:** [sentinel.thohatventures.com](https://sentinel.thohatventures.com) — hosted Streamlit interface for multi-zone phase analysis and `.sent` evidence export (no local install required).

## Repository Layout

```
Auditor-OS-V50-Sentinel/
├── App.py                      # Streamlit operations interface
├── Engine.py                   # Stateless fiduciary kernel (V50-S core)
├── Forensic_kernel.py          # Cryptographic chain-of-custody layer
├── Data_Synthesizer.py         # Planetary reference telemetry generator
├── Biometric_Synthesizer.py    # BIOMETRIC_SENTINEL demo stream generator
├── resign_telemetry_chain.py   # Re-mint per-zone row_hash seals on a stream
├── evaluate_corpus.py          # Faithful Section 6 results-matrix generator
├── test_engine.py              # Automated validation suite
├── requirements.txt
├── LICENSE                     # BSL 1.1 (Apache 2.0 after May 25, 2030)
├── assets/                     # Brand assets (sidebar logo)
├── data/                       # Sample & generated telemetry streams
└── docs/                       # White papers & specialized addendums
    ├── README.md               # Documentation index & contribution horizons
    ├── THEORY.md               # Core mathematical framework
    └── APPENDIX_B_BIOMETRIC_SENTINEL.md
```

### 📑 Theoretical Foundations & Public Records

The mathematical architecture, scale-invariant algorithms, and multi-domain validation use cases governing the reference kernel inside this repository are fully documented across the following public open-access preprints.

**Core Mathematical Theory**

- **Scale-Invariant Thermodynamic Attribution: A Stateless Alternative for Complex System Data Modelling**
  - *Scope:* Establishes the core mathematical architecture, detailing the sub-resolution titration firewall ($\epsilon = 1 \times 10^{-7}$) and the finite-difference evaluation loops required to isolate the instantaneous kinetic acceleration ($\ddot{\theta}$) of non-linear data streams without legacy moving-average lag.
  - *Permanent Digital Record:* [https://doi.org/10.5281/zenodo.20548469](https://doi.org/10.5281/zenodo.20548469)

**Domain-Specific Implementations**

- **Scale-Invariant Phase Space Tracking of Planetary Fluid Currents and Atmospheric Vortices**
  - *Scope:* Implements the protocol across macro-environmental fluid loops (the AMOC conveyor and Equatorial Pacific ENSO heat engines) to track sub-grid multiscale variability and isolate localized thermodynamic transitions under computational constraints.
  - *Permanent Digital Record:* [doi.org/10.5281/zenodo.20548898](https://doi.org/10.5281/zenodo.20548898)

- **Scale-Invariant Phase Space Tracking in Non-Linear Biological Systems: Preemptive Characterisation of Autonomic Degradation Windows**
  - *Scope:* Applies the continuity protocol to high-frequency biometric telemetry streams (Heart Rate Variability inter-beat intervals) to decode real-time sympathetic redlining, bypass conscious sensory masking, and predict systemic executive burnout before macroscopic onset ($\Phi \ge 0.07$).
  - *Permanent Digital Record:* [doi.org/10.5281/zenodo.20549045](https://doi.org/10.5281/zenodo.20549045)

**Macroeconomic Framework**

- **The Fiduciary Theory of Entropy**
  - *Scope:* Connects the stateless physical titration engine to real-world value attribution, risk mitigation, and automated clearing systems within tokenized sovereign asset networks.
  - *Financial Research Network Vector:* [SSRN Abstract 6704958](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6704958)

[![Watch the video](https://img.youtube.com/vi/MGH7lfhtYGo/maxresdefault.jpg)](https://youtu.be/MGH7lfhtYGo)

## 1. Mathematical Foundation

Unlike legacy generative simulation models that rely on macro-scale spatial grids, the V50-S core evaluates point-source time-series streams to capture the **Instantaneous Kinetic Acceleration** ($\ddot{\theta}$) of systemic deviation:

$$\ddot{\theta} = \frac{d^2\theta}{dt^2}$$

The tactical layer passes this acceleration vector through a sub-resolution titration firewall ($\epsilon = 1 \times 10^{-7}$). These events are integrated across a rolling temporal baseline by the **T-30 Momentum Engine** to compute the continuous **Fatigue Coefficient** ($F_c$):

$$F_c = \int_{T-30}^{T} \left| \frac{d^2\theta}{dt^2} \right| \cdot w(\theta, \nabla \mathbf{X}) \, dt$$

> **Technical Note on Discretization:** In the reference software implementation, the continuous temporal integral for the Fatigue Coefficient ($F_c$) is evaluated using a uniform 30-step rolling average proxy ($\frac{1}{k}\sum_{i=0}^{k-1} |\ddot{\theta}|$). This discretization effectively captures the long-term strategic signal of decay while maintaining zero processing overhead on standard distributed compute networks.

The resulting unit-less entropy vector ($\Phi$) provides a deterministic calculation of the system's **Remaining Useful Life (RUL)** before crossing non-linear phase transition tipping points.

### ⚠️ The Law of Continuous Observation (Telemetry Opacity Failure Mode)

The scale-invariant thermodynamic attribution loop is strictly bounded by the law of continuous observation. The V50-S engine is a deterministic physical framework, not a predictive oracle for closed, hidden, or structurally opaque systems.

For the mathematical second-derivative continuum to calculate a reliable, deterministic Predictive Remaining Useful Life (RUL) Vector, the target system must continuously broadcast its internal state vector via an accessible, time-series telemetry stream ($\theta$).

```
┌───────────────────────────┐
│ Raw Streaming Telemetry   │
└─────────────┬─────────────┘
              │
┌─────────────┴─────────────┐
▼                           ▼
[Continuous Physics Signals]    [Data Starvation / Opacity]
Underlying thermodynamic        Insulated or closed internal vectors
governance
Trackable kinetic acceleration  Purely stochastic non-physical noise
│                               │
▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ V50 Sentinel Operational  │   │ Titration Firewall Core   │
│ Solvency Calculated       │   │ Axiom Collapses           │
└───────────────────────────┘   └───────────────────────────┘
```

#### Absolute Failure Parameters

1. **Data Starvation:** If the input stream undergoes non-linear decay but its internal micro-variances are completely insulated from point-source telemetry capture, the titration firewall experiences absolute data starvation.
2. **Pure Stochastic Noise:** If the streaming jitter is driven by purely non-physical random noise with zero underlying thermodynamic governance, the engine's calculus will yield zero predictive value.

The engine requires data velocity to map the path to collapse; it cannot interrogate a ledger that remains closed.

## 2. Core Repository Architecture

* `Engine.py`: The stateless fiduciary kernel executing the second-derivative acceleration tracking, rolling fatigue integrals, and boundary phase state evaluations.
* `Forensic_kernel.py`: Handles the local cryptographic chain-of-custody validation layer via sequential, state-less SHA-256 row-pair hashing.
* `App.py`: Streamlit operations interface with the **Sentinel Domain Workspace** (zone → physics preset routing) and multi-zone phase space portraits with `.sent` evidence export.
* `DOMAIN_PROFILES` (`Engine.py`): `PLANETARY_INFRASTRUCTURE`, `BIOMETRIC_SENTINEL`, `QUANTUM_COHERENCE` — scale-invariant gates with domain-specific shear and energy limits.
* `Data_Synthesizer.py`: An empirical data synthesizer that seeds a 100-year multi-zone climate/structural dataset profile (AMOC decay lifecycle vs. control baseline) embedded with sub-resolution anomalies.

## 📚 Core Architecture & Theory

For the deep mathematical proofs governing the universal scale-invariant thermodynamic loop across infrastructure, biometrics, and cosmological systems, see the full [V50-S Isomorphism White Paper](docs/THEORY.md).

## 📑 Documentation & Specialized Addendums

* **Domain Beta (Biometrics):** For developer onboarding regarding high-frequency biological telemetry insulation and adaptive moving-average smoothing, see [docs/APPENDIX_B_BIOMETRIC_SENTINEL.md](docs/APPENDIX_B_BIOMETRIC_SENTINEL.md).

## 3. Quickstart Deployment

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Reference Telemetry:**
   ```bash
   python Data_Synthesizer.py
   ```
   This writes `data/MACRO_SYSTEM_PLANETARY_STREAM.csv` (15,600 rows: 5,200 weekly steps × 3 observation zones). For the biometric domain demo, run `python Biometric_Synthesizer.py` to write `data/BIOMETRIC_SENTINEL_STREAM.csv`.

3. **Run the validation suite (optional):**
   ```bash
   python -m pytest test_engine.py -v
   ```

   Reproduce the Section 6 empirical results matrix directly from the shipped engine:
   ```bash
   python evaluate_corpus.py
   ```

4. **Launch the Operations Interface:**
   - **Hosted:** [sentinel.thohatventures.com](https://sentinel.thohatventures.com)
   - **Local development:**
     ```bash
     streamlit run App.py
     ```
     Open the local URL shown in the terminal (typically `http://localhost:8501`), upload `data/MACRO_SYSTEM_PLANETARY_STREAM.csv`, and inspect per-zone phase metrics, kinetic trajectory plots, and `.sent` evidence exports. Use the sidebar **Sentinel Domain Workspace** to select a monitoring zone and its physics blueprint; synthesized `sensor_id` values auto-map to planetary presets.

> **Operational Note on UI Behavior:** The Global Master Status Ribbon dynamically reflects the phase state of the worst-performing zone across the entire fleet (the maximum calculated $\Phi$ vector), while individual per-node metric grids track the specific sensor node selected in the dropdown menu.

## 4. Required Telemetry Schema

Uploaded CSV streams must include:

| Column | Description |
|--------|-------------|
| `timestamp` | Chronological observation stamp (`YYYY-MM-DD HH:MM:SS`) |
| `sensor_id` | Multi-zone observation node identifier |
| `observed_value` | Primary observable coordinate (e.g., titration fraction) |
| `power_matrix` | Kinetic pump / thermal transport delta (MW) |
| `spatial_displacement` | Boundary or structural shear drift (km) |
| `row_hash` | *(Optional)* Per-row SHA-256 chain seal; required for chain-of-custody verification |

## 5. Phase Boundary Gates

| State | Φ Range | Label |
|-------|---------|-------|
| Homeostatic | &lt; 0.07 | Pristine thermodynamic equilibrium |
| Metastable | 0.07 – 0.19 | Integral momentum gap active |
| Topological Bifurcation | ≥ 0.19 | Critical structural veto triggered |

**Reference constants:** titration ceiling `1e-7`, metastable margin `0.07`, collapse veto `0.19`.

## 6. Cryptographic Chain of Custody

When `row_hash` is present, `Forensic_kernel.py` validates each `sensor_id` chain independently (protocol `THOHAT-V50-SENTINEL`):

- Each zone is sorted chronologically and anchored by a deterministic genesis hash, `SHA-256("GENESIS_<sensor_id>")`.
- Every row binds the prior row's seal: `Hash_t = SHA-256(NormalizedFeatures_t || prev_hash:Hash_{t-1} || salt)`.
- Numeric fields are canonicalized at fixed decimal precision so the chain stays stable across CSV round-trips.

Regenerate signed telemetry via `Data_Synthesizer.py` (which delegates sealing to the resign utility), or re-seal an existing stream in place:

```bash
python resign_telemetry_chain.py
```

> **Compatibility note:** This sealing model is not backward compatible with streams signed by earlier revisions. Re-seal any legacy CSV through `resign_telemetry_chain.py` before verification.

## 7. Academic Citation

For the full open-access record and per-domain DOIs, see **Theoretical Foundations & Public Records** at the top of this document.

If you utilize this framework, the V50-S core metrics, or the scale-invariant phase space mathematics in an academic, institutional, or commercial research capacity, please cite the foundational paper:

```bibtex
@misc{olaiya2026scale,
  title={Scale-Invariant Thermodynamic Attribution: A Stateless Alternative for Complex System Data Modelling},
  author={Olaiya, Remi},
  year={2026},
  publisher={Zenodo},
  doi={10.5281/zenodo.20548469},
  url={https://doi.org/10.5281/zenodo.20548469},
  note={Operational Core: Core V50-S Sentinel Framework}
}
```

## ⚖️ Scope, Academic Verification, & Commercial Licensing

The equations, finite-difference observer loops, and scale-invariant titration firewalls housed within this repository represent the foundational mathematical kernel of the **Auditor OS V50 Sentinel** open-source release. This code is designed to demonstrate the computational reproducibility of the thermodynamic continuity tracking method when running against clean, normalized, or post-processed research baselines (e.g., idealized PhysioNet or synthetic clinical control arrays). The boundary thresholds and domain profiles are reference defaults intended for independent empirical calibration, not validated clinical constants.

> ⚠️ **IMPORTANT COMMERCIAL DISCLAIMER**
>
> The open-source core is a reference implementation of the tracking calculus, intended to be computationally reproducible against clean or idealized baselines. Running this model live on an active field operator or an ambulatory patient — without drowning in strenuous physical-motion noise — requires the proprietary signal-conditioning matrices engineered exclusively into **Auditor OS Oracle**.

### 💼 Enterprise Production Inquiries

If your organization requires real-time telemetry processing for high-acuity clinical environments, defense logistics, tactical ambulatory deployment, or commercial wearable hardware integration, please contact our institutional team to secure an enterprise deployment license for the **Auditor OS Oracle** platform. 

The commercial layer includes:
* **Adaptive Noise-Gate Engineering:** Dynamic signal-conditioning matrices designed to filter out stride impacts, muscle tremors, and electrode movement artifacts natively.
* **Live Automated Actuator Hooks:** Production-ready closed-loop hooks to bridge 0.19 $\Phi$ veto verdicts directly into hardware overrides.
* **C-Suite Multi-Page Reporting Engines:** Automatic, context-aware PDF generation pipelines tailored for corporate risk committees and underwriters.

🌐 Learn more or request an evaluation sandbox at [sentinel.thohatventures.com](https://sentinel.thohatventures.com) or [auditor.thohatventures.com](https://auditor.thohatventures.com).

## 8. License

This repository is licensed under the **Business Source License 1.1 (BSL 1.1)** by Thohat Ventures. Non-commercial research and developer use is permitted; commercial production use requires a separate license from Thohat Ventures. The Software transitions to **Apache 2.0** on **May 25, 2030**.

See [LICENSE](LICENSE) for the full terms.

### ⚖️ Academic Nomenclature & Calibration Notice

The Auditor OS V50 Sentinel Core Protocol provides a scale-invariant condition-monitoring architecture and cryptographic data governance reference implementation. 

To maintain lightweight operational execution, terms such as 'solvency', 'entropy path (Phi)', and 'topological bifurcation collapse' are utilized as structured physics-based metaphors and domain-calibrated health indices to profile system degradation over sequential data frames. These indicators are constructed using standard digital signal processing, finite difference methods, and absolute deviation limits. 

This reference implementation is designed to establish a standardized telemetry audit trail and automated alert gating specification. Independent researchers and operators are encouraged to fork this repository to empirically calibrate boundary thresholds, test alternative smoothing windows, and submit domain-specific physics validation profiles against live empirical datasets.

---

**THOHAT Ventures** — Auditor OS V50 Sentinel Reference Implementation
