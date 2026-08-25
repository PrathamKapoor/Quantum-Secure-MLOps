import { useMemo } from "react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import type { DriftEvent } from "../types";
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  SeverityBadge,
} from "../components/ui";

const SEVERITY_DOTS: Record<string, string> = {
  HIGH: "bg-red-500",
  MEDIUM: "bg-amber-500",
  LOW: "bg-sky-500",
};

function formatTimestamp(ts: DriftEvent["timestamp"]): string {
  if (ts === null || ts === undefined || ts === "") return "—";
  const n = Number(ts);
  const date = Number.isFinite(n) ? new Date(n) : new Date(String(ts));
  return isNaN(date.getTime()) ? String(ts) : date.toLocaleString();
}

export default function DriftMonitoring() {
  const events = useApi(api.fetchDriftEvents);
  const list = events.data ?? [];

  const counts = useMemo(() => {
    const c = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    for (const e of events.data ?? []) {
      const s = (e.severity ?? "").toUpperCase() as keyof typeof c;
      if (s in c) c[s] += 1;
    }
    return c;
  }, [events.data]);

  return (
    <>
      <PageHeader
        title="Drift Monitoring"
        description="Chronological record of drift checks performed by the monitoring pipeline. Severity reflects the maximum per-feature drift score at check time."
      />

      {!events.loading && !events.error && (
        <div className="mb-4 grid grid-cols-3 gap-4 sm:max-w-md">
          {(["HIGH", "MEDIUM", "LOW"] as const).map((sev) => (
            <div
              key={sev}
              className="rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm"
            >
              <div className="flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${SEVERITY_DOTS[sev]}`}
                  aria-hidden
                />
                <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
                  {sev}
                </p>
              </div>
              <p className="mt-1 font-mono text-lg font-semibold text-slate-900">
                {counts[sev]}
              </p>
            </div>
          ))}
        </div>
      )}

      {events.loading ? (
        <LoadingState />
      ) : events.error ? (
        <ErrorState message={events.error} />
      ) : list.length === 0 ? (
        <EmptyState message="No drift events recorded." />
      ) : (
        <ol className="relative space-y-3 border-l border-slate-300 pl-6">
          {list.map((event, i) => (
            <li key={event.event_id ?? i} className="relative" data-testid="drift-event-item">
              <span
                aria-hidden
                className={`absolute -left-[31px] top-5 h-2.5 w-2.5 rounded-full ring-4 ring-slate-100 ${
                  SEVERITY_DOTS[(event.severity ?? "").toUpperCase()] ?? "bg-slate-400"
                }`}
              />
              <Card>
                <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
                  <div className="flex items-center gap-2">
                    <SeverityBadge severity={event.severity ?? "UNKNOWN"} />
                    <span className="text-sm font-semibold text-slate-800">
                      {event.target}
                    </span>
                  </div>
                  <span className="font-mono text-xs text-slate-400">
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>

                <dl className="mt-2 grid grid-cols-1 gap-x-8 gap-y-1.5 text-sm sm:grid-cols-4">
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-400">Drift type</dt>
                    <dd className="font-mono text-slate-700">{event.drift_type}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-400">Score</dt>
                    <dd className="font-mono text-slate-700">
                      {Number(event.score).toFixed(4)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-400">Event ID</dt>
                    <dd className="font-mono text-xs text-slate-500">{event.event_id}</dd>
                  </div>
                  <div>
                    <dt className="text-xs uppercase tracking-wide text-slate-400">Reason / evidence</dt>
                    <dd
                      className="truncate font-mono text-xs text-slate-500"
                      title={String(event.explanation_reference)}
                    >
                      {String(event.explanation_reference)}
                    </dd>
                  </div>
                </dl>
              </Card>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
