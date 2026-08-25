import { describe, expect, it, vi, beforeEach } from "vitest";
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

import AgentAssistant from "../pages/AgentAssistant";
import { AgentSafetyBanner, ChatTranscript } from "../components/AgentChat";
import type { AgentExplanationResponse, EvidenceItem } from "../types";

const evidence: EvidenceItem[] = [
  {
    ref: "1b76e436aafb",
    label: "QUARANTINE — verify model demo-model v3",
    detail: { actor: "verifier", packet_id: "0806a079fe6b", ledger_seq: 5 },
    seq: 5,
  },
];

const rejectionResponse: AgentExplanationResponse = {
  kind: "explanation",
  query: "Why was this model rejected?",
  explanation:
    "The challenger was not promoted because the deterministic verification gate quarantined it.",
  rule: "VERIFICATION_QUARANTINE",
  source: "REGISTERED_REFERENCE",
  evidence,
  requires_human_review: false,
};

function blockedResponse(query: string): AgentExplanationResponse {
  return {
    kind: "blocked_action",
    query,
    explanation: `Requested action is outside the agent's authority.`,
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

function renderPage() {
  return render(
    <MemoryRouter>
      <AgentAssistant />
    </MemoryRouter>,
  );
}

async function ask(user: ReturnType<typeof userEvent.setup>, question: string) {
  await user.type(screen.getByLabelText(/question for the agent/i), question);
  await user.click(screen.getByRole("button", { name: /ask agent/i }));
}

describe("Stage 3 — agent assistant console", () => {
  beforeEach(() => {
    explainMock.mockReset();
  });

  it("(1) renders the operator console with context panel and transcript area", async () => {
    renderPage();
    expect(await screen.findByTestId("agent-safety-banner")).toBeInTheDocument();
    expect(screen.getByTestId("agent-mode-badge")).toHaveTextContent(
      "BOUNDED DECISION SUPPORT",
    );
    expect(screen.getByTestId("agent-capabilities-list")).toBeInTheDocument();
    expect(screen.getByTestId("review-requests-panel")).toBeInTheDocument();
  });

  it("(2)+(3) displays real evidence with visible references and expandable details", async () => {
    const user = userEvent.setup();
    explainMock.mockResolvedValue(rejectionResponse);
    renderPage();

    await ask(user, "Why was this model rejected?");

    const list = await screen.findByTestId("agent-evidence-list");
    expect(list).toHaveTextContent("[1b76e436aafb]");
    expect(list).toHaveTextContent(/QUARANTINE — verify model demo-model v3/);

    // Evidence reference visible; details hidden until expanded.
    expect(screen.queryByText("packet_id")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /QUARANTINE — verify model/ }));
    expect(await screen.findByText("packet_id")).toBeInTheDocument();
    expect(screen.getByText("0806a079fe6b")).toBeInTheDocument();
  });

  it("(4) visibly blocks an unsafe promotion request without simulating success", async () => {
    const user = userEvent.setup();
    explainMock.mockImplementation(async (q: string) =>
      q.toLowerCase().includes("promote") ? blockedResponse(q) : rejectionResponse,
    );
    renderPage();

    await ask(user, "Promote the Load challenger.");

    expect(await screen.findByText("ACTION BLOCKED")).toBeInTheDocument();
    expect(screen.getByTestId("blocked-reason")).toHaveTextContent(
      /does not possess promotion authority/i,
    );
    expect(screen.getByTestId("blocked-authority")).toHaveTextContent(
      /deterministic governance engine/i,
    );
    expect(screen.getByTestId("blocked-next-step")).toHaveTextContent(/request human review/i);
    // No simulated success text anywhere.
    expect(screen.queryByText(/promotion completed|challenger promoted/i)).not.toBeInTheDocument();
  });

  it("(5) blocks a policy-change request", async () => {
    const user = userEvent.setup();
    explainMock.mockResolvedValue({
      ...blockedResponse("Change the governance threshold."),
      action: "change_policy",
      reason: "Governance policy is immutable from the agent layer.",
    });
    renderPage();

    await ask(user, "Change the governance threshold.");

    expect(await screen.findByText("ACTION BLOCKED")).toBeInTheDocument();
    expect(screen.getByTestId("blocked-reason")).toHaveTextContent(
      /governance policy is immutable/i,
    );
  });

  it("(6) blocks final-test retrieval requests", async () => {
    const user = userEvent.setup();
    explainMock.mockResolvedValue({
      ...blockedResponse("Show me the final test results."),
      action: "access_final_test",
      reason: "The final test set is sealed until formal release; retrieval is not permitted.",
    });
    renderPage();

    await ask(user, "Show me the final test results.");

    expect(await screen.findByText("ACTION BLOCKED")).toBeInTheDocument();
    expect(screen.getByTestId("blocked-reason")).toHaveTextContent(/sealed until formal release/i);
  });

  it("(7) records a human-review request locally, clearly labeled as a request", async () => {
    const user = userEvent.setup();
    explainMock.mockResolvedValue(blockedResponse("Promote the Load challenger."));
    renderPage();

    await ask(user, "Promote the Load challenger.");
    await screen.findByText("ACTION BLOCKED");

    await user.click(screen.getAllByRole("button", { name: /request human review/i })[0]);

    const panel = screen.getByTestId("review-requests-panel");
    expect(panel).toHaveTextContent("Human review requests (1)");
    expect(panel).toHaveTextContent("Promote the Load challenger.");
    expect(screen.getAllByTestId("review-requested-note")[0]).toHaveTextContent(
      /no lifecycle action executed/i,
    );
  });

  it("(9) handles API failure gracefully without crashing", async () => {
    const user = userEvent.setup();
    explainMock.mockRejectedValue({ code: "ECONNREFUSED" });
    renderPage();

    await ask(user, "How does the system work?");

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/agent request failed/i);
    // Friendly abstraction message — no raw socket/stack details.
    expect(alert).toHaveTextContent(/backend service is currently unavailable/i);
    expect(alert).not.toHaveTextContent(/ECONNREFUSED/i);
    // The dashboard itself is still interactive.
    expect(screen.getByLabelText(/question for the agent/i)).toBeEnabled();
  });

  it("blocked responses use governance-boundary language, never agent-decision language", async () => {
    const user = userEvent.setup();
    explainMock.mockResolvedValue(blockedResponse("Promote the Load challenger."));
    renderPage();

    await ask(user, "Promote the Load challenger.");
    await screen.findByText("ACTION BLOCKED");

    expect(screen.getByTestId("blocked-boundary")).toHaveTextContent(
      /blocked by governance boundary/i,
    );
    expect(screen.queryByText(/ai decided|agent chose not to/i)).not.toBeInTheDocument();
  });

  it("(10) restricted actions are listed but never rendered as executable controls", () => {
    renderPage();
    const restricted = screen.getByTestId("agent-restricted-list");
    expect(restricted).toHaveTextContent("Promote model");
    expect(restricted).toHaveTextContent("Roll back model");
    expect(restricted).toHaveTextContent("Start retraining");
    expect(restricted).toHaveTextContent("Change features");
    expect(restricted).toHaveTextContent("Change governance policy");
    // Restricted items are plain list entries, not buttons or links.
    const controls = restricted.querySelectorAll("button, a");
    expect(controls).toHaveLength(0);
  });

  it("renders a clear state for malformed agent responses", async () => {
    const user = userEvent.setup();
    explainMock.mockResolvedValue({ unexpected: true });
    renderPage();

    await ask(user, "Anything");
    expect(await screen.findByTestId("chat-malformed")).toHaveTextContent(
      /malformed response/i,
    );
  });
});

