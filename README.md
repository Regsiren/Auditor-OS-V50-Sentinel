# The Sentinel Protocol (Auditor OS V50-S Core)

> **Scale-Invariant Thermodynamic Attribution: Mapping Non-Linear Phase Transitions in Macro-Systems via Stateless Telemetry Auditing**

This repository contains the reference implementation framework for the **V50 Sentinel (V50-S) Core**, a stateless, hardware-agnostic telemetry cross-examination engine designed to monitor structural and environmental stability boundaries.

## Repository Layout

```
Auditor-OS-V50-Sentinel/
├── App.py                      # Streamlit operations interface
├── Engine.py                   # Stateless fiduciary kernel (V50-S core)
├── Forensic_kernel.py          # Cryptographic chain-of-custody layer
├── Data_Synthesizer.py         # Reference telemetry generator
├── test_engine.py              # Automated validation suite
├── requirements.txt
├── assets/                     # Brand assets (sidebar logo)
├── data/                       # Sample & generated telemetry streams
└── docs/                       # White papers & specialized addendums
    ├── THEORY.md
    └── APPENDIX_B_BIOMETRIC_SENTINEL.md
```

### 📑 Authoritative Preprints (SSRN Working Paper Series)

1. Core Physical Asset Tracking Architecture: [INSERT LIVE PRIMARY SSRN URL HERE]
2. [Supplemental Note on the Cross-Domain Mathematical Isomorphism of the Sentinel Loop](docs/THEORY.md) (Biometric & Gravothermal Extensions): [INSERT LIVE COMPANION SSRN URL HERE]

[![Watch the video](https://img.youtube.com/vi/MGH7lfhtYGo/maxresdefault.jpg)](https://youtu.be/MGH7lfhtYGo)

## 1. Mathematical Foundation

Unlike legacy generative simulation models that rely on macro-scale spatial grids, the V50-S core evaluates point-source time-series streams to capture the **Instantaneous Kinetic Acceleration** ($\ddot{\theta}$) of systemic deviation:

$$\ddot{\theta} = \frac{d^2\theta}{dt^2}$$

The tactical layer passes this acceleration vector through a sub-resolution titration firewall ($\epsilon = 1 \times 10^{-7}$). These events are integrated across a rolling temporal baseline by the **T-30 Momentum Engine** to compute the continuous **Fatigue Coefficient** ($F_c$):

$$F_c = \int_{T-30}^{T} \left| \frac{d^2\theta}{dt^2} \right| \cdot w(\theta, \nabla \mathbf{X}) \, dt$$

> **Technical Note on Discretization:** In the reference software implementation, the continuous temporal integral for the Fatigue Coefficient ($F_c$) is evaluated using a uniform 30-step rolling average proxy ($\frac{1}{k}\sum_{i=0}^{k-1} |\ddot{\theta}|$). This discretization effectively captures the long-term strategic signal of decay while maintaining zero processing overhead on standard distributed compute networks.

The resulting unit-less entropy vector ($\Phi$) provides a deterministic calculation of the system's **Remaining Useful Life (RUL)** before crossing non-linear phase transition tipping points.

## 2. Core Repository Architecture

* `Engine.py`: The stateless fiduciary kernel executing the second-derivative acceleration tracking, rolling fatigue integrals, and boundary phase state evaluations.
* `Forensic_kernel.py`: Handles the local cryptographic chain-of-custody validation layer via sequential, state-less SHA-256 row-pair hashing.
* `App.py`: Streamlit-driven operations interface displaying multi-zone phase space portraits and exporting signed `.sent` evidence bags.
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
   This writes `data/MACRO_SYSTEM_PLANETARY_STREAM.csv` (15,600 rows: 5,200 weekly steps × 3 observation zones).

3. **Launch the Operations Interface:**
   ```bash
   streamlit run App.py
   ```
   Open the local URL shown in the terminal (typically `http://localhost:8501`), upload `data/MACRO_SYSTEM_PLANETARY_STREAM.csv`, and inspect per-zone phase metrics, kinetic trajectory plots, and `.sent` evidence exports.

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

When `row_hash` is present, `Forensic_kernel.py` validates each zone independently: each row hash incorporates the prior row's seal (`prev_hash` chaining). Regenerate signed telemetry via `Data_Synthesizer.py` after any schema or hashing logic change.

## 7. Academic Citation

For live preprint URLs, see **Authoritative Preprints (SSRN Working Paper Series)** at the top of this document.

If you utilize this framework, the V50-S core metrics, or the scale-invariant phase space mathematics in an academic, institutional, or commercial research capacity, please cite the foundational paper:

```bibtex
@article{olaiya2026scale,
  title={Scale-Invariant Thermodynamic Attribution: Mapping Non-Linear Phase Transitions in Macro-Systems via Stateless Telemetry Auditing},
  author={Olaiya, Remi},
  journal={SSRN Electronic Journal},
  year={2026},
  publisher={Thohat Ventures Research Series},
  note={Operational Core: Core V50-S Sentinel Framework}
}
```

---

**THOHAT Ventures** — Auditor OS V50 Sentinel Reference Implementation
