export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-md bg-surface-subtle ${className}`}
      aria-hidden
    />
  );
}

export function TableSkeleton() {
  return (
    <div className="space-y-2 p-4" role="status" aria-label="Loading">
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-14 w-full" />
      <Skeleton className="h-14 w-full" />
      <Skeleton className="h-14 w-full" />
      <span className="sr-only">Loading records</span>
    </div>
  );
}
