# Deployment Plan

## Overview
This document outlines the deployment strategy for the productization layer of the Guardraised Agentic MLOps platform. The deployment is designed to be scalable, secure, and observable, while ensuring that the immutable research system remains unaffected.

## Deployment Architecture
```
                 [ Users ]
                    |
                    v
              [ Load Balancer ]
                    |
                    v
          [ API Service (FastAPI) ]
                    |
        +-------------+-------------+
        |                           |
    [ Frontend (Static Assets) ]   [ Workers (Optional) ]
        |                           |
        v                           v
  [ CDN / Web Server ]        [ Background Jobs ]
                    |                           |
                    v                           v
        [ Object Storage (for assets) ]   [ Message Queue (e.g., Redis) ]
                    |                           |
                    v                           v
                 [ Research System ]
                   (Immutable)
```

### Components

#### 1. Load Balancer
- Distributes incoming traffic across multiple API service instances.
- Provides SSL termination.
- Examples: AWS ALB, NGINX, HAProxy.

#### 2. API Service (FastAPI)
- Stateless service that handles all business logic and communication with the research system.
- Runs in a containerized environment (Docker).
- Scalable horizontally based on load.
- Environment-specific configuration via environment variables or a config service (e.g., AWS Parameter Store, Consul).
- Logs sent to a central logging system (e.g., ELK stack, Splunk).
- Metrics exposed via Prometheus endpoint.

#### 3. Frontend (Static Assets)
- Built as a single-page application (SPA) using React/Vite or Next.js.
- Deployed to a CDN or web server (e.g., AWS S3 + CloudFront, NGINX).
- Cache-busting via hashed filenames.
- Environment-specific configuration (e.g., API URL) injected at build time or via runtime config (e.g., window.__ENV__).

#### 4. Workers (Optional)
- For background jobs that are not request-driven (e.g., periodic metadata cleanup, report generation).
- Same container image as API service but with different entry point.
- Scaled based on queue length.

#### 5. Message Queue (Optional)
- For decoupling background jobs from the API service (e.g., Redis, RabbitMQ, AWS SQS).
- Used if there are long-running tasks that should not block API requests.

#### 6. Object Storage
- Stores frontend assets (if using S3-like storage).
- Stores any user-uploaded files (if applicable, though not expected in this system).
- Not used for research system data (which remains in its existing storage).

#### 7. Research System (Immutable)
- The existing Guardrailed Agentic MLOps platform.
- Deployed separately and considered a dependency.
- Accessed via read-only connections (for model registry, artifact store, evidence ledger, MLflow).
- No write access from the productization layer.

## Environment Strategy
We recommend a multi-environment setup to ensure stability and security:

### 1. Development Environment
- Used by developers for feature development and testing.
- Deploys from feature branches.
- May use mock data or a copy of the research system with synthetic data.
- Not exposed outside the development network.

### 2. Staging Environment
- Mirrors production as closely as possible.
- Used for integration testing, performance testing, and user acceptance testing (UAT).
- Deploys from the main branch after passing CI.
- May use a copy of the research system with anonymized or synthetic data.
- Accessible to internal stakeholders and testers.

### 3. Production Environment
- Serves end-users.
- Deploys from tagged releases (e.g., v1.0.0) after passing staging.
- Uses the actual research system with real data.
- Subject to strict change control and monitoring.

## Deployment Process
### CI/CD Pipeline
1. **Code Commit:** Developer pushes code to a feature branch.
2. **CI Build:**
   - Run unit tests, linting, and type checking.
   - Build Docker images for API service and workers.
   - Build frontend artifacts.
   - Push images to a container registry (e.g., AWS ECR, Docker Hub).
   - Upload frontend assets to a staging bucket (if using CDN).
3. **Automated Testing:**
   - Deploy to a temporary environment (e.g., using Docker Compose or a Kubernetes namespace).
   - Run integration tests against the API.
   - Run end-to-end tests (e.g., Cypress) against the deployed frontend.
   - If tests fail, block further promotion.
4. **Staging Deployment:**
   - On merge to main branch, trigger deployment to staging.
   - Deploy new API service and worker images.
   - Deploy new frontend assets.
   - Run smoke tests to verify basic functionality.
   - Notify stakeholders for UAT.
