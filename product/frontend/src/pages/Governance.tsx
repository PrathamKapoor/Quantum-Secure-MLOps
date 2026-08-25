import { useCallback, useMemo, useState } from "react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import type { GovernanceEvent } from "../types";
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "../components/ui";

const DECISION_STYLES: Record<string, string> = {
  BLOCKED: "bg-red-50 text-red-700 ring-red-200",
  APPROVED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  COMPLETED: "bg-sky-50 text-sky-700 ring-sky-200",
};

function classify(type: string): "BLOCKED" | "APPROVED" | "COMPLETED" | "NEUTRAL" {
  const t = type.toUpperCase();
  if (t === "ROLLBACK_COMPLETED") return "COMPLETED";
  if (t.includes("BLOCKED") || t.includes("QUARANTINE") || t.includes("DENIED"))
    return "BLOCKED";
  if (t.includes("APPROVED")) return "APPROVED";
  if (t.includes("DEPLOYED") || t.includes("COMPLETED") || t.includes("PASSED"))
    return "COMPLETED";
  return "NEUTRAL";
}

function badgeClass(cls: string): string {
  if (cls === "NEUTRAL") return "bg-slate-100 text-slate-700 ring-slate-200";
  return DECISION_STYLES[cls];
}

function formatTime(ts: GovernanceEvent["timestamp"]): string {
  if (ts === null || ts === undefined || ts === "") return "--:--";
  const n = Number(ts);
  const date = Number.isFinite(n) ? new Date(n) : new Date(String(ts));
  if (isNaN(date.getTime())) return String(ts);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatFullDate(ts: GovernanceEvent["timestamp"]): string {
  const n = Number(ts);
  const date = Number.isFinite(n) ? new Date(n) : new Date(String(ts));
  return isNaN(date.getTime()) ? String(ts) : date.toLocaleString();
}

/** Plain-language copy for major deterministic decisions. */
const DECISION_COPY: Record<string, string> = {
  MODEL_PROMOTION_BLOCKED:
    "The challenger was not promoted — it did not pass the required gate.",
  RETRAINING_APPROVED: "Adaptive retraining was approved by supervision.",
  MODEL_DEPLOYED: "A verified model was deployed as the new champion.",
  ROLLBACK_COMPLETED: "The previous champion was restored after a rollback.",
  VERIFICATION_PASSED: "The challenger passed the verification gate.",
};

function decisionHeadline(type: string): string {
  if (DECISION_COPY[type]) return DECISION_COPY[type];
  const words = type.toLowerCase().split("_");
  return (
    words[0].charAt(0).toUpperCase() +
    words[0].slice(1) +
    (words.length > 1 ? " " + words.slice(1).join(" ") : "")
  );
}

export default function Governance() {
  const [source, setSource] = useState<"audit" | "decisions">("audit");
  const fetchAudit = useCallback(() => api.fetchGovernanceEvents(), []);
  const fetchDecisions = useCallback(() => api.fetchGovernanceDecisions(), []);
  const events = useApi(source === "decisions" ? fetchDecisions : fetchAudit);
  const [filter, setFilter] = useState<string>("ALL");
  const list = events.data ?? [];

  const eventTypes = useMemo(
    () => ["ALL", ...Array.from(new Set((events.data ?? []).map((e) => e.type))).sort()],
    [events.data],
  );
  const filtered = filter === "ALL" ? list : list.filter((e) => e.type === filter);

  return (
    <>
      <PageHeader
        title="Governance Audit Timeline"
        description="Tamper-evident record of governance decisions: blocked promotions, approved retraining, deployments, rollbacks and lifecycle transitions. Read-only."
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        {/* Source toggle: full audit vs decision packets only (Stage-1 API) */}
        <div
          role="group"
          aria-label="Timeline source"
          className="flex overflow-hidden rounded-md border border-slate-300 text-xs font-medium"
        >
          {(
            [
              ["audit", "Audit timeline"],
              ["decisions", "Decisions only"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              aria-pressed={source === value}
              onClick={() => setSource(value)}
              data-testid={`gov-source-${value}`}
              className={[
                "px-3 py-1.5 transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600",
                source === value
                  ? "bg-slate-900 text-white"
                  : "bg-white text-slate-600 hover:bg-slate-50",
              ].join(" ")}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {!events.loading && !events.error && list.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {eventTypes.map((t) => (
            <button
              key={t}
              type="button"
              aria-pressed={filter === t}
              onClick={() => setFilter(t)}
              className={[
                "rounded-md border px-3 py-1 font-mono text-[11px] font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600",
                filter === t
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50",
              ].join(" ")}
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {events.loading ? (
        <LoadingState />
      ) : events.error ? (
        <ErrorState message={events.error} />
      ) : filtered.length === 0 ? (
        <EmptyState
          message={
            filter === "ALL"
              ? "No governance events recorded."
              : `No events of type ${filter}.`
          }
        />
      ) : (
        <ol className="relative space-y-3 border-l border-slate-300 pl-6" data-testid="audit-timeline">
          {filtered.map((event, i) => {
            const cls = classify(event.type);
            return (
              <li key={`${event.seq ?? i}-${event.evidence_ref}`} className="relative">
                <span
                  aria-hidden
                  className={`absolute -left-[31px] top-5 h-2.5 w-2.5 rounded-full ring-4 ring-slate-100 ${
                    cls === "BLOCKED"
                      ? "bg-red-500"
                      : cls === "APPROVED"
                        ? "bg-emerald-500"
                        : cls === "COMPLETED"
                          ? "bg-sky-500"
                          : "bg-slate-400"
                  }`}
                />
                <Card>
                  <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                      <time
                        dateTime={new Date(Number(event.timestamp)).toISOString()}
                        className="font-mono text-sm font-bold text-slate-900"
                        title={formatFullDate(event.timestamp)}
                      >
                        {formatTime(event.timestamp)}
                      </time>
                      <span
                        data-testid="audit-event-type"
                        className={`inline-flex items-center rounded px-2 py-0.5 font-mono text-[11px] font-semibold tracking-wide ring-1 ${badgeClass(cls)}`}
                      >
                        {event.type}
                      </span>
                    </div>
                    <span
                      className="max-w-[14rem] truncate font-mono text-xs text-slate-400"
                      title={`Ledger ref ${event.evidence_ref}`}
                      data-testid="audit-evidence-ref"
                    >
                      Evidence: {event.evidence_ref || "—"}
                    </span>
                  </div>

                  {/* Plain-language decision summary for non-experts */}
                  <p className="mt-3 text-sm font-semibold text-slate-800" data-testid="decision-headline">
                    {decisionHeadline(event.type)}
                  </p>

                  <dl className="mt-2 grid grid-cols-1 gap-x-8 gap-y-2 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-slate-400">Decision</dt>
                      <dd data-testid="decision-value" className="mt-0.5 font-medium text-slate-700">
                        {cls === "BLOCKED"
                          ? "Blocked by governance boundary"
                          : cls === "APPROVED"
                            ? "Approved under current policy"
                            : cls === "COMPLETED"
                              ? "Executed and verified"
                              : "Recorded by the evidence ledger"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-slate-400">Reason</dt>
                      <dd data-testid="decision-reason" className="mt-0.5 truncate text-slate-600" title={event.reason ?? ""}>
                        {event.reason || "—"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-slate-400">Policy</dt>
                      <dd className="mt-0.5 text-slate-600">
                        Deterministic governance policy (frozen)
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-slate-400">Evidence</dt>
                      <dd className="mt-0.5 truncate font-mono text-xs text-slate-500" title={event.evidence_ref}>
                        Ledger ref {event.evidence_ref || "—"}
                        {event.seq !== null && event.seq !== undefined
                          ? ` · seq ${event.seq}`
                          : ""}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-slate-400">Actor</dt>
                      <dd data-testid="audit-actor" className="mt-0.5 font-mono text-slate-700">
                        {event.actor || "system"}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs uppercase tracking-wide text-slate-400">Target</dt>
                      <dd data-testid="audit-target" className="mt-0.5 truncate font-mono text-slate-600" title={event.target}>
                        {event.target}
                      </dd>
                    </div>
                  </dl>
                </Card>
              </li>
            );
          })}
        </ol>
      )}
    </>
  );
}
