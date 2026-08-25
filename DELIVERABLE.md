# Quantum-Secure Agentic MLOps Pipeline Management System

## Architecture Summary

This system implements a comprehensive quantum-secure MLOps platform with the following key architectural layers:

### 1. Quantum Trust Layer (Bottom)
- **Post-Quantum Cryptography**: ML-KEM (Kyber) for encryption, ML-DSA (Dilithium) for signatures, SHA-3 for hashing
- **Cryptographic Agility**: Pluggable provider abstraction enabling algorithm migration
- **Key Management**: Versioned keystore with rotation, revocation, and trust anchors

### 2. Verification Engine
- **Verification Packets**: Immutable evidence for every operation (training, deployment, health checks)
- **Evidence Ledger**: Append-only hash-chained ledger for tamper-evident audit trail

### 3. Model Trust System
- **Model Passport**: Cryptographic identity binding model, dataset, code, environment, metrics
- **QML-BOM**: Complete supply-chain bill of materials (dataset → preprocessing → training → artifact)
- **Secure Registry**: State machine (REGISTERED → VERIFIED → APPROVED → DEPLOYED) with cryptographic gates

### 4. Agentic MLOps Layer
- **Specialized Agents**: Data, Performance, Security, Quantum Security, Red Team
- **Adaptive Supervisor**: Observe → Detect → Reason → Act → Verify → Learn control loop
- **Learning Store**: Adaptive memory tracking decisions, outcomes, and false positives

### 5. Self-Healing Pipeline
- **Drift Detection**: Feature, data, and prediction drift monitoring
- **Performance Monitoring**: Accuracy, precision, recall, latency, error rate tracking
- **Automatic Recovery**: Retrain → Verify → Deploy or Rollback based on supervisor decision

---

## Implemented Features

### 1. Quantum Secure Model Passport (`qsmlops/passport/`)
- ✅ Cryptographic identity for every model
- ✅ Fields: passport_id, model_id, model_name, version, owner, dataset_reference, training_reference, code_hash, environment_hash, performance_metrics, security_status, signature, created_at, deployment_history
- ✅ Capabilities: create, validate, update deployment history, verify authenticity
- ✅ ML-DSA signature over canonical JSON document

### 2. Quantum ML Supply Chain Security (QML-BOM) (`qsmlops/supplychain/`)
- ✅ Tracks: dataset versions, libraries, frameworks, dependencies, source info, hashes, vulnerabilities
- ✅ Answers: "Where did this model come from?" and "Was anything modified?"
- ✅ BOM diff capability for supply-chain change detection

### 3. Quantum Secure Model Registry (`qsmlops/registry/`)
- ✅ Stores: model artifacts, versions, passports, QML-BOM, verification packets, signatures, deployment status
- ✅ State machine: CREATED/REGISTERED → TESTING/VERIFIED → APPROVED → DEPLOYED → QUARANTINED/ROLLED_BACK/REVOKED
- ✅ Deployment gates: signature validation, passport presence, verification success, integrity checks
- ✅ Separation of duties: verifier ≠ signer

### 4. Post-Quantum Cryptography Layer (`qsmlops/crypto/`)
- ✅ Provider abstraction (SignatureProvider, KEMProvider interfaces)
- ✅ ML-KEM support: ML-KEM-512, ML-KEM-768, ML-KEM-1024
- ✅ ML-DSA support: ML-DSA-44, ML-DSA-65, ML-DSA-87
- ✅ SHA-3-256 hashing with canonical JSON serialization
- ✅ Key generation, encryption, decapsulation, signing, verification, hashing, rotation

### 5. Quantum Verification Packet (`qsmlops/evidence/`)
- ✅ packet_id, objective, operation, input_artifacts, output_artifacts, metrics, security_checks, cryptographic_checks, timestamp, decision
- ✅ Hash-chained evidence ledger with integrity verification

### 6. AI Red Team Agent (`qsmlops/agents/redteam.py`)
- ✅ Integrity attack (tamper detection validation)
- ✅ Adversarial probing (decision boundary testing)
- ✅ Poisoning probe (outlier influence measurement)
- ✅ Unauthorized modification detection
- ✅ Outputs SecurityReport with findings, severity, evidence, recommendations

