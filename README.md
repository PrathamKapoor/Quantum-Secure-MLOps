# Quantum-Secure MLOps Pipeline

A post-quantum cryptographic MLOps platform that secures the full machine learning lifecycle -- from data ingestion through model deployment -- using ML-DSA signatures, ML-KEM encryption, and SHA-3 hashing.

## What This Is

QSMLOps implements a governed, self-healing MLOps pipeline where every artifact (model, dataset, code, environment) is bound to a cryptographic passport signed with post-quantum algorithms. The system enforces separation of duties, maintains an immutable evidence ledger, and uses specialized agents to continuously verify model integrity.

The core problem it solves: in safety-critical ML deployments, you need cryptographic proof that a model hasn't been tampered with, that its training data is what you think it is, and that every deployment decision was authorized. Traditional ML pipelines rely on trust; QSMLOps replaces trust with verification.

## Architecture

```
+---------------------------------------------------+
|           Self-Healing Pipeline                    |
|  (train -> evaluate -> approve -> deploy -> heal)  |
+---------------------------------------------------+
|        Agentic MLOps Layer                         |
|  (5 agents + adaptive supervisor)                 |
+---------------------------------------------------+
|        Model Trust System                          |
|  (passports, QML-BOM, secure registry)            |
+---------------------------------------------------+
|        Verification Engine                         |
|  (verification packets, evidence ledger)           |
+---------------------------------------------------+
|        Quantum Trust Layer                         |
|  (ML-DSA, ML-KEM, SHA-3, key management)          |
+---------------------------------------------------+
```

### Quantum Trust Layer

Post-quantum cryptography via pluggable providers:

- **ML-DSA** (Dilithium): Digital signatures for artifact authentication
- **ML-KEM** (Kyber): Key encapsulation for secure communications
- **SHA-3-256**: Hashing for integrity verification
- **Cryptographic Agility**: Algorithm registry with status tracking, migration planning, and deprecation handling

### Model Trust System

Every model gets a cryptographic passport binding:

- Model weights (hash)
- Training dataset (hash + lineage)
- Code version (hash)
- Environment (hash)
- Metrics and evaluation results

Passports are signed with ML-DSA and registered in a state machine:

```
REGISTERED -> VERIFIED -> APPROVED -> DEPLOYED
                                    \-> QUARANTINED / REVOKED / ROLLED_BACK
```

### Verification Engine

- **Verification Packets**: Immutable, signed records for every operation
- **Evidence Ledger**: Append-only, hash-chained audit trail (tamper-evident)

### Agentic Layer

Five specialized agents evaluate models against governance policies:

| Agent | Responsibility |
|-------|---------------|
| Data Agent | Dataset integrity and preprocessing verification |
| Performance Agent | ML metrics evaluation and drift detection |
| Security Agent | Dependency CVE scanning and artifact integrity |
| Quantum Security Agent | Cryptographic posture verification |
| Red Team Agent | Adversarial testing (integrity, poisoning, boundary probing) |

The **Adaptive Supervisor** aggregates findings using severity-weighted risk scores and makes policy-based decisions: ACCEPT, DEPLOY, RETRAIN, QUARANTINE, ROTATE_KEYS, BLOCK_DEPLOYMENT, or ESCALATE.

### Self-Healing Pipeline

Automatic recovery flow:

```
Drift Detected -> Agent Evaluation -> Supervisor Decision ->
  |-> ACCEPT -> Deploy
  |-> RETRAIN -> Verify -> Deploy
  |-> QUARANTINE -> Block
  \-> ROLLBACK -> Previous version
```

## Installation

