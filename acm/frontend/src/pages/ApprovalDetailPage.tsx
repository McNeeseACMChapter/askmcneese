import { useState } from "react";
import { useParams } from "react-router-dom";
import { PageChrome } from "../components/layout/PageChrome";
import { routeManifest } from "../routes/manifest";
import { useAttachEvidenceMutation, useDecideApprovalMutation, useFixtureState } from "../data/hooks";
import { usePrototype } from "../state/PrototypeContext";
import { useToast } from "../components/toast/ToastProvider";
import { Surface } from "../components/ui/Surface";
import { Button } from "../components/ui/Button";
import { EvidenceList } from "../components/ui/EvidenceList";
import { ApprovalHistory } from "../components/ui/ApprovalHistory";
import { StatusBadge, type StatusTone } from "../components/ui/StatusBadge";
import type { ApprovalStatus } from "../data/types";

const route = routeManifest.find((r) => r.id === "approvals")!;

const statusTone: Record<ApprovalStatus, StatusTone> = {
  pending: "warning",
  changes_requested: "warning",
  approved: "success",
  declined: "danger",
};

type Decision = Exclude<ApprovalStatus, "pending">;

export function ApprovalDetailPage() {
  const { approvalId } = useParams();
  const state = useFixtureState();
  const { user, roleId } = usePrototype();
  const { push } = useToast();
  const decideMutation = useDecideApprovalMutation();
  const attachMutation = useAttachEvidenceMutation();
  const [pendingEvidenceId, setPendingEvidenceId] = useState<string | null>(null);

  const approval = state.approvals.find((a) => a.id === approvalId) ?? state.approvals[0];

  if (!approval) {
    return (
      <PageChrome route={route} title="Approval not found">
        <Surface level="content" className="p-8">
          <p>No fixture approvals available.</p>
        </Surface>
      </PageChrome>
    );
  }

  function decide(decision: Decision) {
    decideMutation.mutate(
      { id: approval.id, decision, actor: user.name, actorInitials: user.initials, roleId },
      {
        onSuccess: () => {
          push({
            title:
              decision === "approved"
                ? "Approved"
                : decision === "declined"
                  ? "Declined"
                  : "Changes requested",
            description: `${approval.title} — recorded in the fixture audit log.`,
            tone: decision === "declined" ? "warning" : "success",
          });
        },
        onError: (error) => {
          push({
            title: "Decision failed",
            description: error instanceof Error ? error.message : "Fixture error.",
            tone: "failure",
          });
        },
      },
    );
  }

  function attach(evidenceId: string) {
    setPendingEvidenceId(evidenceId);
    attachMutation.mutate(
      { approvalId: approval.id, evidenceId, roleId },
      {
        onSuccess: () => push({ title: "Evidence attached", tone: "success" }),
        onError: (error) =>
          push({
            title: "Attach failed",
            description: error instanceof Error ? error.message : "Fixture error.",
            tone: "failure",
          }),
        onSettled: () => setPendingEvidenceId(null),
      },
    );
  }

  const canDecide = roleId === "advisor" || roleId === "president";
  const canAttach =
    roleId === "advisor" || roleId === "president" || roleId === "secretary";
  const missing = approval.evidence.filter((e) => !e.present);
  const pendingDecision = decideMutation.isPending ? decideMutation.variables?.decision : undefined;

  return (
    <PageChrome route={route} title={approval.title}>

      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge label={approval.status.replace("_", " ")} tone={statusTone[approval.status]} />
      </div>
      <p className="page-lede">
        {approval.kind} · Requested by {approval.requester}
      </p>

      <div className="space-y-4">
        <Surface level="approval" className="space-y-3">
          <h2 className="text-lg">Request summary</h2>
          <p className="text-sm text-text-secondary">{approval.reason}</p>
          <p className="text-sm">
            <span className="font-semibold">Impact: </span>
            <span className="text-text-secondary">{approval.impact}</span>
          </p>
        </Surface>

        {approval.missingEvidence ? (
          <div className="status-callout status-callout--gold" role="status">
            Missing evidence blocks a clean approval path. Attach the required item below before
            approving.
          </div>
        ) : null}

        <Surface level="content" className="p-5">
          <h2 className="text-lg">Required evidence</h2>
          <div className="mt-3">
            <EvidenceList items={approval.evidence} />
          </div>
          {missing.length > 0 && canAttach ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {missing.map((item) => (
                <Button
                  key={item.id}
                  variant="secondary"
                  disabled={pendingEvidenceId === item.id}
                  onClick={() => attach(item.id)}
                >
                  {pendingEvidenceId === item.id ? "Attaching…" : `Attach ${item.label}`}
                </Button>
              ))}
            </div>
          ) : null}
        </Surface>

        <Surface level="content" className="p-5">
          <h2 className="text-lg">Approval history</h2>
          <div className="mt-3">
            <ApprovalHistory items={approval.history} />
          </div>
        </Surface>

        <div className="status-callout status-callout--warning" role="note">
          <strong>Conflict of interest / SoD.</strong> {approval.conflictNotice}
        </div>

        {canDecide ? (
          <Surface level="content" className="flex flex-col gap-3 p-5 sm:flex-row sm:justify-end">
            <Button variant="danger-outline" disabled={decideMutation.isPending} onClick={() => decide("declined")}>
              {pendingDecision === "declined" ? "Declining…" : "Decline"}
            </Button>
            <Button
              variant="secondary"
              disabled={decideMutation.isPending}
              onClick={() => decide("changes_requested")}
            >
              {pendingDecision === "changes_requested" ? "Requesting…" : "Request changes"}
            </Button>
            <Button
              variant="primary"
              disabled={approval.missingEvidence || decideMutation.isPending}
              onClick={() => decide("approved")}
            >
              {pendingDecision === "approved" ? "Approving…" : "Approve"}
            </Button>
          </Surface>
        ) : (
          <Surface level="content" className="p-5">
            <div className="flex items-start gap-3">
              <StatusBadge label="View only" tone="muted" />
              <p className="text-sm text-text-secondary">
                {user.roleLabel} can inspect this request but cannot attach governance evidence or
                decide it. Advisor or President authority is required and is re-checked by policy.
              </p>
            </div>
          </Surface>
        )}
      </div>
    </PageChrome>
  );
}
