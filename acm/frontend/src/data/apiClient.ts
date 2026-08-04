import type { AccessContractResponse } from "./accessContract";
import type { ProjectHealth, ProjectRecord, RoleId } from "./types";

const API_BASE = import.meta.env.VITE_ACM_API_BASE ?? "/api/acm";

export class AcmApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "AcmApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(API_BASE + path, {
    ...init,
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) {
    let message = "Request failed (" + response.status + ")";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // A non-JSON proxy or network response keeps the status fallback.
    }
    throw new AcmApiError(message, response.status);
  }
  return (await response.json()) as T;
}

export interface PersistedProject {
  id: string;
  name: string;
  owner: string;
  ownerInitials: string;
  health: ProjectHealth;
  progressPercent: number;
  nextMilestone: string;
  dueDate: string;
  scope: string;
  updatedAt: string;
}

export interface ProjectUpdateInput {
  id: string;
  actor: string;
  actorInitials: string;
  roleId: RoleId;
  reason: string;
  changes: Partial<
    Pick<ProjectRecord, "scope" | "nextMilestone" | "dueDate" | "progressPercent" | "health">
  >;
}

export const acmApi = {
  getAccessContract() {
    return request<AccessContractResponse>("/access-contract");
  },

  getProjects() {
    return request<PersistedProject[]>("/projects");
  },

  updateProject(input: ProjectUpdateInput) {
    return request<PersistedProject>("/projects/" + input.id, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "X-ACM-Actor": input.actor,
        "X-ACM-Role": input.roleId,
      },
      body: JSON.stringify({
        ...input.changes,
        reason: input.reason,
      }),
    });
  },
};