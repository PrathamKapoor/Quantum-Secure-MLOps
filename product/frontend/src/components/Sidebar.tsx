import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Overview", end: true },
  { to: "/forecasting", label: "Forecasting" },
  { to: "/models", label: "Models" },
  { to: "/drift", label: "Drift Monitoring" },
  { to: "/governance", label: "Governance" },
  { to: "/agent", label: "Agent Assistant" },
  { to: "/demo", label: "Demo Mode" },
  { to: "/reports", label: "Reports" },
];

export default function Sidebar() {
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-5 py-4">
        <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">
          Guardrailed Agentic MLOps
        </p>
        <h1 className="mt-1 text-sm font-bold text-slate-800">
          Energy Forecasting Platform
        </h1>
      </div>

      <nav aria-label="Main navigation" className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  [
                    "block rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-slate-900 text-white"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-slate-200 px-5 py-3">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2 py-1 text-[11px] font-medium text-emerald-700 ring-1 ring-emerald-200">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Research pipeline locked
        </span>
      </div>
    </aside>
  );
}
