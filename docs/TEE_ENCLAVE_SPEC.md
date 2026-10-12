# TEE Enclave Specification — Observer Trust Boundary

**Protocol:** THOHAT-V50-SENTINEL / Sovereign Oracle Protocol  
**Companion:** Dual-Head Governor (`PrefillSentinelAuditor`, `HardenedHomeostaticSentinelCore`)  
**Schema:** [`spec/sent_attestation.json`](../spec/sent_attestation.json)  
**Master DOI:** [10.5281/zenodo.23185495](https://doi.org/10.5281/zenodo.23185495)

---

## 1. Purpose

This document specifies the **Observer Trust Boundary** for confidential compute deployments of Auditor OS V50-S. The open-source repository ships the Dual-Head governor and Dual-Pillar `.sent` mint path in userspace Python. Production isolation of that observer against a compromised root host is an optional closed-source / partner deployment layer (Auditor OS Oracle) using:

- **AWS Nitro Enclaves**, or  
- **AMD SEV-SNP** confidential virtual machines (and equivalent TEE CVMs)

This is a design specification for implementers and auditors — not a shipped enclave image in this open-source release.

---

## 2. Threat Model

| Adversary | Capability | Goal |
|-----------|------------|------|
| Compromised root host / hypervisor guest agent | Read/write ordinary process memory, replace PyTorch hooks, kill mint threads | Suppress or forge Ω telemetry; prevent `.sent` emission |
| Multi-tenant noisy neighbour | Steal HSM API quota / induce signing latency | DoS attestation path |
| Network MITM | Observe TLS pipe | Irrelevant to payload attestation if `.sent` signatures verify |

**Out of scope for this TEE layer:** dishonest model weights *inside* the enclave (supply-chain), physical side channels beyond the TEE product claims, and social engineering of key custodians.

---

## 3. Isolation Model

```
┌──────────────────────────── Root Host (untrusted) ───────────────────────────┐
│  Orchestrator / Streamlit / agent runtime                                     │
│       │ vsock / attested channel                                              │
│       ▼                                                                       │
│  ┌────────────────── TEE / Confidential VM (trusted observer) ─────────────┐ │
│  │  PrefillSentinelAuditor  (Stage I)                                       │ │
│  │  HardenedHomeostaticSentinelCore (Stage II)                              │ │
│  │  Forensic_kernel.mint_sentinel_v10_bag / ephemeral session keys          │ │
│  │  PyTorch forward hooks bound to enclave-resident model shard             │ │
│  │  Ephemeral Ed25519 session keys (HSM-bound public key attestation)       │ │
│  └───────────────────────────────┬─────────────────────────────────────────┘ │
│                                  │ signed .sent bags only                    │
└──────────────────────────────────┼───────────────────────────────────────────┘
                                   ▼
                     Counterparties / eBPF policy / ISO 20022 bridge
```

### 3.1 Guarantees (when correctly deployed)

1. **Hook integrity:** PyTorch forward hooks that feed Stage I / Stage II run inside the enclave memory space. A compromised root host process **cannot alter or suppress** those hooks without breaking the attested enclave measurement.
2. **Mint non-suppression:** Dual-Pillar `.sent` bag construction and signing occur inside the enclave. Host compromise cannot silently disable minting prior to signature without failing remote attestation / PCR checks.
3. **Key separation:** Root HSM master keys remain outside the hot path; the enclave holds **ephemeral session keys** (`generate_ephemeral_session_key`) whose public keys are bound by the root HSM signature in `attestation_header.crypto_seed_matrix`.
4. **Egress minimization:** Only schema-valid signed `.sent` JSON (and optional sealed telemetry digests) leave the enclave. Raw residual tensors need not be exported.

### 3.2 Non-guarantees

- TEE product firmware bugs or host physical attacks beyond vendor claims.  
- Operator misconfiguration (running the governor on the host “for convenience”).  
- Verification skipped by counterparties — bags only help if consumers check signatures.

---

## 4. Attestation Flow

1. Enclave boots; PCR / attestation document is produced (Nitro attestation doc, SEV-SNP report).  
2. Operator / KMS releases wrapping keys only to attested measurements that include the Dual-Head governor hash.  
3. Enclave unwraps or mints an ephemeral session key bound to `root_hsm_key_id`.  
4. Per veto: mint Dual-Pillar v1.0 bag with ephemeral signature + root binding metadata.  
5. Host forwards bags; verifiers check (a) schema, (b) ephemeral signature, (c) root binding, (d) enclave attestation freshness.

---

## 5. Relationship to Ephemeral Session Keys

High-throughput multi-tenant nodes must not invoke the HSM on every bag. The ephemeral session architecture in `Forensic_kernel.generate_ephemeral_session_key`:

- Signs locally at software Ed25519 speed (design target: 10,000+ req/sec per node).  
- Binds the ephemeral public key under the root HSM identity once per session (`validity_hours`, default 1).  
- Records binding fields under `attestation_header.crypto_seed_matrix` without exposing raw HSM secret material.

Inside a TEE, the ephemeral private key never leaves enclave memory; only the public key and root binding signature are visible to the host.

---

## 6. Open-Source Scope

| Component | This repository |
|-----------|-----------------|
| Dual-Head governor + slow-burn geodesic bound | ✅ `auditor_ai/adaptive_engine.py` |
| Dual-Pillar mint + ephemeral session keys | ✅ `Forensic_kernel.py` |
| True 3-strata HF hook demo | ✅ `examples/demo_huggingface_hook.py` |
| TEE enclave images / Nitro/SEV deployers | ❌ Closed-source / partner deployment |
| Remote attestation verifier service | ❌ Closed-source / partner deployment |

---

## 7. Reviewer Checklist

- [ ] Confirm Stage I / Stage II veto paths still mint schema v1.0 bags when run outside a TEE (functional parity).  
- [ ] Confirm ephemeral session binding verifies without contacting the HSM on the hot path.  
- [ ] Confirm deployment runbooks refuse to mark a node “Oracle-grade” unless the governor measurement is TEE-attested.  
- [ ] Confirm host-side Streamlit is treated as an untrusted UI that only *displays* enclave-produced bags.

Return to the [documentation index](README.md) or the [main repository README](../README.md).
