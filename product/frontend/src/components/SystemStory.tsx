/**
 * Static, accurate summary of the platform narrative:
 * forecasting → drift → deterministic governance → challenger evaluation →
 * bounded agent explanation. Purely informational; no invented capabilities.
 */

const STAGES = [
  {
    title: "Forecasting",
    body: "Locked models forecast Load, Wind and PV at horizon H24.",
  },
  {
    title: "Drift monitoring",
    body: "Live error is checked against frozen drift thresholds.",
  },
  {
    title: "Deterministic governance",
    body: "Policies decide whether adaptation is permitted — never the agent.",
  },
  {
    title: "Challenger evaluation",
    body: "Retraining produces challengers; the verification gate gates promotion.",
  },
  {
    title: "Bounded agent",
    body: "Explains decisions with ledger evidence. Explain only — no execution.",
  },
];

export default function SystemStory() {
  return (
    <section
      aria-label="How the platform works"
      data-testid="system-story"
      className="mb-6 rounded-lg border border-slate-200 bg-white px-5 py-4 shadow-sm"
    >
      <h2 className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">
        How this platform works
      </h2>
      <ol className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-5">
        {STAGES.map((s, i) => (
          <li key={s.title} className="relative rounded-md bg-slate-50 px-3 py-2.5">
            <p className="font-mono text-[11px] font-bold text-slate-400">
              {String(i + 1).padStart(2, "0")}
            </p>
            <p className="mt-0.5 text-xs font-semibold text-slate-800">{s.title}</p>
            <p className="mt-1 text-[11px] leading-relaxed text-slate-500">{s.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
