export function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-ad-border bg-ad-surface p-5">
      <p className="text-sm text-ad-ink-muted">{label}</p>
      <p className="mt-2 text-3xl font-semibold tabular-nums text-ad-ink">
        {value}
      </p>
    </div>
  );
}
