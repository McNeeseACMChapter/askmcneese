import {
  normalizeStepId,
  resolveStep,
  routeMatches,
  stepForRoute,
  stepIndex,
  TOUR_STEPS,
} from "./tourSteps";

export type OnboardingPhase =
  | "BOOTSTRAPPING"
  | "ADMISSION"
  | "TOUR_ENTERING"
  | "TOUR_ACTIVE"
  | "DRAWER_SUBSTATE"
  | "ROUTE_TRANSITION"
  | "GUIDED_READING"
  | "TOUR_COMPLETING"
  | "TOUR_EXITING"
  | "COMPLETED"
  | "RECOVERABLE_ERROR";

export interface TourMachineState {
  phase: OnboardingPhase;
  stepIndex: number;
  menuOpen: boolean;
  readingProgress: number;
  desiredRoute: string | null;
  awaitedRoute: string | null;
}

export type TourMachineEvent =
  | { type: "BOOTSTRAP" }
  | { type: "ADMIT" }
  | { type: "START"; stepId: string | null; pathname: string; isMobile: boolean }
  | { type: "ENTERED"; pathname: string; isMobile: boolean }
  | { type: "ACK"; pathname: string; isMobile: boolean }
  | { type: "TARGET"; targetId: string; pathname: string; isMobile: boolean }
  | { type: "ROUTE_CHANGED"; pathname: string; isMobile: boolean }
  | { type: "MENU_CHANGED"; open: boolean; pathname: string; isMobile: boolean }
  | { type: "READ_PROGRESS"; progress: number; complete: boolean; pathname: string; isMobile: boolean }
  | { type: "COMPLETE_REQUEST" }
  | { type: "COMPLETE_SUCCESS" }
  | { type: "COMPLETE_EXITED" }
  | { type: "FAIL" }
  | { type: "DONE" };

export const INITIAL_TOUR_STATE: TourMachineState = {
  phase: "BOOTSTRAPPING",
  stepIndex: 0,
  menuOpen: false,
  readingProgress: 0,
  desiredRoute: null,
  awaitedRoute: null,
};

function isTourPhase(phase: OnboardingPhase): boolean {
  return phase === "TOUR_ENTERING"
    || phase === "TOUR_ACTIVE"
    || phase === "DRAWER_SUBSTATE"
    || phase === "ROUTE_TRANSITION"
    || phase === "GUIDED_READING";
}

function settleStep(
  state: TourMachineState,
  pathname: string,
  isMobile: boolean,
): TourMachineState {
  const step = resolveStep(TOUR_STEPS[state.stepIndex] ?? TOUR_STEPS[0], isMobile);

  if (
    step.route
    && step.interaction === "ack"
    && !routeMatches(pathname, step.route)
  ) {
    return {
      ...state,
      phase: "ROUTE_TRANSITION",
      desiredRoute: step.route,
      awaitedRoute: null,
    };
  }

  if (step.interaction === "about" && routeMatches(pathname, step.route)) {
    return {
      ...state,
      phase: "GUIDED_READING",
      desiredRoute: null,
      awaitedRoute: null,
    };
  }

  if (isMobile && step.requiresMobileMenu && !state.menuOpen) {
    return {
      ...state,
      phase: "DRAWER_SUBSTATE",
      desiredRoute: null,
      awaitedRoute: null,
    };
  }

  return {
    ...state,
    phase: "TOUR_ACTIVE",
    desiredRoute: null,
    awaitedRoute: null,
  };
}

function enterStep(
  state: TourMachineState,
  nextIndex: number,
  pathname: string,
  isMobile: boolean,
): TourMachineState {
  const bounded = Math.max(0, Math.min(nextIndex, TOUR_STEPS.length - 1));
  return settleStep(
    {
      ...state,
      stepIndex: bounded,
      menuOpen: false,
      readingProgress: 0,
      desiredRoute: null,
      awaitedRoute: null,
    },
    pathname,
    isMobile,
  );
}

function advance(
  state: TourMachineState,
  pathname: string,
  isMobile: boolean,
): TourMachineState {
  if (state.stepIndex >= TOUR_STEPS.length - 1) return state;
  return enterStep(state, state.stepIndex + 1, pathname, isMobile);
}

