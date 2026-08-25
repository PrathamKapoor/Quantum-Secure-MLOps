import { api, getBaseUrl } from "../services/api";
import { useApi } from "../hooks/useApi";
import type { Report } from "../types";
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "../components/ui";

const TYPE_LABELS: Record<string, string> = {
  phase_report: "Phase report",
  final_evaluation: "Final evaluation",
  research_table: "Research table",
  research_paper: "Research package",
};

function reportFileUrl(path: string) {
  return `${getBaseUrl()}/api/reports/file?path=${encodeURIComponent(path)}`;
}

export default function Reports() {
  const reports = useApi(api.fetchReports);
  const list = reports.data ?? [];

  const grouped = list.reduce<Record<string, Report[]>>((acc, r) => {
    (acc[r.type] ??= []).push(r);
    return acc;
  }, {});

  return (
    <>
      <PageHeader
        title="Reports"
        description="Phase reports, final evaluation artifacts and the research package produced by the locked pipeline."
      />

      {reports.loading ? (
        <LoadingState />
      ) : reports.error ? (
        <ErrorState message={reports.error} />
      ) : list.length === 0 ? (
        <EmptyState message="No reports available." />
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([type, items]) => (
            <Card
              key={type}
              title={TYPE_LABELS[type] ?? type}
              subtitle={`${items.length} document${items.length > 1 ? "s" : ""}`}
            >
              <ul className="divide-y divide-slate-100">
                {items.map((r) => (
                  <li
                    key={`${r.type}-${r.path}`}
                    className="flex flex-wrap items-center justify-between gap-3 py-2.5 first:pt-0 last:pb-0"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-slate-800">
                        {r.name}
                      </p>
                      <p className="truncate font-mono text-xs text-slate-400" title={r.path}>
                        {r.path}
                      </p>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <a
                        href={reportFileUrl(r.path)}
                        target="_blank"
                        rel="noreferrer"
                        className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:border-slate-900 hover:text-slate-900"
                      >
                        View
                      </a>
                      <a
                        href={reportFileUrl(r.path)}
                        download
                        className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800"
                      >
                        Download
                      </a>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      )}
    </>
  );
}
