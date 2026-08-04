import { Surface } from "./Surface";

export function MetricSummary({
  items,
}: {
  items: { label: string; value: string; hint?: string }[];
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {items.map((item) => (
        <Surface key={item.label} level="content" className="p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            {item.label}
          </p>
          <p className="mt-1 text-2xl font-semibold text-text-primary" style={{ fontFamily: "var(--font-ui)" }}>
            {item.value}
          </p>
          {item.hint ? (
            <p className="mt-1 text-xs text-text-secondary">{item.hint}</p>
          ) : null}
        </Surface>
      ))}
    </div>
  );
}
