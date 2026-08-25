# Quantum-Secure Agentic MLOps Pipeline Management System

## Overview
This repository contains the implementation of a guardrailed agentic MLOps platform designed for self-adaptive energy forecasting in renewable-integrated smart grids. The system integrates quantum-secure cryptography, agentic AI, and self-healing capabilities to provide a trustworthy forecasting platform that ensures model integrity, operational safety, and regulatory compliance.

## Research Motivation
Renewable energy integration introduces variability and forecasting challenges that complicate grid operations. Traditional MLOps pipelines lack the governance and adaptability required for safe, self-adaptive forecasting in safety-critical smart grid applications. This work addresses the gap by proposing a guardrailed agentic MLOps framework that enforces deterministic governance over agentic actions, ensuring that automation enhances rather than endangers grid operations.

## System Architecture
The system consists of five layers:

1. **Quantum Trust Layer** (Bottom): Implements post-quantum cryptography (ML-KEM for encryption, ML-DSA for signatures, SHA-3 for hashing) to secure all artifacts and communications. Includes cryptographic agility and versioned key management.

2. **Verification Engine**: Generates immutable verification packets for every operation (training, deployment, health checks) and maintains an append-only hash-chained evidence ledger for tamper-evident auditing.

3. **Model Trust System**: Binds model, dataset, code, environment, and metrics into a cryptographic model passport. Uses a QML-BOM for full supply-chain tracking. The secure registry enforces a state machine with cryptographic gates (REGISTERED → VERIFIED → APPROVED → DEPLOYED) and separation of duties.

4. **Agentic MLOps Layer**: Deploys five specialized agents (Data, Performance, Security, Quantum Security, Red Team) that produce evidence-based findings. An adaptive supervisor implements an Observe → Detect → Reason → Act → Verify → Learn control loop, making decisions (ACCEPT, RETRAIN, QUARANTINE, etc.) based on risk scores and learning state.

5. **Self-Healing Pipeline**: Orchestrates the lifecycle: provision data → train → build QML-BOM → sign passport → register → agent evaluation → supervisor decision → deploy gate → health monitoring → automatic recovery (retrain/verify/deploy or rollback).

## Key Features
- **Quantum-Secure Model Passport**: Cryptographic identity for every model with ML-DSA signatures over canonical JSON documents.
- **QML-BOM (Quantum ML Bill of Materials)**: Complete supply-chain tracking of dataset versions, libraries, frameworks, dependencies, source info, hashes, and vulnerabilities.
- **Post-Quantum Cryptography Layer**: Provider abstraction for ML-KEM (encryption) and ML-DSA (signatures) with SHA-3-256 hashing.
- **Verification Engine & Evidence Ledger**: Immutable verification packets and hash-chained ledger for tamper-evident audit trails.
- **Specialized Agents**: 
  - Data Agent: Dataset integrity and preprocessing verification
  - Performance Agent: ML metrics evaluation (R², MSE, drift) and performance monitoring
  - Security Agent: Dependency CVEs and artifact integrity checking
  - Quantum Security Agent: Cryptographic posture verification (signature validity, suite status, key age)
  - Red Team Agent: Autonomous adversarial testing (integrity attacks, decision boundary probing, poisoning attempts)
- **Adaptive Agentic Supervisor**: Control loop with risk scoring, severity-weighted aggregation, and policy-based decisions (ACCEPT, DEPLOY, RETRAIN, QUARANTINE, ROTATE_KEYS, BLOCK_DEPLOYMENT, ESCALATE).
- **Self-Healing MLOps**: Automatic recovery via retrain → verify → deploy or rollback based on supervisor decisions, with adaptive memory for learning from outcomes.
- **Cryptographic Agility Engine**: Algorithm registry with status tracking, cipher suite selection, migration planning, and inventory audit for deprecated algorithms.

