import { useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useFixtureState } from "../data/hooks";
import { roleOptions, usersByRole } from "../data/seed";
import { ProgressRing } from "../components/viz/ProgressRing";
import { Surface } from "../components/ui/Surface";
import { StatusBadge } from "../components/ui/StatusBadge";

const route = routeManifest.find((r) => r.id === "governance")!;

const workflowNodes: Node[] = [
  { id: "submit", position: { x: 0, y: 40 }, data: { label: "Submit request" }, type: "input" },
  { id: "evidence", position: { x: 180, y: 40 }, data: { label: "Evidence check" } },
  { id: "officer", position: { x: 360, y: 0 }, data: { label: "Officer review" } },
  { id: "board", position: { x: 360, y: 90 }, data: { label: "Board (if required)" } },
  { id: "record", position: { x: 560, y: 40 }, data: { label: "Record + audit" }, type: "output" },
];

const workflowEdges: Edge[] = [
  { id: "e1", source: "submit", target: "evidence" },
  { id: "e2", source: "evidence", target: "officer" },
  { id: "e3", source: "evidence", target: "board" },
  { id: "e4", source: "officer", target: "record" },
  { id: "e5", source: "board", target: "record" },
];


export function GovernancePage() {
  const state = useFixtureState();
  const pendingApprovals = state.approvals.filter((a) => a.status === "pending");
  const quorumReadyMeetings = state.meetings.filter((m) => m.quorumReady).length;
  const quorumPercent = Math.round(
    (quorumReadyMeetings / Math.max(state.meetings.length, 1)) * 100,
  );
  const nodes = useMemo(() => workflowNodes, []);
  const edges = useMemo(() => workflowEdges, []);

  return (
    <PageChrome route={route} title="Governance">
      <Surface level="content" className="p-4">
        <h2 className="text-lg">Approval authority map</h2>
        <p className="mt-1 mb-3 text-sm text-text-secondary">
          Read-only fixture workflow — pan and zoom only; nodes are not editable.
        </p>
        <div className="acm-flow" aria-label="Governance approval workflow">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            nodesDraggable={false}
            nodesConnectable={false}
            elementsSelectable={false}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={16} size={1} />
            <MiniMap pannable zoomable />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
      </Surface>

      <div className="home-grid">
        <div className="space-y-4">
          <Surface level="content" className="overflow-hidden">
            <div className="border-b border-[var(--border-subtle)] px-5 py-4">
              <h2>Pending approvals</h2>
              <p className="mt-1 text-sm text-text-secondary">
                Governance decisions awaiting sign-off.
              </p>
            </div>
            {pendingApprovals.length === 0 ? (
              <p className="px-5 py-8 text-sm text-text-muted">
                No pending governance approvals in fixture.
              </p>
            ) : (
              <ul className="divide-y divide-[var(--border-subtle)]">
                {pendingApprovals.map((a) => (
                  <li
                    key={a.id}
                    className="row-hover flex flex-wrap items-center justify-between gap-3 px-5 py-4"
                  >
                    <div>
                      <p className="text-sm font-semibold text-text-primary">{a.title}</p>
                      <p className="text-xs text-text-muted">
                        {a.kind} · Requested by {a.requester}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      {a.missingEvidence ? (
                        <StatusBadge label="Missing evidence" tone="warning" />
                      ) : null}
                      <Link to={`/approvals/${a.id}`} className="acm-btn acm-btn--secondary no-underline">
                        Review
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Surface>

          <Surface level="content" className="p-5">
            <h2 className="text-lg">Recorded decisions</h2>
            <ul className="mt-3 space-y-3">
              {state.decisions.map((d) => (
                <li key={d.id} className="flex items-center justify-between gap-3 text-sm">
                  <span className="text-text-secondary">{d.title}</span>
                  <span className="flex items-center gap-2">
                    <span className="text-xs text-text-muted">{d.at}</span>
                    <StatusBadge label={d.status} tone="muted" />
                  </span>
                </li>
              ))}
            </ul>
          </Surface>
        </div>

        <div className="space-y-4">
          <Surface level="content" className="flex flex-col items-center gap-3 p-5 text-center">
            <h2 className="text-lg">Quorum health</h2>
            <ProgressRing value={quorumPercent} label="Quorum-ready meetings" size={96} />
            <p className="text-sm text-text-secondary">
              {quorumReadyMeetings} of {state.meetings.length} scheduled meetings meet quorum
              (fixture).
            </p>
          </Surface>

          <Surface level="content" className="p-5">
            <h2 className="text-lg">Officer terms</h2>
            <ul className="mt-3 space-y-3">
              {roleOptions.map((role) => {
                const officer = usersByRole[role.id];
                return (
                  <li key={role.id} className="flex items-center justify-between gap-3 text-sm">
                    <div>
                      <p className="font-semibold text-text-primary">{officer.name}</p>
                      <p className="text-xs text-text-muted">{role.label}</p>
                    </div>
                    <span className="text-xs font-semibold text-text-secondary">
                      {officer.termLabel}
                    </span>
                  </li>
                );
              })}
            </ul>
          </Surface>
        </div>
      </div>
    </PageChrome>
  );
}
