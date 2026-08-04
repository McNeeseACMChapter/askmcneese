import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { CompactMetric } from "../components/viz/CompactMetric";
import { ProgressBar } from "../components/viz/ProgressBar";
import { Surface } from "../components/ui/Surface";
import { StatusBadge } from "../components/ui/StatusBadge";

const route = routeManifest.find((r) => r.id === "sga")!;

const stageLabels: Record<string, string> = {
  DRAFT: "Draft",
  HEARING: "Hearing scheduled",
  ACM_APPROVED: "ACM approved",
  SGA_APPROVED: "SGA approved",
  DISBURSED: "Disbursed",
};

function currency(value: number) {
  return `$${value.toLocaleString()}`;
}

export function SgaPage() {
  const state = useFixtureState();
  const totalRequested = state.sga.reduce((sum, r) => sum + r.requested, 0);
  const totalAwarded = state.sga.reduce((sum, r) => sum + r.awarded, 0);
  const openConditions = state.sga.reduce((sum, r) => sum + r.conditionsOpen, 0);
  const stages = Array.from(new Set(state.sga.map((r) => r.stage)));

  return (
    <PageChrome route={route} title="SGA">
      <div className="acm-metric-strip">
        <CompactMetric label="Requests" value={state.sga.length} />
        <CompactMetric label="Total requested" value={currency(totalRequested)} />
        <CompactMetric
          label="Total awarded"
          value={currency(totalAwarded)}
          deltaTone={totalAwarded > 0 ? "up" : "flat"}
        />
        <CompactMetric label="Open conditions" value={openConditions} />
      </div>

      <div className="board-cols">
        {stages.map((stage) => (
          <div key={stage} className="board-col">
            <h3>{stageLabels[stage] ?? stage}</h3>
            <div className="space-y-2">
              {state.sga
                .filter((r) => r.stage === stage)
                .map((request) => (
                  <Surface key={request.id} level="content" className="p-3">
                    <p className="text-sm font-semibold text-text-primary">{request.title}</p>
                    <div className="mt-2 flex items-center justify-between text-xs text-text-muted">
                      <span>Requested {currency(request.requested)}</span>
                      <span>Awarded {currency(request.awarded)}</span>
                    </div>
                    <div className="mt-2">
                      <ProgressBar
                        value={
                          request.requested > 0
                            ? Math.round((request.awarded / request.requested) * 100)
                            : 0
                        }
                        label="Awarded of requested"
                      />
                    </div>
                    <div className="mt-2 flex items-center justify-between">
                      {request.hearing ? (
                        <span className="text-xs text-text-muted">Hearing {request.hearing}</span>
                      ) : (
                        <span />
                      )}
                      {request.conditionsOpen > 0 ? (
                        <StatusBadge
                          label={`${request.conditionsOpen} condition${request.conditionsOpen > 1 ? "s" : ""}`}
                          tone="warning"
                        />
                      ) : (
                        <StatusBadge label="Clear" tone="success" />
                      )}
                    </div>
                  </Surface>
                ))}
            </div>
          </div>
        ))}
      </div>
    </PageChrome>
  );
}
