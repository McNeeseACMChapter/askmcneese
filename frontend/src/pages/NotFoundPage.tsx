import { Link } from "react-router-dom";
import { ArrowLeft, Compass, MessageCircleQuestion } from "lucide-react";

export function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-[var(--page-gutter)] py-16 text-center">
      <div
        className="pointer-events-none absolute inset-0 overflow-hidden"
        aria-hidden="true"
      >
        <div className="absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 rounded-full bg-brand-100/60 blur-3xl" />
      </div>

      <div className="relative glass-content max-w-lg rounded-2xl border border-[var(--glass-border)] bg-[var(--glass-content-bg)] p-10 backdrop-blur">
        <p className="mb-2 font-mono text-sm font-medium text-brand-700">404</p>
        <h1 className="mb-3 font-serif text-3xl font-semibold text-text-primary">
          Page not found
        </h1>
        <p className="mb-8 leading-relaxed text-text-secondary">
          The page you requested does not exist or may have moved. Return to AskMcNeese to continue
          exploring campus information.
        </p>

        <div className="flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            to="/ask"
            className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-action-primary px-5 py-2.5 text-sm font-medium text-action-primary-text transition-colors hover:bg-action-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus sm:w-auto"
          >
            <MessageCircleQuestion className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
            Return to Ask
          </Link>
          <Link
            to="/about"
            className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-[var(--glass-border)] bg-surface px-5 py-2.5 text-sm font-medium text-brand-700 transition-colors hover:border-[var(--border-active)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus sm:w-auto"
          >
            <Compass className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
            About AskMcNeese
          </Link>
        </div>

        <p className="mt-6">
          <Link
            to="/ask"
            className="inline-flex items-center gap-1 text-sm text-text-muted hover:text-brand-700"
          >
            <ArrowLeft className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
            Go back to the assistant
          </Link>
        </p>
      </div>
    </div>
  );
}