## Results
The final evaluation (Phase 19) executed successfully, demonstrating:
- Inference-only evaluation on frozen models (no training, HPO, feature selection, model selection, or retraining)
- Forecast generation and computation of standard metrics (MAE, RMSE, sMAPE, nMAE, nRMSE)
- Governance compliance (no unsafe agent actions, evidence ledger integrity)
- Lineage recording for reproducibility

Detailed results are available in:
- `artifacts/final_evaluation/final_predictions.csv`
- `artifacts/research_tables/final_forecasting_results.csv`

## Safety Guarantees
The system ensures safety through:
- Cryptographic model passports verifying integrity of models, datasets, code, and environment
- QML-BOM providing end-to-end supply-chain provenance
- Evidence ledger providing tamper-evident audit trail for all operations
- Governance engine enforcing strict policy constraints on agentic AI agents
- Separation of duties preventing unauthorized operations (signer ≠ verifier)
- Key management with rotation, revocation, and trust anchors
- Verification packets for every operation enabling reproducible audits

## Agentic AI Design
The agentic AI layer consists of five specialized agents operating under strict governance bounds:
- **Data Agent**: Validates dataset integrity and preprocessing steps
- **Performance Agent**: Evaluates ML metrics (R², MSE) and detects performance drift
- **Security Agent**: Checks for dependency vulnerabilities and artifact integrity
- **Quantum Security Agent**: Verifies cryptographic signatures, certificate status, and key age
- **Red Team Agent**: Conducts adversarial testing for integrity attacks, decision boundary probing, and poisoning attempts

The adaptive supervisor aggregates agent findings using severity-weighted risk scores and makes decisions based on policy rules, ensuring that agentic actions are bounded and safe.

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/your-org/quantum-secure-agentic-mlops.git
   cd quantum-secure-agentic-mlops
   ```
2. Create a virtual environment (optional but recommended):
   ```
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Execution
To run the final evaluation (Phase 19):
```
python run_phase19_evaluation.py
```
To run the full system demonstration:
```
python demo.py
```
To run the test suite:
```
python -m pytest tests/
```

## Limitations
- Single synthetic dataset (RTS-GMLC); real-world utility data validation pending
- Limited temporal coverage (one year); multi-year seasonal extremes untested
- Simulated drift mechanisms; long-term drift adaptation unvalidated
- No production grid deployment; simulation-only evaluation
- No human operator study; usability and trust effects unknown
- Bounded agent scope; open-ended agentic behaviors not supported
- External benchmark dependencies not integrated (RTS DAY_AHEAD, H24 Daily Persistence)
- Quantum cryptography overhead; performance impact on high-frequency forecasting unmeasured
- Hard-coded governance policies; declarative policy engine (OPA/Rego) not integrated

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements
This work was supported by [insert funding sources if any].

## References
[1] Sculley et al., "Hidden technical debt in machine learning systems," NeurIPS, 2015.
[2] Rajkomar et al., "Scalable and accurate deep learning with electronic health records," PLOS Medicine, 2018.
[3] Bojarski et al., "End to end learning for self-driving cars," arXiv, 2016.
[4] Wang et al., "HuggingGPT: Solving AI tasks with chatGPT and its friends in huggingface," arXiv, 2023.
[5] Yao et al., "Tree of thoughts: Deliberate problem solving with large language models," NeurIPS, 2023.
[6] Feurer et al., "Efficient and robust automated machine learning," NeurIPS, 2019.
[7] Zeng et al., "AgentTuning: Enabling generalized agent abilities for LLMs," arXiv, 2023.
[8] Hadfield-Menell et al., "The off-switch game," arXiv, 2016.
[9] Hong and Fan, "Probabilistic electric load forecasting: A tutorial review," International Journal of Forecasting, 2016.
[10] Liu et al., "A review of deep learning applications in renewable energy forecasting," Renewable Energy, 2019.
[11] Noorollahi et al., "A review on wind power forecasting models," Renewable and Sustainable Energy Reviews, 2019.
[12] Zhang et al., "Optimizing short-term wind power forecasting using deep learning," Energy, 2020.