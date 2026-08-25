import { describe, expect, it, vi, beforeEach } from "vitest";

const getMock = vi.fn();
const postMock = vi.fn();

vi.mock("axios", () => ({
  default: {
    create: () => ({
      get: (...args: unknown[]) => getMock(...args),
      post: (...args: unknown[]) => postMock(...args),
    }),
  },
}));

// Import after the axios mock is in place.
const { api, getBaseUrl, getApiErrorMessage } = await import("../services/api");

function lastGetUrl() {
  const call = getMock.mock.calls.at(-1);
  return { url: call?.[0] as string };
}

describe("API error abstraction", () => {
  it("maps network failure to a friendly unavailable message", () => {
    const msg = getApiErrorMessage({ code: "ECONNREFUSED", message: "connect ECONNREFUSED" });
    expect(msg).toBe("Backend service is currently unavailable.");
  });

  it("maps timeout to a retry message", () => {
    expect(getApiErrorMessage({ code: "ECONNABORTED" })).toMatch(/did not respond in time/i);
    expect(getApiErrorMessage(new Error("timeout of 15000ms exceeded"))).toMatch(
      /did not respond in time/i,
    );
  });

  it("maps HTTP statuses without exposing internals", () => {
    expect(getApiErrorMessage({ response: { status: 500 } })).toBe(
      "Backend request failed (HTTP 500).",
    );
    expect(getApiErrorMessage({ response: { status: 404 } })).toBe(
      "Backend request failed (HTTP 404).",
    );
  });

  it("never leaks stack traces or raw exception text", () => {
    // A generic Error carries no response → treated as network failure,
    // and its message must never surface.
    const msg = getApiErrorMessage(new Error("secret internal path /c:/x/y at line 42"));
    expect(msg).not.toMatch(/secret|line 42/);
    expect(msg).toBe("Backend service is currently unavailable.");
  });

  it("handles non-object throws safely", () => {
    expect(getApiErrorMessage(undefined)).toBe(
      "Unexpected response from the backend service.",
    );
    expect(getApiErrorMessage("boom")).toBe(
      "Unexpected response from the backend service.",
    );
  });
});

describe("API service layer", () => {
  beforeEach(() => {
    getMock.mockReset();
    postMock.mockReset();
    getMock.mockResolvedValue({ data: {} });
    postMock.mockResolvedValue({ data: {} });
  });

  it("fetchHealth hits /health", async () => {
    await api.fetchHealth();
    expect(lastGetUrl().url).toBe("/health");
  });

  it("fetchForecastStatus hits the status endpoint", async () => {
    await api.fetchForecastStatus();
    expect(lastGetUrl().url).toBe("/api/forecast/status");
  });

  it("fetchPredictions hits the predictions endpoint", async () => {
    await api.fetchPredictions();
    expect(lastGetUrl().url).toBe("/api/forecast/predictions");
  });

  it("fetchModels is a GET (read-only)", async () => {
    await api.fetchModels();
    expect(lastGetUrl().url).toBe("/api/models");
    expect(getMock).toHaveBeenCalledTimes(1);
    expect(postMock).not.toHaveBeenCalled();
  });

  it("fetchDriftEvents and fetchGovernanceEvents use read-only GETs", async () => {
    await api.fetchDriftEvents();
    expect(lastGetUrl().url).toBe("/api/drift/events");
    await api.fetchGovernanceEvents();
    expect(lastGetUrl().url).toBe("/api/governance/events");
    expect(postMock).not.toHaveBeenCalled();
  });

  it("explain POSTs the query body to /api/agents/explain", async () => {
    await api.explain("Why was this model rejected?");
    expect(postMock).toHaveBeenCalledWith("/api/agents/explain", {
      query: "Why was this model rejected?",
    });
  });

  it("fetchReports hits /api/reports", async () => {
    await api.fetchReports();
    expect(lastGetUrl().url).toBe("/api/reports");
  });

  it("exposes a configurable base URL defaulting to localhost:8000", () => {
    expect(getBaseUrl()).toContain("localhost:8000");
  });

  it("never exposes write operations other than explain", () => {
    const fns = Object.keys(api);
    for (const fn of fns) {
      if (fn !== "explain") {
        // every non-explain operation must resolve via GET
        // (verified per-function above; here assert no delete/put helpers exist)
        expect(fn.toLowerCase()).not.toMatch(/promote|retrain|rollback|delete|quarantine/);
      }
    }
  });
});
