import type { AgentExplanationResponse } from "../types";
import { EvidenceList } from "./EvidenceList";

export interface ChatTurn {
  id: string;
  role: "user" | "agent";
  query?: string;
  response?: AgentExplanationResponse;
  /** Set when the backend returned something we cannot safely render. */
  malformed?: boolean;
  reviewRequested?: boolean;
}

interface Props {
  turns: ChatTurn[];
  busy: boolean;
  onRequestReview: (turnId: string) => void;
}

/**
 * Safety-critical rendering rules:
 * - Always render the bounded-mode disclaimer.
 * - Only ever describe the agent as providing explanations.
 * - Protected actions render as ACTION BLOCKED refusals, never simulated
 *   success, and carry no executable controls.
 */
export function AgentSafetyBanner() {
  return (
    <div
      data-testid="agent-safety-banner"
      className="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"
    >
      <svg viewBox="0 0 16 16" fill="currentColor" className="mt-0.5 h-4 w-4 shrink-0" aria-hidden>
        <path d="M8 1a3.5 3.5 0 0 0-3.5 3.5V6H4a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-.5V4.5A3.5 3.5 0 0 0 8 1Zm2 5H6.5V4.5a1.5 1.5 0 1 1 3 0V6Z" />
      </svg>
      <span>
        Agents provide explanation only. They observe locked research state and
        cannot approve, promote, retrain, roll back or change any model.
      </span>
    </div>
  );
}

function RuleSourceChips({ rule, source }: { rule: string; source: string }) {
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      <span
        data-testid="agent-rule-chip"
        className="inline-flex items-center rounded border border-slate-300 bg-white px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-700"
        title="Deterministic rule that produced this outcome"
      >
        RULE&nbsp;<span className="text-slate-900">{rule}</span>
      </span>
      <span
        data-testid="agent-source-chip"
        className="inline-flex items-center rounded border border-sky-200 bg-sky-50 px-2 py-0.5 font-mono text-[11px] font-semibold text-sky-800"
        title="Origin of the referenced evidence"
      >
        SOURCE&nbsp;<span>{source}</span>
      </span>
    </div>
  );
}

function BlockedActionCard({
  response,
  turnId,
  reviewRequested,
  onRequestReview,
}: {
  response: AgentExplanationResponse;
  turnId: string;
  reviewRequested?: boolean;
  onRequestReview: (id: string) => void;
}) {
  return (
    <div
      data-testid="chat-agent-turn"
      role="status"
      className="max-w-2xl rounded-lg border-l-4 border-red-500 bg-white p-4 shadow-sm ring-1 ring-slate-200"
    >
      <p data-testid="blocked-title" className="font-mono text-sm font-bold tracking-widest text-red-600">
        ACTION BLOCKED
      </p>
      <p data-testid="blocked-boundary" className="mt-0.5 text-xs font-medium text-red-500">
        Blocked by governance boundary.
      </p>
      <dl className="mt-3 space-y-2 text-sm">
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Reason</dt>
          <dd data-testid="blocked-reason" className="mt-0.5 text-slate-700">{response.reason}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Authority</dt>
          <dd data-testid="blocked-authority" className="mt-0.5 text-slate-700">{response.authority}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Recommended next step</dt>
          <dd data-testid="blocked-next-step" className="mt-0.5 text-slate-700">{response.recommended_next_step}</dd>
        </div>
      </dl>

      {!reviewRequested ? (
        <button
          type="button"
          onClick={() => onRequestReview(turnId)}
          className="mt-3 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-slate-900 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600"
        >
          Request human review
        </button>
      ) : (
        <p data-testid="review-requested-note" className="mt-3 text-xs font-medium text-emerald-700">
          ✓ Human review requested (recorded locally — no lifecycle action executed)
        </p>
      )}
    </div>
  );
}

function ExplanationCard({
  response,
  turnId,
  reviewRequested,
  onRequestReview,
}: {
  response: AgentExplanationResponse;
  turnId: string;
  reviewRequested?: boolean;
  onRequestReview: (id: string) => void;
}) {
  return (
    <div
      data-testid="chat-agent-turn"
      className="max-w-2xl rounded-lg rounded-bl-sm border border-slate-200 bg-white px-4 py-3 shadow-sm"
    >
      <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">
        Explanation agent · bounded mode
      </p>

      <h3 className="mt-2 text-[11px] font-semibold uppercase tracking-wide text-slate-500">Answer</h3>
      <p
        data-testid="agent-explanation-text"
        className="mt-1 whitespace-pre-wrap text-sm leading-relaxed text-slate-800"
      >
        {response.explanation}
      </p>

      <h3 className="mt-3 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        Evidence ({response.evidence.length})
      </h3>
      <EvidenceList evidence={response.evidence} />

      <RuleSourceChips rule={response.rule} source={response.source} />

      <div className="mt-3 flex items-center justify-between gap-3 border-t border-slate-100 pt-2">
        <p className="text-xs text-slate-500">
          Human review required:{" "}
          <strong data-testid="human-review-flag">{response.requires_human_review ? "yes" : "no"}</strong>.
          Decisions remain with the governance engine.
        </p>
        {!reviewRequested && (
          <button
            type="button"
            onClick={() => onRequestReview(turnId)}
            className="shrink-0 rounded-md border border-slate-300 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:border-slate-900 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600"
          >
            Request human review
          </button>
        )}
        {reviewRequested && (
          <p data-testid="review-requested-note" className="shrink-0 text-[11px] font-medium text-emerald-700">
            ✓ Review requested (local record only)
          </p>
        )}
      </div>
    </div>
  );
}

export function ChatTranscript({ turns, busy, onRequestReview }: Props) {
  return (
    <ol className="space-y-4" aria-label="Conversation transcript" data-testid="chat-transcript">
      {turns.map((turn) =>
        turn.role === "user" ? (
          <li key={turn.id} className="flex justify-end" data-testid="chat-user-turn">
            <div className="max-w-xl rounded-lg rounded-br-sm bg-slate-900 px-4 py-2.5 text-sm text-white">
              {turn.query}
            </div>
          </li>
        ) : (
          <li key={turn.id} className="flex justify-start">
            {turn.malformed || !turn.response ? (
              <div
                data-testid="chat-malformed"
                role="alert"
                className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-800"
              >
                The agent returned a malformed response. No action was taken.
              </div>
            ) : turn.response.kind === "blocked_action" ? (
              <BlockedActionCard
                response={turn.response}
                turnId={turn.id}
                reviewRequested={turn.reviewRequested}
                onRequestReview={onRequestReview}
              />
            ) : (
              <ExplanationCard
                response={turn.response}
                turnId={turn.id}
                reviewRequested={turn.reviewRequested}
                onRequestReview={onRequestReview}
              />
            )}
          </li>
        ),
      )}
      {busy && (
        <li
          className="flex justify-start"
          data-testid="chat-busy"
          role="status"
          aria-live="polite"
        >
          <div className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-500 shadow-sm">
            Consulting evidence ledger…
          </div>
        </li>
      )}
    </ol>
  );
}

export interface SuggestedQuestion {
  label: string;
  query: string;
}

export function SuggestionChips({
  suggestions,
  onPick,
}: {
  suggestions: SuggestedQuestion[];
  onPick: (q: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2" role="list" aria-label="Suggested questions">
      {suggestions.map((s) => (
        <button
          key={s.label}
          type="button"
          role="listitem"
          onClick={() => onPick(s.query)}
          className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-600 transition-colors hover:border-slate-900 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600"
        >
          {s.label}
        </button>
      ))}
    </div>
  );
}
