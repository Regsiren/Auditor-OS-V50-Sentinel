# Project AEGIS: MIT Solve 2027 Technical Appendix

Welcome to the technical verification layer for **Project AEGIS** (Autonomous Ecosystem & Grid Integration Sentinel), powered by the Auditor OS V50-S Architecture. 

This directory serves as the interactive technical appendix for our MIT Solve 2027 Global Climate Challenge submission (Track: *Resilient Water, Cooling Systems, & Infrastructure Design*).

## The Goal
To prove that AEGIS can statelessly transform noisy municipal fluid infrastructure telemetry (SCADA) into cryptographically verifiable, predictive early-warning signals without requiring heavy simulation models or new physical IoT hardware.

## Directory Contents

*   **`NODE-02-HYDRAULIC-PRESSURE-DECAY-UNIFORM.csv`**: A temporal-normalised, uniform SCADA dataset representing a high-consequence municipal fluid manifold undergoing hidden material decay.
*   **`NODE-02-HYDRAULIC-PHASE-SPACE.png`**: The visual proof. This chart tracks the calculated Macro Uncertainty Vector ($\Phi_t$) as the asset transitions from a Homeostatic Base ($\Phi < 0.07$) into Metastable Impairment ($0.07 \le \Phi < 0.19$). 
*   **`NODE-02-TERMINAL-EVIDENCE.sent`**: The terminal RFC-001 Cryptographic Evidence Container generated at the end of the simulation. This proves the thermodynamic state is immutable and bankable.
*   **`verify_sent_bag.py`**: A lightweight, standalone Python script to execute sub-50µs offline verification of the `.sent` container.

## 30-Second Verification Runbook for Evaluators

We invite evaluators to independently verify the structural integrity attestation of the simulated municipal fluid manifold.

**1. Install Requirement**
The only dependency required for the verification script is `PyNaCl` (for the Ed25519 digital signature authentication).
```bash
pip install pynacl
```

**2. Execute Offline Verification**
Run the verifier against the provided `.sent` evidence bag.
```bash
python verify_sent_bag.py NODE-02-TERMINAL-EVIDENCE.sent
```

**3. Expected Outcome**
The script will parse the four-block JSON schema, recompute the SHA-256 canonical row hash, and authenticate the Ed25519 digital signature. A successful output confirms, with zero-knowledge mathematical certainty, that the infrastructure telemetry was not retroactively altered and that the asset is accurately classified in a state of 'Metastable Impairment.'

---
*Developed by Thohat Ventures. For inquiries regarding the proprietary finite-difference calculus engine and the T-30 Momentum Engine, please refer to the primary MIT Solve application portal.*
