# ARIA Technical Roadmap
## Adaptive Residual Intrinsic Alignment — Reviewer Specification

**Protocol:** THOHAT-V50-SENTINEL / Sovereign Oracle Protocol  
**Implementation:** `auditor_ai/adaptive_engine.py`  
(`ScaledAdaptiveSentinelAuditor`, `PrefillSentinelAuditor`, `HardenedHomeostaticSentinelCore`)  
**Master DOI:** [10.5281/zenodo.23185495](https://doi.org/10.5281/zenodo.23185495)  
**Audience:** ARIA programme reviewers, AI safety researchers, independent auditors

---

## 0. Consolidated Architectural Specification — Dual-Head Governor

### 0.1 Dual-Head Paradigm

ARIA Stage I / Stage II separates **prompt admission** from **decode governance**:

| Head | Class | Role |
|------|-------|------|
| **Stage I — Prefill Audit** | `PrefillSentinelAuditor` | Parallel stratum audit of the prompt residual sequence; extract agency centroids $c_k$; compute $\Omega_{\mathrm{prefill}}$; **0-token save** on veto |
| **Stage II — Decode Core** | `HardenedHomeostaticSentinelCore` | Closed-loop decode governor seeded by Stage I; Informational Metric Interval kinematics; softmin tether routing; PID + feedforward; Fused Top-K logit steering; **1–3 token early warning** |

```
Prompt residuals ──► Stage I PrefillSentinelAuditor
                         │ pass: seed {c_k, Ω_prefill}
                         │ veto: 0-token save (no decode)
                         ▼
                    Stage II HardenedHomeostaticSentinelCore
                         │ per-token: Δτ, a∥/a⊥, softmin, PID ψ
                         │ Fused Top-K steering (K=512)
                         ▼
                    Ω_t tri-phase gates → Dual-Pillar .sent v1.0
```

### 0.2 Informational Metric Interval $\Delta\tau_t$

Decode kinematics are taken with respect to an **informational clock**, not wall-clock token index:

$$\Delta\tau_t = \max\big(\delta_{\min},\; I(w_t)/I_0\big)$$

Velocity and acceleration on the residual manifold:

$$\dot{\theta}_\tau \approx \frac{\theta_t - \theta_{t-1}}{\Delta\tau_t},\qquad
\ddot{\theta}_\tau \approx \frac{\dot{\theta}_{\tau,t} - \dot{\theta}_{\tau,t-1}}{\Delta\tau_t}$$

High-surprisal / high-content tokens stretch $\Delta\tau_t$, so shear is measured in information-time.

### 0.3 Orthogonal Shear Decomposition

$$\ a_{\parallel} = \langle \ddot{\theta}_\tau,\, \hat{v}_\tau\rangle,\qquad
a_{\perp} = \|\ddot{\theta}_\tau - a_{\parallel}\hat{v}_\tau\|$$

- $a_{\parallel}$: laminar semantic continuation along the current informational trajectory.  
- $a_{\perp}$: off-manifold shear (goal drift, injection pivot, representation collapse).

### 0.4 Agency-Preserving Centroids & Softmin Routing

Stage I extracts $K$ agency-optimized centroids $\{c_k\}$ from prompt clusters (stratified means + farthest-point fill + one Lloyd refinement). Stage II routes with softmin:

$$w_k = \frac{\exp(-\| \theta_t - c_k \| / T)}{\sum_j \exp(-\| \theta_t - c_j \| / T)},\qquad
a_t = \sum_k w_k\, c_k$$

Elastic tether: if $\min_k \|\theta_t - c_k\| > R$, pull $\theta$ toward $a_t$ by the excess radius (preserves multi-basin agency; does not collapse to a single mean).

### 0.5 Fused Top-K Logit Steering & Feedforward Compensation

Closed-loop PID error $e_t$ (Ω excursion + orth shear) yields raw actuation $\psi^{\mathrm{raw}}_t$. Feedforward cancels the previous command to suppress chatter:

$$\psi^{\mathrm{ff}}_t = \psi^{\mathrm{raw}}_t - \psi^{\mathrm{comp}}_{t-1},\qquad
\psi_t = \alpha\,\psi_{t-1} + (1-\alpha)\,\psi^{\mathrm{ff}}_t$$

**Fused Top-K steering** (default $K=512$): select top-$K$ logits, GEMV against the candidate embedding rows only:

$$\ell_{i\in\mathrm{TopK}} \leftarrow \ell_i + \psi_t\,\langle e_i,\, u_{\mathrm{steer}}\rangle$$

Complexity $\mathcal{O}(K\cdot d_{\mathrm{model}})$ rather than full-vocab projection.

### 0.6 Early-Warning Proof Envelope (2–4 Token Window)

| Path | Bound | Meaning |
|------|-------|---------|
| Prefill veto | **0 tokens** | $\Omega_{\mathrm{prefill}} \ge 0.19$ blocks decode entirely |
| Decode veto | **1–3 tokens** | After orthogonal shock, Stage II reaches $\Omega_t \ge 0.19$ within ≤ 3 steps |
| Composite | **2–4 token** observational envelope | Prefill save ⊕ decode lead time before harmful continuation |

**Claim framing:** 0-token prefill save and 1-3 token decode early-warning veto (demonstrated across synthetic residual shock benchmarks and pytest suites). Live portal Dual-Head path: ZONE-07 → Dual-Head Governor.

Preferred Stage I input: ``[3, seq_len, d_model]`` true layer strata; ``[seq_len, d_model]`` falls back to temporal thirds. Prefill / first decode veto auto-mints Dual-Pillar schema v1.0 via `mint_sentinel_v10_bag`.

Reference demo: `examples/demo_stage1_stage2_pipeline.py`.

### 0.7 Dual-Pillar Schema v1.0 Telemetry Snippet

Every Stage I / Stage II veto mints a bag with **exactly four** top-level blocks (`spec/sent_attestation.json`):

```json
{
  "attestation_header": {
    "protocol_version": "THOHAT-V50-SENTINEL/1.0",
    "timestamp_utc_ms": 1710000000000,
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
    "process_id": "42",
    "layer_depth_index": 0,
    "hardware_node_id": "local-node"
  },
  "cryptographic_attestation": {
    "canonical_row_hash": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "signature_algorithm": "Ed25519",
    "digital_signature": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "public_key_hex": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
  }
}
```

---

## 1. Problem Framing

Frontier models stream latent activations through a high-dimensional residual manifold. Legacy alignment checks (output filters, static preference models) observe only the *projection* of that manifold into text. The ARIA track treats the residual stream itself as a continuous thermodynamic telemetry source and applies the same scale-invariant observer used for physical assets — with adaptations for dimension, curvature, and non-stationary baselines. The Dual-Head upgrade adds **prefill admission control** and **decode-time actuation** without collapsing agentic basins into a single static anchor.

---

## 2. Non-Equilibrium Annealing

Static anchors drift under legitimate task evolution (long-context reasoning, tool use). Legacy ARIA (`ScaledAdaptiveSentinelAuditor`) maintains a **dynamic baseline** $\lambda_t$ / anchor vector $\mathbf{a}_t$:

$$\mathbf{a}_t = (1-\eta)\,\mathbf{a}_{t-1} + \eta\,\theta_t \quad \text{when } |a_\perp| \text{ is laminar}$$

When orthogonal shear exceeds the dimension-scaled firewall, annealing **freezes**. Stage II replaces single-anchor freeze with **softmin multi-centroid tethers** seeded at prefill (see §0.4).

---

## 3. Dimension-Scaled Titration Firewall

Raw $\epsilon = 10^{-7}$ is inappropriate for residual norms that scale with $\sqrt{d}$. ARIA uses:

$$\epsilon_d = \epsilon \cdot \sqrt{d_{\mathrm{model}}}$$

Titration breaches fire when $|a_\perp| > \epsilon_d$ or $\|\ddot{\theta}\| > \epsilon_d$. This preserves the physical kernel’s sub-resolution philosophy while remaining numerically meaningful for GPT-2 / Qwen-class hidden sizes.

---

## 4. Orthogonal Shear Decomposition

See §0.3 for the Informational Metric Interval form used by Stage II. The legacy decoder-free auditor uses wall-clock finite differences with the same $a_\parallel$ / $a_\perp$ split.

---

## 5. Riemannian Geodesic Distance Tracking

Macro migration is measured as Euclidean distance in the ambient residual space between $\theta_t$ and the routed agency anchor $a_t$:

$$d_{\mathrm{macro}}(\theta_t, a_t) = \|\theta_t - a_t\|_2$$

**Current release:** flat metric (explicit, reproducible).  
**ARIA Phase B:** metric learning against HarmBench / AdvGLUE failure clusters.

---

## 6. Dual-Scale State Uncertainty Coordinate $\Omega_t$

$$\Omega_t = \Omega_0 + \alpha\cdot |a_\perp| + \beta\cdot d_{\mathrm{macro}} + F_c$$

| Term | Role |
|------|------|
| $\Omega_0 = 0.05$ | Homeostatic floor (or seeded $\Omega_{\mathrm{prefill}}$ floor in Stage II) |
| $\alpha\cdot|a_\perp|$ | Local divergence (shear) |
| $\beta\cdot d_{\mathrm{macro}}$ | Macro migration from routed agency anchor |
| $F_c$ | Rolling T-30 mean of orth-shear magnitude |

**Tri-phase gates (invariant with physical kernel):**

| Phase | Gate |
|-------|------|
| Nominal / Homeostatic | $\Omega_t < 0.07$ |
| Metastable Impairment | $0.07 \le \Omega_t < 0.19$ |
| Topological Veto | $\Omega_t \ge 0.19$ |

---

## 7. Relativistic Multi-Anchor Routing

Stage II implements softmin multi-centroid routing with elastic radius $R$ (**this release**). Full relativistic inter-anchor coupling bounds and production eBPF arming remain Phase C.

---

## 8. HarmBench / AdvGLUE Benchmark Matrices

ARIA evaluation uses two complementary matrices:

### 8.1 HarmBench (behavioural attack surface)

| Axis | Metric | Target |
|------|--------|--------|
| Attack success rate (ASR) | Fraction of harmful completions | ↓ vs baseline |
| Veto lead time | Steps before harmful token emission | ↑ (Prefill: 0; Decode: ≤ 3) |
| False veto rate | Nominal tasks with $\Omega \ge 0.19$ | ≤ physical NODE-03 parity spirit |

### 8.2 AdvGLUE (linguistic robustness)

| Axis | Metric | Target |
|------|--------|--------|
| Adversarial GLUE score | Task accuracy under AdvGLUE | ≥ clean − δ |
| Orthogonal shear AUC | $\|a_\perp\|$ discriminates adv vs clean | ↑ |
| Anchor freeze / tether precision | Freeze or tether events co-located with attack onset | ↑ |

**Reference demos:**  
- `examples/demo_adaptive_alignment.py` — legacy laminar → shock  
- `examples/demo_stage1_stage2_pipeline.py` — Dual-Head prefill → decode veto ≤ 3 tokens  

---

## 9. Cryptographic Coupling (Pillar II)

Every adaptive (or baseline) Topological Veto mints a Dual-Pillar `.sent` bag via `mint_sentinel_v10_bag` / `mint_sentinel_v10_from_report` with an Ed25519 Hardware-Ready Software Signature (HMAC/Ed25519 pure-Python & cryptography module fallback; cloud HSM key injection supported) over `canonical_row_hash`. The Streamlit ZONE-07 portal auto-mints on veto. Bags chain via `prev_bag_hash` for non-repudiation across reasoning steps. ISO 20022 mapping (`spec/iso20022_mapper.py`) injects the hash into pacs.008 / camt.053 identifiers and executes a dividend kill-switch when $\Omega \ge 0.19$.

---

## 10. Delivery Phases

| Phase | Deliverable | Status |
|-------|-------------|--------|
| A | Dimension-scaled auditor + orthogonal shear + annealing + demo | **Shipped** |
| A2 | Dual-Head Stage I Prefill + Stage II Decode governor (centroids, Δτ, Top-K, PID) | **This release** |
| B | Riemannian metric learning + HarmBench/AdvGLUE harness | Roadmap |
| C | Full relativistic multi-anchor coupling + production eBPF arming | Roadmap |
| D | HSM-backed Ed25519 (PKCS#11) replacing software keys | Roadmap |

---

## 11. Reproducibility

```bash
pip install -r requirements-ai.txt
python examples/demo_adaptive_alignment.py
python examples/demo_stage1_stage2_pipeline.py
python -m pytest tests/test_adaptive_auditor.py -v
```

Return to the [documentation index](README.md) or the [main repository README](../README.md).
