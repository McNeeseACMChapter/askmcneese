import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  /** Optional custom UI when a child throws. */
  fallback?: ReactNode;
  /** Hook for logging or telemetry. */
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

function WarningIcon() {
  return (
    <svg
      className="h-12 w-12 text-mcneese-gold"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    </svg>
  );
}

function DefaultFallback({ error, onReset }: { error: Error | null; onReset: () => void }) {
  function handleReload() {
    window.location.reload();
  }

  return (
    <div className="flex h-full justify-center bg-[var(--bg-page)] sm:items-center sm:py-6">
      <div
        role="alert"
        className="flex h-full w-full flex-col bg-[var(--bg-surface)] shadow-xl sm:h-[640px] sm:max-w-md sm:overflow-hidden sm:rounded-2xl"
      >
        <header className="bg-[var(--bg-header)] px-4 py-3 text-[var(--text-on-header)]">
          <h1 className="text-lg font-bold tracking-tight">AskMcNeese</h1>
          <p className="text-xs text-[var(--text-on-header-muted)]">We ran into a problem</p>
        </header>

        <main className="flex flex-1 flex-col items-center justify-center px-6 text-center">
          <WarningIcon />
          <h2 className="mt-4 text-base font-semibold text-[var(--text-primary)]">
            Something went wrong on our end
          </h2>
          <p className="mt-2 max-w-xs text-sm leading-relaxed text-[var(--text-secondary)]">
            The app hit an unexpected error. Reloading usually gets you back to asking questions
            about McNeese.
          </p>

          {import.meta.env.DEV && error && (
            <details className="mt-4 w-full max-w-xs text-left">
              <summary className="cursor-pointer text-xs font-medium text-[var(--text-muted)]">
                Error details (dev only)
              </summary>
              <pre className="mt-2 max-h-28 overflow-auto rounded-lg border border-[var(--error-border)] bg-[var(--error-bg)] p-2 text-[10px] leading-snug text-[var(--error-text)]">
                {error.message}
              </pre>
            </details>
          )}

          <div className="mt-6 flex w-full max-w-xs flex-col gap-2">
            <button
              type="button"
              onClick={handleReload}
              className="rounded-full bg-mcneese-blue px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-mcneese-dark"
            >
              Reload AskMcNeese
            </button>
            <button
              type="button"
              onClick={onReset}
              className="rounded-full border border-[var(--border)] bg-[var(--bg-card)] px-4 py-2.5 text-sm font-medium text-[var(--text-secondary)] transition hover:bg-[var(--bg-page)]"
            >
              Try again without reloading
            </button>
          </div>
        </main>

        <footer className="bg-[var(--bg-card)] py-2 text-center text-[11px] text-[var(--text-muted)]">
          Built by McNeese ACM
        </footer>
      </div>
    </div>
  );
}

/** Catches render errors in child components and shows a recovery UI. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    this.props.onError?.(error, info);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <DefaultFallback error={this.state.error} onReset={this.handleReset} />
        )
      );
    }

    return this.props.children;
  }
}