```bash
git clone https://github.com/PrathamKapoor/Quantum-Secure-MLOps.git
cd Quantum-Secure-MLOps
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### Dependencies

Core: `kyber-py`, `dilithium-py`, `numpy`, `scipy`, `cryptography`, `pyyaml`, `fastapi`, `uvicorn`, `click`, `scikit-learn`, `pydantic`, `python-pkcs11`

Dev: `pytest`, `httpx`

## Usage

### Run the demo

```bash
python demo.py
```

This executes the full pipeline: train a model, generate a passport, sign it, register it, run agents, make a supervisor decision, and deploy.

### Run the test suite

```bash
pytest tests/ -q
```

### Use as a Python package

```python
from qsmlops.crypto.keys import KeyStore
from qsmlops.passport.passport import Passport
from qsmlops.crypto.agility import AgilityEngine

# Generate a signing key
keystore = KeyStore("./keystore")
keystore.generate_keypair("SIGNER", "ML-DSA-65", owner="alice")

# Create and sign a passport
passport = Passport("my-model", 1, "alice", "dataset-hash", "model-hash")
agility = AgilityEngine()
suite_id = agility.select_suite("ML-DSA-65")
passport.sign(keystore, agility, "alice", suite_id=suite_id)

# Verify
assert passport.verify_signature(keystore)
```

## HSM / PKCS#11 Support (Optional)

The system supports hardware security modules via PKCS#11. For development and testing, SoftHSM2 can be used:

```powershell
# Bootstrap SoftHSM2 (Windows)
powershell -ExecutionPolicy Bypass -File scripts/bootstrap_softhsm2.ps1
```

Set environment variables:

```bash
export SOFTHSM2_CONF=/path/to/softhsm2.conf
export QSMLOPS_A12_LIB=/path/to/softhsm2-x64.dll
export QSMLOPS_A12_TOKEN_LABEL=your-token-label
export QSMLOPS_A12_PIN=your-pin
```

**Current limitations:**

- SoftHSM2 v2.5.0 does not support ML-DSA -- only ECDSA/RSA operations work via PKCS#11
- ML-DSA operations fall back to the software provider (dilithium-py)
- Hardware-backed ML-DSA requires a PKCS#11 provider with native ML-DSA support
- See `reports/A12_REAL_PKCS11_CERTIFICATION.md` and `reports/A13_MLDSA_PROVIDER_CERTIFICATION.md` for certification details

## Testing

```bash
# Full test suite
pytest tests/ -q

# HSM-specific tests (requires SoftHSM2)
pytest tests/test_hsm_a12_real_provider.py -v

# ML-DSA provider tests
pytest tests/test_hsm_a13_mldsa_certification.py -v

# Compile check
python -m compileall -q qsmlops
```

## Project Structure

```
qsmlops/
  crypto/          # Post-quantum cryptography providers, HSM, key management
  passport/        # Cryptographic model passports
  evidence/        # Verification packets and evidence ledger
  agents/          # Specialized evaluation agents
  supervisor/      # Adaptive supervisor with risk scoring
  pipeline/        # Self-healing pipeline orchestration
  security/        # Security policies, identity, audit
  serving/         # Deployment and serving
  registry/        # Secure model registry
  database/        # Storage and persistence
  ml/              # ML adapters and drift detection
  monitoring/      # Health monitoring and alerts
  supplychain/     # QML-BOM and supply chain tracking
  config.py        # Configuration management
  cli.py           # Command-line interface
  app.py           # Application entry point
tests/             # Test suite (450+ tests)
configs/           # Environment-specific configuration
reports/           # Certification and audit reports
docs/              # Architecture and implementation documentation
scripts/           # Bootstrap and utility scripts
demo.py            # Full system demonstration
```

## Limitations

- Synthetic evaluation dataset (RTS-GMLC); production grid data validation pending
- Simulation-only; no live deployment tested
- SoftHSM2 lacks ML-DSA PKCS#11 support; hardware-backed PQC signing unexercised
- Single-session SoftHSM2 lockout limits concurrent HSM test execution
- Governance policies are code-based; declarative policy engine (OPA/Rego) not integrated

## License

MIT License

## Author

Pratham Kapoor
