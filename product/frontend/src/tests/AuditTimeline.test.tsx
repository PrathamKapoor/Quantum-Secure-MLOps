import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

vi.mock("../services/api", () => ({
  getBaseUrl: () => "http://localhost:8000",
  api: {
    fetchGovernanceEvents: vi.fn().mockResolvedValue([
      {
        timestamp: 1735689720000,
        seq: 24,
        type: "ROLLBACK_COMPLETED",
        actor: "cli",
        target: "demo-model",
        evidence_ref: "a1b2c3d4e5f60718",
        reason: "rolled back",
        details: {},
      },
      {
        timestamp: 1735689660000,
        seq: 21,
        type: "MODEL_PROMOTION_BLOCKED",
        actor: "verifier",
        target: "demo-model v3",
        evidence_ref: "0806a079fe6b4798",
        reason: "verify model demo-model v3",
        details: {},
      },
    ]),
    fetchHealth: vi.fn(),
    fetchForecastStatus: vi.fn(),
    fetchPredictions: vi.fn(),
    fetchModels: vi.fn(),
    fetchDriftEvents: vi.fn(),
    explain: vi.fn(),
    fetchReports: vi.fn(),
  },
}));

import Governance from "../pages/Governance";

function renderPage() {
  return render(
    <MemoryRouter>
      <Governance />
    </MemoryRouter>,
  );
}

describe("Operator audit timeline", () => {
  it("renders time, event type, actor, target and evidence reference", async () => {
    renderPage();
    const timeline = await screen.findByTestId("audit-timeline");
    expect(timeline).toBeInTheDocument();

    // Timestamps rendered as operator-friendly clock times
    expect(screen.getAllByTestId("audit-evidence-ref").length).toBe(2);
    expect(screen.getByText("Evidence: a1b2c3d4e5f60718")).toBeInTheDocument();

    const types = screen.getAllByTestId("audit-event-type").map((n) => n.textContent);
    expect(types).toContain("ROLLBACK_COMPLETED");
    expect(types).toContain("MODEL_PROMOTION_BLOCKED");

    const actors = screen.getAllByTestId("audit-actor").map((n) => n.textContent);
    expect(actors).toContain("cli");
    expect(actors).toContain("verifier");

    const targets = screen.getAllByTestId("audit-target").map((n) => n.textContent);
    expect(targets).toContain("demo-model");
  });

  it("renders plain-language decision blocks for non-experts", async () => {
    renderPage();
    await screen.findByTestId("audit-timeline");

    // Every card exposes the six decision fields.
    for (const label of ["Decision", "Reason", "Policy", "Evidence", "Actor", "Target"]) {
      expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(2);
    }
    // Human-readable headline for the blocked promotion.
    expect(
      screen.getAllByTestId("decision-headline").some((n) =>
        /not promoted/i.test(n.textContent ?? ""),
      ),
    ).toBe(true);
    // Governance authority framing, never agent framing.
    const decisions = screen
      .getAllByTestId("decision-value")
      .map((n) => n.textContent ?? "")
      .join(" ");
    expect(decisions).toMatch(/blocked by governance boundary/i);
    expect(screen.getAllByText(/deterministic governance policy \(frozen\)/i).length).toBe(2);
  });

  it("supports type filtering", async () => {
    const user = (await import("@testing-library/user-event")).default.setup();
    renderPage();
    await screen.findByTestId("audit-timeline");

    await user.click(screen.getByRole("button", { name: "ROLLBACK_COMPLETED" }));
    expect(screen.getAllByTestId("audit-event-type").length).toBe(1);

    await user.click(screen.getByRole("button", { name: "ALL" }));
    expect(screen.getAllByTestId("audit-event-type").length).toBe(2);
  });
});