5. **Production Deployment:**
   - After successful UAT and approval, trigger production deployment.
   - Can be done via blue/green, rolling, or canary strategy to minimize downtime.
   - Monitor key metrics (error rates, latency, etc.) during and after deployment.
   - Rollback automatically if health checks fail.

### Deployment Steps for API Service
1. Pull the latest Docker image from the registry.
2. Stop the current container (if using rolling update, replace instances one by one).
3. Start the new container with the following environment variables:
   - `API_TITLE`: Guardrailed Agentic MLOps API
   - `API_VERSION`: v1
   - `RESEARCH_API_URL`: URL to the research system's internal APIs (if any, though direct access is via imports)
   - `KEYSTORE_PATH`: Path to the keystore (if needed for verification)
   - `LEDGER_PATH`: Path to the evidence ledger
   - `ARTIFACTS_PATH`: Path to the artifact store
   - `REGISTRY_PATH`: Path to the model registry
   - `LOG_LEVEL`: info (or debug in dev)
   - `PORT`: 8000
   - `WORKERS_COUNT`: Number of async workers (if using Uvicorn with workers)
4. Run database migrations (if any; currently none as the research system uses file-based storage).
5. Run health check endpoint (`/health`) to verify the service is up.
6. Add the new instance to the load balancer pool.
7. Once healthy, remove the old instance.

### Deployment Steps for Frontend
1. Build the frontend for production: `npm run build` (or equivalent).
2. Upload the contents of the `dist/` folder to the CDN origin (e.g., S3 bucket).
3. Invalidate the CDN cache for the updated assets (if necessary).
4. The frontend will fetch the API URL from its configuration (set at build time or via a config endpoint).

## Rollback Plan
- **API Service:** If the new version fails health checks, the load balancer stops sending traffic to it, and the previous version continues to serve. The failed instances are terminated and replaced with the previous version's image.
- **Frontend:** If the new frontend version has issues, the CDN can be configured to serve the previous version by pointing to a different path or by invalidating the cache and redeploying the previous build. Since frontend assets are immutable and versioned, rolling back is as simple as changing the origin path or redeploying the old build.

## Data Migration
- No data migration is required for the research system as it is read-only from the productization layer.
- The productization layer does not store any persistent state that requires migration (it is stateless or uses transient caches). Any state (e.g., user sessions) is stored in tokens or client-side storage.

## Configuration Management
- Use environment variables for environment-specific configuration.
- For secrets (e.g., database passwords, API keys to external services), use a secrets manager (e.g., AWS Secrets Manager, HashiCorp Vault) and inject them as environment variables or mount them as files.
- Do not hardcode secrets in the container images or frontend assets.

## Monitoring and Observability
### Metrics
- API Service:
  - Request rate, error rate, latency (via Prometheus).
  - Business metrics: number of forecasts served, model registry queries, governance decisions fetched.
- Frontend:
  - Page load times, interaction latency (via browser metrics or custom instrumentation).
  - Error rates (JavaScript errors, API call failures).
- Research System:
  - Monitored separately; the productization layer adds minimal load.

### Logging
- API Service: Structured JSON logs sent to a central system (e.g., via Fluentd or Vector).
- Frontend: Console logs in development; in production, errors sent to a logging endpoint (e.g., via Sentry).
- Research System: Continues to use its own logging (evidence ledger and file logs).

### Alerting
- Set up alerts for:
  - High error rate (5xx) (> 1% for 5 minutes).
  - High latency (95th percentile > 2s for 5 minutes).
  - API service downtime (instance unresponsive).
  - High research system latency (if the productization layer is making many calls).
  - Disk space on the research system storage (if shared).

