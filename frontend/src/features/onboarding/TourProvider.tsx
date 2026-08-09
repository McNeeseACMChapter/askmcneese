import {
  createContext, useCallback, useContext, useEffect, useMemo, useReducer,
  useRef, useState, type ReactNode,
} from "react";
import { AnimatePresence } from "framer-motion";
import { useLocation, useNavigate } from "react-router-dom";
import {
  bootstrapGuest, completeTour, replayTour, skipTour,
  type GuestSession, type GuestUsage,
} from "./onboardingApi";
import { GuestAdmission } from "./GuestAdmission";
import { TourPersistQueue } from "./persistQueue";
import {
  CANONICAL_STEP_COUNT, resolveStep, routeMatches, stepIndex, TOUR_STEPS, type TourStep,
} from "./tourSteps";
import { INITIAL_TOUR_STATE, tourReducer, type OnboardingPhase } from "./tourMachine";
import { TourOverlay, type SpotlightRect } from "./TourOverlay";
import "./onboarding.css";

export type { OnboardingPhase } from "./tourMachine";

interface TourContextValue {
  active: boolean;
  phase: OnboardingPhase;
  step: TourStep | null;
  guestAlias: string | null;
  guestUsage: GuestUsage | null;
  showWelcomeGuest: boolean;
  openMobileMenu: boolean;
  requestOpenMobileMenu: () => void;
  notifyMobileMenuOpen: (open: boolean) => void;
  notifyTargetActivated: (tourId: string) => void;
  replayWalkthrough: () => Promise<void>;
}
const TourContext = createContext<TourContextValue>({
  active: false, phase: "BOOTSTRAPPING", step: null, guestAlias: null,
  guestUsage: null, showWelcomeGuest: false, openMobileMenu: false,
  requestOpenMobileMenu: () => undefined,
  notifyMobileMenuOpen: () => undefined,
  notifyTargetActivated: () => undefined,
  replayWalkthrough: async () => undefined,
});
export function useTour() { return useContext(TourContext); }

