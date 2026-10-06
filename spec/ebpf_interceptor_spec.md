# eBPF Interceptor Specification — Topological Veto Path

**Protocol:** THOHAT-V50-SENTINEL  
**Schema companion:** [`sent_attestation.json`](sent_attestation.json)  
**Trigger condition:** $\Omega_{\text{final}} \ge 0.19$ (Topological Bifurcation / Institutional Binary Veto Gate)  
**Master whitepaper:** [doi:10.5281/zenodo.23185495](https://doi.org/10.5281/zenodo.23185495)

---

## 1. Purpose

When the AI Homeostasis auditor (or a physical telemetry zone) asserts a **Topological Veto**, the Sovereign Oracle Protocol may arm a Linux kernel-level interceptor. This document specifies the **reference architecture** for that interceptor. It is a design specification for implementers and auditors — not a shipped kernel module in this open-source release.

The open-source V50-S core **detects and attests** the veto. Production packet drop / socket severing is an optional closed-source deployment layer (Auditor OS Oracle) that consumes `.sent` bags conforming to schema v1.0.

---

## 2. Trigger Semantics

| Symbol | Gate | Action |
|--------|------|--------|
| $\Omega_t < 0.07$ | Homeostatic | Observe only; mint optional attestation |
| $0.07 \le \Omega_t < 0.19$ | Metastable | Soft warn; escalate telemetry sampling |
| $\Omega_t \ge 0.19$ | **Topological Veto** | Mint `.sent` bag; arm eBPF interceptor policy |

Arming requires all of:

1. `flags.topological_veto == true` in a schema-valid `.sent` bag  
2. Operator-enabled intercept policy for the session / zone  
3. Valid `cryptographic_attestation.auth_sig` under the deployment salt

---

## 3. Architecture Overview

```
┌──────────────────────────┐     Ω_final ≥ 0.19      ┌─────────────────────────┐
│ SentinelActivationAuditor│ ──────────────────────► │ .sent Attestation Bag   │
│ (userspace / PyTorch)    │                         │ (JSON Schema v1.0)      │
└──────────────────────────┘                         └───────────┬─────────────┘
                                                                  │ verified sig
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

1. Validate incoming `.sent` bags against `spec/sent_attestation.json`.
2. Verify `auth_sig` using the deployment salt (never log the salt).
3. If `topological_veto && ebpf_intercept_armed`: update BPF maps; emit audit event.
4. On subsequent Homeostatic attestation for the same session: clear map entries (recovery).

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
| $\Omega_t$ / $\Phi$ observer gates | ✅ `Engine.py`, `auditor_ai/sentinel_engine.py` |
| `.sent` schema | ✅ `spec/sent_attestation.json` |
| Demo veto trajectory | ✅ `examples/demo_residual_stream.py` |
| Production eBPF programs / policy daemon | ❌ Closed-source / partner deployment |

This specification exists so independent reviewers can verify that the **mathematical veto** and the **kernel containment path** share the same $0.19$ threshold and attestation contract.
