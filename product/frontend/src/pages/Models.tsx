import { api } from "../services/api";
import { useApi } from "../hooks/useApi";
import {
  Card,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "../components/ui";

/**
 * Presentational classification derived strictly from the existing
 * lifecycle_state values. It clarifies that non-deployed versions are
 * evaluation candidates — never production models. No new semantics are
 * invented and no lifecycle actions are exposed.
 */
const ROLE_MAP: Record<string, { label: string; style: string }> = {
  REGISTERED: {
    label: "Challenger",
    style: "bg-sky-50 text-sky-700 ring-sky-200",
  },
  VERIFIED: {
    label: "Challenger · verified",
    style: "bg-sky-50 text-sky-700 ring-sky-200",
  },
  APPROVED: {
    label: "Promotion-eligible",
    style: "bg-teal-50 text-teal-700 ring-teal-200",
  },
  QUARANTINED: {
    label: "Promotion-rejected",
    style: "bg-red-50 text-red-700 ring-red-200",
  },
  REVOKED: {
    label: "Blocked",
    style: "bg-slate-200 text-slate-700 ring-slate-300",
  },
  ROLLED_BACK: {
    label: "Rolled back (challenger)",
    style: "bg-amber-50 text-amber-700 ring-amber-200",
  },
  DEPLOYED: {
    label: "Production champion",
    style: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  },
};

function RegistryRole({ state }: { state: string }) {
  const role = ROLE_MAP[state.toUpperCase()] ?? {
    label: "Challenger (reference)",
    style: "bg-slate-100 text-slate-600 ring-slate-200",
  };
  return (
    <span
      data-testid="registry-role"
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ring-1 ${role.style}`}
    >
      {role.label}
    </span>
  );
}

function LifecycleBadge({ state }: { state: string }) {
  const normalized = state.toUpperCase();
  const styles: Record<string, string> = {
    ACTIVE: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    REGISTERED: "bg-sky-50 text-sky-700 ring-sky-200",
    QUARANTINED: "bg-amber-50 text-amber-700 ring-amber-200",
    REVOKED: "bg-red-50 text-red-700 ring-red-200",
    RETIRED: "bg-slate-100 text-slate-600 ring-slate-200",
  };
  const style = styles[normalized] ?? styles.RETIRED;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wide ring-1 ${style}`}
    >
      {state}
    </span>
  );
}

/**
 * READ-ONLY registry view. Intentionally exposes no lifecycle action
 * controls (promote / retrain / rollback / quarantine): those operations
 * belong exclusively to the research-side governance engine.
 */
export default function Models() {
  const models = useApi(api.fetchModels);

  return (
    <>
      <PageHeader
        title="Model Registry"
        description="Read-only view of the locked model registry. Lifecycle changes are governed by the research pipeline and cannot be performed here."
      />

      <div className="mb-4 inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-500">
        <svg viewBox="0 0 16 16" fill="currentColor" className="h-3.5 w-3.5 text-slate-400" aria-hidden>
          <path d="M8 1a3.5 3.5 0 0 0-3.5 3.5V6H4a1 1 0 0 0-1 1v7a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-.5V4.5A3.5 3.5 0 0 0 8 1Zm2 5H6.5V4.5a1.5 1.5 0 1 1 3 0V6Z" />
        </svg>
        Read-only registry — no promote / retrain / rollback actions available
      </div>

      <Card>
        {models.loading ? (
          <LoadingState />
        ) : models.error ? (
          <ErrorState message={models.error} />
        ) : (models.data ?? []).length === 0 ? (
          <EmptyState message="No models registered in the registry." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr>
                  {["Target", "Model", "Feature Set", "Fingerprint", "Lifecycle State", "Registry Role"].map(
                    (h) => (
                      <th
                        key={h}
                        scope="col"
                        className="px-3 py-2.5 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500"
                      >
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(models.data ?? []).map((m) => (
                  <tr key={`${m.target}-${m.fingerprint}`} className="hover:bg-slate-50">
                    <td className="whitespace-nowrap px-3 py-2.5 font-medium text-slate-800">
                      {m.target}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-slate-600">
                      {m.model_name}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5 text-slate-600">
                      {m.feature_set}
                    </td>
                    <td className="max-w-[16rem] truncate px-3 py-2.5 font-mono text-xs text-slate-500" title={m.fingerprint}>
                      {m.fingerprint}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5">
                      <LifecycleBadge state={m.lifecycle_state} />
                    </td>
                    <td className="whitespace-nowrap px-3 py-2.5">
                      <RegistryRole state={m.lifecycle_state} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 border-t border-slate-100 pt-3 text-xs leading-relaxed text-slate-500" data-testid="registry-role-note">
              Registry roles are derived read-only from the lifecycle state.
              Challengers are evaluation candidates — they are not production
              models, and only the governance engine can change lifecycle state.
            </p>
          </div>
        )}
      </Card>
    </>
  );
}
