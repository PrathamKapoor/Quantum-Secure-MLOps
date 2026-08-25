import { useCallback, useState } from "react";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import type { ExperimentRun } from "../types";
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "../components/ui";

function RunRow({ run }: { run: ExperimentRun }) {
  const [open, setOpen] = useState(false);
  const paramEntries = Object.entries(run.params);
  const metricEntries = Object.entries(run.metrics);
  return (
    <li className="rounded-md border border-slate-200 bg-white">
      <button
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="flex w-full flex-wrap items-center justify-between gap-2 px-3 py-2 text-left hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-slate-500"
      >
        <span className="font-mono text-xs font-semibold text-slate-700">
          {run.run_id.slice(0, 12)}…
        </span>
        <span className="flex items-center gap-3 text-[11px] text-slate-500">
          <span data-testid={`run-status-${run.run_id}`}>{run.status ?? "—"}</span>
          <span>{paramEntries.length} params</span>
          <span>{metricEntries.length} metrics</span>
          <span aria-hidden>{open ? "▾" : "▸"}</span>
        </span>
      </button>
      {open && (
        <div className="grid grid-cols-1 gap-4 border-t border-slate-100 px-3 py-2.5 text-xs sm:grid-cols-3">
          {[
            ["Params", paramEntries],
            ["Metrics", metricEntries.map(([k, v]) => [k, String(v)] as [string, string])],
            ["Tags", Object.entries(run.tags)],
          ].map(([label, entries]) => (
            <div key={label as string}>
              <h4 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                {label as string}
              </h4>
              {(entries as [string, string][]).length === 0 ? (
                <p className="italic text-slate-400">none recorded</p>
              ) : (
                <dl className="space-y-0.5">
                  {(entries as [string, string][]).map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-2">
                      <dt className="truncate font-mono text-slate-500" title={k}>
                        {k}
                      </dt>
                      <dd className="truncate text-right font-mono text-slate-700" title={v}>
                        {v}
                      </dd>
                    </div>
                  ))}
                </dl>
              )}
            </div>
          ))}
        </div>
      )}
    </li>
  );
}

export default function Experiments() {
  const experiments = useApi(api.fetchExperiments);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const detailFn = useCallback(
    () => api.fetchExperimentDetail(selectedId ?? ""),
    [selectedId],
  );
  // Detail is fetched only when a selection exists; skip via enabled-style guard
  // by rendering the child component conditionally instead.
  const list = experiments.data?.experiments ?? [];

  return (
    <>
      <PageHeader
        title="Experiments"
        description="Experiment lineage from the MLflow tracking store, read-only. Answers “what experiment produced this model?” without exposing raw MLflow complexity."
      />

      {experiments.loading ? (
        <LoadingState label="Loading experiment lineage…" />
      ) : experiments.error ? (
        <ErrorState message={experiments.error} />
      ) : !experiments.data?.available ? (
        <EmptyState message="MLflow tracking store not present in this environment." />
      ) : list.length === 0 ? (
        <EmptyState message="No experiments recorded." />
      ) : (
        <div className="space-y-4">
          {experiments.data.note && (
            <p
              data-testid="experiments-note"
              className="rounded-md border border-sky-200 bg-sky-50 px-4 py-2.5 text-sm text-sky-800"
            >
              {experiments.data.note}
            </p>
          )}
          <Card>
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr>
                  {["ID", "Name", "Lifecycle", "Runs"].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className="px-3 py-2 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {list.map((e) => (
                  <tr
                    key={e.experiment_id}
                    className="cursor-pointer hover:bg-slate-50"
                    onClick={() => setSelectedId(e.experiment_id)}
                    tabIndex={0}
                    role="button"
                    aria-label={`Open experiment ${e.name}`}
                    onKeyDown={(ev) =>
                      ev.key === "Enter" && setSelectedId(e.experiment_id)
                    }
                    data-testid={`experiment-row-${e.experiment_id}`}
                  >
                    <td className="px-3 py-2 font-mono text-xs">{e.experiment_id}</td>
                    <td className="px-3 py-2 font-medium text-slate-800">{e.name}</td>
                    <td className="px-3 py-2 text-slate-600">{e.lifecycle_stage}</td>
                    <td className="px-3 py-2 font-mono">{e.run_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>

          {selectedId !== null && (
            <ExperimentDetail id={selectedId} fetcher={detailFn} />
          )}
        </div>
      )}
    </>
  );
}

function ExperimentDetail({
  id,
  fetcher,
}: {
  id: string;
  fetcher: () => Promise<import("../types").ExperimentDetailResponse>;
}) {
  const detail = useApi(fetcher, [id]);
  return (
    <section aria-label={`Experiment ${id} detail`}>
      <h2 className="mb-2 mt-6 text-sm font-bold uppercase tracking-wide text-slate-600">
        Lineage — experiment {id}
      </h2>
      {detail.loading ? (
        <LoadingState label="Loading runs…" />
      ) : detail.error ? (
        <ErrorState message={detail.error} />
      ) : (detail.data?.runs ?? []).length === 0 ? (
        <EmptyState message="No runs recorded for this experiment yet." />
      ) : (
        <ul className="space-y-2">
          {(detail.data?.runs ?? []).map((run) => (
            <RunRow key={run.run_id} run={run} />
          ))}
        </ul>
      )}
    </section>
  );
}