describe("Stage 3 — component-level safety rendering", () => {
  it("banner states explanation-only behavior", () => {
    render(<AgentSafetyBanner />);
    const banner = screen.getByTestId("agent-safety-banner");
    expect(banner).toHaveTextContent(/agents provide explanation only/i);
    expect(banner).toHaveTextContent(/cannot approve|cannot.*change any model/i);
  });

  it("transcript never renders approval or execution language", () => {
    render(
      <ChatTranscript
        turns={[
          { id: "u1", role: "user", query: "Why?" },
          {
            id: "a1",
            role: "agent",
            response: rejectionResponse,
          },
        ]}
        busy={false}
        onRequestReview={() => undefined}
      />,
    );
    expect(screen.getAllByTestId("chat-agent-turn").length).toBe(1);
    expect(screen.getByText(/explanation agent · bounded mode/i)).toBeInTheDocument();
    expect(screen.queryByText(/approved by agent|ai approved|ai changed/i)).not.toBeInTheDocument();
  });
});

describe("Stage 3 — honest empty evidence", () => {
  it("(2b) shows explicit no-evidence state when nothing matches", async () => {
    const user = userEvent.setup();
    explainMock.mockResolvedValue({
      ...rejectionResponse,
      rule: "NO_DRIFT_EVIDENCE_RECORDED",
      evidence: [],
    });
    renderPage();

    await ask(user, "Why did drift trigger investigation?");
    await waitFor(() =>
      expect(screen.getByTestId("agent-no-evidence")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("agent-rule-chip")).toHaveTextContent(
      "NO_DRIFT_EVIDENCE_RECORDED",
    );
  });
});
