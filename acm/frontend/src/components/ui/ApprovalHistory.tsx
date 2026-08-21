export function ApprovalHistory({
  items,
}: {
  items: { id: string; actor: string; action: string; at: string }[];
}) {
  return (
    <ol className="space-y-3">
      {items.map((item) => (
        <li key={item.id} className="border-l-2 border-[var(--border-default)] pl-3">
          <p className="text-sm font-semibold text-text-primary">{item.action}</p>
          <p className="text-xs text-text-muted">
            {item.actor} · {item.at}
          </p>
        </li>
      ))}
    </ol>
  );
}
