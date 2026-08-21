import type { LucideIcon } from "lucide-react";
import {
  Banknote,
  Bell,
  CalendarDays,
  ClipboardList,
  Database,
  FileText,
  FolderKanban,
  Gavel,
  Home,
  Landmark,
  LayoutDashboard,
  Megaphone,
  Scale,
  Settings2,
  Shield,
  Users,
  ScrollText,
  PartyPopper,
} from "lucide-react";

export type NavGroup = "overview" | "operations" | "organization" | "resources" | "system";
export type RouteLayout =
  | "command-center"
  | "work-queue"
  | "collection"
  | "detail"
  | "calendar"
  | "workflow"
  | "analytics"
  | "library"
  | "event-stream"
  | "directory"
  | "auth";
export type PageWidth = "wide" | "standard" | "reading";
export type Density = "comfortable" | "compact";

export interface AcmRouteDefinition {
  id: string;
  path: string;
  navGroup: NavGroup;
  label: string;
  breadcrumb: string;
  purpose: string;
  layout: RouteLayout;
  width: PageWidth;
  density: Density;
  icon: LucideIcon;
  showInSidebar: boolean;
  showInMobilePrimary?: boolean;
  showInMobileMore?: boolean;
  requiredPermission?: "admin" | "audit";
  primaryAction?: { label: string; permission?: string };
  end?: boolean;
}