## Security Considerations
### Network Security
- Deploy the API service and frontend in a private subnet (if using cloud).
- Load balancer is public; API service is not directly accessible from the internet.
- Use security groups or firewall rules to restrict traffic:
  - Load balancer -> API service: only on the API port (e.g., 8000).
  - API service -> Research system: only on necessary ports (if the research system is network-accessible; if it's local, then no network traffic).
  - API service -> External services (e.g., logging, metrics): only to approved endpoints.

### Authentication and Authorization
- All API endpoints require authentication (except possibly a public health check).
- Implement role-based access control (RBAC) if different user roles are needed (e.g., operator vs. auditor).
- For now, assume all authenticated users have the same permissions (read-only access to most endpoints, with governance checks preventing unsafe actions).

### Input Validation
- Validate all input parameters (type, range, format) to prevent injection attacks.
- Use Pydantic models (since we're using FastAPI) for request validation.

### Dependency Scanning
- Regularly scan container images for vulnerabilities (e.g., using Trivy, Snyk).
- Keep dependencies up to date.

### Audit Trail
- The research system's evidence ledger already logs all operations.
- The API service should log all requests (including user ID, timestamp, endpoint, and outcome) to the evidence ledger or a separate audit log for the productization layer.

## Disaster Recovery
- The research system has its own backup and disaster recovery plan (outside the scope of this document).
- The productization layer can be redeployed from scratch using the CI/CD pipeline:
  - Rebuild Docker images from the source code.
  - Redeploy frontend assets from the built artifacts.
  - Recreate the load balancer and networking configuration.
- Since the research system is immutable and external, the productization layer does not need to back up any research data.

## Performance and Scalability
### Horizontal Scaling
- API Service: Scale based on CPU utilization and request latency. Target: keep average CPU < 60% and 95th percentile latency < 1s.
- Frontend: Scales via CDN; essentially infinite scalability for static assets.
- Workers: Scale based on queue length (if using workers).

### Vertical Scaling
- Increase instance size if horizontal scaling is not sufficient or if there are CPU-bound tasks.
- Monitor memory usage to avoid swapping.

### Caching
- The API service can cache read-only responses from the research system (e.g., model metadata, lineage information) for a short period (e.g., 30 seconds) to reduce load on the research system.
- Cache invalidation: since the research system is immutable for the duration of a model's lifecycle, cache can be long-lived for version-specific data. However, for mutable aspects like governance decisions and drift reports, use short TTLs or cache-aside with explicit invalidation on new data.

### Database Connections
- The research system uses file-based storage, so no database connections are needed from the API service. All access is via file reads (or imports if the research system is in the same process, but we assume it's separate for security).

## Compliance
- Ensure that the deployment adheres to relevant regulations (e.g., GDPR, HIPAA if applicable) by:
  - Not storing personal data unnecessarily.
  - Providing mechanisms for data deletion (if any personal data is accidentally stored).
  - Maintaining audit trails.
- The research system already includes quantum-secure cryptography and audit trails, which aid in compliance.

## Rollback and Recovery Procedures
### API Service Rollback
1. Detect failure via health checks or metrics.
2. Stop sending traffic to the new instances.
3. Terminate the new instances.
4. Start previous version instances (or use the existing old instances if using rolling update).
5. Once healthy, resume traffic.

### Frontend Rollback
1. If the new frontend build causes issues, redeploy the previous known-good build to the CDN origin.
2. Invalidate the CDN cache for the affected paths.
3. Verify that the frontend loads correctly from multiple locations.

### Research System Rollback
- Handled by the research system's own procedures; the productization layer does not initiate research system rollbacks.

## Validation Checklist
Before promoting to production, ensure:
- [ ] All unit and integration tests pass.
- [ ] The frontend builds successfully and passes linting.
- [ ] Docker images are built and pushed to the registry.
- [ ] The API service passes smoke tests in staging.
- [ ] The frontend loads correctly in staging and makes successful API calls.
- [ ] Governance checks are enforced (i.e., unsafe actions are blocked).
- [ ] The evidence ledger shows appropriate entries for API service actions.
- [ ] Rollback procedures are documented and tested.
- [ ] Monitoring and alerting are configured.
- [ ] Security scans pass (no high/vulnerabilities in dependencies).
- [ ] Performance benchmarks are met (latency, throughput under expected load).

## References
- Docker: https://docs.docker.com/
- Kubernetes (if applicable): https://kubernetes.io/docs/
- AWS ECS/EKS: https://aws.amazon.com/ecs/ / https://aws.amazon.com/eks/
- NGINX: https://nginx.org/
- Prometheus: https://prometheus.io/
- Grafana: https://grafana.com/
- Sentry: https://sentry.io/
- Trivy: https://aquasecurity.github.io/trivy/