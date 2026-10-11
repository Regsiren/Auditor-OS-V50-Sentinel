# eBPF Interceptor Specification — Topological Veto Path

**Protocol:** THOHAT-V50-SENTINEL  
**Schema companion:** [`sent_attestation.json`](sent_attestation.json) (Dual-Pillar v1.0)  
**Trigger condition:** `thermodynamic_state_vector.state_coordinate_omega >= 0.19` (Topological Veto)  
**Master whitepaper:** [doi:10.5281/zenodo.23185495](https://doi.org/10.5281/zenodo.23185495)

---

## 1. Purpose

When the AI Homeostasis auditor (baseline or ARIA adaptive) or a physical telemetry zone asserts a **Topological Veto**, the Sovereign Oracle Protocol may arm a Linux kernel-level interceptor. This document specifies the **reference architecture** for that interceptor. It is a design specification for implementers and auditors — not a shipped kernel module in this open-source release.

The open-source V50-S core **detects and attests** the veto by minting a Dual-Pillar schema v1.0 `.sent` bag. Production packet drop / socket severing is an optional closed-source deployment layer (Auditor OS Oracle) that consumes those bags.

---

## 2. Trigger Semantics (Schema v1.0)

| Schema field | Gate | Action |
|--------------|------|--------|
| `thermodynamic_state_vector.state_coordinate_omega < 0.07` | Homeostatic | Observe only; mint optional attestation |
| `0.07 ≤ state_coordinate_omega < 0.19` | Metastable | Soft warn; escalate telemetry sampling |
| `state_coordinate_omega ≥ 0.19` | **Topological Veto** | Mint `.sent` bag; arm eBPF interceptor policy |
| `thermodynamic_state_vector.sub_resolution_jitter_j_tau > 1e-7` | Micro-titration breach | Escalate sampling; contribute to veto evidence |

Arming requires all of:

1. Schema-valid Dual-Pillar v1.0 `.sent` bag with exactly four top-level blocks  
2. `thermodynamic_state_vector.state_coordinate_omega >= 0.19`  
   (equivalently `phase_boundary_state == "Topological Veto (≥ 0.19 Ω)"`)  
3. Operator-enabled intercept policy for the session / zone  
4. Valid `cryptographic_attestation.digital_signature` over `canonical_row_hash`  
   (`signature_algorithm` is `Ed25519` or `HMAC-SHA256-FALLBACK`)

Micro-titration evidence (non-arming by itself, but recorded in the bag):

- `thermodynamic_state_vector.sub_resolution_jitter_j_tau > 1e-7`

---

## 3. Architecture Overview

```
┌──────────────────────────┐  Ω ≥ 0.19 (schema v1.0)  ┌─────────────────────────┐
│ Baseline / ARIA auditor  │ ──────────────────────► │ .sent Attestation Bag   │
│ (userspace / PyTorch)    │   mint_sentinel_v10_*   │ (JSON Schema v1.0)      │
└──────────────────────────┘                         └───────────┬─────────────┘
                                                                  │ verify digital_signature
                                                                  ▼
                                                     ┌─────────────────────────┐
                                                     │ Policy Daemon (userspace)│
                                                     │ loads / updates maps     │
                                                     └───────────┬─────────────┘
                                                                  │
                    ┌─────────────────────────────────────────────┼──────────────────────────┐
                    ▼                                             ▼                          ▼
         ┌──────────────────┐                        ┌──────────────────┐        ┌──────────────────┐
         │ XDP program      │                        │ cgroup/sock_ops  │        │ Tracepoint audit │
         │ (ingress drop)   │                        │ (socket sever)   │        │ (immutable log)  │
         └──────────────────┘                        └──────────────────┘        └──────────────────┘
```

---

## 4. XDP_DROP Path (Ingress Containment)

**Attachment point:** NIC ingress via `BPF_PROG_TYPE_XDP` (native preferred; SKB mode as fallback).

**Behaviour when armed:**

1. Policy daemon writes the offending 5-tuple / session key into a pinned BPF hash map (`veto_sessions`).
2. XDP program looks up the packet's flow key.
3. On hit: return `XDP_DROP` immediately — no SKB allocation, no userspace handoff.
4. On miss: return `XDP_PASS`.

**Design constraints:**

- Map keys are session-scoped (not global blackholes) to avoid collateral damage.
- TTL / absolute expiry on map entries prevents permanent lockout after a recovery attestation.
- Drop counters are exported via per-CPU maps for observability.

---

## 5. Socket Severing Path (Egress / Established Flows)

Ingress drop alone does not tear down already-established sockets. Companion programs:

| Hook | Type | Action on veto |
|------|------|----------------|
| `sock_ops` | `BPF_PROG_TYPE_SOCK_OPS` | Mark sockets matching veto session; force close path |
| `cgroup/connect4` / `connect6` | cgroup egress | Reject new connects for vetoed cgroup / UID |
| `BPF_SOCK_OPS_TCP_LISTEN_CB` (optional) | listen path | Refuse new listeners for the compromised service identity |

**Sever semantics:** Prefer orderly `ECONNRESET` / force-close of matching sockets so peer stacks observe a hard abort rather than a silent blackhole that triggers long TCP timeouts.

---

## 6. Userspace Policy Daemon Contract

Minimal responsibilities:

1. Validate incoming `.sent` bags against `spec/sent_attestation.json` (four-block Dual-Pillar v1.0).
2. Verify `cryptographic_attestation.digital_signature` over `canonical_row_hash`  
   (Ed25519 via injected / HSM-backed key material, or HMAC-SHA256 fallback on lean hosts).
3. If `state_coordinate_omega >= 0.19` and intercept policy is enabled: update BPF maps; emit audit event.
4. Optionally inspect `sub_resolution_jitter_j_tau > 1e-7` for micro-titration escalation telemetry.
5. On subsequent Homeostatic attestation for the same session (`state_coordinate_omega < 0.07`): clear map entries (recovery).

---

## 7. Failure & Safety Modes

- **Fail-closed vs fail-open:** Deployments must document the chosen default. Ship-critical / safety-critical environments should fail-open for physical actuators and fail-closed only for the *untrusted inference channel* (model egress).
- **Attestation forgery:** Unsigned or invalid `.sent` bags must never arm maps.
- **Map exhaustion:** Cap `veto_sessions` size; overflow → alert, do not silently drop unrelated traffic.
- **Privilege:** Loading XDP / cgroup programs requires `CAP_BPF` / `CAP_NET_ADMIN`; the open-source repo does not ship privileged installers.

---

## 8. Relationship to Open-Source Scope

| Component | This repository |
|-----------|-----------------|
| $\Omega_t$ / $\Phi$ observer gates | ✅ `Engine.py`, `auditor_ai/sentinel_engine.py`, `auditor_ai/adaptive_engine.py` |
| Dual-Pillar `.sent` schema v1.0 | ✅ `spec/sent_attestation.json` |
| Portal / veto mint path | ✅ `Forensic_kernel.mint_sentinel_v10_*`, `App.py` |
| Demo veto trajectory | ✅ `examples/demo_residual_stream.py`, `examples/demo_adaptive_alignment.py` |
| Production eBPF programs / policy daemon | ❌ Closed-source / partner deployment |

This specification exists so independent reviewers can verify that the **mathematical veto** and the **kernel containment path** share the same $0.19$ threshold and Dual-Pillar schema v1.0 attestation contract.
