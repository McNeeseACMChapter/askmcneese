interface EmptyStateProps {
  title: string;
  body: string;
}

export function EmptyState({ title, body }: EmptyStateProps) {
  return (
    <div className="px-6 py-12 text-center">
      <h2 className="editorial-title mb-2">{title}</h2>
      <p className="mx-auto max-w-md text-sm text-text-secondary">{body}</p>
    </div>
  );
}
