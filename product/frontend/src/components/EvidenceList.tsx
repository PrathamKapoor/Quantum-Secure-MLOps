import type { EvidenceItem } from "../types";
import { useState } from "react";

/**
 * Expandable evidence list. Refs are real ledger references served by the
 * backend; details render only registered fields.
 */
export function EvidenceList({ evidence }: { evidence: EvidenceItem[] }) {
  const [openRefs, setOpenRefs] = useState<Set<string>>(new Set());

  if (evidence.length === 0) {
    return (
      <p
        data-testid="agent-no-evidence"
        className="text-xs italic text-slate-400"
      >
        No ledger evidence matched this question.
      </p>
    );
  }

  const toggle = (ref: string) => {
    setOpenRefs((prev) => {
      const next = new Set(prev);
      if (next.has(ref)) next.delete(ref);
      else next.add(ref);
      return next;
    });
  };

  return (
    <ul className="mt-1 space-y-1.5" data-testid="agent-evidence-list">
      {evidence.map((item) => {
        const open = openRefs.has(item.ref);
        const detailId = `evidence-detail-${item.ref}-${item.seq ?? "x"}`;
        return (
          <li key={`${item.ref}-${item.seq}`} className="rounded-md border border-slate-200 bg-slate-50">
            <button
              type="button"
              aria-expanded={open}
              aria-controls={detailId}
              onClick={() => toggle(item.ref)}
              className="flex w-full items-center justify-between gap-2 px-2.5 py-1.5 text-left text-xs text-slate-700 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-slate-500"
            >
              <span className="min-w-0">
                <span className="font-mono font-semibold text-slate-500">
                  [{item.ref}]
                </span>{" "}
                <span className="font-medium">{item.label}</span>
              </span>
              <span aria-hidden className="shrink-0 text-slate-400">
                {open ? "▾" : "▸"}
              </span>
            </button>
            {open && (
              <dl id={detailId} className="border-t border-slate-200 px-2.5 py-2 text-[11px]">
                {Object.entries(item.detail).map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-3 py-0.5">
                    <dt className="uppercase tracking-wide text-slate-400">{k}</dt>
                    <dd className="truncate text-right font-mono text-slate-600" title={String(v)}>
                      {String(v)}
                    </dd>
                  </div>
                ))}
              </dl>
            )}
          </li>
        );
      })}
    </ul>
  );
}
