export function Timeline({
  items,
}: {
  items: { id: string; title: string; meta: string }[];
}) {
  return (
    <ol className="space-y-4">
      {items.map((item, index) => (
        <li key={item.id} className="flex gap-3">
          <div className="flex flex-col items-center">
            <span
              className="mt-1 h-2.5 w-2.5 rounded-full bg-brand-700"
              aria-hidden
            />
            {index < items.length - 1 ? (
              <span className="mt-1 w-px flex-1 bg-[var(--border-default)]" aria-hidden />
            ) : null}
          </div>
          <div className="pb-3">
            <p className="text-sm font-semibold text-text-primary">{item.title}</p>
            <p className="text-xs text-text-muted">{item.meta}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