export function tourReducer(
  state: TourMachineState,
  event: TourMachineEvent,
): TourMachineState {
  switch (event.type) {
    case "BOOTSTRAP":
      return { ...INITIAL_TOUR_STATE };
    case "ADMIT":
      return { ...INITIAL_TOUR_STATE, phase: "ADMISSION" };
    case "START":
      return {
        ...INITIAL_TOUR_STATE,
        phase: "TOUR_ENTERING",
        stepIndex: stepIndex(normalizeStepId(event.stepId) ?? "welcome"),
      };
    case "ENTERED":
      if (state.phase !== "TOUR_ENTERING") return state;
      return settleStep(state, event.pathname, event.isMobile);
    case "ACK": {
      if (!isTourPhase(state.phase)) return state;
      const step = resolveStep(TOUR_STEPS[state.stepIndex], event.isMobile);
      if (step.interaction === "finish") return state;
      if (step.interaction === "about") {
        const required = step.aboutAnchors?.length ?? 0;
        if (state.phase !== "GUIDED_READING" || state.readingProgress < required) return state;
      } else if (step.interaction !== "ack") {
        return state;
      }
      return advance(state, event.pathname, event.isMobile);
    }
    case "TARGET": {
      if (!isTourPhase(state.phase)) return state;
      const step = resolveStep(TOUR_STEPS[state.stepIndex], event.isMobile);
      const waitingForMenu = event.isMobile && !!step.requiresMobileMenu && !state.menuOpen;
      if (waitingForMenu) return state;
      if (step.targetId !== event.targetId) return state;

      if (step.interaction === "about") {
        if (routeMatches(event.pathname, step.route)) {
          return { ...state, phase: "GUIDED_READING", awaitedRoute: null };
        }
        return {
          ...state,
          phase: "ROUTE_TRANSITION",
          awaitedRoute: step.completeRoute ?? step.route ?? null,
          desiredRoute: null,
        };
      }

      if (step.interaction !== "click-target") return state;
      if (!step.completeRoute || routeMatches(event.pathname, step.completeRoute)) {
        return advance(state, event.pathname, event.isMobile);
      }
      return {
        ...state,
        phase: "ROUTE_TRANSITION",
        awaitedRoute: step.completeRoute,
        desiredRoute: null,
      };
    }
    case "ROUTE_CHANGED": {
      if (!isTourPhase(state.phase)) return state;
      const step = resolveStep(TOUR_STEPS[state.stepIndex], event.isMobile);

      if (state.desiredRoute && routeMatches(event.pathname, state.desiredRoute)) {
        return settleStep(
          { ...state, desiredRoute: null, awaitedRoute: null },
          event.pathname,
          event.isMobile,
        );
      }

      if (state.awaitedRoute && routeMatches(event.pathname, state.awaitedRoute)) {
        if (step.interaction === "about") {
          return {
            ...state,
            phase: "GUIDED_READING",
            desiredRoute: null,
            awaitedRoute: null,
            menuOpen: false,
          };
        }
        return advance(state, event.pathname, event.isMobile);
      }

      if (step.interaction === "about" && routeMatches(event.pathname, step.route)) {
        return {
          ...state,
          phase: "GUIDED_READING",
          desiredRoute: null,
          awaitedRoute: null,
        };
      }

      if (step.interaction === "click-target" && routeMatches(event.pathname, step.completeRoute)) {
        return advance(state, event.pathname, event.isMobile);
      }

      if (state.phase !== "ROUTE_TRANSITION" && step.requiresMobileMenu && !state.menuOpen) {
        if (event.isMobile) return { ...state, phase: "DRAWER_SUBSTATE" };
      }
      if (!event.isMobile && state.phase === "DRAWER_SUBSTATE") {
        return { ...state, phase: "TOUR_ACTIVE" };
      }

      const mapped = stepForRoute(event.pathname, state.stepIndex);
      if (mapped != null && mapped < state.stepIndex) {
        return enterStep(state, mapped, event.pathname, event.isMobile);
      }

      if (step.route && step.interaction === "ack" && !routeMatches(event.pathname, step.route)) {
        return {
          ...state,
          phase: "ROUTE_TRANSITION",
          desiredRoute: step.route,
          awaitedRoute: null,
        };
      }

      return state;
    }
    case "MENU_CHANGED": {
      if (!isTourPhase(state.phase)) return { ...state, menuOpen: event.open };
      const next = { ...state, menuOpen: event.open };
      if (state.phase === "ROUTE_TRANSITION") return next;
      const step = resolveStep(TOUR_STEPS[state.stepIndex], event.isMobile);
      if (!event.isMobile || !step.requiresMobileMenu) return next;
      return {
        ...next,
        phase: event.open ? "TOUR_ACTIVE" : "DRAWER_SUBSTATE",
      };
    }
    case "READ_PROGRESS":
      if (state.phase !== "GUIDED_READING") return state;
      if (event.complete) return advance(state, event.pathname, event.isMobile);
      if (event.progress <= state.readingProgress) return state;
      return { ...state, readingProgress: event.progress };
    case "COMPLETE_REQUEST":
      return { ...state, phase: "TOUR_COMPLETING" };
    case "COMPLETE_SUCCESS":
      return { ...state, phase: "TOUR_EXITING" };
    case "COMPLETE_EXITED":
    case "DONE":
      return { ...INITIAL_TOUR_STATE, phase: "COMPLETED" };
    case "FAIL":
      return { ...state, phase: "RECOVERABLE_ERROR" };
    default:
      return state;
  }
}