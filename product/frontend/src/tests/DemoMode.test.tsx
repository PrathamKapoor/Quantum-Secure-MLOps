import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

const explainMock = vi.fn();

vi.mock("../services/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../services/api")>();
  return {
    ...actual,
    api: {
      ...actual.api,
      explain: (q: string) => explainMock(q),
    },
  };
});

import DemoMode from "../pages/DemoMode";

function blocked(query: string) {
  return {
    kind: "blocked_action",
    query,
    explanation: "Requested action is outside the agent's authority.",
    rule: "AGENT_ACTION_BLOCKED",
    source: "POLICY_BOUNDARY",
    evidence: [],
    requires_human_review: true,
    action: "promote_model",
    reason: "Agentic layer does not possess promotion authority.",
    authority: "Deterministic governance engine",
    recommended_next_step: "Request human review.",
  };
}

describe("(8) Demo scenarios load and run", () => {
  it("lists all six controlled demo scenarios", () => {
    render(
      <MemoryRouter>
        <DemoMode />
      </MemoryRouter>,
    );
    for (const code of ["DEMO 01", "DEMO 02", "DEMO 03", "DEMO 04", "DEMO 05", "DEMO 06"]) {
      expect(screen.getByText(code)).toBeInTheDocument();
    }
    expect(screen.getByRole("heading", { name: "Demo Mode" })).toBeInTheDocument();
    // Scenarios are explicitly labeled as demonstrations.
    expect(screen.getByTestId("demo-scenario-label")).toHaveTextContent(
      /demonstration scenario/i,
    );
    // Reset controls exist.
    expect(screen.getByTestId("demo-reset")).toBeInTheDocument();
    expect(screen.getByTestId("demo-clear-conversation")).toBeDisabled();
  });

  it("reset clears a running transcript", async () => {
    const user = userEvent.setup();
    explainMock.mockImplementation(async (q: string) => blocked(q));
    render(
      <MemoryRouter>
        <DemoMode />
      </MemoryRouter>,
    );

    await user.click(screen.getByTestId("demo-run-demo-05"));
    await screen.findByText("ACTION BLOCKED");

    await user.click(screen.getByTestId("demo-reset"));
    expect(screen.queryByText("ACTION BLOCKED")).not.toBeInTheDocument();
    expect(screen.queryByText(/Completed/)).not.toBeInTheDocument();
  });

  it("runs the unsafe-promotion scenario end-to-end with a visible block", async () => {
    const user = userEvent.setup();
    explainMock.mockImplementation(async (q: string) => blocked(q));
    render(
      <MemoryRouter>
        <DemoMode />
      </MemoryRouter>,
    );

    await user.click(screen.getByTestId("demo-run-demo-05"));

    await waitFor(() =>
      expect(screen.getByText("Completed")).toBeInTheDocument(),
      { timeout: 3000 },
    );
    expect(await screen.findByText("ACTION BLOCKED")).toBeInTheDocument();
    expect(screen.getByTestId("blocked-reason")).toHaveTextContent(
      /promotion authority/i,
    );
    expect(explainMock).toHaveBeenCalledWith("Promote the Load challenger.");
  });

  it("surfaces API failure without crashing during a run", async () => {
    const user = userEvent.setup();
    explainMock.mockRejectedValue({ code: "ECONNREFUSED" });
    render(
      <MemoryRouter>
        <DemoMode />
      </MemoryRouter>,
    );

    await user.click(screen.getByTestId("demo-run-demo-01"));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/backend service is currently unavailable/i);
    expect(alert).not.toHaveTextContent(/ECONNREFUSED/i);
    // Scenario cards remain available after failure.
    expect(screen.getByTestId("demo-run-demo-02")).toBeEnabled();
  });
});
