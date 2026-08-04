import type { ProjectHealth } from "../../data/types";

const map: Record<ProjectHealth, { color: string; label: string }> = {
  on_track: { color: "var(--success)", label: "On track" },
  at_risk: { color: "var(--warning)", label: "At risk" },
  blocked: { color: "var(--danger)", label: "Blocked" },
  completed: { color: "var(--brand-700)", label: "Completed" },
  archived: { color: "var(--text-muted)", label: "Archived" },
};

export function HealthStrip({ health }: { health: ProjectHealth }) {
  const m = map[health];
  return (
    <span className="inline-flex items-center gap-2 text-xs font-semibold" style={{ fontFamily: "var(--font-ui)" }}>
      <span
        aria-hidden
        style={{
          width: 8,
          height: 8,
          borderRadius: 999,
          background: m.color,
          boxShadow: `0 0 0 2px color-mix(in srgb, ${m.color} 25%, transparent)`,
        }}
      />
      <span style={{ color: m.color }}>{m.label}</span>
    </span>
  );
}
