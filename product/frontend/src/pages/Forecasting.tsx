import { useCallback, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  MetricTile,
  PageHeader,
} from "../components/ui";

const TARGETS = ["load", "wind", "pv"] as const;
type Target = (typeof TARGETS)[number];

const LABELS: Record<Target, string> = { load: "Load", wind: "Wind", pv: "PV" };

interface TargetPayload {
  target: string;
  horizon: string;
  model: string | null;
  count: number | null;
  mae_from_absolute_errors: number | null;
  predictions: {
    timestamp: string;
    prediction: number;
    actual: number;
    absolute_error: number;
  }[];
}

export default function Forecasting() {
  const [target, setTarget] = useState<Target>("load");

  // Stable fetcher bound to the selected target — Stage-1 per-target endpoint.
  const fetcher = useCallback(() => api.fetchPredictionsForTarget(target), [target]);
  const status = useApi(api.fetchForecastStatus);
  const data = useApi<TargetPayload>(fetcher, [target]);

  const rows = data.data?.predictions ?? [];

  // Downsample long series to keep the chart responsive.
  const MAX_POINTS = 500;
  const step = rows.length > MAX_POINTS ? Math.ceil(rows.length / MAX_POINTS) : 1;
  const chartData = rows
    .filter((_, i) => i % step === 0)
    .map((r) => ({
      t: r.timestamp,
      Actual: r.actual,
      Predicted: r.prediction,
    }));

  return (
    <>
      <PageHeader
        title="Forecasts"
        description={`Locked final-evaluation forecasts at horizon ${status.data?.horizon ?? "H24"}. Values are served verbatim from the released artifact; metrics are not recomputed.`}
      />

      <div className="mb-4 flex flex-wrap gap-2" role="tablist" aria-label="Forecast target">
        {TARGETS.map((t) => {
          const isActive = t === target;
          return (
            <button
              key={t}
              role="tab"
              aria-selected={isActive}
              onClick={() => setTarget(t)}
              data-testid={`forecast-tab-${t}`}
              className={[
                "rounded-md border px-4 py-1.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600",
                isActive
                  ? "border-slate-900 bg-slate-900 text-white"
                  : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50",
              ].join(" ")}
            >
              {LABELS[t]}
            </button>
          );
        })}
      </div>

      {data.loading || status.loading ? (
        <LoadingState label="Loading forecast data…" />
      ) : data.error ? (
        <ErrorState message={data.error} />
      ) : rows.length === 0 ? (
        <EmptyState message="No prediction rows available for this target." />
      ) : (
        <>
          {/* Metrics served by the API where available */}
          <div className="mb-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <MetricTile label="Model" value={data.data?.model ?? "unavailable"} />
            <MetricTile label="Points" value={data.data?.count ?? rows.length} />
            <MetricTile
              label="MAE (artifact)"
              value={
                data.data?.mae_from_absolute_errors != null
                  ? Number(data.data.mae_from_absolute_errors).toFixed(4)
                  : "—"
              }
            />
            <MetricTile label="Horizon" value={data.data?.horizon ?? "H24"} />
          </div>

          <Card
            title={`${LABELS[target]} — actual vs predicted`}
            subtitle={`${rows.length} evaluation points · released evaluation artifact · not a live forecast`}
          >
            <div className="h-[420px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    dataKey="t"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v) => `#${v}`}
                    minTickGap={48}
                    stroke="#94a3b8"
                  />
                  <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" width={56} />
                  <Tooltip contentStyle={{ fontSize: 12, borderRadius: 6 }} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Line type="monotone" dataKey="Actual" stroke="#0f172a" strokeWidth={1.5} dot={false} />
                  <Line
                    type="monotone"
                    dataKey="Predicted"
                    stroke="#0284c7"
                    strokeWidth={1.5}
                    dot={false}
                    strokeDasharray="5 3"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-3 border-t border-slate-100 pt-2 text-xs text-slate-500">
              ACTUAL = recorded values from the evaluation window · PREDICTED =
              frozen-model output. Future horizons are not shown because no live
              forecasting service exists in this stage.
            </p>
          </Card>
        </>
      )}
    </>
  );
}
