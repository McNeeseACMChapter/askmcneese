/**
 * AskMcNeese chain of command — facts from project docs + chapter governance.
 * Photo slots use public paths when assets exist; otherwise initials render.
 */
export type OrgTenure = {
  label: string;
  /** Soft visual treatment for alumni / departed contributors */
  status: "active" | "former";
  /** ISO date YYYY-MM-DD — role start (local calendar) */
  startDate: string;
  /** ISO date YYYY-MM-DD — role end; omit while still active */
  endDate?: string;
};

export type OrgPerson = {
  id: string;
  name: string;
  role: string;
  detail?: string;
  tenure?: OrgTenure;
  /** Optional portrait under /public/about/team/{id}.jpg */
  photoSrc?: string;
  initials: string;
};

export type OrgNode =
  | { kind: "org"; id: string; title: string; subtitle: string }
  | { kind: "person"; person: OrgPerson };

const MS_DAY = 86_400_000;

/** Parse YYYY-MM-DD as local midnight (avoids UTC off-by-one). */
export function parseLocalDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/**
 * Inclusive calendar days in role.
 * Active: start → today. Former: start → endDate.
 */
export function daysInRole(
  tenure: Pick<OrgTenure, "startDate" | "endDate">,
  now: Date = new Date(),
): number {
  const start = parseLocalDate(tenure.startDate);
  const end = tenure.endDate
    ? parseLocalDate(tenure.endDate)
    : new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.round((end.getTime() - start.getTime()) / MS_DAY) + 1;
  return Math.max(1, days);
}

export function formatDaysInRole(days: number): string {
  return days === 1 ? "1 day" : `${days} days`;
}

export const orgUmbrella = {
  id: "acm",
  title: "McNeese ACM",
  subtitle: "Student Chapter · Organizational home",
  logoSrc: "/about/team/acm-logo.svg",
} as const;

export const orgPresident: OrgPerson = {
  id: "kody-vo",
  name: "Kody Vo",
  role: "Chapter President",
  detail: "Works closely with the project manager on chapter alignment.",
  initials: "KV",
  photoSrc: "/about/team/kody-vo.jpg",
};

export const orgAdvisor: OrgPerson = {
  id: "vipin-menon",
  name: "Dr. Vipin Menon",
  role: "Project Advisor",
  detail: "Validates Prince’s product vision and sprint deliverables.",
  tenure: {
    label: "June 8 – Current",
    status: "active",
    startDate: "2026-06-08",
  },
  initials: "VM",
  photoSrc: "/about/team/vipin-menon.jpg",
};

export const orgManager: OrgPerson = {
  id: "prince-pudasaini",
  name: "Prince Pudasaini",
  role: "Project Manager",
  detail: "Owns delivery end-to-end — product direction, sprints, and coordination.",
  tenure: {
    label: "June 8 – Current",
    status: "active",
    startDate: "2026-06-08",
  },
  initials: "PP",
  photoSrc: "/about/team/prince-pudasaini.jpg",
};

/** Same-row builders under the PM */
export const orgBuilders: OrgPerson[] = [
  {
    id: "landon-peurta",
    name: "Landon Peurta",
    role: "Backend Developer",
    detail: "Sprint 1–2 backend track.",
    tenure: {
      label: "June 8 – July 2",
      status: "former",
      startDate: "2026-06-08",
      endDate: "2026-07-02",
    },
    initials: "LP",
    photoSrc: "/about/team/landon-peurta.jpg",
  },
  {
    id: "ziyan",
    name: "Ziyan",
    role: "Backend Developer",
    detail: "Current backend ownership after July 2 handoff.",
    tenure: {
      label: "July 2 – Current",
      status: "active",
      startDate: "2026-07-02",
    },
    initials: "Z",
    photoSrc: "/about/team/ziyan.jpg",
  },
  {
    id: "evan-weber",
    name: "Evan Weber",
    role: "Frontend Developer",
    detail: "Ask experience, shell, and client delivery.",
    tenure: {
      label: "June 8 – Current",
      status: "active",
      startDate: "2026-06-08",
    },
    initials: "EW",
    photoSrc: "/about/team/evan-weber.jpg",
  },
];
