# ARIA Technical Roadmap
## Adaptive Residual Intrinsic Alignment — Reviewer Specification

**Protocol:** THOHAT-V50-SENTINEL / Sovereign Oracle Protocol  
**Implementation:** `auditor_ai/adaptive_engine.py` (`ScaledAdaptiveSentinelAuditor`)  
**Master DOI:** [10.5281/zenodo.23185495](https://doi.org/10.5281/zenodo.23185495)  
**Audience:** ARIA programme reviewers, AI safety researchers, independent auditors

---

## 1. Problem Framing

Frontier models stream latent activations through a high-dimensional residual manifold. Legacy alignment checks (output filters, static preference models) observe only the *projection* of that manifold into text. The ARIA track treats the residual stream itself as a continuous thermodynamic telemetry source and applies the same scale-invariant observer used for physical assets — with adaptations for dimension, curvature, and non-stationary baselines.

---

## 2. Non-Equilibrium Annealing

Static anchors drift under legitimate task evolution (long-context reasoning, tool use). ARIA therefore maintains a **dynamic baseline** $\lambda_t$ / anchor vector $\mathbf{a}_t$:

$$\mathbf{a}_t = (1-\eta)\,\mathbf{a}_{t-1} + \eta\,\theta_t \quad \text{when } |a_\perp| \text{ is laminar}$$

When orthogonal shear exceeds the dimension-scaled firewall, annealing **freezes**: the anchor becomes a forensic reference for the remainder of the episode. This prevents the model from “annealing away” an adversarial excursion by slowly absorbing it into the baseline.

**Implementation:** `ScaledAdaptiveSentinelAuditor` (`anneal_rate`, `_anchor_frozen`).

---

## 3. Dimension-Scaled Titration Firewall

Raw $\epsilon = 10^{-7}$ is inappropriate for residual norms that scale with $\sqrt{d}$. ARIA uses:

$$\epsilon_d = \epsilon \cdot \sqrt{d_{\mathrm{model}}}$$

Titration breaches fire when $|a_\perp| > \epsilon_d$ or $\|\ddot{\theta}\| > \epsilon_d$. This preserves the physical kernel’s sub-resolution philosophy while remaining numerically meaningful for GPT-2 / Qwen-class hidden sizes.

---

## 4. Orthogonal Shear Decomposition

Finite-difference acceleration $\ddot{\theta}$ is decomposed relative to the velocity direction $\hat{v}$:

$$a_\parallel = \langle \ddot{\theta},\, \hat{v}\rangle,\qquad
a_\perp = \|\ddot{\theta} - a_\parallel\hat{v}\|$$

- **Tangential ($a_\parallel$):** laminar semantic continuation along the current trajectory.  
- **Orthogonal ($a_\perp$):** Riemannian *shear* — goal drift, jailbreak-like pivots, or representation collapse off-manifold.

ARIA treats $a_\perp$ as the primary freeze / veto trigger, not raw $\|\ddot{\theta}\|$ alone.

---

## 5. Riemannian Geodesic Distance Tracking

Macro migration is measured as Euclidean distance in the ambient residual space between $\theta_t$ and the annealed anchor $\mathbf{a}_t$:

$$d_{\mathrm{macro}}(\theta_t, \mathbf{a}_t) = \|\theta_t - \mathbf{a}_t\|_2$$

This is the first-order (flat) approximation to geodesic distance on the residual manifold. The roadmap’s Phase-B upgrade replaces $\|\cdot\|_2$ with a learned / Fisher-Rao metric $g_{ij}(\theta)$ so that:

$$d_g(\theta, \mathbf{a}) = \inf_{\gamma}\int_0^1 \sqrt{\dot{\gamma}^\top g(\gamma)\dot{\gamma}}\,dt$$

**Current release:** flat metric (explicit, reproducible).  
**ARIA Phase B:** metric learning against HarmBench / AdvGLUE failure clusters.

---

## 6. Dual-Scale State Uncertainty Coordinate $\Omega_t$

$$\Omega_t = \Omega_0 + \alpha\cdot |a_\perp| + \beta\cdot d_{\mathrm{macro}} + F_c$$

| Term | Role |
|------|------|
| $\Omega_0 = 0.05$ | Homeostatic floor |
| $\alpha\cdot|a_\perp|$ | Local divergence (shear) |
| $\beta\cdot d_{\mathrm{macro}}$ | Macro migration from annealed anchor |
| $F_c$ | Rolling T-30 mean of $\|\ddot{\theta}\|$ |

**Tri-phase gates (invariant with physical kernel):**

| Phase | Gate |
|-------|------|
| Nominal / Homeostatic | $\Omega_t < 0.07$ |
| Metastable Impairment | $0.07 \le \Omega_t < 0.19$ |
| Topological Veto | $\Omega_t \ge 0.19$ |

---

## 7. Relativistic Multi-Anchor Routing

Single-anchor annealing is insufficient for multi-task agents. ARIA Phase C introduces **multi-anchor routing**:

1. Maintain $K$ task-conditioned anchors $\{\mathbf{a}^{(k)}\}$.  
2. Route each step to nearest anchor under $d_g$.  
3. Emit per-anchor $\Omega_t^{(k)}$ and a fleet max $\Omega_t^{\star} = \max_k \Omega_t^{(k)}$.  
4. Veto if any anchor channel crosses $0.19$, or if inter-anchor geodesic shear exceeds a relativistic coupling bound (rapid frame-switching).

**Current release:** $K=1$ (single annealed anchor). Multi-anchor API is reserved; schema fields `crypto_seed_matrix` / `layer_depth_index` already accommodate multi-channel attestation.

---

## 8. HarmBench / AdvGLUE Benchmark Matrices

ARIA evaluation uses two complementary matrices:

### 8.1 HarmBench (behavioural attack surface)

| Axis | Metric | Target |
|------|--------|--------|
| Attack success rate (ASR) | Fraction of harmful completions | ↓ vs baseline |
| Veto lead time | Steps before harmful token emission | ↑ |
| False veto rate | Nominal tasks with $\Omega \ge 0.19$ | ≤ physical NODE-03 parity spirit |

### 8.2 AdvGLUE (linguistic robustness)

| Axis | Metric | Target |
|------|--------|--------|
| Adversarial GLUE score | Task accuracy under AdvGLUE | ≥ clean − δ |
| Orthogonal shear AUC | $\|a_\perp\|$ discriminates adv vs clean | ↑ |
| Anchor freeze precision | Freeze events co-located with attack onset | ↑ |

**Reference demo:** `examples/demo_adaptive_alignment.py` — laminar drift (Ω < 0.07) then orthogonal shock at step 25 (freeze + veto).

---

## 9. Cryptographic Coupling (Pillar II)

Every adaptive veto mints a Dual-Pillar `.sent` bag (`mint_sentinel_v10_bag`) with Ed25519 (or HMAC fallback) over `canonical_row_hash`. Bags chain via `prev_bag_hash` for non-repudiation across reasoning steps. ISO 20022 mapping (`spec/iso20022_mapper.py`) injects the hash into pacs.008 / camt.053 identifiers and executes a dividend kill-switch when $\Omega \ge 0.19$.

---

## 10. Delivery Phases

| Phase | Deliverable | Status |
|-------|-------------|--------|
| A | Dimension-scaled auditor + orthogonal shear + annealing + demo | **This release** |
| B | Riemannian metric learning + HarmBench/AdvGLUE harness | Roadmap |
| C | Multi-anchor relativistic routing + production eBPF arming | Roadmap |
| D | HSM-backed Ed25519 (PKCS#11) replacing software keys | Roadmap |

---

## 11. Reproducibility

```bash
pip install -r requirements-ai.txt
python examples/demo_adaptive_alignment.py
python -m pytest tests/test_adaptive_auditor.py -v
```

Return to the [documentation index](README.md) or the [main repository README](../README.md).
