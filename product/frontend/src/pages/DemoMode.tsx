import { useState } from "react";
import { api, getApiErrorMessage } from "../services/api";
import { DEMO_SCENARIOS } from "../services/demoScenarios";
import type { DemoScenario } from "../services/demoScenarios";
import { AgentSafetyBanner } from "../components/AgentChat";
import type { ChatTurn } from "../components/AgentChat";
import { ChatTranscript } from "../components/AgentChat";
import { Card, ErrorState, PageHeader } from "../components/ui";

let demoTurnCounter = 0;
const nextId = () => `demo-turn-${++demoTurnCounter}`;

interface RunningScenario {
  scenario: DemoScenario;
  turns: ChatTurn[];
  activeStep: number;
  done: boolean;
}

export default function DemoMode() {
  const [running, setRunning] = useState<RunningScenario | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(scenario: DemoScenario) {
    setError(null);
    setRunning({ scenario, turns: [], activeStep: 0, done: false });
    const turns: ChatTurn[] = [];
    for (let i = 0; i < scenario.steps.length; i++) {
      const step = scenario.steps[i];
      setRunning({ scenario, turns: [...turns], activeStep: i, done: false });
      setBusy(true);
      const userTurn: ChatTurn = { id: nextId(), role: "user", query: step.question };
      turns.push(userTurn);
      setRunning({ scenario, turns: [...turns], activeStep: i, done: false });
      try {
        const response = await api.explain(step.question);
        const malformed =
          !response ||
          typeof response.explanation !== "string" ||
          !Array.isArray(response.evidence);
        turns.push({
          id: nextId(),
          role: "agent",
          response: malformed ? undefined : response,
          malformed,
        });
      } catch (err) {
        setBusy(false);
        setError(getApiErrorMessage(err));
        return;
      }
      setBusy(false);
    }
    setRunning({ scenario, turns: [...turns], activeStep: scenario.steps.length, done: true });
  }

  return (
    <>
      <PageHeader
        title="Demo Mode"
        description="Scripted operator walkthroughs of the guardrailed lifecycle. Every step is a live question to the bounded agent; answers cite registered evidence. No metrics are fabricated."
      />

      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <span
          data-testid="demo-scenario-label"
          className="inline-flex items-center rounded border border-sky-200 bg-sky-50 px-2.5 py-1 font-mono text-[11px] font-bold uppercase tracking-widest text-sky-800"
        >
          Demonstration scenario
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setRunning(null)}
            disabled={!running || busy}
            data-testid="demo-clear-conversation"
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 hover:border-slate-900 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Clear conversation
          </button>
          <button
            type="button"
            onClick={() => {
              setRunning(null);
              setError(null);
            }}
            disabled={busy}
            data-testid="demo-reset"
            className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Reset demo
          </button>
        </div>
      </div>

      <div className="mb-4">
        <AgentSafetyBanner />
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {DEMO_SCENARIOS.map((s) => {
          const isRunning = running?.scenario.id === s.id;
          return (
            <Card key={s.id} className={isRunning ? "ring-2 ring-slate-900" : ""}>
              <p className="font-mono text-[11px] font-bold uppercase tracking-widest text-slate-400">
                {s.code}
              </p>
              <h2 className="mt-1 text-sm font-semibold text-slate-800">{s.title}</h2>
              <p className="mt-1.5 min-h-[4.5rem] text-xs leading-relaxed text-slate-500">
                {s.story}
              </p>
              <button
                type="button"
                onClick={() => void run(s)}
                disabled={busy}
                data-testid={`demo-run-${s.id}`}
                className="mt-3 w-full rounded-md bg-slate-900 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-600 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isRunning && !running.done ? "Running…" : "Run scenario"}
              </button>
            </Card>
          );
        })}
      </div>

      {error && (
        <div className="mt-4">
          <ErrorState message={error} />
        </div>
      )}

      {running && (
        <section className="mt-6" aria-label={`Transcript for ${running.scenario.title}`}>
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="text-sm font-bold text-slate-800">
              {running.scenario.code} — {running.scenario.title}
            </h2>
            <p className="text-xs text-slate-500">
              {running.done ? "Completed" : `Step ${running.activeStep + 1} / ${running.scenario.steps.length}`}
            </p>
          </div>

          {running.turns.map((turn, i) => (
            <div key={turn.id} className="mb-4">
              {turn.role === "user" && (
                <p className="mb-1 font-mono text-[11px] uppercase tracking-wide text-slate-400">
                  Step narration: {running.scenario.steps[i / 2]?.narration ?? ""}
                </p>
              )}
              <ChatTranscript turns={[turn]} busy={false} onRequestReview={() => undefined} />
            </div>
          ))}

          {busy && (
            <p className="text-xs italic text-slate-500">Querying agent endpoint…</p>
          )}
        </section>
      )}
    </>
  );
}
