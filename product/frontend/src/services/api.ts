import axios from "axios";
import type {
  AgentExplanationResponse,
  DriftEvent,
  ExperimentDetailResponse,
  ExperimentListResponse,
  GovernanceEvent,
  HealthResponse,
  ModelInfo,
  ModelVersion,
  ModelVersionDetail,
  PredictionRow,
  Report,
} from "../types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

export const getBaseUrl = () => API_BASE_URL;

/**
 * Consistent, user-safe API error abstraction.
 * Raw exception details (stacks, socket codes, URLs) never reach the UI;
 * callers render the returned message verbatim.
 */
export function getApiErrorMessage(err: unknown): string {
  if (typeof err === "object" && err !== null) {
    const e = err as {
      code?: string;
      message?: string;
      response?: { status?: number };
    };
    if (
      e.code === "ECONNABORTED" ||
      (e.message ?? "").toLowerCase().includes("timeout")
    ) {
      return "The backend service did not respond in time. Please retry.";
    }
    if (e.response?.status) {
      return `Backend request failed (HTTP ${e.response.status}).`;
    }
    if (!e.response) {
      // Network error, connection refused, DNS failure, CORS…
      return "Backend service is currently unavailable.";
    }
  }
  return "Unexpected response from the backend service.";
}

export const api = {
  fetchHealth: () =>
    client.get<HealthResponse>("/health").then((r) => r.data),

  fetchForecastStatus: () =>
    client
      .get<{
        targets: string[];
        horizon: string;
        models_locked: boolean;
      }>("/api/forecast/status")
      .then((r) => r.data),

  fetchPredictions: () =>
    client.get<PredictionRow[]>("/api/forecast/predictions").then((r) => r.data),

  fetchModels: () => client.get<ModelInfo[]>("/api/models").then((r) => r.data),

  fetchDriftEvents: () =>
    client.get<DriftEvent[]>("/api/drift/events").then((r) => r.data),

  fetchGovernanceEvents: () =>
    client.get<GovernanceEvent[]>("/api/governance/events").then((r) => r.data),

  explain: (query: string) =>
    client
      .post<AgentExplanationResponse>("/api/agents/explain", { query })
      .then((r) => r.data),

  fetchReports: () => client.get<Report[]>("/api/reports").then((r) => r.data),

  /* ---- Stage 1 additions ---- */

  fetchPredictionsForTarget: (target: string) =>
    client
      .get<{
        target: string;
        horizon: string;
        model: string | null;
        count: number | null;
        mae_from_absolute_errors: number | null;
        predictions: PredictionRow[];
      }>(`/api/forecast/predictions/${encodeURIComponent(target)}`)
      .then((r) => r.data),

  fetchTargetSummary: (target: string) =>
    client
      .get<{
        target: string;
        horizon: string;
        model: string | null;
        count: number | null;
        mae_from_absolute_errors: number | null;
      }>(`/api/forecast/summary/${encodeURIComponent(target)}`)
      .then((r) => r.data),

  fetchModelVersions: (modelName: string) =>
    client
      .get<{ model_name: string; versions: ModelVersion[] }>(
        `/api/models/${encodeURIComponent(modelName)}/versions`,
      )
      .then((r) => r.data),

  fetchModelVersionDetail: (modelName: string, versionId: string) =>
    client
      .get<ModelVersionDetail>(
        `/api/models/${encodeURIComponent(modelName)}/versions/${encodeURIComponent(versionId)}`,
      )
      .then((r) => r.data),

  fetchExperiments: () =>
    client.get<ExperimentListResponse>("/api/experiments").then((r) => r.data),

  fetchExperimentDetail: (experimentId: string | number) =>
    client
      .get<ExperimentDetailResponse>(
        `/api/experiments/${encodeURIComponent(String(experimentId))}`,
      )
      .then((r) => r.data),

  fetchGovernanceDecisions: () =>
    client.get<GovernanceEvent[]>("/api/governance/decisions").then((r) => r.data),
};

export type ApiClient = typeof api;
