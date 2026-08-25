The following limitations apply to the research presented:

1. **Single Dataset**: Evaluation was conducted on the synthetic RTS-GMLC dataset; generalization to real-world utility data remains untested.
2. **Limited Temporal Coverage**: The dataset spans one year; multi-year seasonal extremes and rare events (e.g., storms) are not represented.
3. **Simulated Drift**: Drift detection and recovery mechanisms were not activated during evaluation due to stationary synthetic data; long-term drift adaptation is unvalidated.
4. **Simulated Operational Workflows**: The self-healing pipeline was tested in a controlled environment; real-world integration with SCADA and EMS systems is pending.
5. **No Production Grid Deployment**: The system has not been deployed in an operational smart grid; all results are from simulation.
6. **No Human Operator Study**: The agentic-supervisor interaction was not evaluated with human operators; usability and trust effects are unknown.
7. **Bounded Agent Scope**: Agent capabilities are limited to predefined functions (data validation, drift detection, etc.); open-ended agentic behaviors are not supported.
8. **External Benchmark Dependency**: Baseline comparisons rely on external implementations (RTS DAY_AHEAD, H24 Daily Persistence) that were not integrated into the codebase.
9. **Quantum Cryptography Overhead**: Post-quantum cryptographic operations introduce computational latency; performance impacts on high-frequency forecasting are unmeasured.
10. **Policy Language Expressiveness**: Hard-coded governance policies limit adaptability to evolving regulatory requirements without code changes.

These limitations delineate the scope of the claimed contributions and identify avenues for future work.