### 7. Cryptographic Agility Engine (`qsmlops/crypto/agility.py`)
- ✅ Algorithm registry with status tracking (recommended/acceptable/deprecated/emergency)
- ✅ Cipher suite selection (signature + KEM + hash combinations)
- ✅ Migration planning between suites
- ✅ Inventory audit for deprecated algorithm detection

### 8. Adaptive Agentic Supervisor (`qsmlops/supervisor/`)
- ✅ Control loop: Observe → Detect → Reason → Act → Verify → Learn
- ✅ 5 specialized agents with evidence-based findings
- ✅ Risk scoring with severity-weighted aggregation
- ✅ Decision actions: ACCEPT, DEPLOY, RETRAIN, ROLLBACK, QUARANTINE, ROTATE_KEYS, BLOCK_DEPLOYMENT, ESCALATE
- ✅ Learning store for adaptive behavior

### Self-Healing MLOps (`qsmlops/pipeline/selfheal.py`)
- ✅ Drift detection (feature, data, prediction)
- ✅ Performance monitoring (accuracy, precision, recall, latency, error rate)
- ✅ Failure recovery: detect → root cause → supervisor decision → retrain → verify → deploy
- ✅ Adaptive memory: situation + action + outcome + confidence + recommendation

---

## Folder Structure

```
quantum_secure_mlops/
├── qsmlops/
│   ├── __init__.py              # Public API exports
│   ├── config.py                # Platform configuration
│   ├── cli.py                   # Command-line interface
│   ├── crypto/
│   │   ├── __init__.py
│   │   ├── providers.py         # ML-KEM, ML-DSA providers
│   │   ├── keys.py              # KeyStore with rotation/revocation
│   │   ├── hashing.py           # SHA-3, canonical JSON
│   │   └── agility.py           # CryptoAgilityEngine
│   ├── artifacts/
│   │   ├── __init__.py
│   │   └── store.py             # Content-addressed artifact store
│   ├── passport/
│   │   ├── __init__.py
│   │   └── passport.py          # ModelPassport with signing/verification
│   ├── supplychain/
│   │   ├── __init__.py
│   │   └── bom.py               # QMLBOM with supply-chain tracking
│   ├── registry/
│   │   ├── __init__.py
│   │   └── registry.py          # ModelRegistry with state machine
│   ├── evidence/
│   │   ├── __init__.py
│   │   ├── packet.py            # VerificationPacket
│   │   └── ledger.py            # Hash-chained EvidenceLedger
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py              # BaseAgent, Finding, Observation
│   │   ├── data_agent.py        # Dataset integrity verification
│   │   ├── performance_agent.py # ML metrics evaluation
│   │   ├── security_agent.py    # Dependency vuln + artifact integrity
│   │   ├── quantum_agent.py     # Crypto posture verification
│   │   └── redteam.py           # Autonomous adversarial testing
│   ├── supervisor/
│   │   ├── __init__.py
│   │   ├── decisions.py         # Decision enum, risk scoring, policy
│   │   ├── learning.py          # LearningStore for adaptive memory
│   │   └── supervisor.py        # AdaptiveSupervisor control loop
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── training.py          # Reference trainer (linear regression)
│   │   └── selfheal.py          # SelfHealingMLOps orchestrator
│   └── ...
├── tests/
│   ├── conftest.py
│   ├── test_crypto.py           # Crypto layer tests (13 tests)
│   ├── test_artifacts_passport.py # Artifact/Passport/BOM/Registry (10 tests)
│   ├── test_agents.py           # Agent system tests (13 tests)
│   └── test_supervisor.py       # Supervisor/self-healing tests (8 tests)
├── demo.py                      # Full workflow demonstration
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Security Design

### Cryptographic Primitives
| Purpose | Algorithm | NIST Standard |
|---------|-----------|---------------|
| Key Encapsulation | ML-KEM (Kyber) | FIPS 203 |
| Digital Signatures | ML-DSA (Dilithium) | FIPS 204 |
| Hashing | SHA3-256 | FIPS 202 |

### Trust Model
1. **Root of Trust**: Producer/Verifier signing keys in KeyStore
2. **Passport Chain**: Model → Passport (signed) → Registry → Verification Packet → Ledger
3. **Separation of Duties**: Signer (producer) ≠ Verifier (independent agent)
4. **Content Addressing**: All artifacts addressed by SHA3-256 digest
5. **Tamper Evidence**: Hash-chained ledger detects any retroactive modification

### Deployment Gates
A model CANNOT be deployed if:
- ✅ Passport signature invalid
- ✅ Passport missing
- ✅ Verification failed (any CRITICAL check)
- ✅ Integrity check failed (artifact/BOM mismatch)
- ✅ Crypto suite deprecated
- ✅ Signing key past rotation window

---

## Agent Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    ADAPTIVE SUPERVISOR                      │
│  Observe → Detect → Reason → Act → Verify → Learn          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────┬───────────┼───────────┬─────────┐
        ▼         ▼           ▼           ▼         ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │  Data  │ │Performance│ │Security │ │Quantum │ │Red Team│
   │ Agent  │ │ Agent    │ │ Agent   │ │ Agent  │ │ Agent  │
   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
        │         │           │           │         │
        └─────────┴───────────┴───────────┴─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Risk Aggregation │
                    │  (Weighted Score) │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Decision Policy  │
                    │  Thresholds +     │
                    │  Learning State   │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │    Action         │
                    │ ACCEPT/RETRAIN/   │
                    │ QUARANTINE/...    │
                    └───────────────────┘
```

