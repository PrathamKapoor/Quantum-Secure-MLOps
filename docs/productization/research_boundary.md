# Research Boundary

## Purpose
This document defines the strict boundary between the immutable research system and the productization layer. The research system, encompassing all scientific components, experiments, models, datasets, features, evaluation results, frozen protocols, governance policies, agent safety boundaries, and final research artifacts, must remain unchanged during productization efforts. The productization layer is strictly a consumer of the research system's public interfaces and must not alter any research components in any way.

## Immutable Research Components
The following components are **frozen and must not be modified** by the productization layer or any productization-related activities:

### 1. Models
- All forecasting models (Random Forest, HistGradientBoosting, etc.) for LOAD, WIND, and PV targets.
- Model artifacts (serialized bytes) stored in the artifact store.
- Model passports (including signatures, metadata, and QML-BOM references).
- Model versions and their lineage in the model registry.
- Any model-related code in the `qsmlops/pipeline/training.py`, `qsmlops/ml/adapters/`, and related files.

### 2. Datasets
- The RTS-GMLC dataset (or any dataset used in Phase 11-19) as stored in the artifact store.
- Dataset provenance and versioning information.
- Any dataset loading or validation code in the research system (e.g., `qsmlops/pipeline/selfheal.py` provisioning methods).

### 3. Features
- Feature sets (e.g., B_lags_only) as defined in the data loading scripts and used in model training and inference.
- Feature extraction and transformation code.
- Any feature store or feature versioning components.

### 4. Experiments and Evaluation Results
- All experimental protocols from Phases 0-19.
- Evaluation results (metrics, predictions) stored in the artifact store or evidence ledger.
- Final evaluation outputs from Phase 19:
  - `artifacts/final_evaluation/final_predictions.csv`
  - `artifacts/research_tables/final_forecasting_results.csv`
- Any code that generates or processes these results.

### 5. Frozen Protocols
- The experimental protocols governing model selection, hyperparameter optimization (HPO), feature selection, and evaluation.
- The final frozen evaluation protocol (inference-only, no training, HPO, feature selection, model selection, or retraining).
- Any scripts or documents that define these protocols (e.g., HANDOFF.md, phase-specific completion reports).

### 6. Governance Policies
- The governance engine policy rules (e.g., retrain_on_high_drift, quarantine_on_critical_finding).
- The decision-making logic in the adaptive supervisor (`qsmlops/supervisor/supervisor.py`).
- The policy language and risk scoring mechanism.
- Any governance-related code in `qsmlops/supervisor/decisions.py`, `qsmlops/supervisor/learning.py`, and related files.

### 7. Agent Safety Boundaries
- The definitions and implementations of the five specialized agents:
  - Data Agent (`qsmlops/agents/data_agent.py`)
  - Performance Agent (`qsmlops/agents/performance_agent.py`)
  - Security Agent (`qsmlops/agents/security_agent.py`)
  - Quantum Security Agent (`qsmlops/agents/quantum_agent.py`)
  - Red Team Agent (`qsmlops/agents/redteam.py`)
- The agent observation and finding structures.
- The agent-agent interaction protocols (via the supervisor).
- Any code that would allow an agent to execute lifecycle operations (e.g., triggering a retrain directly).

### 8. Final Research Artifacts
- All files and directories that constitute the final research output, including but not limited to:
  - `artifacts/` (especially the final evaluation subdirectories)
  - `reports/` (all phase completion reports and lineage reports)
  - `docs/paper/` (the research paper drafts)
  - `run_phase19_evaluation.py` (the final evaluation script)
  - `demo.py` (the demonstration script)
  - `requirements.txt` (the exact set of dependencies used for research)
  - `pyproject.toml` (the project configuration)
  - Any other files referenced in the research completion documentation.

## Permitted Interactions
The productization layer may **only** interact with the research system through the following **read-only** interfaces:

### 1. Model Registry
- Read model versions, metadata, and lineage.
- Read model passports and QML-BOMs.
- **No write access** to register new models, transition states, or modify existing entries.

### 2. Artifact Store
- Read artifact bytes (models, datasets, BOMs, passports, etc.).
- **No write access** to put, delete, or modify artifacts.
- **No access** to modify the storage structure or hash validation.

### 3. Evidence Ledger
- Read verification packets, ledger entries, and chain integrity.
- **No write access** to append new entries or modify existing ones.
- **No access** to alter the hash-chaining mechanism.

### 4. MLflow Tracking (if used)
- Read runs, parameters, metrics, and artifacts.
- **No write access** to create new runs, log new parameters, or modify existing data.

### 5. Inference Engine
- Use frozen models to generate predictions on provided feature data.
- **No access** to modify model weights, retrain, or fine-tune models.
- **No access** to change the feature set or preprocessing steps.

### 6. Metadata and Configuration
- Read non-sensitive configuration (e.g., model types, feature set definitions) from the research system's public interfaces.
- **No access** to modify configuration files, environment variables, or internal state.

## Prohibited Interactions
The productization layer **must not**:
- Modify any file in the `qsmlops/`, `mlops/`, or research-specific directories.
- Add, remove, or alter any code in the research system.
- Change the behavior of any research system function or method.
- Modify any data stored in the artifact store, evidence ledger, model registry, or MLflow.
- Alter the definitions of models, features, datasets, or evaluation protocols.
- Change governance policies, agent behaviors, or supervisor decision logic.
- Modify the final research artifacts or reports.
- Attempt to reverse-engineer or extract sensitive information (e.g., model weights, cryptographic keys) for use outside the research system.
- Use reflection, monkey-patching, or any other technique to change the research system's behavior at runtime.
- Deploy a modified version of the research system under the guise of "bug fixes" or "optimizations" without explicit authorization and re-validation as research.

## Validation and Enforcement
To ensure the research boundary is respected:
1. **Immutability Checks:** The research system's artifacts and code should be version-controlled and checksummed. Any unauthorized changes will be detected by:
   - Comparing file hashes against known-good values (stored in a secure location).
   - Verifying that the research system's test suite passes (though note that some tests may be expected to fail due to infrastructure issues, as seen in the post-phase-20 validation).
2. **Access Controls:** The productization layer runs with limited permissions, ideally with read-only access to the research system's storage directories.
3. **Code Reviews:** All productization layer code changes must be reviewed to ensure they do not attempt to modify the research system.
4. **Architectural Separation:** The productization layer is deployed in a separate container or process, with no direct write access to the research system's storage.
5. **Research Boundary Document:** This document serves as the definitive guide for what constitutes the research system and what is forbidden to modify.

## Consequences of Violation
Any violation of the research boundary:
- Invalidates the scientific integrity of the research.
- May compromise the safety and trustworthiness of the system.
- Requires a full re-evaluation of the research findings.
- Is considered a serious breach of scientific conduct and may result in the rejection of the research outcomes.

## Acknowledgement
By working on this project, all contributors acknowledge that they have read, understood, and agreed to respect the research boundary as defined herein. The research system is the foundation of the product, and its integrity is paramount.

## Effective Date
This boundary is effective immediately upon the completion of Phase 20 and the declaration of research lock (as stated in HANDOFF.md and phase_20_completion.md).

## Contact
For any questions about what constitutes a permissible interaction with the research system, please consult the project lead or the research integrity officer.