import { computePulse, createSeedState, type SeedState } from "./seed";
import { acmApi, type ProjectUpdateInput } from "./apiClient";
import type { ApprovalStatus, AuditEvent, RoleId } from "./types";

export type FailureMode = "none" | "network" | "permission" | "conflict";

let state = createSeedState();
let failureMode: FailureMode = "none";
let delayMs = 450;
const listeners = new Set<() => void>();

function notify() {
  listeners.forEach((l) => l());
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

async function gate<T>(fn: () => T): Promise<T> {
  await sleep(delayMs);
  if (failureMode === "network") throw new Error("Network unavailable (fixture).");
  if (failureMode === "permission") throw new Error("Permission denied (fixture).");
  if (failureMode === "conflict") throw new Error("Conflict of interest (fixture).");
  return fn();
}

function pushAudit(partial: Omit<AuditEvent, "id" | "at"> & { at?: string }) {
  const event: AuditEvent = {
    id: `a-${Date.now()}`,
    at: partial.at ?? new Date().toISOString(),
    actor: partial.actor,
    actorInitials: partial.actorInitials,
    action: partial.action,
    resource: partial.resource,
    before: partial.before,
    after: partial.after,
    reason: partial.reason,
    severity: partial.severity,
  };
  state = { ...state, audit: [event, ...state.audit] };
}

export const fixtureRepo = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  getSnapshot(): SeedState {
    return state;
  },
  reset() {
    state = createSeedState();
    failureMode = "none";
    notify();
  },
  setFailureMode(mode: FailureMode) {
    failureMode = mode;
  },
  setDelay(ms: number) {
    delayMs = ms;
  },
  async getState() {
    return gate(() => structuredClone(state));
  },
  async getPulse() {
    return gate(() => computePulse(state));
  },
  async getProjects() {
    return gate(() => structuredClone(state.projects.filter((p) => !p.archived)));
  },
  async getProject(id: string) {
    return gate(() => {
      const p = state.projects.find((x) => x.id === id);
      if (!p) throw new Error("Project not found");
      return structuredClone(p);
    });
  },
  async getApproval(id: string) {
    return gate(() => {
      const a = state.approvals.find((x) => x.id === id);
      if (!a) throw new Error("Approval not found");
      return structuredClone(a);
    });
  },
  async decideApproval(input: {
    id: string;
    decision: Exclude<ApprovalStatus, "pending">;
    actor: string;
    actorInitials: string;
    roleId: RoleId;
    allowMissingEvidence?: boolean;
  }) {
    return gate(() => {
      if (input.roleId !== "advisor" && input.roleId !== "president") {
        throw new Error("This role cannot decide organizational approvals.");
      }
      const idx = state.approvals.findIndex((a) => a.id === input.id);
      if (idx < 0) throw new Error("Approval not found");
      const current = state.approvals[idx];
      if (current.missingEvidence && input.decision === "approved" && !input.allowMissingEvidence) {
        throw new Error("Missing evidence blocks approval.");
      }
      const before = current.status;
      const next = {
        ...current,
        status: input.decision,
        history: [
          ...current.history,
          {
            id: `h-${Date.now()}`,
            actor: input.actor,
            action:
              input.decision === "approved"
                ? "Approved"
                : input.decision === "declined"
                  ? "Declined"
                  : "Requested changes",
            at: new Date().toLocaleString(),
          },
        ],
      };
      const approvals = [...state.approvals];
      approvals[idx] = next;

      let workItems = state.workItems;
      if (input.decision === "approved") {
        workItems = workItems.map((w) =>
          w.href.includes(input.id)
            ? {
                ...w,
                bucket: "completed" as const,
                status: "Approved",
                statusTone: "success" as const,
                progress: 100,
              }
            : w,
        );
      }

      let projects = state.projects;
      if (input.id === "ap-proj-001" && input.decision === "approved") {
        projects = [
          {
            id: "proj-api-ws",
            name: "Campus API workshop",
            owner: "Taylor Brooks",
            ownerInitials: "TB",
            health: "on_track",
            progressPercent: 5,
            nextMilestone: "Kickoff agenda",
            dueDate: "2026-10-01",
            updated: "just now",
            scope: "4-week ENCS workshop series.",
            riskCount: 0,
            riskSeverity: "low",
            evidenceCompleteness: 30,
            trend: [0, 0, 0, 0, 0, 0, 5],
            milestones: [
              { id: "m1", label: "Kickoff", done: false, due: "Aug 5" },
            ],
            risks: [],
            team: [{ name: "Taylor Brooks", initials: "TB", role: "Lead" }],
          },
          ...projects,
        ];
      }

      state = { ...state, approvals, workItems, projects };
      pushAudit({
        actor: input.actor,
        actorInitials: input.actorInitials,
        action: input.decision.toUpperCase(),
        resource: `Approval:${input.id}`,
        before,
        after: input.decision,
        severity: input.decision === "declined" ? "warning" : "info",
      });
      notify();
      return structuredClone(next);
    });
  },
  async markNotificationRead(id: string) {
    return gate(() => {
      state = {
        ...state,
        notifications: state.notifications.map((n) =>
          n.id === id ? { ...n, unread: false } : n,
        ),
      };
      notify();
      return structuredClone(state.notifications);
    });
  },
  async attachEvidence(approvalId: string, evidenceId: string, roleId: RoleId) {
    return gate(() => {
      if (roleId !== "advisor" && roleId !== "president" && roleId !== "secretary") {
        throw new Error("This role cannot attach governance evidence.");
      }
      const approvals = state.approvals.map((a) => {
        if (a.id !== approvalId) return a;
        const evidence = a.evidence.map((e) =>
          e.id === evidenceId ? { ...e, present: true } : e,
        );
        const missingEvidence = evidence.some((e) => !e.present);
        return { ...a, evidence, missingEvidence };
      });
      state = { ...state, approvals };
      notify();
      return structuredClone(approvals.find((a) => a.id === approvalId)!);
    });
  },  async hydrateProjects() {
    const persisted = await acmApi.getProjects();
    const byId = new Map(persisted.map((project) => [project.id, project]));
    state = {
      ...state,
      projects: state.projects.map((project) => {
        const remote = byId.get(project.id);
        if (!remote) return project;
        return {
          ...project,
          scope: remote.scope,
          nextMilestone: remote.nextMilestone,
          dueDate: remote.dueDate,
          progressPercent: remote.progressPercent,
          health: remote.health,
          updated: "persisted",
        };
      }),
    };
    notify();
    return structuredClone(state.projects);
  },
  async updateProject(input: ProjectUpdateInput) {
    const current = state.projects.find((project) => project.id === input.id);
    if (!current) throw new Error("Project not found");
    const persisted = await acmApi.updateProject(input);
    state = {
      ...state,
      projects: state.projects.map((project) =>
        project.id === input.id
          ? {
              ...project,
              scope: persisted.scope,
              nextMilestone: persisted.nextMilestone,
              dueDate: persisted.dueDate,
              progressPercent: persisted.progressPercent,
              health: persisted.health,
              updated: "just now",
            }
          : project,
      ),
    };
    pushAudit({
      actor: input.actor,
      actorInitials: input.actorInitials,
      action: "PROJECT_UPDATED",
      resource: "Project:" + input.id,
      before: JSON.stringify({
        scope: current.scope,
        nextMilestone: current.nextMilestone,
        dueDate: current.dueDate,
        progressPercent: current.progressPercent,
        health: current.health,
      }),
      after: JSON.stringify(input.changes),
      reason: input.reason,
      severity: "info",
    });
    notify();
    return structuredClone(state.projects.find((project) => project.id === input.id)!);
  },
};
