export function EmptyState() {
  return (
    <div className="flex h-full flex-col items-center justify-center px-6 text-center">
      <svg
        className="mb-3 h-10 w-10 text-mcneese-blue/40"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
      <p className="text-sm font-semibold text-gray-600">Ask AskMcNeese anything</p>
      <p className="mt-1 max-w-xs text-xs text-gray-400">
        Try “When is the application deadline?” Answers will come from official McNeese sources.
      </p>
    </div>
  );
}
