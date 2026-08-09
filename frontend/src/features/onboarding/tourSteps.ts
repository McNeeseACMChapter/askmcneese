export type TourInteraction =
  | "ack"
  | "click-target"
  | "finish"
  | "about";

export interface TourStep {
  id: string;
  title: string;
  description: string;
  targetId: string | null;
  route?: string;
  /** Route that completes a click-target step when observed. */
  completeRoute?: string;
  interaction: TourInteraction;
  nextLabel: string;
  /** Shown instead of a duplicate CTA when the real control must be used. */
  actionHint?: string;
  /** On mobile, open the more-menu before this target is available. */
  requiresMobileMenu?: boolean;
  allowScroll?: boolean;
  readingMode?: boolean;
  aboutAnchors?: string[];
}

export const TOUR_VERSION = 1;

/** Canonical conceptual sequence — same length on every viewport. */
export const TOUR_STEPS: TourStep[] = [
  {
    id: "welcome",
    title: "Welcome to AskMcNeese",
    description: "A quick walkthrough of the main parts of the platform.",
    targetId: "logo",
    route: "/ask",
    interaction: "ack",
    nextLabel: "Start tour",
  },
  {
    id: "ask",
    title: "Ask",
    description: "Ask questions about McNeese resources, academics, services, and campus information.",
    targetId: "ask",
    route: "/ask",
    completeRoute: "/ask",
    interaction: "click-target",
    nextLabel: "Next",
    actionHint: "Tap Ask to continue.",
  },
  {
    id: "ask_input",
    title: "Ask in your own words",
    description: "Describe what you’re trying to find. You don’t need the exact office or webpage.",
    targetId: "ask-input",
    route: "/ask",
    interaction: "ack",
    nextLabel: "Got it",
  },
  {
    id: "class_planner",
    title: "Class Planner",
    description: "Build and check your class schedule using real McNeese section data.",
    targetId: "class-planner",
    completeRoute: "/class-planner",
    interaction: "click-target",
    nextLabel: "Next",
    actionHint: "Tap Class Planner.",
    requiresMobileMenu: true,
  },
  {
    id: "planner_week",
    title: "Your week",
    description: "See your classes, times, rooms, and live position in your day.",
    targetId: "planner-week",
    route: "/class-planner",
    interaction: "ack",
    nextLabel: "Next",
  },
  {
    id: "planner_find",
    title: "Find classes",
    description: "Search McNeese sections when you’re building or changing your schedule.",
    targetId: "planner-find",
    route: "/class-planner",
    interaction: "ack",
    nextLabel: "Next",
  },
  {
    id: "about",
    title: "About",
    description: "See what AskMcNeese is and how the project works.",
    targetId: "about",
    route: "/about",
    completeRoute: "/about",
    interaction: "about",
    nextLabel: "Next",
    actionHint: "Tap About to continue.",
    allowScroll: true,
    readingMode: true,
    aboutAnchors: ["about-s1", "about-s2", "about-s3"],
  },
  {
    id: "updates",
    title: "Updates",
    description: "See what’s changed and what we’re improving.",
    targetId: "updates",
    completeRoute: "/updates",
    interaction: "click-target",
    nextLabel: "Next",
    actionHint: "Tap Updates to continue.",
    requiresMobileMenu: true,
  },
  {
    id: "usage",
    title: "Usage",
    description: "See your current platform usage.",
    targetId: "usage",
    completeRoute: "/status",
    interaction: "click-target",
    nextLabel: "Next",
    actionHint: "Tap Usage to continue.",
    requiresMobileMenu: true,
  },
  {
    id: "conversations",
    title: "Conversations",
    description: "Return to previous Ask conversations on this device.",
    targetId: "conversations",
    route: "/ask",
    interaction: "ack",
    nextLabel: "Got it",
    requiresMobileMenu: true,
  },
  {
    id: "home_banner",
    title: "Welcome area",
    description: "When Ask is empty, this area greets you and invites your first question.",
    targetId: "home-banner",
    route: "/ask",
    interaction: "ack",
    nextLabel: "Next",
  },
  {
    id: "settings",
    title: "Settings",
    description: "Manage available AskMcNeese preferences.",
    targetId: "settings",
    completeRoute: "/settings",
    interaction: "click-target",
    nextLabel: "Next",
    actionHint: "Tap Settings to continue.",
    requiresMobileMenu: true,
  },
  {
    id: "feedback",
    title: "Feedback",
    description: "Tell us when something is incorrect, confusing, or could be improved.",
    targetId: "feedback",
    completeRoute: "/feedback",
    interaction: "click-target",
    nextLabel: "Next",
    actionHint: "Tap Feedback to continue.",
    requiresMobileMenu: true,
  },
  {
    id: "complete",
    title: "You’re ready",
    description: "You’ve seen the main parts of AskMcNeese. Explore the platform normally.",
    targetId: null,
    interaction: "finish",
    nextLabel: "Start using AskMcNeese",
  },
];

const LEGACY_STEP_MAP: Record<string, string> = {
  menu: "class_planner",
  about_scroll: "about",
  about_reading: "about",
};

export function normalizeStepId(id: string | null | undefined): string | null {
  if (!id) return null;
  if (id in LEGACY_STEP_MAP) return LEGACY_STEP_MAP[id];
  return TOUR_STEPS.some((step) => step.id === id) ? id : "welcome";
}

export function resolveStep(step: TourStep, isMobile: boolean): TourStep {
  if (isMobile && step.id === "ask") {
    return {
      ...step,
      targetId: "logo",
      actionHint: "Tap AskMcNeese to continue.",
    };
  }
  if (isMobile && step.id === "conversations") {
    return {
      ...step,
      interaction: "click-target",
      actionHint: "Tap History to continue.",
    };
  }
  return step;
}

export function stepIndex(id: string | null | undefined): number {
  const normalized = normalizeStepId(id);
  if (!normalized) return 0;
  const index = TOUR_STEPS.findIndex((step) => step.id === normalized);
  return index >= 0 ? index : 0;
}

export function routeMatches(pathname: string, route: string | undefined): boolean {
  if (!route) return false;
  if (route === "/ask") return pathname === "/" || pathname === "/ask" || pathname.startsWith("/ask/");
  if (route === "/about") return pathname === "/about" || pathname.startsWith("/about/");
  return pathname === route || pathname.startsWith(`${route}/`);
}

/** Policy A: browser Back maps location → nearest earlier conceptual step when possible. */
export function stepForRoute(pathname: string, fromIndex: number): number | null {
  for (let i = fromIndex; i >= 0; i -= 1) {
    const step = TOUR_STEPS[i];
    const candidate = step.completeRoute ?? step.route;
    if (candidate && routeMatches(pathname, candidate)) return i;
  }
  return null;
}

export const CANONICAL_STEP_COUNT = TOUR_STEPS.length;
