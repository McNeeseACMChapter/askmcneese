interface TermBadgeProps {
  label: string;
}

export function TermBadge({ label }: TermBadgeProps) {
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium"
      style={{
        fontFamily: "var(--font-ui)",
        background: "var(--brand-50)",
        color: "var(--brand-800)",
        border: "1px solid var(--border-subtle)",
      }}
    >
      {label}
    </span>
  );
}
