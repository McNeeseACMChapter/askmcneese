interface SkeletonProps {
  className?: string;
}

/** Pulsing placeholder block — uses theme border token for light/dark support. */
export function Skeleton({ className = "" }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded-md bg-[var(--border)] ${className}`}
      aria-hidden="true"
    />
  );
}

function CitationSkeleton() {
  return (
    <li className="border-l-2 border-[var(--border)] pl-3">
      <Skeleton className="mb-2 h-3 w-full" />
      <Skeleton className="mb-2 h-3 w-[92%]" />
      <Skeleton className="h-3 w-4/5" />
      <Skeleton className="mt-2 h-2.5 w-2/5" />
    </li>
  );
}

/** Skeleton layout shown while POST /ask is in flight. */
export function AskLoadingSkeleton() {
  return (
    <div className="flex justify-start" aria-busy="true" aria-label="Loading answer">
      <div className="max-w-[80%] rounded-2xl rounded-bl-sm border border-[var(--border)] bg-[var(--bg-card)] px-4 py-3 shadow-sm">
        <Skeleton className="mb-3 h-3 w-48" />
        <ul className="space-y-3">
          <CitationSkeleton />
          <CitationSkeleton />
        </ul>
      </div>
    </div>
  );
}
