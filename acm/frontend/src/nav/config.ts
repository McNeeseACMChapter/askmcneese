import type { LucideIcon } from "lucide-react";
import {
  Banknote,
  Bell,
  CalendarDays,
  ClipboardList,
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
} from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
  requiresAdmin?: boolean;
  requiresAudit?: boolean;
}

export interface NavGroup {
  id: string;
  label: string;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    id: "overview",
    label: "Overview",
    items: [
      { to: "/home", label: "Home", icon: Home, end: true },
      { to: "/my-work", label: "My Work", icon: ClipboardList, end: true },
    ],
  },
  {
    id: "operations",
    label: "Operations",
    items: [
      { to: "/projects", label: "Projects", icon: FolderKanban },
      { to: "/meetings", label: "Meetings", icon: CalendarDays },
      { to: "/events", label: "Events", icon: LayoutDashboard },
    ],
  },
  {
    id: "organization",
    label: "Organization",
    items: [
      { to: "/members", label: "Members", icon: Users },
      { to: "/governance", label: "Governance", icon: Scale },
      { to: "/sga", label: "SGA", icon: Landmark },
    ],
  },
  {
    id: "resources",
    label: "Resources",
    items: [
      { to: "/finance", label: "Finance", icon: Banknote },
      { to: "/communications", label: "Communications", icon: Megaphone },
      { to: "/documents", label: "Documents", icon: FileText },
      { to: "/reports", label: "Reports", icon: ScrollText },
    ],
  },
];

export const footerNav: NavItem[] = [
  { to: "/notifications", label: "Notifications", icon: Bell, end: true },
  {
    to: "/administration",
    label: "Administration",
    icon: Settings2,
    end: true,
    requiresAdmin: true,
  },
  {
    to: "/audit",
    label: "Audit",
    icon: Shield,
    end: true,
    requiresAudit: true,
  },
];

export const mobilePrimary = [
  { to: "/home", label: "Home", icon: Home, end: true },
  { to: "/my-work", label: "My Work", icon: ClipboardList, end: true },
  { to: "/meetings", label: "Meetings", icon: CalendarDays, end: false },
] as const;

export const mobileMoreItems: NavItem[] = [
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/events", label: "Events", icon: LayoutDashboard },
  { to: "/members", label: "Members", icon: Users },
  { to: "/governance", label: "Governance", icon: Scale },
  { to: "/finance", label: "Finance", icon: Banknote },
  { to: "/sga", label: "SGA", icon: Landmark },
  { to: "/communications", label: "Communications", icon: Megaphone },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/reports", label: "Reports", icon: ScrollText },
  {
    to: "/administration",
    label: "Administration",
    icon: Settings2,
    requiresAdmin: true,
  },
  { to: "/profile", label: "Profile", icon: Gavel },
];

export function pathActive(pathname: string, to: string, end?: boolean): boolean {
  if (end) return pathname === to;
  return pathname === to || pathname.startsWith(`${to}/`);
}