function useIsMobile() {
  const [mobile, setMobile] = useState(() =>
    typeof window !== "undefined" && window.matchMedia("(max-width: 767px)").matches,
  );
  useEffect(() => {
    const media = window.matchMedia("(max-width: 767px)");
    const update = () => setMobile(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  return mobile;
}
function measureTarget(id: string | null): SpotlightRect | null {
  if (!id) return null;
  const node = document.querySelector(`[data-tour-id="${id}"]`) as HTMLElement | null;
  if (!node) return null;
  const r = node.getBoundingClientRect();
  return r.width >= 2 && r.height >= 2
    ? { top: r.top, left: r.left, width: r.width, height: r.height } : null;
}
function scrollRootFor(ids: string[]): HTMLElement | null {
  for (const id of ids) {
    const anchor = document.querySelector(`[data-tour-id="${id}"]`);
    if (!anchor) continue;
    const root = anchor.closest("[data-tour-scroll-root]");
    if (root instanceof HTMLElement) return root;
    return document.scrollingElement instanceof HTMLElement
      ? document.scrollingElement : document.documentElement;
  }
  return null;
}
function aliasOf(session: GuestSession | null) {
  if (!session) return null;
  return session.displayAlias
    || session.guestId.replace(/^guest_/, "").slice(0, 4).toUpperCase()
    || null;
}
const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const WELCOME_KEY = "askmcneese_welcome_guest";

export function TourProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useIsMobile();
  const [machine, dispatch] = useReducer(tourReducer, INITIAL_TOUR_STATE);
  const [session, setSession] = useState<GuestSession | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);
  const [completeError, setCompleteError] = useState<string | null>(null);
  const [savingFinal, setSavingFinal] = useState(false);
  const [rect, setRect] = useState<SpotlightRect | null>(null);
  const [targetMissing, setTargetMissing] = useState(false);
  const [showWelcomeGuest, setShowWelcomeGuest] = useState(false);

  const environment = useRef({ pathname: location.pathname, isMobile });
  environment.current = { pathname: location.pathname, isMobile };
  const persistRef = useRef<TourPersistQueue | null>(null);
  const persistedIndex = useRef(-1);
  const enterTimer = useRef<number | null>(null);
  const exitTimer = useRef<number | null>(null);
  const actionTimer = useRef<number | null>(null);
  const actionLocked = useRef(false);
  const finishing = useRef(false);
  const rectRef = useRef<SpotlightRect | null>(null);
  const measureRaf = useRef<number | null>(null);
  const highlighted = useRef<string | null>(null);
  const scrolledTarget = useRef<string | null>(null);

  const phase = machine.phase;
  const active = [
    "TOUR_ENTERING", "TOUR_ACTIVE", "DRAWER_SUBSTATE", "ROUTE_TRANSITION",
    "GUIDED_READING", "TOUR_COMPLETING", "TOUR_EXITING",
  ].includes(phase) && session?.onboardingMode !== "disabled";
  const step = active ? resolveStep(TOUR_STEPS[machine.stepIndex], isMobile) : null;
  const waitingForDrawer = !!step && isMobile && !!step.requiresMobileMenu
    && !machine.menuOpen && phase === "DRAWER_SUBSTATE";
  const onAboutRoute = routeMatches(location.pathname, "/about");

  const displayStep = useMemo<TourStep | null>(() => {
    if (!step) return null;
    if (waitingForDrawer) {
      return {
        ...step,
        description: `Open the menu, then choose ${step.id === "conversations" ? "History" : step.title}.`,
        targetId: "menu", interaction: "click-target",
        actionHint: "Tap the highlighted menu button.", readingMode: false,
      };
    }
    if (step.interaction !== "about") return step;
    if (!onAboutRoute) {
      return {
        ...step,
        description: "Open About, then read through the story from beginning to end.",
        targetId: "about", interaction: "click-target", readingMode: false,
        actionHint: isMobile ? "Tap About to continue." : "Click About in the sidebar.",
      };
    }
    const anchors = step.aboutAnchors ?? [];
    const i = Math.min(Math.max(machine.readingProgress, 1) - 1, Math.max(anchors.length - 1, 0));
    return {
      ...step,
      description: "Read through the story. Reaching the final section releases the walkthrough.",
      targetId: anchors[i] ?? anchors[0] ?? "about-s1",
      interaction: "about", readingMode: true, nextLabel: "Continue",
      actionHint: "Scroll down to continue.",
    };
  }, [isMobile, machine.readingProgress, onAboutRoute, step, waitingForDrawer]);

  const overlayPhase = phase === "TOUR_ENTERING" ? "entering"
    : phase === "TOUR_EXITING" ? "exiting"
      : phase === "ROUTE_TRANSITION" ? "route" : "active";

  const runOnce = useCallback((action: () => void) => {
    if (actionLocked.current) return;
    actionLocked.current = true;
    action();
    if (actionTimer.current != null) window.clearTimeout(actionTimer.current);
    actionTimer.current = window.setTimeout(() => {
      actionLocked.current = false;
      actionTimer.current = null;
    }, 180);
  }, []);
  useEffect(() => {
    actionLocked.current = false;
    setTargetMissing(false);
    scrolledTarget.current = null;
  }, [machine.stepIndex]);

  useEffect(() => {
    const queue = new TourPersistQueue((next) => { if (next) setSession(next); });
    persistRef.current = queue;
    return () => queue.dispose();
  }, []);
  useEffect(() => {
    if (!active || !step || step.interaction === "finish") return;
    if (machine.stepIndex <= persistedIndex.current) return;
    persistedIndex.current = machine.stepIndex;
    persistRef.current?.enqueue(step.id);
  }, [active, machine.stepIndex, step]);

  const beginTour = useCallback((id: string | null) => {
    const env = environment.current;
    actionLocked.current = false;
    dispatch({ type: "START", stepId: id, pathname: env.pathname, isMobile: env.isMobile });
  }, []);
  const bootstrap = useCallback(async (signal?: AbortSignal) => {
    dispatch({ type: "BOOTSTRAP" });
    setBootError(null);
    setCompleteError(null);
    try {
      const next = await bootstrapGuest(signal);
      setSession(next);
      if (next.onboardingMode === "disabled" || next.tour.status === "completed") {
        persistedIndex.current = TOUR_STEPS.length - 1;
        dispatch({ type: "DONE" });
        const flag = sessionStorage.getItem(WELCOME_KEY);
        setShowWelcomeGuest(flag === next.guestId || flag === "1");
        return;
      }
      const admissionKey = `askmcneese_admission_done_${next.guestId}`;
      if (next.tour.status === "not_started" && next.isNewAssignment !== false
          && !sessionStorage.getItem(admissionKey)) {
        persistedIndex.current = -1;
        dispatch({ type: "ADMIT" });
        return;
      }
      persistedIndex.current = stepIndex(next.tour.currentStep ?? "welcome");
      beginTour(next.tour.currentStep ?? "welcome");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setBootError("We couldn’t start your guest session.");
      dispatch({ type: "FAIL" });
    }
  }, [beginTour]);
  useEffect(() => {
    const controller = new AbortController();
    void bootstrap(controller.signal);
    return () => {
      controller.abort();
      [enterTimer, exitTimer, actionTimer].forEach((ref) => {
        if (ref.current != null) window.clearTimeout(ref.current);
      });
      if (measureRaf.current != null) window.cancelAnimationFrame(measureRaf.current);
    };
  }, [bootstrap]);

  useEffect(() => {
    const refreshUsage = () => {
      void bootstrapGuest()
        .then((next) => setSession(next))
        .catch(() => undefined);
    };
    window.addEventListener("askmcneese:usage-changed", refreshUsage);
    return () => window.removeEventListener("askmcneese:usage-changed", refreshUsage);
  }, []);

  useEffect(() => {
    if (phase !== "TOUR_ENTERING") return;
    enterTimer.current = window.setTimeout(() => {
      const env = environment.current;
      dispatch({ type: "ENTERED", pathname: env.pathname, isMobile: env.isMobile });
      enterTimer.current = null;
    }, prefersReducedMotion() ? 0 : 240);
    return () => {
      if (enterTimer.current != null) window.clearTimeout(enterTimer.current);
      enterTimer.current = null;
    };
  }, [phase]);
  useEffect(() => {
    dispatch({ type: "ROUTE_CHANGED", pathname: location.pathname, isMobile });
  }, [isMobile, location.pathname]);
  useEffect(() => {
    if (!machine.desiredRoute) return;
    if (routeMatches(location.pathname, machine.desiredRoute)) {
      dispatch({ type: "ROUTE_CHANGED", pathname: location.pathname, isMobile });
    } else {
      navigate(machine.desiredRoute, { replace: true });
    }
  }, [isMobile, location.pathname, machine.desiredRoute, navigate]);

  const finishTour = useCallback(async () => {
    if (finishing.current) return;
    finishing.current = true;
    setSavingFinal(true);
    setCompleteError(null);
    dispatch({ type: "COMPLETE_REQUEST" });
    try {
      const next = await completeTour();
      setSession(next);
      setSavingFinal(false);
      dispatch({ type: "COMPLETE_SUCCESS" });
      exitTimer.current = window.setTimeout(() => {
        dispatch({ type: "COMPLETE_EXITED" });
        setShowWelcomeGuest(true);
        sessionStorage.setItem(WELCOME_KEY, next.guestId || "1");
        navigate("/ask", { replace: true });
        finishing.current = false;
      }, prefersReducedMotion() ? 0 : 340);
    } catch {
      finishing.current = false;
      setSavingFinal(false);
      setCompleteError("We couldn’t save your walkthrough yet. Check your connection and try again.");
      dispatch({ type: "FAIL" });
    }
  }, [navigate]);

  useEffect(() => {
    document.body.classList.toggle("tour-drawer-promoted", active && machine.menuOpen);
    return () => document.body.classList.remove("tour-drawer-promoted");
  }, [active, machine.menuOpen]);

  useEffect(() => {
    if (phase !== "GUIDED_READING" || !step || step.interaction !== "about") return;
    const anchors = step.aboutAnchors ?? [];
    let cancelled = false;
    let retryTimer: number | null = null;
    let unbind: (() => void) | null = null;

    const bind = () => {
      if (cancelled) return;
      const root = scrollRootFor(anchors);
      if (!root) {
        retryTimer = window.setTimeout(bind, 50);
        return;
      }

      const documentScroll = root === document.scrollingElement
        || root === document.documentElement || root === document.body;
      const eventTarget: Window | HTMLElement = documentScroll ? window : root;
      const update = (userInitiated: boolean) => {
        if (cancelled) return;
        const bottom = documentScroll ? window.innerHeight : root.getBoundingClientRect().bottom;
        let progress = 0;
        anchors.forEach((id, i) => {
          const node = document.querySelector(`[data-tour-id="${id}"]`);
          if (node && node.getBoundingClientRect().top <= bottom * 0.86) progress = i + 1;
        });
        const max = Math.max(0, root.scrollHeight - root.clientHeight);
        const atBottom = max <= 4 || root.scrollTop >= max - 4;
        const last = anchors.length
          ? document.querySelector(`[data-tour-id="${anchors[anchors.length - 1]}"]`) : null;
        const lastVisible = last ? last.getBoundingClientRect().bottom <= bottom + 4 : atBottom;
        dispatch({
          type: "READ_PROGRESS", progress,
          complete: userInitiated && root.scrollTop > 8 && (atBottom || lastVisible),
          pathname: environment.current.pathname, isMobile: environment.current.isMobile,
        });
      };
      const onScroll = () => update(true);
      eventTarget.addEventListener("scroll", onScroll, { passive: true });
      const observer = new ResizeObserver(() => update(false));
      observer.observe(root);
      anchors.forEach((id) => {
        const node = document.querySelector(`[data-tour-id="${id}"]`);
        if (node instanceof HTMLElement) observer.observe(node);
      });
      const raf = window.requestAnimationFrame(() => update(false));
      unbind = () => {
        window.cancelAnimationFrame(raf);
        eventTarget.removeEventListener("scroll", onScroll);
        observer.disconnect();
      };
    };

    bind();
    return () => {
      cancelled = true;
      if (retryTimer != null) window.clearTimeout(retryTimer);
      unbind?.();
    };
  }, [phase, step]);

  const applyTargetClass = useCallback((id: string | null) => {
    if (highlighted.current === id) {
      const found = id ? document.querySelector(`[data-tour-id="${id}"]`) : null;
      if (!id || found?.classList.contains("tour-target-active")) return;
    }
    document.querySelectorAll("[data-tour-id].tour-target-active")
      .forEach((node) => node.classList.remove("tour-target-active"));
    highlighted.current = id;
    if (id) document.querySelector(`[data-tour-id="${id}"]`)?.classList.add("tour-target-active");
  }, []);
  const refreshRect = useCallback(() => {
    if (!displayStep || phase === "ROUTE_TRANSITION" || phase === "TOUR_EXITING") {
      if (rectRef.current) {
        rectRef.current = null;
        setRect(null);
      }
      applyTargetClass(null);
      return;
    }
    const next = measureTarget(displayStep.targetId);
    const prev = rectRef.current;
    const changed = (!!next !== !!prev) || (!!next && !!prev && (
      Math.abs(next.top - prev.top) > .5 || Math.abs(next.left - prev.left) > .5
      || Math.abs(next.width - prev.width) > .5 || Math.abs(next.height - prev.height) > .5
    ));
    if (changed) {
      rectRef.current = next;
      setRect(next);
    }
    if (next && displayStep.targetId) {
      setTargetMissing(false);
      applyTargetClass(displayStep.targetId);
    } else if (!next) applyTargetClass(null);
  }, [applyTargetClass, displayStep, phase]);
  const scheduleMeasure = useCallback(() => {
    if (measureRaf.current != null) return;
    measureRaf.current = requestAnimationFrame(() => {
      measureRaf.current = null;
      refreshRect();
    });
  }, [refreshRect]);

  useEffect(() => {
    if (!displayStep?.targetId || !active) {
      rectRef.current = null;
      setRect(null);
      applyTargetClass(null);
      scrolledTarget.current = null;
      return;
    }
    let cancelled = false;
    let retry: number | null = null;
    let tries = 0;
    const id = displayStep.targetId;
    const find = () => {
      if (cancelled) return;
      const node = document.querySelector(`[data-tour-id="${id}"]`) as HTMLElement | null;
      if (node) {
        if (scrolledTarget.current !== id && !machine.menuOpen && phase !== "GUIDED_READING") {
          scrolledTarget.current = id;
          node.scrollIntoView({
            block: "nearest", inline: "nearest",
            behavior: prefersReducedMotion() ? "auto" : "smooth",
          });
        }
        refreshRect();
      } else if (++tries >= 40) {
        setTargetMissing(true);
        if (import.meta.env.DEV) console.warn(`[onboarding] target not found: ${id}`);
      } else retry = window.setTimeout(find, 50);
    };
    find();
    const mutation = new MutationObserver(scheduleMeasure);
    mutation.observe(document.body, { childList: true, subtree: true });
    const resize = new ResizeObserver(scheduleMeasure);
    resize.observe(document.documentElement);
    addEventListener("resize", scheduleMeasure);
    addEventListener("scroll", scheduleMeasure, { passive: true, capture: true });
    return () => {
      cancelled = true;
      if (retry != null) clearTimeout(retry);
      mutation.disconnect();
      resize.disconnect();
      removeEventListener("resize", scheduleMeasure);
      removeEventListener("scroll", scheduleMeasure, true);
      if (measureRaf.current != null) cancelAnimationFrame(measureRaf.current);
      measureRaf.current = null;
      applyTargetClass(null);
    };
  }, [
    active, applyTargetClass, displayStep?.targetId, machine.menuOpen,
    phase, refreshRect, scheduleMeasure,
  ]);

  useEffect(() => {
    if (!active || !step || step.allowScroll || phase === "GUIDED_READING" || machine.menuOpen) {
      document.body.classList.remove("tour-lock-scroll");
      return;
    }
    document.body.classList.add("tour-lock-scroll");
    return () => document.body.classList.remove("tour-lock-scroll");
  }, [active, machine.menuOpen, phase, step]);
  useEffect(() => {
    if (!active) return;
    const blockEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    addEventListener("keydown", blockEscape, true);
    return () => removeEventListener("keydown", blockEscape, true);
  }, [active]);

  const notifyMobileMenuOpen = useCallback((open: boolean) => {
    const env = environment.current;
    dispatch({ type: "MENU_CHANGED", open, pathname: env.pathname, isMobile: env.isMobile });
  }, []);
  const notifyTargetActivated = useCallback((targetId: string) => {
    if (!displayStep || !step || (waitingForDrawer && targetId === "menu")) return;
    runOnce(() => {
      const env = environment.current;
      dispatch({ type: "TARGET", targetId, pathname: env.pathname, isMobile: env.isMobile });
    });
  }, [displayStep, runOnce, step, waitingForDrawer]);
  const onAck = useCallback(() => {
    if (!displayStep || !step) return;
    if (step.interaction === "finish") {
      void finishTour();
      return;
    }
    runOnce(() => {
      const env = environment.current;
      dispatch({ type: "ACK", pathname: env.pathname, isMobile: env.isMobile });
    });
  }, [displayStep, finishTour, runOnce, step]);
  const onTargetClick = useCallback(() => {
    if (!displayStep?.targetId) return;
    (document.querySelector(
      `[data-tour-id="${displayStep.targetId}"]`,
    ) as HTMLElement | null)?.click();
  }, [displayStep]);
  const skipWalkthrough = useCallback(async () => {
    if (!session) return;
    try {
      const next = await skipTour();
      setSession(next);
      dispatch({ type: "DONE" });
      setShowWelcomeGuest(true);
      sessionStorage.setItem(WELCOME_KEY, next.guestId || "1");
      navigate("/ask", { replace: true });
    } catch {
      setBootError("We couldn’t save your choice. Try again.");
      dispatch({ type: "FAIL" });
    }
  }, [navigate, session]);

  const replayWalkthrough = useCallback(async () => {
    setShowWelcomeGuest(false);
    sessionStorage.removeItem(WELCOME_KEY);
    persistedIndex.current = -1;
    try {
      setSession(await replayTour());
    } catch {
      // Local replay still works while persistence is unavailable.
    }
    beginTour("welcome");
    navigate("/ask", { replace: true });
  }, [beginTour, navigate]);

  const startWalkthrough = useCallback(() => {
    if (session?.guestId) {
      sessionStorage.setItem(`askmcneese_admission_done_${session.guestId}`, "1");
    }
    beginTour("welcome");
  }, [beginTour, session?.guestId]);

  const guestAlias = aliasOf(session);
  const contextValue = useMemo<TourContextValue>(() => ({
    active, phase, step: displayStep, guestAlias,
    guestUsage: session?.usage ?? null,
    showWelcomeGuest: showWelcomeGuest && phase === "COMPLETED",
    openMobileMenu: false,
    requestOpenMobileMenu: () => undefined,
    notifyMobileMenuOpen, notifyTargetActivated, replayWalkthrough,
  }), [
    active, displayStep, guestAlias, notifyMobileMenuOpen, notifyTargetActivated,
    phase, replayWalkthrough, session?.usage, showWelcomeGuest,
  ]);
  const readingDone = phase === "GUIDED_READING" && !!step
    && machine.readingProgress >= (step.aboutAnchors?.length ?? Infinity);
  const showAck = !!displayStep
    && (displayStep.interaction === "ack" || displayStep.interaction === "finish" || readingDone)
    && phase !== "ROUTE_TRANSITION";
  const subLabel = phase === "GUIDED_READING" && (step?.aboutAnchors?.length ?? 0) > 0
    ? `Reading ${Math.min(Math.max(machine.readingProgress, 1), step!.aboutAnchors!.length)}/${step!.aboutAnchors!.length}`
    : waitingForDrawer ? "Menu" : null;

  return (
    <TourContext.Provider value={contextValue}>
      {children}
      <AnimatePresence>
        {phase === "ADMISSION" && guestAlias ? (
          <GuestAdmission
            key="admission"
            alias={guestAlias}
            mode="admission"
            onStart={startWalkthrough}
            onSkip={() => void skipWalkthrough()}
          />
        ) : null}
      </AnimatePresence>
      {phase === "RECOVERABLE_ERROR" && bootError && !session ? (
        <GuestAdmission alias="" mode="bootstrap-error" message={bootError}
          onRetry={() => void bootstrap()} />
      ) : null}
      {phase === "RECOVERABLE_ERROR" && completeError ? (
        <GuestAdmission alias={guestAlias ?? ""} mode="saving" message={completeError}
          onRetry={() => void finishTour()} />
      ) : null}
      {savingFinal && phase === "TOUR_COMPLETING" ? (
        <div className="tourSavingHint" aria-live="polite">Saving your setup…</div>
      ) : null}
      {displayStep && active ? (
        <TourOverlay
          open phase={overlayPhase} step={displayStep}
          stepNumber={machine.stepIndex + 1} stepCount={CANONICAL_STEP_COUNT}
          isMobile={isMobile} rect={rect}
          interactiveTarget={displayStep.interaction === "click-target"}
          drawerOpen={machine.menuOpen} readingMode={phase === "GUIDED_READING"}
          subLabel={subLabel} showAck={showAck} targetMissing={targetMissing}
          onAck={onAck}
          onSkip={() => void skipWalkthrough()}
          onRetryTarget={() => { setTargetMissing(false); refreshRect(); }}
          onTargetClick={onTargetClick}
        />
      ) : null}
    </TourContext.Provider>
  );
}
