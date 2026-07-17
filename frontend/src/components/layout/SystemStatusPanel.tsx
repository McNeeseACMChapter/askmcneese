import { useEffect, useState } from "react";
import { AnimatedMetric } from "../motion/AnimatedMetric";
import { RouteEnter } from "../motion/RouteEnter";
import { fetchAskStats, fetchHealth, type AskStatsResponse } from "../../lib/api";

export function SystemStatusPanel() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [stats, setStats] = useState<AskStatsResponse | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([fetchHealth(controller.signal), fetchAskStats(controller.signal)])
      .then(([, result]) => {
        setOnline(true);
        setStats(result);
      })
      .catch(() => setOnline(false));
    return () => controller.abort();
  }, []);

  return (
    <RouteEnter>
      <Panel title="System status" description="Current availability and aggregate request activity.">
        <div id="health" className="scroll-mt-24 rounded-xl border border-border bg-surface p-5">
          <div className="flex items-center gap-3">
            <span
              className={`h-3 w-3 rounded-full ${
                online === null ? "bg-warning animate-pulse" : online ? "bg-success" : "bg-error"
              }`}
            />
            <div>
              <p className="font-semibold">
                {online === null ? "Checking" : online ? "Online" : "Offline"}
              </p>
              <p className="text-sm text-text-muted">
                {online
                  ? "AskMcNeese is ready for questions."
                  : "The service is temporarily unavailable."}
              </p>
            </div>
          </div>
        </div>
        {online && stats && (
          <>
            <div id="knowledge" className="scroll-mt-24">
              <Stat
                label="Indexed sources"
                value={stats.knowledge_base?.count}
                format={(n) => String(Math.round(n))}
              />
            </div>
            <div id="model" className="scroll-mt-24 grid gap-3 sm:grid-cols-2">
              <Stat
                label="Recent queries"
                value={stats.pipeline?.total_queries}
                format={(n) => String(Math.round(n))}
              />
              <Stat
                label="Success rate"
                value={stats.pipeline?.success_rate}
                format={(n) => `${Math.round(n)}%`}
              />
            </div>
            <div id="config" className="scroll-mt-24">
              <Stat
                label="Average response"
                value={stats.pipeline?.avg_latency_ms}
                format={(n) => `${Math.round(n)} ms`}
              />
            </div>
          </>
        )}
      </Panel>
    </RouteEnter>
  );
}

function Stat({
  label,
  value,
  format,
}: {
  label: string;
  value: number | null | undefined;
  format: (n: number) => string;
}) {
  if (value === undefined || value === null) return null;
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="text-xs uppercase tracking-wide text-text-muted">{label}</p>
      <p className="mt-1 text-xl font-semibold">
        <AnimatedMetric value={value} format={format} />
      </p>
    </div>
  );
}

export function Panel({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <main className="w-full px-5 py-8 md:px-8 md:py-12">
      <div className="mx-auto max-w-3xl">
        <h1 className="font-editorial text-3xl font-semibold">{title}</h1>
        <p className="mt-1 text-text-secondary">{description}</p>
        <div className="mt-6 space-y-4">{children}</div>
      </div>
    </main>
  );
}
