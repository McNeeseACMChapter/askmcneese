import { CheckCircle2, CircleDashed } from "lucide-react";

export function EvidenceList({
  items,
}: {
  items: { id: string; label: string; present: boolean }[];
}) {
  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex items-center gap-2 text-sm text-text-primary"
        >
          {item.present ? (
            <CheckCircle2 size={18} strokeWidth={1.75} className="text-[var(--success)]" aria-hidden />
          ) : (
            <CircleDashed size={18} strokeWidth={1.75} className="text-[var(--warning)]" aria-hidden />
          )}
          <span>
            {item.label}{" "}
            <span className="text-text-muted">
              ({item.present ? "Attached" : "Missing"})
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}
