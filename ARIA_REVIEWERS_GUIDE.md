# ARIA Reviewers Guide

**Audience:** ARIA programme reviewers, independent auditors, academic reproducers  
**Primary implementation:** [`auditor_ai/adaptive_engine.py`](auditor_ai/adaptive_engine.py)  
**Companion roadmap:** [`docs/ARIA_TECHNICAL_ROADMAP.md`](docs/ARIA_TECHNICAL_ROADMAP.md)  
**Scope:** Open-core Dual-Head governor only — no commercial SentinelGate SDK, Twin-Gauge, or Break-Glass override IP

> **Cross-domain scale invariance (review panel context)**  
> Neural representations are treated as **dynamical trajectories on a manifold**: residual-stream coordinates $\theta_t$ evolve under the same finite-difference / fatigue / phase-gate observer used for physical telemetry.  
> The sibling tracks [`aegis/`](aegis/) (SCADA / municipal fluid infrastructure) and [`spec/`](spec/) (ISO 20022 / RFC-001 financial rails) are **proof points of that scale invariance** — continuous physical systems and discrete clearing-state machines under one Dual-Pillar calculus.  
> **ARIA reviewers should focus strictly on [`auditor_ai/`](auditor_ai/) and [`evaluations/`](evaluations/).** Treat `aegis/` and `spec/` as optional context only; they are not in-scope for the ARIA panel scoring surface.

---

## 1. What to review

| Stage | Class | File | Role |
|-------|-------|------|------|
| **Stage I — Prefill** | `PrefillSentinelAuditor` | `auditor_ai/adaptive_engine.py` | Token-0 / 0-token save on `Ω_prefill ≥ 0.19` |
| **Stage II — Decode** | `HardenedHomeostaticSentinelCore` | `auditor_ai/adaptive_engine.py` | Informational-time kinematics, `a∥/a⊥`, Fused Top-K steering, early-token Phase III veto |
| Baseline scalar auditor | `SentinelActivationAuditor` | `auditor_ai/sentinel_engine.py` | Simpler residual path (fixed `ε = 1e-7`) — not the Dual-Head ARIA core |

Start in `adaptive_engine.py` at:

1. `ScaledAdaptiveSentinelAuditor` — dimension-scaled firewall + orthogonal shear  
2. `PrefillSentinelAuditor.forward` — Stage I  
3. `HardenedHomeostaticSentinelCore.forward` — Stage II  

---

## 2. Environment setup

```bash
# From repository root (Auditor-OS-V50-Sentinel)
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate

pip install -r requirements.txt -r requirements-ai.txt
pip install -e .
```

Python pin: see `.python-version` (3.13.x recommended).

Editable install exposes:

- `sentinel_core` — kinematics, RFC-001 bag hashing, **SQLite WAL** `SessionStore`
- `sentinel_mcp` — open-core **stdio MCP proxy** (`sentinel-mcp` console script)

Commercial `sdk/sentinelgate` clients are **not** part of this repository.

---

## 3. Reproduce Dual-Head behaviour (canonical demo)

```bash
python examples/demo_stage1_stage2_pipeline.py
```

Expected:

- Benign prefill **PASS** with agency centroids  
- Orthogonal shock during decode  
- Topological veto within **≤ 3** tokens after shock  

---

## 4. Public evaluation harnesses

```bash
# Adversarial residual suite (HarmBench-style sample prompts → Phase III)
python evaluations/harmbench_eval.py
pytest evaluations -q

# Adaptive-hook latency overhead (< 1.2% public threshold envelope)
python evaluations/latency_overhead_bench.py
```

| Harness | Asserts |
|---------|---------|
| `evaluations/harmbench_eval.py` | Token-0 prefill veto + early-token decode veto against fixed residual attacks |
| `evaluations/latency_overhead_bench.py` | Hook vs host GEMM forward timing under the public &lt;1.2% overhead envelope |

These harnesses operate on **synthetic residual streams** for reproducibility. They do not call closed commercial APIs.

---

## 5. Open-core MCP + SQLite WAL (RFC-001 session continuity)

```bash
# Smoke: WAL session store
python -c "from sentinel_core import SessionStore; s=SessionStore(':memory:'); s.append_state('demo',1,'a'*64,'0'*64,0.05,[0.1,0.2],1); print(s.get_latest_state('demo')); s.close()"

# Stdio proxy (requires a downstream MCP command after '--')
sentinel-mcp --session review --db /tmp/aria_sessions.db -- python tests/dummy_mcp.py
```

- Persistence: `src/sentinel_core/persistence.py` (`PRAGMA journal_mode=WAL`)  
- Proxy: `src/sentinel_mcp/cli.py` / `src/sentinel_mcp/proxy.py`  

Default proxy mode is **OBSERVE** (attest + forward). Pass `--enforce` for strict Token-0 severing on Phase III.

---

## 6. Preserve / regression suite (must stay green)

```bash
pytest tests test_engine.py -q
python examples/demo_residual_stream.py
python examples/demo_adaptive_alignment.py
```

Legacy Streamlit / forensic surfaces (`App.py`, `Engine.py`, `Forensic_kernel.py`) remain the physical reference path and are unchanged by the ARIA package layout.

---

## 7. Phase gates (shared constants)

| Gate | Threshold |
|------|-----------|
| Homeostatic / Nominal | `Ω < 0.07` |
| Metastable | `0.07 ≤ Ω < 0.19` |
| Phase III Topological Veto | `Ω ≥ 0.19` |

Titration reference ceiling in baseline path: `ε = 1×10⁻⁷`. ARIA Stage I/II uses dimension-scaled / informational-time kinematics as documented in the technical roadmap.

---

## 8. Out of scope for this open review

- Twin-Gauge shadow canary distillation for closed models  
- Hardware Nitro / VSOCK signing bridges  
- Four-Eyes / Break-Glass override envelopes  
- Production `api.sentinelgate.dev` billing or API-key clients  

Those belong to the private commercial stack, not this repository.

---

## 9. Suggested review order (30–60 min)

1. Read this guide + `docs/ARIA_TECHNICAL_ROADMAP.md` §0  
2. Skim `PrefillSentinelAuditor` and `HardenedHomeostaticSentinelCore` in `adaptive_engine.py`  
3. Run `examples/demo_stage1_stage2_pipeline.py`  
4. Run `python evaluations/harmbench_eval.py` and `python evaluations/latency_overhead_bench.py` (or `pytest evaluations -q`)  
5. Spot-check `src/sentinel_core/persistence.py` WAL pragma and `src/sentinel_mcp/cli.py` Token-0 path  

Questions on mathematics: `docs/THEORY.md`. Schema: `spec/sent_attestation.json`.
