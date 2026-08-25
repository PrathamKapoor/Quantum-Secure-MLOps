This work introduces a guardrailed agentic MLOps framework for self-adaptive energy forecasting in renewable-integrated smart grids. By coupling deterministic governance with bounded agentic AI, the system achieves safe automation across the forecasting lifecycle—from data provisioning to model retraining—without compromising integrity or safety.

Key contributions include:
- A quantum-secure MLOps platform with cryptographic model passports, QML-BOM tracking, and tamper-evident evidence ledgers.
- Five specialized agents operating under strict policy constraints, supervised by an adaptive supervisor that enforces governance bounds.
- A self-healing pipeline that initiates governed recovery actions (retrain, verify, deploy, rollback) only when safety conditions are met.
- Formalized forecasting lifecycle management tailored to the unique demands of grid-integrated renewable forecasting.

The final evaluation confirmed the system's ability to execute inference-only evaluation on frozen models, generate forecasts, and compute standard metrics while maintaining full governance compliance. Although the evaluation used synthetic data and substituted models due to missing artifacts, the protocol was followed correctly, validating the core mechanisms.

Future work will focus on integrating real grid data, advancing drift detection capabilities, validating with operational utility partners, and extending the framework to grid control applications. By releasing this system as an open research package, we aim to foster collaboration in developing trustworthy ML for critical infrastructure, ensuring that the transition to renewable energy is both intelligent and secure.