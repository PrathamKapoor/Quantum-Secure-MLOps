import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../services/api", () => ({
  getBaseUrl: () => "http://localhost:8000",
  api: {
    fetchHealth: vi
      .fn()
      .mockResolvedValue({ status: "healthy", research_pipeline: "locked", product_api: "running" }),
    fetchForecastStatus: vi.fn().mockResolvedValue({
      targets: ["load", "wind", "pv"],
      horizon: "H24",
      models_locked: true,
    }),
    fetchModels: vi.fn().mockResolvedValue([
      {
        target: "wind",
        model_name: "Random Forest",
        feature_set: "core_v1",
        fingerprint: "fp-1",
        lifecycle_state: "ACTIVE",
      },
    ]),
    fetchGovernanceEvents: vi.fn().mockResolvedValue([
      { timestamp: 1735689600000, type: "MODEL_PROMOTION_BLOCKED", details: { actor: "governance" } },
    ]),
    fetchDriftEvents: vi.fn().mockResolvedValue([]),
    fetchPredictions: vi.fn().mockResolvedValue([]),
    explain: vi.fn(),
    fetchReports: vi.fn().mockResolvedValue([]),
  },
}));

import Overview from "../pages/Overview";

function renderPage() {
  return render(
    <MemoryRouter>
      <Overview />
    </MemoryRouter>,
  );
}

describe("Overview dashboard rendering", () => {
  it("renders system status from /health", async () => {
    renderPage();
    expect(
      await screen.findByRole("heading", { name: "System Status" }),
    ).toBeInTheDocument();
    expect(screen.getByText("healthy")).toBeInTheDocument();
    expect(screen.getByText("locked")).toBeInTheDocument();
  });

  it("lists all three forecast targets", async () => {
    renderPage();
    await screen.findByRole("heading", { name: "Forecast Targets" });
    expect(await screen.findByText("Load")).toBeInTheDocument();
    expect(screen.getByText("Wind")).toBeInTheDocument();
    expect(screen.getByText("PV")).toBeInTheDocument();
  });

  it("shows model health counts and governance status", async () => {
    renderPage();
    expect(await screen.findByText("Registered")).toBeInTheDocument();
    expect(screen.getByText("Blocked actions")).toBeInTheDocument();
    const govCard = screen
      .getByRole("heading", { name: "Governance Status" })
      .closest("section")!;
    // Mock has one governance event of which one is a blocked action.
    expect(within(govCard).getAllByText("1")).toHaveLength(2);
  });

  it("communicates bounded agent mode", async () => {
    renderPage();
    expect(await screen.findByText("Bounded mode")).toBeInTheDocument();
    expect(screen.getByText(/cannot promote|cannot.*modify any model/i)).toBeTruthy();
  });

  it("shows the platform system story strip", async () => {
    renderPage();
    const story = await screen.findByTestId("system-story");
    expect(story).toHaveTextContent("How this platform works");
    expect(story).toHaveTextContent("Forecasting");
    expect(story).toHaveTextContent("Drift monitoring");
    expect(story).toHaveTextContent("Deterministic governance");
    expect(story).toHaveTextContent("Challenger evaluation");
    // The agent stage must communicate explain-only authority.
    expect(story).toHaveTextContent(/explain only — no execution/i);
  });
});
