import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
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
    fetchPredictions: vi.fn().mockResolvedValue([]),
    fetchModels: vi.fn().mockResolvedValue([
      {
        target: "load",
        model_name: "Random Forest",
        feature_set: "core_v1",
        fingerprint: "abc123",
        lifecycle_state: "REGISTERED",
      },
      {
        target: "wind",
        model_name: "Random Forest",
        feature_set: "core_v1",
        fingerprint: "def456",
        lifecycle_state: "QUARANTINED",
      },
    ]),
    fetchDriftEvents: vi.fn().mockResolvedValue([]),
    fetchGovernanceEvents: vi.fn().mockResolvedValue([]),
    explain: vi.fn(),
    fetchReports: vi.fn().mockResolvedValue([]),
  },
}));

import App from "../App";

async function renderApp() {
  return render(
    <MemoryRouter>
      <App />
    </MemoryRouter>,
  );
}

describe("Dashboard navigation", () => {
  it("renders all sidebar sections including demo mode", async () => {
    await renderApp();
    const nav = screen.getByRole("navigation", { name: /main navigation/i });
    const { within } = await import("@testing-library/react");
    for (const label of [
      "Overview",
      "Forecasting",
      "Models",
      "Drift Monitoring",
      "Governance",
      "Agent Assistant",
      "Demo Mode",
      "Reports",
    ]) {
      expect(within(nav).getByRole("link", { name: label })).toBeInTheDocument();
    }
  });

  it("navigates to the Model Registry and shows the read-only notice", async () => {
    const user = (await import("@testing-library/user-event")).default.setup();
    await renderApp();
    await screen.findByText("Overview");

    await user.click(screen.getByRole("link", { name: "Models" }));

    expect(await screen.findByRole("heading", { name: "Model Registry" })).toBeInTheDocument();
    expect(screen.getByText(/read-only registry/i)).toBeInTheDocument();
    // Registry roles distinguish challengers from production models.
    const roles = screen.getAllByTestId("registry-role").map((n) => n.textContent);
    expect(roles).toContain("Challenger");
    expect(roles).toContain("Promotion-rejected");
    expect(screen.getByTestId("registry-role-note")).toHaveTextContent(
      /challengers are evaluation candidates/i,
    );
    // No write-action buttons exist anywhere on the page.
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /retrain/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /rollback/i })).not.toBeInTheDocument();
  });

  it("shows the locked research pipeline indicator in the sidebar", async () => {
    await renderApp();
    expect(screen.getByText(/research pipeline locked/i)).toBeInTheDocument();
  });
});
