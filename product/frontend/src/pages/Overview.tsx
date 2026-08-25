import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import SystemStory from "../components/SystemStory";
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  MetricTile,
  PageHeader,
} from "../components/ui";

const TARGET_LABELS: Record<string, string> = {
  load: "Load",
  wind: "Wind",
  pv: "PV",
};

function formatTarget(target: string) {
  return TARGET_LABELS[target.toLowerCase()] ?? target;
}

export default function Overview() {
  const health = useApi(api.fetchHealth);
  const forecastStatus = useApi(api.fetchForecastStatus);
  const models = useApi(api.fetchModels);
  const governance = useApi(api.fetchGovernanceEvents);
  const drift = useApi(api.fetchDriftEvents);

  const loading =
    health.loading || forecastStatus.loading || models.loading || governance.loading || drift.loading;
  const error =
    health.error ?? forecastStatus.error ?? models.error ?? governance.error ?? drift.error;

  const [lastUpdated, setLastUpdated] = useState<string>("");
  useEffect(() => {
    if (!loading) setLastUpdated(new Date().toLocaleTimeString());
  }, [loading]);

  if (loading) return <LoadingState label="Collecting platform status…" />;
  if (error) return <ErrorState message={error} />;

  const blockedActions = (governance.data ?? []).filter(
    (e) => e.type.toUpperCase().includes("BLOCKED"),
  ).length;

  const activeModels = models.data ?? [];
  const healthyModels = activeModels.filter(
    (m) => m.lifecycle_state.toUpperCase() === "ACTIVE",
  ).length;

  return (
    <>
      <PageHeader
        title="Overview"
        description="Executive view of the guardrailed MLOps platform for renewable-integrated smart grid forecasting."
      />

      <SystemStory />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card title="System Status" subtitle="API and research pipeline state">
          <dl className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <dt className="text-slate-500">API status</dt>
              <dd className="font-mono font-semibold text-emerald-600 uppercase">
                {health.data?.status ?? "unknown"}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-slate-500">Research pipeline</dt>
              <dd className="font-mono font-semibold text-slate-800 uppercase">
                {health.data?.research_pipeline ?? "unknown"}
              </dd>
            </div>
          </dl>
        </Card>

        <Card title="Forecast Targets" subtitle={`Horizon ${forecastStatus.data?.horizon ?? ""}`}>
          {forecastStatus.data && forecastStatus.data.targets.length > 0 ? (
            <ul className="grid grid-cols-1 gap-2">
              {forecastStatus.data.targets.map((t) => (
                <li
                  key={t}
                  className="flex items-center justify-between rounded-md border border-slate-100 bg-slate-50 px-3 py-2 text-sm"
                >
                  <span className="font-medium text-slate-700">
                    {formatTarget(t)}
                  </span>
                  <span className="text-xs text-slate-400">
                    models {forecastStatus.data?.models_locked ? "locked" : "unlocked"}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState message="No forecast targets reported." />
          )}
        </Card>

        <Card title="Model Health" subtitle="Registered model lifecycle">
          <div className="grid grid-cols-2 gap-3">
            <MetricTile label="Registered" value={activeModels.length} />
            <MetricTile label="Active" value={healthyModels} />
          </div>
          {activeModels.length === 0 && (
            <EmptyState message="No models registered yet." />
          )}
        </Card>

        <Card title="Governance Status" subtitle="Policy enforcement summary">
          <div className="grid grid-cols-2 gap-3">
            <MetricTile label="Audit events" value={(governance.data ?? []).length} />
            <MetricTile label="Blocked actions" value={blockedActions} />
          </div>
          <p className="mt-3 text-xs text-slate-500">
            All lifecycle transitions are enforced by the governance engine; the
            dashboard is read-only.
          </p>
        </Card>

        <Card title="Agent Status" subtitle="Bounded observation agents">
          <p className="text-sm font-medium text-slate-700">Bounded mode</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            Agents observe the system and produce explanations only. They cannot
            promote, retrain, roll back, or otherwise modify any model.
          </p>
        </Card>
      </div>
    </>
  );
}