### Agent Responsibilities
| Agent | Monitors | Outputs |
|-------|----------|---------|
| Data Agent | Dataset integrity, preprocessing | ACCEPT/QUARANTINE |
| Performance Agent | R², MSE, drift | ACCEPT/RETRAIN |
| Security Agent | Dependency CVEs, artifact integrity | ACCEPT/ESCALATE/BLOCK |
| Quantum Agent | Signature validity, suite status, key age | ACCEPT/QUARANTINE/ROTATE |
| Red Team Agent | Tamper detection, adversarial robustness, poisoning | ACCEPT/ESCALATE/QUARANTINE |

---

## Self-Healing Workflow

```
┌─────────────┐
│  Deployed   │
│  Model v1   │
└──────┬──────┘
       │ Health Check
       ▼
┌─────────────────┐
│  Metrics Check  │──► R² < 0.8 or MSE > 0.05
│  (Performance)  │
└────────┬────────┘
         │ Degraded
         ▼
┌─────────────────┐
│  Supervisor     │──► Decision: RETRAIN
│  Reasoning      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Auto-Retrain   │──► New Model v2
│  Pipeline       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Verify v2      │──► All agents ACCEPT
│  (Full Eval)    │
└────────┬────────┘
         │ Verified
         ▼
┌─────────────────┐
│  Deploy v2      │──► Active = v2
│  (Atomic)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Learn          │──► Record outcome
│  (Adaptive)     │    Update failure streaks
└─────────────────┘
```

### Recovery Actions
| Trigger | Supervisor Decision | Action |
|---------|---------------------|--------|
| Performance degradation | RETRAIN | Train new version, verify, deploy |
| Critical security finding | QUARANTINE | Isolate version, alert |
| Dependency vulnerability | BLOCK_DEPLOYMENT | Prevent deploy, require fix |
| Key rotation needed | ROTATE_KEYS | Generate new signing key |
| Repeated failures | ESCALATE | Human intervention required |
| Active model compromised | ROLLBACK | Restore previous approved version |

---

## Tests Executed

### Test Suite Summary: 44 Tests Passed

| Test Module | Tests | Coverage |
|-------------|-------|----------|
| `test_crypto.py` | 13 | Hashing, providers, keys, agility |
| `test_artifacts_passport.py` | 10 | Artifact store, passport, BOM, registry |
| `test_agents.py` | 13 | All 5 agents (data, performance, security, quantum, redteam) |
| `test_supervisor.py` | 8 | Risk scoring, supervisor decisions, learning, self-healing |

