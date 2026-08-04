export type DataMode = "managed" | "workflow" | "derived" | "immutable" | "restricted";

export interface ModuleAccessContract {
  module: string;
  route: string;
  mode: DataMode;
  editable: string;
  controlled: string;
  derived: string;
  destination: string;
}

export interface AccessContractResponse {
  environment: string;
  authoritativeTarget: string;
  currentAdapter: string;
  modules: ModuleAccessContract[];
}

export const moduleAccessContracts: ModuleAccessContract[] = [
  {
    module: "Home & reports",
    route: "/home",
    mode: "derived",
    editable: "None directly",
    controlled: "Source records only",
    derived: "Counts, health rollups, activity, trends",
    destination: "Read model built from operational records",
  },
  {
    module: "Projects",
    route: "/projects",
    mode: "managed",
    editable: "Scope, milestone, due date, progress, health reason",
    controlled: "Owner, approval, completion, archive",
    derived: "Trend, risk count, evidence completeness",
    destination: "PostgreSQL target · SQLite development adapter",
  },
  {
    module: "Meetings & minutes",
    route: "/meetings",
    mode: "workflow",
    editable: "Draft agenda, time, location, draft minutes",
    controlled: "Publish, quorum, approved minutes, archive",
    derived: "Attendance and agenda completion rollups",
    destination: "Meeting records + immutable minutes versions",
  },
  {
    module: "Events",
    route: "/events",
    mode: "workflow",
    editable: "Concept, schedule, venue plan, volunteer plan",
    controlled: "Budget clearance, approval, completion",
    derived: "Readiness and registration percentages",
    destination: "Event records + linked finance/content workflows",
  },
  {
    module: "Members & roles",
    route: "/members",
    mode: "managed",
    editable: "Own availability, skills, contact preferences",
    controlled: "Role, term, standing, privileged access",
    derived: "Engagement and onboarding completion",
    destination: "Membership records + role-assignment workflow",
  },
  {
    module: "Governance",
    route: "/governance",
    mode: "workflow",
    editable: "Proposals and evidence before submission",
    controlled: "Votes, approvals, officer terms, recorded decisions",
    derived: "Quorum health",
    destination: "Append-only decision and approval records",
  },
  {
    module: "Finance",
    route: "/finance",
    mode: "workflow",
    editable: "Requests, vendor, purpose, receipt submission",
    controlled: "Budget, approvals, reconciliation, close",
    derived: "Actual, remaining, variance, aging",
    destination: "Finance ledger + object storage for receipts",
  },
  {
    module: "SGA",
    route: "/sga",
    mode: "workflow",
    editable: "Packet draft, request amount, hearing notes",
    controlled: "ACM approval, external award, disbursement",
    derived: "Award percentage and open-condition count",
    destination: "SGA request records + external evidence",
  },
  {
    module: "Communications",
    route: "/communications",
    mode: "workflow",
    editable: "Draft body, channel, proposed publish time",
    controlled: "Review, sensitive approval, publish",
    derived: "Pipeline counts and schedule status",
    destination: "Content records + published artifact archive",
  },
  {
    module: "Documents",
    route: "/documents",
    mode: "managed",
    editable: "Title, description, replacement upload",
    controlled: "Classification, retention, official version",
    derived: "Expiry and evidence completeness warnings",
    destination: "Object storage bytes + relational metadata",
  },
  {
    module: "Notifications",
    route: "/notifications",
    mode: "managed",
    editable: "Read state and personal delivery preferences",
    controlled: "System-generated message and recipient",
    derived: "Unread and priority counts",
    destination: "Notification delivery log",
  },
  {
    module: "Administration",
    route: "/administration",
    mode: "restricted",
    editable: "Technical configuration with change reason",
    controlled: "Organizational approvals and finance authority",
    derived: "Service health",
    destination: "Configuration store + immutable audit",
  },
  {
    module: "Audit",
    route: "/audit",
    mode: "immutable",
    editable: "Nothing",
    controlled: "Export by authorized roles",
    derived: "Filtered views only",
    destination: "Append-only audit log",
  },
];

export const modeLabels: Record<DataMode, string> = {
  managed: "Managed edit",
  workflow: "Workflow-controlled",
  derived: "System-derived",
  immutable: "Immutable",
  restricted: "Restricted",
};