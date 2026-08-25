import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import type { ModelVersionDetail } from "../types";
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "../components/ui";

function StateBadge({ state }: { state?: string | null }) {
  const normalized = (state ?? "").toUpperCase();
  const styles: Record<string, string> = {
    DEPLOYED: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    APPROVED: "bg-teal-50 text-teal-700 ring-teal-200",
    VERIFIED: "bg-sky-50 text-sky-700 ring-sky-200",
    REGISTERED: "bg-slate-100 text-slate-600 ring-slate-200",
    QUARANTINED: "bg-red-50 text-red-700 ring-red-200",
    ROLLED_BACK: "bg-amber-50 text-amber-700 ring-amber-200",
    REVOKED: "bg-slate-200 text-slate-700 ring-slate-300",
  };
  const style = styles[normalized] ?? styles.REGISTERED;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wide ring-1 ${style}`}
    >
      {state || "unknown"}
    </span>
  );
}

/**
 * Read-only version history for one model. Lifecycle states are displayed;
 * no promote / rollback / retrain controls exist by design.
 */
export default function ModelDetail() {
  const { modelName = "" } = useParams();
  const versions = useApi(
    useCallback(() => api.fetchModelVersions(modelName), [modelName]),
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const detailFn = useCallback(
    () => api.fetchModelVersionDetail(modelName, selectedId ?? ""),
    [modelName, selectedId],
  );

  const list = versions.data?.versions ?? [];

  return (
    <>
      <PageHeader
        title={`Model — ${modelName}`}
        description="Read-only version history from the secure registry. Lifecycle changes happen only through the research governance engine."
      />

      <Link
        to="/models"
        className="mb-4 inline-block text-xs font-medium text-slate-500 hover:text-slate-900"
      >
        ← All models
      </Link>

      {versions.loading ? (
        <LoadingState label="Loading version history…" />
      ) : versions.error ? (
        <ErrorState message={versions.error} />
      ) : list.length === 0 ? (
        <EmptyState message="No versions registered for this model." />
      ) : (
        <>
          <Card title="Version history">
            <div className="overflow-x-auto">
              <table
                className="min-w-full divide-y divide-slate-200 text-sm"
                data-testid="version-history-table"
              >
                <thead>
                  <tr>
                    {["Version", "Version ID", "State", "Created"].map((h) => (
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
                  {list.map((v) => (
                    <tr
                      key={v.version_id}
                      onClick={() => setSelectedId(v.version_id)}
                      onKeyDown={(e) =>
                        e.key === "Enter" && setSelectedId(v.version_id)
                      }
                      tabIndex={0}
                      role="button"
                      aria-label={`Select version ${v.version}`}
                      className={[
                        "cursor-pointer",
                        selectedId === v.version_id ? "bg-slate-100" : "hover:bg-slate-50",
                      ].join(" ")}
                      data-testid={`version-row-${v.version_id}`}
                    >
                      <td className="px-3 py-2 font-mono">v{v.version}</td>
                      <td
                        className="max-w-[14rem] truncate px-3 py-2 font-mono text-xs text-slate-500"
                        title={v.version_id}
                      >
                        {v.version_id}
                      </td>
                      <td className="px-3 py-2">
                        <StateBadge state={v.state} />
                      </td>
                      <td className="px-3 py-2 font-mono text-xs text-slate-500">
                        {v.created_at ? new Date(Number(v.created_at) * 1000).toLocaleString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {selectedId && (
            <SelectedVersion
              modelName={modelName}
              versionId={selectedId}
              fetcher={detailFn}
            />
          )}
        </>
      )}
    </>
  );
}

function SelectedVersion({
  modelName,
  versionId,
  fetcher,
}: {
  modelName: string;
  versionId: string;
  fetcher: () => Promise<ModelVersionDetail>;
}) {
  const detail = useApi(fetcher, [modelName, versionId]);
  return (
    <Card
      className="mt-4"
      title={`Version detail — ${versionId.slice(0, 12)}…`}
      subtitle="Fields served by the Stage-1 registry API; unknown values reflect what the frozen passport records."
    >
      {detail.loading ? (
        <LoadingState />
      ) : detail.error ? (
        <ErrorState message={detail.error} />
      ) : detail.data ? (
        <dl className="grid grid-cols-1 gap-x-8 gap-y-2 text-sm sm:grid-cols-2" data-testid="version-detail-grid">
          {[
            ["Passport ID", detail.data.passport_id],
            ["Feature set", detail.data.feature_set],
            ["Signature suite", detail.data.signature_suite],
            ["Signed by", detail.data.signed_by],
            ["Lifecycle state", detail.data.state ?? null],
          ].map(([label, value]) => (
            <div key={label as string} className="flex justify-between gap-3 border-b border-slate-100 py-1">
              <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
              <dd className="truncate text-right font-mono text-slate-700" title={String(value ?? "")}>
                {value ? String(value) : "—"}
              </dd>
            </div>
          ))}
        </dl>
      ) : null}
    </Card>
  );
}
