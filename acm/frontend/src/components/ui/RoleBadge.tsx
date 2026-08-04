interface RoleBadgeProps {
  label: string;
}

export function RoleBadge({ label }: RoleBadgeProps) {
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold"
      style={{
        fontFamily: "var(--font-ui)",
        background: "var(--accent-gold-soft)",
        color: "var(--accent-gold-text)",
        border: "1px solid color-mix(in srgb, var(--accent-gold) 40%, transparent)",
      }}
    >
      {label}
    </span>
  );
}
