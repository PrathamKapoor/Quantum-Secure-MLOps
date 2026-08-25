/**
 * Static capability boundary for the bounded decision-support agent.
 * This panel is the single source of truth for what the agent can and
 * cannot do — restricted actions are never wired to any executable control.
 */

const CAPABILITIES = [
  "Explain decisions",
  "Summarize system state",
  "Investigate recorded events",
  "Retrieve registered evidence",
  "Request human review",
  "Generate reports",
];

const RESTRICTED = [
  "Promote model",
  "Roll back model",
  "Start retraining",
  "Change features",
  "Change governance policy",
  "Access final test set",
];

export default function AgentContextPanel() {
  return (
    <aside
      aria-label="Agent capability boundary"
      data-testid="agent-context-panel"
      className="w-full shrink-0 space-y-4 lg:w-80"
    >
      <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
        <header className="border-b border-slate-100 px-4 py-3">
          <h2 className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">
            Agent mode
          </h2>
          <p
            className="mt-1 inline-flex items-center gap-1.5 rounded bg-slate-900 px-2 py-1 font-mono text-xs font-semibold tracking-wide text-white"
            data-testid="agent-mode-badge"
          >
            BOUNDED DECISION SUPPORT
          </p>
        </header>

        <div className="px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-emerald-600">
            Capabilities
          </h3>
          <ul className="mt-2 space-y-1.5" data-testid="agent-capabilities-list">
            {CAPABILITIES.map((c) => (
              <li key={c} className="flex items-start gap-2 text-sm text-slate-700">
                <span
                  aria-hidden
                  className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-[10px] font-bold text-emerald-700"
                >
                  ✓
                </span>
                <span>
                  {c}
                  <span className="sr-only"> (allowed)</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="border-t border-slate-100 px-4 py-3">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-red-600">
            Restricted — governance authority only
          </h3>
          <ul className="mt-2 space-y-1.5" data-testid="agent-restricted-list">
            {RESTRICTED.map((r) => (
              <li key={r} className="flex items-start gap-2 text-sm text-slate-500">
                <span
                  aria-hidden
                  className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-red-100 text-[10px] font-bold text-red-700"
                >
                  ✕
                </span>
                <span>
                  {r}
                  <span className="sr-only"> (restricted, not executable)</span>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <footer className="border-t border-slate-100 px-4 py-3 text-[11px] leading-relaxed text-slate-500">
          The agent is decision support only. Lifecycle authority rests with the
          deterministic governance engine and human operators.
        </footer>
      </section>
    </aside>
  );
}
