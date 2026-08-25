# Backend API Service

This is the backend API layer for the productization of the Guardrailed Agentic MLOps Platform.

## Purpose

The API layer provides a clean, versioned interface to the research system's capabilities. It enforces the security boundary by only allowing read operations and explanations, blocking any write operations that could modify the research system.

## Architecture

The API is built with FastAPI and includes the following routers:

- `/health`: Health check endpoint
- `/api/forecast`: Forecasting status and predictions
- `/api/models`: Model registry information
- `/api/drift`: Drift monitoring events
- `/api/governance`: Governance decisions and events
- `/api/agents`: Agent explanations and findings
- `/api/reports`: Available reports (phase reports, final evaluation, etc.)

## Security Boundary

The API enforces that:
- No write operations are allowed on the research system (models, datasets, features, etc.)
- All interactions with the research system are read-only.
- The agent API only allows explanations, not actions that could modify the system.
- The governance API only allows reading decisions, not making new decisions.

## Running the API

To run the API in development:

```bash
# From the project root
python -m product.backend_api.app.main
```

Or using uvicorn:

```bash
uvicorn product.backend_api.app.main:app --reload
```

The API will be available at http://localhost:8000.

## API Documentation

Once the API is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Tests for the API are located in the `tests/` directory (to be created).

## Notes

- The API relies on the research system being available and immutable.
- The API does not contain business logic that replaces existing research modules; it only exposes existing capabilities.
- All requests are logged to the evidence ledger for auditability.