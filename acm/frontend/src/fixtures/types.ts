export type RoleId =
  | "advisor"
  | "president"
  | "vice_president"
  | "treasurer"
  | "secretary"
  | "project_manager"
  | "sga_representative"
  | "social_media_manager"
  | "general_member";

export type ProjectHealth = "on_track" | "at_risk" | "blocked" | "completed" | "archived";

export interface FixtureUser {
  id: string;
  name: string;
  initials: string;
  roleId: RoleId;
  roleLabel: string;
  termLabel: string;
  canViewAdmin: boolean;
  canViewAudit: boolean;
}

export interface AttentionItem {
  id: string;
  title: string;
  reason: string;
  deadline: string;
  status: string;
  statusTone: "info" | "warning" | "danger" | "success";
  actionLabel: string;
  href: string;
}

export interface ProjectRecord {
  id: string;
  name: string;
  owner: string;
  health: ProjectHealth;
  nextMilestone: string;
  dueDate: string;
  updated: string;
  scope: string;
  risks: string[];
  archived?: boolean;
}

export interface ApprovalRecord {
  id: string;
  title: string;
  kind: string;
  requester: string;
  reason: string;
  impact: string;
  missingEvidence: boolean;
  conflictNotice: string;
  evidence: { id: string; label: string; present: boolean }[];
  history: { id: string; actor: string; action: string; at: string }[];
}
