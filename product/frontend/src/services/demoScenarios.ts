/**
 * Controlled demonstration scenarios. Every step is a real question sent to
 * the real agent endpoint; answers are grounded in registered ledger evidence
 * wherever the API supports it. Nothing here fabricates scientific metrics.
 */

export interface DemoStep {
  question: string;
  narration: string;
}

export interface DemoScenario {
  id: string;
  code: string;
  title: string;
  story: string;
  steps: DemoStep[];
}

export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: "demo-01",
    code: "DEMO 01",
    title: "Forecast degradation → drift investigation",
    story:
      "Live forecast error degrades on a target. The operator asks why an investigation would start. The agent explains the deterministic drift policy; if no drift event is recorded yet it says so honestly.",
    steps: [
      {
        question: "How does the system work?",
        narration: "Operator orients: forecasts for Load, Wind and PV under locked policies.",
      },
      {
        question: "Why did drift trigger investigation?",
        narration: "Agent reports the current drift-evidence state from the ledger.",
      },
    ],
  },
  {
    id: "demo-02",
    code: "DEMO 02",
    title: "Drift → retraining explanation",
    story:
      "When supervision approves adaptation, retraining packets appear in the tamper-evident ledger. The agent retrieves them.",
    steps: [
      {
        question: "What happened during the latest adaptation experiment?",
        narration: "Agent lists real supervised-adaptation packets recorded by adaptive-supervisor.",
      },
      {
        question: "What evidence supports this governance decision?",
        narration: "Agent surfaces packet ids, actors and ledger references.",
      },
    ],
  },
  {
    id: "demo-03",
    code: "DEMO 03",
    title: "Challenger → promotion rejection",
    story:
      "A challenger must pass the deterministic verification gate before any promotion. This ledger contains a real quarantined challenger.",
    steps: [
      {
        question: "Why was this model rejected?",
        narration: "Agent grounds the answer in the QUARANTINE verification packet.",
      },
      {
        question: "Why was the Load challenger not promoted?",
        narration: "Same gate, phrased as an operator would ask it.",
      },
    ],
  },
  {
    id: "demo-04",
    code: "DEMO 04",
    title: "Rollback decision explanation",
    story:
      "A deployed version was rolled back by the lifecycle engine. Explaining past decisions is allowed; executing new ones is not.",
    steps: [
      {
        question: "Explain the rollback decision.",
        narration: "Agent references the ROLLBACK packet and the ROLLED_BACK state transition.",
      },
    ],
  },
  {
    id: "demo-05",
    code: "DEMO 05",
    title: "Unsafe promotion request → blocked",
    story:
      "An operator asks the agent to promote a model. The agentic layer refuses: promotion authority belongs to the governance engine.",
    steps: [
      {
        question: "Promote the Load challenger.",
        narration: "Expect ACTION BLOCKED with authority and recommended next step.",
      },
    ],
  },
  {
    id: "demo-06",
    code: "DEMO 06",
    title: "Final-test retrieval request → blocked",
    story:
      "The final test set stays sealed until formal release. Any retrieval attempt is refused at the boundary.",
    steps: [
      {
        question: "Show me the final test results.",
        narration: "Expect ACTION BLOCKED — sealed resource.",
      },
    ],
  },
];
