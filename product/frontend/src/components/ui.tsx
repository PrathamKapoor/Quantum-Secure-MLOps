import type { ReactNode } from "react";

export function Card({
  title,
  subtitle,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-slate-200 bg-white shadow-sm ${className}`}
    >
      {(title || subtitle) && (
        <header className="border-b border-slate-100 px-5 py-3.5">
          {title && (
            <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
          )}
          {subtitle && (
            <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>
          )}
        </header>
      )}
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

export function PageHeader({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <header className="mb-6">
      <h1 className="text-xl font-bold tracking-tight text-slate-900">
        {title}
      </h1>
      {description && (
        <p className="mt-1 max-w-3xl text-sm text-slate-500">{description}</p>
      )}
    </header>
  );
}

export function MetricTile({
  label,
  value,
  unit,
}: {
  label: string;
  value: string | number;
  unit?: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
        {label}
      </p>
      <p className="mt-1 font-mono text-lg font-semibold text-slate-900">
        {value}
        {unit && (
          <span className="ml-1 text-xs font-normal text-slate-500">{unit}</span>
        )}
      </p>
    </div>
  );
}

export function LoadingState({ label = "Loading data…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 px-1 py-8 text-sm text-slate-500">
      <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
      {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
    >
      API error: {message}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <p className="py-6 text-center text-sm text-slate-500">{message}</p>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    HIGH: "bg-red-50 text-red-700 ring-red-200",
    MEDIUM: "bg-amber-50 text-amber-700 ring-amber-200",
    LOW: "bg-sky-50 text-sky-700 ring-sky-200",
    UNKNOWN: "bg-slate-50 text-slate-600 ring-slate-200",
  };
  const style = styles[severity.toUpperCase()] ?? styles.UNKNOWN;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ring-1 ${style}`}
    >
      {severity}
    </span>
  );
}
