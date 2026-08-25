import { useCallback, useState } from "react";
import type { FormEvent } from "react";
import { api, getApiErrorMessage } from "../services/api";
import { DEMO_SCENARIOS } from "../services/demoScenarios";
import {
  AgentSafetyBanner,
  ChatTranscript,
  SuggestionChips,
} from "../components/AgentChat";
import type { ChatTurn, SuggestedQuestion } from "../components/AgentChat";
import AgentContextPanel from "../components/AgentContextPanel";
import { PageHeader } from "../components/ui";
import type { ReviewRequest } from "../types";

const SUGGESTIONS: SuggestedQuestion[] = [
  { label: "Why was the Load model rejected?", query: "Why was the Load model rejected?" },
  { label: "Why did drift trigger investigation?", query: "Why did drift trigger investigation?" },
  { label: "Why was this challenger not promoted?", query: "Why was this challenger not promoted?" },
  { label: "What evidence supports this governance decision?", query: "What evidence supports this governance decision?" },
  { label: "What happened during the latest adaptation experiment?", query: "What happened during the latest adaptation experiment?" },
];

let turnCounter = 0;
const nextId = () => `turn-${++turnCounter}`;

export default function AgentAssistant() {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewRequests, setReviewRequests] = useState<ReviewRequest[]>([]);

  const ask = useCallback(async (query: string) => {
    if (!query.trim() || busy) return;
    setError(null);
    setBusy(true);
    setTurns((t) => [...t, { id: nextId(), role: "user", query }]);
    try {
      const response = await api.explain(query);
      const malformed =
        !response || typeof response.explanation !== "string" || !Array.isArray(response.evidence);
      setTurns((t) => [
        ...t,
        {
          id: nextId(),
          role: "agent",
          response: malformed ? undefined : response,
          malformed,
        },
      ]);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }, [busy]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    setInput("");
    void ask(q);
  };

  const requestReview = useCallback((turnId: string) => {
    setTurns((prev) =>
      prev.map((t) => (t.id === turnId && !t.reviewRequested ? { ...t, reviewRequested: true } : t)),
    );
    const turn = turns.find((t) => t.id === turnId);
    setReviewRequests((prev) => [
      {
        id: turnId,
        query: turn?.response?.query ?? "(agent turn)",
        createdAt: new Date().toLocaleTimeString(),
        rule: turn?.response?.rule ?? null,
      },
      ...prev,
    ]);
  }, [turns]);

  return (
    <>
      <PageHeader
        title="Agent Assistant"
        description="Bounded decision-support console. Ask about registry state, governance decisions and recorded events — grounded in tamper-evident ledger references."
      />

      <div className="flex flex-col gap-6 lg:flex-row">
        <div className="min-w-0 flex-1 space-y-4">
          <AgentSafetyBanner />

          {error && (
            <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <span className="font-semibold">Agent request failed.</span>{" "}
              {error}
            </div>
          )}

          <section className="rounded-lg border border-slate-200 bg-slate-50 p-5 shadow-sm">
            {turns.length === 0 && !busy ? (
              <div className="py-8 text-center">
                <p className="text-sm font-medium text-slate-700">
                  Ask a question about the platform.
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Responses cite registered evidence; protected actions are refused.
                </p>
              </div>
            ) : (
              <ChatTranscript
                turns={turns}
                busy={busy}
                onRequestReview={requestReview}
              />
            )}
          </section>

          <SuggestionChips suggestions={SUGGESTIONS} onPick={(q) => void ask(q)} />

          <form onSubmit={submit} className="flex items-end gap-3">
            <label htmlFor="agent-query" className="sr-only">
              Question for the agent
            </label>
            <textarea
              id="agent-query"
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void ask(input.trim());
                  setInput("");
                }
              }}
              placeholder='e.g. "Why was this model rejected?" or "Promote the Load challenger."'
              className="flex-1 resize-none rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-400"
            />
            <button
              type="submit"
              disabled={busy || input.trim().length === 0}
              className="rounded-md bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {busy ? "Asking…" : "Ask agent"}
            </button>
          </form>
        </div>

        {/* Right context column */}
        <div className="flex w-full shrink-0 flex-col gap-4 lg:w-80">
          <AgentContextPanel />

          <section
            aria-label="Human review requests"
            data-testid="review-requests-panel"
            className="rounded-lg border border-slate-200 bg-white shadow-sm"
          >
            <header className="border-b border-slate-100 px-4 py-3">
              <h2 className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">
                Human review requests ({reviewRequests.length})
              </h2>
            </header>
            <div className="px-4 py-3">
              {reviewRequests.length === 0 ? (
                <p className="text-xs italic text-slate-400">No open review requests.</p>
              ) : (
                <ul className="space-y-2">
                  {reviewRequests.map((r) => (
                    <li key={r.id} className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-900">
                      <p className="font-medium">{r.query}</p>
                      <p className="mt-0.5 text-emerald-700">
                        {r.createdAt}
                        {r.rule ? ` · ${r.rule}` : ""}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
              <p className="mt-3 border-t border-slate-100 pt-2 text-[11px] leading-relaxed text-slate-500">
                Review requests are recorded in this session for demonstration.
                No lifecycle action is executed by the agent layer.
              </p>
            </div>
          </section>

          <section aria-label="Demo scenarios" className="rounded-lg border border-slate-200 bg-white shadow-sm">
            <header className="border-b border-slate-100 px-4 py-3">
              <h2 className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">
                Demo mode
              </h2>
            </header>
            <ul className="divide-y divide-slate-100 px-4 py-1">
              {DEMO_SCENARIOS.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => void runScenario(s.id)}
                    data-testid={`demo-link-${s.code.replace(" ", "-").toLowerCase()}`}
                    className="flex w-full items-center justify-between py-2 text-left text-xs text-slate-600 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-slate-600"
                  >
                    <span>
                      <span className="font-mono font-semibold">{s.code}</span> · {s.title}
                    </span>
                    <span aria-hidden>→</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </>
  );

  async function runScenario(id: string) {
    const scenario = DEMO_SCENARIOS.find((s) => s.id === id);
    if (!scenario) return;
    for (const step of scenario.steps) {
      await ask(step.question);
    }
  }
}
