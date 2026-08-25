export interface HealthResponse {
  status: string;
  research_pipeline: string;
  product_api: string;
}

export interface ForecastStatusResponse {
  targets: string[];
  horizon: string;
  models_locked: boolean;
}

/** Row shape of final_predictions.csv served by /api/forecast/predictions */
export interface PredictionRow {
  timestamp: string;
  target: string;
  model: string;
  prediction: number;
  actual: number;
  absolute_error: number;
}

export interface ModelInfo {
  target: string;
  model_name: string;
  feature_set: string;
  fingerprint: string;
  lifecycle_state: string;
}

export interface DriftEvent {
  event_id?: string;
  timestamp: string | number | null;
  target: string | null;
  drift_type?: string | null;
  severity?: string | null;
  score?: number | null;
  explanation_reference?: string | null;
  reason?: string | null;
  ledger_seq?: number | null;
}

export interface GovernanceEvent {
  timestamp: string | number | null;
  seq?: number | null;
  type: string;
  actor: string;
  target: string;
  evidence_ref: string;
  reason?: string | null;
  details: Record<string, unknown>;
}

export interface EvidenceItem {
  ref: string;
  label: string;
  detail: Record<string, unknown> & { ledger_seq?: number };
  seq?: number | null;
}

/**
 * Response contract of POST /api/agents/explain.
 * `kind` distinguishes grounded explanations from refused protected actions.
 */
export interface AgentExplanationResponse {
  kind: "explanation" | "blocked_action";
  query: string;
  explanation: string;
  rule: string;
  source: string;
  evidence: EvidenceItem[];
  requires_human_review: boolean;
  // Present only when kind === "blocked_action"
  action?: string;
  reason?: string;
  authority?: string;
  recommended_next_step?: string;
}

export interface Report {
  type: string;
  name: string;
  path: string;
}

/* ---- Stage 1 API additions ---- */

export interface TargetForecastSummary {
  target: string;
  horizon: string;
  model: string | null;
  count: number | null;
  mae_from_absolute_errors: number | null;
}

export interface ModelVersion {
  model_name: string;
  version: number;
  version_id: string;
  state?: string | null;
  created_at?: string | number | null;
  [key: string]: unknown;
}

export interface ModelVersionDetail extends ModelVersion {
  passport_id?: string | null;
  feature_set?: string | null;
  signature_suite?: string | null;
  signed_by?: string | null;
}

export interface ExperimentSummary {
  experiment_id: string;
  name: string;
  lifecycle_stage?: string | null;
  run_count: number;
}

export interface ExperimentListResponse {
  available: boolean;
  experiments: ExperimentSummary[];
  note: string;
}

export interface ExperimentRun {
  run_id: string;
  name?: string | null;
  status?: string | null;
  start_time?: number | null;
  end_time?: number | null;
  params: Record<string, string>;
  metrics: Record<string, number>;
  tags: Record<string, string>;
}

export interface ExperimentDetailResponse {
  available: boolean;
  experiment: ExperimentSummary;
  runs: ExperimentRun[];
}

export type Severity = "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";

/** Locally-recorded human review request (UI demonstration only). */
export interface ReviewRequest {
  id: string;
  query: string;
  createdAt: string;
  rule: string | null;
}