export const routeManifest: AcmRouteDefinition[] = [
  {
    id: "home",
    path: "/home",
    navGroup: "overview",
    label: "Home",
    breadcrumb: "Overview",
    purpose: "Chapter condition, recent change, and what needs attention.",
    layout: "command-center",
    width: "wide",
    density: "comfortable",
    icon: Home,
    showInSidebar: true,
    showInMobilePrimary: true,
    end: true,
  },
  {
    id: "my-work",
    path: "/my-work",
    navGroup: "overview",
    label: "My Work",
    breadcrumb: "Overview",
    purpose: "Personal execution: now, waiting, overdue, and completed.",
    layout: "work-queue",
    width: "wide",
    density: "comfortable",
    icon: ClipboardList,
    showInSidebar: true,
    showInMobilePrimary: true,
    end: true,
  },
  {
    id: "projects",
    path: "/projects",
    navGroup: "operations",
    label: "Projects",
    breadcrumb: "Operations",
    purpose: "Portfolio health, progress, risk, and next milestones.",
    layout: "collection",
    width: "wide",
    density: "compact",
    icon: FolderKanban,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "project-detail",
    path: "/projects/:projectId",
    navGroup: "operations",
    label: "Project",
    breadcrumb: "Projects",
    purpose: "Delivery cockpit for a single workstream.",
    layout: "detail",
    width: "standard",
    density: "comfortable",
    icon: FolderKanban,
    showInSidebar: false,
  },
  {
    id: "meetings",
    path: "/meetings",
    navGroup: "operations",
    label: "Meetings",
    breadcrumb: "Operations",
    purpose: "Temporal workspace: calendar, lifecycle, quorum, minutes.",
    layout: "calendar",
    width: "wide",
    density: "comfortable",
    icon: CalendarDays,
    showInSidebar: true,
    showInMobilePrimary: true,
  },
  {
    id: "events",
    path: "/events",
    navGroup: "operations",
    label: "Events",
    breadcrumb: "Operations",
    purpose: "Event operations: readiness, registration, promotion.",
    layout: "calendar",
    width: "wide",
    density: "comfortable",
    icon: PartyPopper,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "members",
    path: "/members",
    navGroup: "organization",
    label: "Members",
    breadcrumb: "Organization",
    purpose: "People, roles, terms, and capability.",
    layout: "directory",
    width: "wide",
    density: "compact",
    icon: Users,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "governance",
    path: "/governance",
    navGroup: "organization",
    label: "Governance",
    breadcrumb: "Organization",
    purpose: "Decisions, quorum, officer terms, and procedures.",
    layout: "workflow",
    width: "standard",
    density: "comfortable",
    icon: Scale,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "sga",
    path: "/sga",
    navGroup: "organization",
    label: "SGA",
    breadcrumb: "Organization",
    purpose: "Funding and representation pipeline.",
    layout: "workflow",
    width: "standard",
    density: "comfortable",
    icon: Landmark,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "finance",
    path: "/finance",
    navGroup: "resources",
    label: "Finance",
    breadcrumb: "Resources",
    purpose: "Budget vs actual, receipts, approvals, reconciliation.",
    layout: "analytics",
    width: "wide",
    density: "compact",
    icon: Banknote,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "communications",
    path: "/communications",
    navGroup: "resources",
    label: "Communications",
    breadcrumb: "Resources",
    purpose: "Editorial pipeline and content calendar.",
    layout: "calendar",
    width: "wide",
    density: "comfortable",
    icon: Megaphone,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "documents",
    path: "/documents",
    navGroup: "resources",
    label: "Documents",
    breadcrumb: "Resources",
    purpose: "Institutional memory and evidence library.",
    layout: "library",
    width: "wide",
    density: "compact",
    icon: FileText,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "reports",
    path: "/reports",
    navGroup: "resources",
    label: "Reports",
    breadcrumb: "Resources",
    purpose: "Analytical trends and term comparisons.",
    layout: "analytics",
    width: "wide",
    density: "comfortable",
    icon: ScrollText,
    showInSidebar: true,
    showInMobileMore: true,
  },
  {
    id: "data-access",
    path: "/data-access",
    navGroup: "system",
    label: "Data & access",
    breadcrumb: "System",
    purpose: "What can change, who may change it, and where every record persists.",
    layout: "collection",
    width: "wide",
    density: "compact",
    icon: Database,
    showInSidebar: true,
    showInMobileMore: true,
    end: true,
  },
  {
    id: "notifications",
    path: "/notifications",
    navGroup: "system",
    label: "Notifications",
    breadcrumb: "System",
    purpose: "Unread actions and chapter alerts.",
    layout: "event-stream",
    width: "standard",
    density: "compact",
    icon: Bell,
    showInSidebar: true,
    showInMobileMore: true,
    end: true,
  },
  {
    id: "administration",
    path: "/administration",
    navGroup: "system",
    label: "Administration",
    breadcrumb: "System",
    purpose: "Technical configuration (no org approval powers).",
    layout: "collection",
    width: "standard",
    density: "comfortable",
    icon: Settings2,
    showInSidebar: true,
    showInMobileMore: true,
    requiredPermission: "admin",
    end: true,
  },
  {
    id: "audit",
    path: "/audit",
    navGroup: "system",
    label: "Audit",
    breadcrumb: "System",
    purpose: "Dense immutable event stream.",
    layout: "event-stream",
    width: "wide",
    density: "compact",
    icon: Shield,
    showInSidebar: true,
    showInMobileMore: true,
    requiredPermission: "audit",
    end: true,
  },
  {
    id: "approvals",
    path: "/approvals/:approvalId",
    navGroup: "operations",
    label: "Approval",
    breadcrumb: "Approvals",
    purpose: "Decision surface with evidence and SoD.",
    layout: "workflow",
    width: "reading",
    density: "comfortable",
    icon: Gavel,
    showInSidebar: false,
  },
  {
    id: "profile",
    path: "/profile",
    navGroup: "system",
    label: "Profile",
    breadcrumb: "System",
    purpose: "Member identity and fixture role context.",
    layout: "detail",
    width: "reading",
    density: "comfortable",
    icon: Users,
    showInSidebar: false,
    showInMobileMore: true,
    end: true,
  },
  {
    id: "login",
    path: "/login",
    navGroup: "system",
    label: "Sign in",
    breadcrumb: "Auth",
    purpose: "UI-only prototype entry.",
    layout: "auth",
    width: "reading",
    density: "comfortable",
    icon: Home,
    showInSidebar: false,
  },
  {
    id: "fixtures",
    path: "/fixtures",
    navGroup: "system",
    label: "Fixture gallery",
    breadcrumb: "Dev",
    purpose: "Development index for states and roles.",
    layout: "collection",
    width: "standard",
    density: "comfortable",
    icon: LayoutDashboard,
    showInSidebar: false,
  },
];

export const navGroupOrder: NavGroup[] = [
  "overview",
  "operations",
  "organization",
  "resources",
  "system",
];

export const navGroupLabels: Record<NavGroup, string> = {
  overview: "Overview",
  operations: "Operations",
  organization: "Organization",
  resources: "Resources",
  system: "System",
};

export function findRouteByPath(pathname: string): AcmRouteDefinition | undefined {
  const exact = routeManifest.find((r) => r.path === pathname);
  if (exact) return exact;
  if (pathname.startsWith("/projects/") && pathname !== "/projects") {
    return routeManifest.find((r) => r.id === "project-detail");
  }
  if (pathname.startsWith("/approvals/")) {
    return routeManifest.find((r) => r.id === "approvals");
  }
  return undefined;
}

export function pathActive(pathname: string, to: string, end?: boolean): boolean {
  if (end) return pathname === to;
  return pathname === to || pathname.startsWith(`${to}/`);
}

export function widthClass(width: PageWidth): string {
  if (width === "wide") return "page-frame page-frame--collection";
  if (width === "reading") return "page-frame page-frame--approval";
  return "page-frame page-frame--detail";
}
