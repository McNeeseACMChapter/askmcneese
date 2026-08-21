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
export type ApprovalStatus = "pending" | "changes_requested" | "approved" | "declined";
export type WorkItemState = "now" | "upcoming" | "waiting" | "completed" | "overdue";
export type MeetingLifecycle =
  | "agenda_draft"
  | "published"
  | "in_progress"
  | "minutes_draft"
  | "under_review"
  | "approved";

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

export interface WorkItem {
  id: string;
  title: string;
  reason: string;
  deadline: string;
  status: string;
  statusTone: "info" | "warning" | "danger" | "success";
  actionLabel: string;
  href: string;
  bucket: WorkItemState;
  parentLabel: string;
  progress: number;
  ownerRole: RoleId | "any";
}

export interface ProjectRecord {
  id: string;
  name: string;
  owner: string;
  ownerInitials: string;
  health: ProjectHealth;
  progressPercent: number;
  nextMilestone: string;
  dueDate: string;
  updated: string;
  scope: string;
  riskCount: number;
  riskSeverity: "low" | "medium" | "high";
  evidenceCompleteness: number;
  trend: number[];
  milestones: { id: string; label: string; done: boolean; due: string }[];
  risks: { id: string; label: string; severity: "low" | "medium" | "high" }[];
  team: { name: string; initials: string; role: string }[];
  archived?: boolean;
}

export interface ApprovalRecord {
  id: string;
  title: string;
  kind: string;
  requester: string;
  reason: string;
  impact: string;
  status: ApprovalStatus;
  missingEvidence: boolean;
  conflictNotice: string;
  evidence: { id: string; label: string; present: boolean }[];
  history: { id: string; actor: string; action: string; at: string }[];
  relatedProjectId?: string;
}

export interface MeetingRecord {
  id: string;
  title: string;
  start: string;
  end: string;
  location: string;
  lifecycle: MeetingLifecycle;
  quorumReady: boolean;
  agendaCompletion: number;
  minutesStatus: string;
  attendanceTrend: number[];
}

export interface EventRecord {
  id: string;
  title: string;
  start: string;
  end: string;
  registrationPercent: number;
  venueReady: boolean;
  volunteerCoverage: number;
  promotionReady: boolean;
  budgetOk: boolean;
  readiness: number;
}

export interface MemberRecord {
  id: string;
  name: string;
  initials: string;
  role: string;
  term: string;
  availability: string;
  skills: string[];
  projects: string[];
  onboardingPercent: number;
  engagement: number[];
}

export interface FinanceSnapshot {
  budget: number;
  actual: number;
  remaining: number;
  categories: { name: string; budget: number; actual: number }[];
  monthly: number[];
  pendingApprovals: number;
  missingReceipts: number;
  reimbursementAgeDays: number;
  fundingSources: { name: string; amount: number }[];
  reconciledPercent: number;
}

export interface AuditEvent {
  id: string;
  at: string;
  actor: string;
  actorInitials: string;
  action: string;
  resource: string;
  before?: string;
  after?: string;
  reason?: string;
  severity: "info" | "warning" | "critical";
}

export interface NotificationItem {
  id: string;
  title: string;
  body: string;
  unread: boolean;
  priority: "normal" | "high";
  href: string;
  at: string;
}

export interface DocumentRecord {
  id: string;
  title: string;
  classification: string;
  owner: string;
  version: string;
  expires?: string;
  related: string;
}

export interface ContentItem {
  id: string;
  title: string;
  channel: string;
  stage: "draft" | "review" | "approved" | "scheduled" | "published";
  publishAt?: string;
}

export interface SgaRequest {
  id: string;
  title: string;
  stage: string;
  requested: number;
  awarded: number;
  hearing?: string;
  conditionsOpen: number;
}

export interface DecisionItem {
  id: string;
  title: string;
  at: string;
  status: string;
}

export interface ChapterPulse {
  attentionCount: number;
  projectsAtRisk: number;
  approvalsWaiting: number;
  nextMeeting: string;
  activity7d: number[];
  portfolioHealth: number[];
}

export type MutationPhase =
  | "idle"
  | "pending"
  | "optimistic"
  | "confirmed"
  | "failed"
  | "reverted";
