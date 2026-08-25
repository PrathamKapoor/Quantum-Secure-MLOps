# Product Architecture

## Overview
The productization layer builds upon the frozen research system to provide a user-friendly interface for interacting with the Guardrailed Agentic MLOps platform. The architecture follows a strict separation: the research pipeline (including models, datasets, features, evaluation results, frozen protocols, governance policies, agent safety boundaries, and final research artifacts) remains immutable. The product layer consumes the research system via well-defined APIs.

## High-Level Architecture
```
                    USER
                     |
                     v
              WEB DASHBOARD
                     |
                     v
              API SERVICE
                     |
        +------------+-------------+
        |                          |
        v                          v
 Forecasting Services       MLOps Services
        |                          |
        v                          v
 Model Registry              MLflow
        |
        v
 Governance Engine
        |
        v
 Agentic Explanation Layer
```

## Components

### 1. Web Dashboard (Frontend)
- Provides interactive visualization and user interface.
- Communicates exclusively with the API Service.
- Does not directly access research components.

### 2. API Service (Backend)
- Implemented as a FastAPI service.
- Exposes endpoints for:
  - Forecasting (predictions, model info)
  - Model registry (version listing, metadata)
  - Drift monitoring (drift reports, severity)
  - Governance (decisions, policy checks, audit events)
  - Agent assistance (explanations for decisions)
- Enforces authentication and authorization.
- All requests are logged to the evidence ledger for auditability.

### 3. Forecasting Services
- Consumes the frozen models from the model registry.
- Generates predictions on demand using the research system's inference pipeline.
- Does not modify models or trigger retraining.

### 4. MLOps Services
- Provides access to research system's MLOps capabilities:
  - Model registry queries
  - Evidence ledger access
  - Artifact store access (read-only)
  - Governance engine queries (policy status, decision history)
- All operations are read-only with respect to the research system.

### 5. Model Registry & MLflow
- Reads from the existing research model registry and MLflow tracking server.
- No writes to these components from the product layer.

### 6. Governance Engine
- Provides read-only access to governance policies, decision logs, and audit trails.
- The product layer cannot modify governance policies; it can only request actions that are then evaluated by the governance engine.

### 7. Agentic Explanation Layer
- Exposes agent findings and explanations via the API.
- The frontend can request explanations for specific decisions (e.g., why a model was not promoted).
- Agents do not execute lifecycle operations; they only provide evidence-based findings.

## Data Flow
1. User interacts with the Web Dashboard.
2. Dashboard sends requests to the API Service.
3. API Service calls the appropriate research system services (forecasting, MLOps, governance, agentic).
4. Research system returns data (read-only) to the API Service.
5. API Service processes and returns data to the Dashboard.
6. Dashboard updates the UI.

## Security Boundary
The frontend must not directly execute:
- Model promotion
- Rollback
- Retraining
- Policy changes
- Feature changes
All such actions must go through the API Service, which enforces governance checks before forwarding requests to the research system.

## Technology Stack
- Backend: FastAPI (Python)
- Frontend: React with Vite (or Next.js) - to be decided
- Visualization: Plotly and Recharts
- Existing storage: Used as-is (no replacement)