### Key Test Scenarios
- ✅ All ML-KEM/ML-DSA parameter sets (keygen, sign/verify, encaps/decaps)
- ✅ KeyStore: generation, rotation, revocation, trust anchors
- ✅ AgilityEngine: suite selection, deprecation, migration planning
- ✅ ArtifactStore: put/get, integrity verification, deduplication
- ✅ Passport: creation, signing, verification, deployment history
- ✅ BOM: entry tracking, diff, artifact verification
- ✅ Registry: state transitions, separation of duties, deploy gates
- ✅ Ledger: append, chain verification, packet indexing
- ✅ Agents: threshold evaluation, vulnerability detection, adversarial testing
- ✅ Supervisor: risk aggregation, policy decisions, learning adaptation
- ✅ Self-healing: full pipeline provision→train→verify→deploy→retrain

---

## Demo Instructions

### Quick Start
```bash
# Initialize platform
python -m qsmlops.cli init

# Provision synthetic dataset
python -m qsmlops.cli provision-dataset --name "my-data" --samples 200

# Train and register model
python -m qsmlops.cli train --model "my-model" --dataset "my-data"

# Evaluate with all agents
python -m qsmlops.cli verify --version-id <VERSION_ID>

# Approve and deploy (if verified)
python -m qsmlops.cli approve --version-id <VERSION_ID>

# Monitor deployed model health
python -m qsmlops.cli health-check --model "my-model" --mse 0.1 --r2 0.5

# Rollback if needed
python -m qsmlops.cli rollback --model "my-model"

# Run red team assessment
python -m qsmlops.cli redteam --model "my-model" --artifact-digest <DIGEST>

# Check platform status
python -m qsmlops.cli status

# Audit evidence ledger
python -m qsmlops.cli audit-ledger
```

### Run Full Demo
```bash
python demo.py
```

The demo executes the complete 12-step workflow in a temporary directory.

---

## Remaining Limitations

### Known Gaps
1. **Real ML Framework Integration**: Uses pure-Python linear regression reference trainer; no native PyTorch/TensorFlow/JAX integration
2. **Distributed Deployment**: Single-node registry/ledger; no multi-node consensus or HA
3. **Model Serving**: No built-in inference server (REST/gRPC) for deployed models
4. **Advanced Drift Detection**: Only basic statistical drift; no KS-test, PSI, or embedding drift
5. **Policy Language**: Hard-coded thresholds; no declarative policy DSL for custom gates
6. **Secret Management**: Keys stored on filesystem; no HSM/KMS integration
7. **Multi-tenancy**: Single producer/verifier model; no namespace isolation
8. **Data Lineage**: BOM tracks artifacts but not full column-level data lineage

### Security Considerations
- Demo uses synthetic data; production needs real dataset provisioning with access controls
- KeyStore uses file-based storage; production should use HSM or cloud KMS
- No network encryption (TLS) for inter-component communication
- No audit logging beyond evidence ledger (no SIEM integration)

---

## Future Roadmap

### Phase 1: Production Hardening (Q1)
- [ ] HSM/KMS integration for key storage
- [ ] TLS/mTLS for all service communication
- [ ] PostgreSQL-backed registry for HA
- [ ] Declarative policy engine (OPA/Rego)

### Phase 2: ML Framework Integration (Q2)
- [ ] PyTorch/TensorFlow/JAX trainer plugins
- [ ] ONNX model artifact support
- [ ] Model card standardization (HF format)
- [ ] Distributed training coordination

### Phase 3: Advanced Security (Q3)
- [ ] Differential privacy training integration
- [ ] Federated learning coordination
- [ ] Zero-trust model serving with attestation
- [ ] SBOM (CycloneDX/SPDX) export

### Phase 4: Platform Features (Q4)
- [ ] Multi-tenant namespace isolation
- [ ] GitOps deployment (ArgoCD/Flux integration)
- [ ] Feature store integration
- [ ] Automated canary/blue-green deployments
- [ ] Real-time monitoring dashboard (Grafana)

### Research Directions
- [ ] Quantum-resistant ML (PQC-secure gradient aggregation)
- [ ] Formal verification of supervisor decision logic
- [ ] Cryptographic proof of training correctness (ZK-ML)
- [ ] Post-quantum secure federated learning