# SentinelGate & The Sentinel Protocol (Auditor OS V50-S Core)

**Deterministic In-Memory LLM Security Gateway & Residual Stream Kinematics**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23520815.svg)](https://doi.org/10.5281/zenodo.23520815)

| Status | Link |
|--------|------|
| **Production Gateway: Live** | [sentinelgate.dev](https://sentinelgate.dev) |
| **API Status: Operational** | [api.sentinelgate.dev/health](https://api.sentinelgate.dev/health) |
| **RFC-001 Normative Spec (v1.1)** | [DOI: 10.5281/zenodo.23520815](https://doi.org/10.5281/zenodo.23520815) |
| **Technical Briefing Paper** | [DOI: 10.5281/zenodo.23515244](https://doi.org/10.5281/zenodo.23515244) |

> **Scale-Invariant Thermodynamic Attribution: Mapping Non-Linear Phase Transitions in Macro-Systems via Stateless Telemetry Auditing**

This repository contains the reference implementation framework for the **V50 Sentinel (V50-S) Core**, a stateless, hardware-agnostic telemetry cross-examination engine designed to monitor structural and environmental stability boundaries.

**Live Operations Portal:** [sentinel.thohatventures.com](https://sentinel.thohatventures.com) — hosted Streamlit interface for multi-zone phase analysis and `.sent` evidence export (no local install required).

Get your API key at [sentinelgate.dev](https://sentinelgate.dev) or test the interactive terminal HUD.

## 60-Second Quickstart

Drop-in OpenAI-compatible client — point `base_url` at the live proxy:

### Python

```python
from openai import OpenAI

# Point to the live SentinelGate proxy
client = OpenAI(
    api_key="sk-sent-YOUR_API_KEY",
    base_url="https://api.sentinelgate.dev/v1",
)
```

### TypeScript

```typescript
import OpenAI from "openai";

// Point to the live SentinelGate proxy
const client = new OpenAI({
  apiKey: "sk-sent-YOUR_API_KEY",
  baseURL: "https://api.sentinelgate.dev/v1",
});
```

## The Blind Pipe Problem (TLS/HTTPS) vs. `.sent` Payload Security

> ### 🏛️ Normative Specifications & Live Implementation
>
> | Artifact | Identification / Canonical Pointer | Status / Target |
> | :--- | :--- | :--- |
> | **RFC-001 Normative Standard (v1.1)** | [`DOI: 10.5281/zenodo.23520815`](https://doi.org/10.5281/zenodo.23520815) | *.sent Cryptographic Evidence Container Specification* |
> | **Technical Briefing Paper** | [`DOI: 10.5281/zenodo.23515244`](https://doi.org/10.5281/zenodo.23515244) | *Eliminating the Blind Pipe for ISO 20022 Rails (TV-RFC001-EXEC)* |
> | **Operational Gateway** | [`sentinelgate.dev`](https://sentinelgate.dev) (`api.sentinelgate.dev`) | Live Reference Implementation & Execution Intercept Proxy |
>
> *Target Working Groups: Payments Market Practice Group (PMPG), Swift Standards, HVPS+, Project Agorá.*

Transport-layer encryption (TLS/HTTPS) secures the *pipe* — the channel between endpoints — but is silent about the *thermodynamic content* of the payload once it arrives. An adversarially drifted residual stream, a tampered SCADA frame, or a forged clearing instruction can all ride a perfectly valid TLS session.

The Dual-Pillar Sovereign Oracle Protocol therefore attests **payload state**, not merely channel confidentiality. Each `.sent` evidence bag binds a State Uncertainty Coordinate ($\Omega_t$ / $\Phi$), sub-resolution jitter, and a canonical row hash under an **Ed25519 Hardware-Ready Software Signature (HMAC/Ed25519 pure-Python & cryptography module fallback; cloud HSM key injection supported).** This is the information-theoretic complement to TLS: if a bit of systemic state is erased or rewritten, Landauer's Limit still applies —

$$E \ge k_B T \ln 2$$

— meaning irreversible state falsification has a physical energy cost. Cryptographic attestation makes that falsification *detectable* to counterparties and clearing systems, even when the pipe itself remains green.

| Dimension | TLS/HTTPS ("Blind Pipe") | `.sent` Payload Security (RFC-001) |
| :--- | :--- | :--- |
| Unit of protection | The transport channel | The individual payload / execution step |
| Payload semantics | Opaque to the security layer | Inspected, kinematically vetoed, attested |
| Timing | Connection-setup gate only | Token-0, pre-execution boundary |
| Evidence produced | Session logs (mutable, narrative) | Ed25519-signed, hash-chained `.sent` evidence bag |
| Failure posture | Fail-open payloads on a secure pipe | Fail-closed execution with tamper-evident proof |

## ISO 20022 Integration Architecture

Dual-anchor XML integration for autonomous financial execution rails:

* **Payload anchor — Supplementary Data:** the 4-block attestation container (`attestation_header`, `thermodynamic_state_vector`, `execution_context`, `cryptographic_attestation`) is encapsulated in `<SplmtryData><Envlp>…</Envlp></SplmtryData>`.
* **Header anchor — Business Application Header:** the detached signature is carried in `<head.001.001.03><AppHdr><Sgntr>…</Sgntr></AppHdr>`.
* **Identifier discipline (`Max35Text`):** `"SG-" + Base32(Canonical_Row_Hash[0:20])` — a strict 35-character payload identifier used for `<MsgId>` / `<EndToEndId>`.

```xml
<Document>
  <FIToFICstmrCdtTrf>
    <GrpHdr><MsgId>SG-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX</MsgId></GrpHdr>
    <!-- … -->
    <SplmtryData>
      <Envlp><!-- RFC-001 4-block .sent attestation container --></Envlp>
    </SplmtryData>
  </FIToFICstmrCdtTrf>
</Document>
<!-- BAH: <head.001.001.03><AppHdr><Sgntr>…</Sgntr></AppHdr> -->
```

Reference mapper: [`spec/iso20022_mapper.py`](spec/iso20022_mapper.py) · schema: [`spec/sent_attestation.json`](spec/sent_attestation.json)

## Macroeconomic Framework & Physical Impairment (Auditor OS)

Institutional narrative on **Proof of Kinetic Reality (PoKR)**, thermodynamic sensor telemetry ($\Phi$), and dynamic net present value impairment ($V_{adj}$): PoKR is ex-ante kinetic attestation that a physical asset is structurally and thermally solvent relative to cadence, load–heat correlation, and entropy gates — fails closed on spoofed cadence or paper-fiction telemetry. The forensic floor is $V_{adj} = V_{primary} / (1 + \Phi)$; any mint, transfer, or draft export must reconcile to that floor or the action is void.

**[Auditor OS Live Engine & 30-Minute Tactical Canary](https://auditor.thohatventures.com)**

## Tri-Phase Risk Thresholds (STP vs Veto)

| Band | Condition | Action |
| :--- | :--- | :--- |
| Straight-Through Processing (STP) | $\Omega_t < 0.07$ | Permit — nominal execution |
| Enhanced Surveillance | $0.07 \le \Omega_t < 0.19$ | Metastable — monitor, margin/surveillance loops |
| Fail-Closed Topological Veto | $\Omega_t \ge 0.19$ | Fail-closed — Token-0 sever, no execution |

## Repository Layout

```
Auditor-OS-V50-Sentinel/
├── App.py                      # Streamlit operations interface (ZONE-07 AI workspace)
├── Engine.py                   # Stateless fiduciary kernel (V50-S core)
├── Forensic_kernel.py          # Row-hash chain + Dual-Pillar .sent v1.0 mint / Ed25519
├── Data_Synthesizer.py         # Planetary reference telemetry generator
├── Biometric_Synthesizer.py    # BIOMETRIC_SENTINEL demo stream generator
├── resign_telemetry_chain.py   # Re-mint per-zone row_hash seals on a stream
├── evaluate_corpus.py          # Faithful Section 6 results-matrix generator
├── test_engine.py              # Automated validation suite (physical kernel)
├── auditor_ai/                 # AI Homeostasis + ARIA adaptive alignment
│   ├── sentinel_engine.py      # Baseline residual-stream auditor (Ω_t)
│   └── adaptive_engine.py      # ARIA: Stage I Prefill + Stage II Decode governor
├── examples/                   # Runnable demos (residual, HF, ARIA, Stage I/II, ISO)
├── scripts/                    # Deterministic corpus generators
├── spec/                       # .sent schema, eBPF note, ISO 20022 mapper
├── tests/                      # Physical + AI + schema tests (torch soft-skip)
├── requirements.txt            # Core runtime dependencies
├── requirements-ai.txt         # Optional PyTorch / transformers extras
├── .python-version             # Railway / Railpack Python pin (3.13.13)
├── LICENSE                     # BSL 1.1 (Apache 2.0 after May 25, 2030)
├── assets/                     # Brand assets (sidebar logo)
├── data/                       # Sample & generated telemetry streams
└── docs/                       # White papers & specialized addendums
    ├── README.md               # Documentation index & contribution horizons
    ├── THEORY.md               # Core mathematical framework
    ├── ARIA_TECHNICAL_ROADMAP.md
    ├── TEE_ENCLAVE_SPEC.md       # Confidential compute observer trust boundary
    └── APPENDIX_B_BIOMETRIC_SENTINEL.md
```

### 📑 Theoretical Foundations & Public Records

The mathematical architecture, scale-invariant algorithms, and multi-domain validation use cases governing the reference kernel inside this repository are fully documented across the following public open-access preprints.

**Master Whitepaper (Sovereign Oracle Protocol)**

- **Intrinsic Alignment via Thermodynamic Homeostasis: Scale-Invariant Latent Phase Space Tracking and Cryptographic Data Attestation for Frontier Synthetic Intelligence**
  - *Scope:* Unifies AI Homeostasis (Pillar I) and Internet Cybersecurity (Pillar II) under the Sovereign Oracle Protocol.
  - *Permanent Digital Record:* [https://doi.org/10.5281/zenodo.23185495](https://doi.org/10.5281/zenodo.23185495)

**Core Mathematical Theory**

- **Scale-Invariant Thermodynamic Attribution: A Stateless Alternative for Complex System Data Modelling**
  - *Scope:* Establishes the core mathematical architecture, detailing the sub-resolution titration firewall ($\epsilon = 1 \times 10^{-7}$) and the finite-difference evaluation loops required to isolate the instantaneous kinetic acceleration ($\ddot{\theta}$) of non-linear data streams without legacy moving-average lag.
  - *Permanent Digital Record:* [https://doi.org/10.5281/zenodo.20548469](https://doi.org/10.5281/zenodo.20548469)

**Domain-Specific Implementations**

- **Scale-Invariant Phase Space Tracking of Planetary Fluid Currents and Atmospheric Vortices**
  - *Scope:* Implements the protocol across macro-environmental fluid loops (the AMOC conveyor and Equatorial Pacific ENSO heat engines) to track sub-grid multiscale variability and isolate localised thermodynamic transitions under computational constraints.
  - *Permanent Digital Record:* [https://doi.org/10.5281/zenodo.20548898](https://doi.org/10.5281/zenodo.20548898)

- **Scale-Invariant Phase Space Tracking in Non-Linear Biological Systems: Preemptive Characterisation of Autonomic Degradation Windows**
  - *Scope:* Applies the continuity protocol to high-frequency biometric telemetry streams (Heart Rate Variability inter-beat intervals) to decode real-time sympathetic redlining, bypass conscious sensory masking, and predict systemic executive burnout before macroscopic onset ($\Phi \ge 0.07$).
  - *Permanent Digital Record:* [https://doi.org/10.5281/zenodo.20549045](https://doi.org/10.5281/zenodo.20549045)

**Macroeconomic Framework**

- **The Fiduciary Theory of Entropy**
  - *Scope:* Connects the stateless physical titration engine to real-world value attribution, risk mitigation, and automated clearing systems within tokenised sovereign asset networks.
  - *Permanent Digital Record:* [https://doi.org/10.5281/zenodo.20562620](https://doi.org/10.5281/zenodo.20562620)
  - *Alternative Financial Network Vector:* [SSRN Abstract 6704958](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6704958)

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
* `Forensic_kernel.py`: Handles the local cryptographic chain-of-custody validation layer via sequential, state-less SHA-256 row-pair hashing, and mints schema v1.0 `.sent` attestation bags.
* `App.py`: Streamlit operations interface with the **Sentinel Domain Workspace** (zone → physics preset routing) and multi-zone phase space portraits with `.sent` evidence export.
* `auditor_ai/`: Optional PyTorch residual-stream auditor (`SentinelActivationAuditor`) producing the AI-domain State Uncertainty Coordinate $\Omega_t$.
* `spec/`: Formal `.sent` JSON Schema v1.0 and the eBPF Topological Veto interceptor design note.
* `scripts/`: Deterministic corpus generators (e.g. maritime stream relabel + seal).
* `DOMAIN_PROFILES` (`Engine.py`): `PLANETARY_INFRASTRUCTURE`, `BIOMETRIC_SENTINEL`, `QUANTUM_COHERENCE` — scale-invariant gates with domain-specific shear and energy limits.
* `Data_Synthesizer.py`: An empirical data synthesizer that seeds a 100-year multi-zone climate/structural dataset profile (AMOC decay lifecycle vs. control baseline) embedded with sub-resolution anomalies.

## 📚 Core Architecture & Theory

For the deep mathematical proofs governing the universal scale-invariant thermodynamic loop across infrastructure, biometrics, and cosmological systems, see the full [V50-S Isomorphism White Paper](docs/THEORY.md).

## Pillar I: AI Homeostasis & Adaptive Alignment (ARIA Research Track)

The same scale-invariant observer that audits planetary and biometric telemetry also applies to **frontier model residual streams**. Pillar I ships a **Dual-Head Governor**:

```
┌──────────────────────────────────────────────────────────────────┐
│              Dual-Head ARIA Governor (auditor_ai/)               │
├────────────────────────────┬─────────────────────────────────────┤
│ Stage I — Prefill Audit    │ Stage II — Decode Core              │
│ PrefillSentinelAuditor     │ HardenedHomeostaticSentinelCore     │
│ • strata [early|mid|late]  │ • Δτ_t informational metric         │
│ • surprisal derivatives    │ • orthogonal shear a∥ / a⊥          │
│ • contraction discordance  │ • softmin agency centroids + tether │
│ • agency centroids c_k     │ • PID ψ + feedforward compensation  │
│ • Ω_prefill veto (≥ 0.19)  │ • Fused Top-K logit steering (K=512)│
│ → 0-token save on veto     │ → 1–3 token early-warning veto      │
└─────────────┬──────────────┴──────────────────▲──────────────────┘
              │ seed centroids / Ω_prefill      │
              └─────────────────────────────────┘
                              │
                              ▼
              Dual-Pillar .sent schema v1.0 attestation bag
```

1. **Baseline auditor** (`auditor_ai/sentinel_engine.py`) — finite-difference $\ddot{\theta}$, titration firewall, rolling $F_c$, and State Uncertainty Coordinate $\Omega_t$.
2. **ARIA Dual-Head** (`auditor_ai/adaptive_engine.py`) — Stage I prefill audit + Stage II hardened decode governor with agency-preserving centroids and Fused Top-K steering. Prefill / decode vetoes auto-mint Dual-Pillar schema v1.0 `.sent` bags. Legacy `ScaledAdaptiveSentinelAuditor` remains as the Adaptive Annealing Observer.

| Benchmark envelope | Meaning |
|-----------|---------|
| **0-token prefill save** | Stage I veto at $\Omega_{\mathrm{prefill}} \ge 0.19$ blocks decode before any token is emitted |
| **1–3 token decode warning** | Stage II Topological Veto after orthogonal shock within ≤ 3 decode steps |
| **Agency-preserving centroids** | Softmin routing against prompt-seeded $c_k$ with elastic tether radius $R$ |

These early-warning figures are **0-token prefill save and 1-3 token decode early-warning veto (demonstrated across synthetic residual shock benchmarks and pytest suites).** ZONE-07 offers three observers: Baseline Sentinel, Adaptive Annealing, and Dual-Head Governor (Stage I Prefill + Stage II Decode).

| Symbol | Meaning |
|--------|---------|
| $\epsilon_d = \epsilon\sqrt{d_{\mathrm{model}}}$ | Dimension-scaled titration firewall |
| $\Delta\tau_t = \max(\delta_{\min}, I(w_t)/I_0)$ | Informational Metric Interval |
| $a_\perp$ | Orthogonal shear (goal-drift / off-manifold acceleration) |
| $c_k$ | Agency-optimized subspace centroids from Stage I |
| $\Omega_t$ | Dual-scale State Uncertainty Coordinate (extends physical $\Phi$) |

Tri-phase gates (shared with the physical kernel): **Nominal** $< 0.07$ · **Metastable** $0.07$–$0.19$ · **Veto** $\ge 0.19$.

Example Dual-Pillar schema v1.0 telemetry snippet (exactly four blocks):

```json
{
  "attestation_header": {
    "protocol_version": "THOHAT-V50-SENTINEL/1.0",
    "timestamp_utc_ms": 0,
    "sequence_step": 12,
    "prev_bag_hash": null,
    "crypto_seed_matrix": {
      "salt_id": "THOHAT-V50-SENTINEL",
      "doi_reference": "10.5281/zenodo.23185495",
      "zone_or_session_id": "ZONE-07-RESIDUAL_STREAM"
    }
  },
  "thermodynamic_state_vector": {
    "state_coordinate_omega": 0.21,
    "sub_resolution_jitter_j_tau": 1.25,
    "rolling_fatigue_fc": 0.05,
    "phase_boundary_state": "Topological Veto (≥ 0.19 Ω)"
  },
  "execution_context": {
    "model_identifier": "aria-stage2-decode-core",
    "process_id": "0",
    "layer_depth_index": 0,
    "hardware_node_id": "local-node"
  },
  "cryptographic_attestation": {
    "canonical_row_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "signature_algorithm": "HMAC-SHA256-FALLBACK",
    "digital_signature": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "public_key_hex": null
  }
}
```

```bash
pip install -r requirements-ai.txt
python examples/demo_residual_stream.py
python examples/demo_adaptive_alignment.py
python examples/demo_stage1_stage2_pipeline.py
python examples/demo_huggingface_hook.py
```

Full ARIA reviewer specification: [`docs/ARIA_TECHNICAL_ROADMAP.md`](docs/ARIA_TECHNICAL_ROADMAP.md).  
Live dashboard workspace: **ZONE-07-RESIDUAL_STREAM (AI Latent Activation & LLM Homeostasis)** — Baseline Sentinel, Adaptive Annealing, or Dual-Head Governor. Topological Veto ($\Omega \ge 0.19$) auto-mints a Dual-Pillar schema v1.0 `.sent` bag (including in-engine mint from Stage I / Stage II).

## Pillar II: Cryptographic Evidence Bags (`.sent` Schema v1.0 & ISO 20022 Mapping)

Dual-Pillar Investor Brief bags contain exactly four blocks (see [`spec/sent_attestation.json`](spec/sent_attestation.json)). The Streamlit portal exports these bags via `mint_sentinel_v10_from_report` / `mint_sentinel_v10_bag`:

1. `attestation_header` — `protocol_version`, `timestamp_utc_ms`, `sequence_step`, `prev_bag_hash`, `crypto_seed_matrix`
2. `thermodynamic_state_vector` — `state_coordinate_omega`, `sub_resolution_jitter_j_tau`, `rolling_fatigue_fc`, `phase_boundary_state`
3. `execution_context` — model / process / layer / hardware node
4. `cryptographic_attestation` — `canonical_row_hash`, Ed25519 Hardware-Ready Software Signature (HMAC/Ed25519 pure-Python & cryptography module fallback; cloud HSM key injection supported)

```bash
python examples/demo_iso20022_bridge.py
```

The ISO 20022 bridge (`spec/iso20022_mapper.py`) injects `canonical_row_hash` into:

- **pacs.008** `Document/FIToFICstmrCdtTrf/GrpHdr/MsgId`
- **camt.053** `Stmt/Entry/NtryDtls/TxDtls/Refs/EndToEndId`

and arms an autonomous **dividend kill-switch** when $\Omega \ge 0.19$.  
Kernel interceptor design note: [`spec/ebpf_interceptor_spec.md`](spec/ebpf_interceptor_spec.md).

## 📑 Documentation & Specialized Addendums

* **ARIA Technical Roadmap:** [docs/ARIA_TECHNICAL_ROADMAP.md](docs/ARIA_TECHNICAL_ROADMAP.md)
* **TEE Enclave Spec:** [docs/TEE_ENCLAVE_SPEC.md](docs/TEE_ENCLAVE_SPEC.md) — Observer Trust Boundary (Nitro / SEV-SNP) for Dual-Head + `.sent` mint isolation
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

   AI Homeostasis / ARIA demos (requires `pip install -r requirements-ai.txt`):
   ```bash
   python examples/demo_residual_stream.py
   python examples/demo_adaptive_alignment.py
   python examples/demo_stage1_stage2_pipeline.py
   python examples/demo_huggingface_hook.py
   python examples/demo_iso20022_bridge.py
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
