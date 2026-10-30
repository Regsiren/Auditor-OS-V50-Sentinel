# Project AEGIS: MIT Solve 2027 Technical Appendix

Welcome to the technical verification layer for **Project AEGIS** (Autonomous Ecosystem & Grid Integration Sentinel), powered by the Auditor OS V50-S Architecture.

This directory serves as the interactive technical appendix for our MIT Solve 2027 Global Climate Challenge submission (Track: *Resilient Water, Cooling Systems, & Infrastructure Design*).

## The Goal

To prove that AEGIS can statelessly transform noisy municipal fluid infrastructure telemetry (SCADA) into cryptographically verifiable, predictive early-warning signals—demonstrating a 36-day detection lead time over standard static alarms.

## Directory Contents

*   **`NODE-02-HYDRAULIC-PRESSURE-DECAY-UNIFORM.csv`**: A temporal-normalised, uniform SCADA dataset representing a high-consequence municipal fluid manifold undergoing hidden material decay over 42 days.
*   **`NODE-02-BAKEOFF.png`**: The visual proof. This dual-axis chart demonstrates AEGIS crossing the 0.07 Metastable gate 36 days before a naive 15% SCADA static alarm registers the terminal pump fracture.
*   **`NODE-02-TERMINAL-EVIDENCE.sent`**: The terminal RFC-001 Cryptographic Evidence Container generated at the end of the simulation.
*   **`pubkey.hex`**: The persistent, custody-grade Ed25519 public key (`f1b7483e...`) representing the simulated HSM master identity.
*   **`verify_sent_bag.py`**: A standalone Python script to execute sub-50µs offline verification of the `.sent` container against the persistent public key.

## 30-Second Verification Runbook for Evaluators

We invite evaluators to independently verify the structural integrity attestation of the simulated municipal fluid manifold.

**1. Install Requirement**  
The only dependency required is `PyNaCl` (for the Ed25519 digital signature authentication).
```bash
pip install pynacl
```

**2. Execute Offline Verification**  
Run the verifier against the provided `.sent` evidence bag. The script will automatically check the signature against `pubkey.hex`.
```bash
python verify_sent_bag.py NODE-02-TERMINAL-EVIDENCE.sent
```

**3. Expected Outcome**  
The script parses the four-block JSON schema, recomputes the SHA-256 canonical row hash, and authenticates the Ed25519 digital signature. A successful `VALID` output confirms, with zero-knowledge mathematical certainty, that the infrastructure telemetry was not retroactively altered.

---
*Developed by Thohat Ventures. For inquiries regarding the proprietary finite-difference calculus engine and the T-30 Momentum Engine, please refer to the primary MIT Solve application portal.*
