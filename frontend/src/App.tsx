import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { ChatPage } from "./components/chat/ChatPage";
import { FeedbackPanel } from "./components/layout/FeedbackPanel";
import { SettingsPanel } from "./components/layout/SettingsPanel";
import { SystemStatusPanel } from "./components/layout/SystemStatusPanel";
import { PublicAppShell } from "./components/shell/PublicAppShell";
import { useAsk } from "./hooks/useAsk";
import { useConversations } from "./hooks/useConversations";
import { useHealth } from "./hooks/useHealth";
import { useSidebarPrefs } from "./hooks/useSidebarPrefs";
import {
  mergeAskResult,
  seedStreamingAssistant,
  streamingMessageForActiveConversation,
  updateStreamingText,
  type StreamingAssistantState,
} from "./lib/askSession";
import {
  applyActivityEvent,
  completeAskRun,
  createAskRun,
  type AskRun,
} from "./lib/askRun";
import { AboutLayout } from "./pages/about/AboutLayout";
import { AcmPanelPage } from "./acm/AcmPanelPage";
import { AcmLoginPage } from "./pages/AcmLoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { VisualProgressFixture } from "./pages/VisualProgressFixture";
import { TourProvider } from "./features/onboarding";
import type { ActivityEvent, ChatMessage, SourceScope } from "./types";

const AboutOverview = lazy(() =>
  import("./pages/about/AboutOverview").then((m) => ({ default: m.AboutOverview })),
);
const UpdatesPage = lazy(() =>
  import("./pages/UpdatesPage").then((m) => ({ default: m.UpdatesPage })),
);
const ClassPlannerPage = lazy(() =>
  import("./features/class-planner/ClassPlannerPage").then((m) => ({
    default: m.ClassPlannerPage,
  })),
);

function RouteFallback() {
  return (
    <div className="px-[var(--page-gutter)] py-10 text-sm text-text-muted" role="status">
      Loading…
    </div>
  );
}

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia(query).matches : true,
  );
  useEffect(() => {
    const media = window.matchMedia(query);
    const change = () => setMatches(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, [query]);
  return matches;
}

function AppRoutes() {
  const desktop = useMediaQuery("(min-width: 1024px)");
  const location = useLocation();
  const { status: healthStatus, capabilities } = useHealth();
  const { ask, stop, isLoading, status: askStatus, requestVisualState } = useAsk();
  const { sidebarCollapsed, setSidebarCollapsed, toggleSidebarCollapsed } = useSidebarPrefs();
  const conversationsApi = useConversations();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(desktop);
  const [sourceScope, setSourceScope] = useState<SourceScope>("adaptive");
  const [streaming, setStreaming] = useState<StreamingAssistantState>(null);
  const [activeRun, setActiveRun] = useState<AskRun | null>(null);
  const activeRequestRef = useRef<string | null>(null);
  const activeConversationRef = useRef<string | null>(null);
  const activeRunRef = useRef<AskRun | null>(null);

  useEffect(() => {
    activeRunRef.current = activeRun;
  }, [activeRun]);

  useEffect(() => setSidebarOpen(desktop), [desktop]);

  // Sync the visible thread only when the selected conversation changes.
  // Do NOT resync on every `updateConversation` persist — that previously wiped the
  // provisional assistant + activeRun and made live activity disappear entirely.
  useEffect(() => {
    const selectedId = conversationsApi.activeId;
    if (
      activeRequestRef.current &&
      activeConversationRef.current &&
      selectedId === activeConversationRef.current
    ) {
      return;
    }
    setMessages(conversationsApi.activeConversation?.messages ?? []);
    setActiveRun(null);
    setStreaming(null);
  }, [conversationsApi.activeId]);

  // Apply each sanitized SSE event immediately. This avoids the state/effect race
  // where the final activity event arrived after the run summary was persisted.
  const applyLiveActivity = useCallback((event: ActivityEvent) => {
    setActiveRun((previous) => {
      if (!previous) return previous;
      const next = applyActivityEvent(previous, event);
      activeRunRef.current = next;
      return next;
    });
  }, []);

  const clearStreaming = useCallback(() => {
    activeRequestRef.current = null;
    setStreaming(null);
  }, []);

  const newChat = useCallback(() => {
    stop();
    clearStreaming();
    setActiveRun(null);
    conversationsApi.selectConversation(null);
    setMessages([]);
    if (!desktop) setSidebarOpen(false);
  }, [clearStreaming, conversationsApi, desktop, stop]);

  const selectConversation = useCallback(
    (id: string) => {
      conversationsApi.selectConversation(id);
      if (!desktop) setSidebarOpen(false);
    },
    [conversationsApi, desktop],
  );

  const send = useCallback(
    async (text: string) => {
      if (isLoading || healthStatus === "offline") return;

      const turnId = `turn-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const requestId = `req-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const runId = `run-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const userMessageId = `u-${Date.now()}`;
      const assistantMessageId = `a-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

      // Claim the in-flight request before any conversation persistence so the
      // activeId sync effect cannot clear the provisional turn / live run.
      activeRequestRef.current = requestId;

      let conversationId = conversationsApi.activeId;
      if (!conversationId) conversationId = conversationsApi.createConversation().id;
      activeConversationRef.current = conversationId;

      const userMessage: ChatMessage = {
        id: userMessageId,
        role: "user",
        text,
        timestamp: new Date(),
      };
      const provisionalAssistant: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        text: "",
        isStreaming: true,
        timestamp: new Date(),
        runId,
      };

      const run = createAskRun({
        runId,
        requestId,
        turnId,
        userMessageId,
        assistantMessageId,
      });
      const runningRun: AskRun = { ...run, status: "running" };
      activeRunRef.current = runningRun;
      setActiveRun(runningRun);
      setStreaming(seedStreamingAssistant(requestId, conversationId, assistantMessageId));

      const pending = [...messages, userMessage, provisionalAssistant];
      setMessages(pending);
      // Persist user turn only; provisional empty assistant is UI-only until complete.
      conversationsApi.updateConversation(conversationId, [...messages, userMessage]);
      const history = messages
        .map((message) => ({
          role: message.role,
          content: (message.text || message.structured?.contentMarkdown || "").trim(),
        }))
        .filter((turn) => turn.content.length > 0);

      const response = await ask(
        text,
        sourceScope,
        (fullText) => {
          if (activeRequestRef.current !== requestId) return;
          if (activeConversationRef.current !== conversationId) return;
          setStreaming((previous) =>
            updateStreamingText(
              previous,
              requestId,
              conversationId,
              fullText,
              assistantMessageId,
            ),
          );
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? { ...message, text: fullText, isStreaming: true, runId }
                : message,
            ),
          );
        },
        history,
        { requestId, turnId, assistantMessageId, runId, userMessageId },
        applyLiveActivity,
      );

      if (activeRequestRef.current !== requestId) return;

      if (!response) {
        const base = activeRunRef.current?.runId === runId ? activeRunRef.current : run;
        const cancelledSnapshot = completeAskRun(base, "cancelled");
        const cancelledAssistant: ChatMessage = {
          id: assistantMessageId,
          role: "assistant",
          text: "",
          isStreaming: false,
          timestamp: new Date(),
          runId,
          runSummary: toPersistedRunSummary(cancelledSnapshot),
        };
        const cancelledThread = mergeAskResult(pending, cancelledAssistant);

        activeRunRef.current = null;
        setActiveRun(null);
        clearStreaming();
        setMessages(cancelledThread);
        conversationsApi.updateConversation(conversationId, cancelledThread);
        return;
      }

      const base =
        activeRunRef.current?.runId === runId ? activeRunRef.current : run;
      const finishedSnapshot = completeAskRun(
        base,
        response.isError ? "failed" : "completed",
      );

      const withSummary: ChatMessage = {
        ...response,
        id: assistantMessageId,
        runId,
        runSummary: toPersistedRunSummary(
          finishedSnapshot,
          response.citations?.length,
        ),
      };

      clearStreaming();
      const complete = mergeAskResult(pending, withSummary);
      setMessages(complete);
      conversationsApi.updateConversation(conversationId, complete);
      activeRunRef.current = null;
      setActiveRun(null);
    },
    [ask, applyLiveActivity, clearStreaming, conversationsApi, healthStatus, isLoading, messages, sourceScope],
  );

  const handleStop = useCallback(() => {
    stop();
    setActiveRun((previous) => {
      if (!previous) return previous;
      const cancelled = completeAskRun(previous, "cancelled");
      activeRunRef.current = cancelled;
      return cancelled;
    });
    clearStreaming();
  }, [clearStreaming, stop]);

  const streamingForActive = streamingMessageForActiveConversation(
    streaming,
    conversationsApi.activeId,
  );
  // Provisional assistant is already in `messages`; only overlay stream text if needed.
  const displayedMessages = useMemo(() => {
    if (!streamingForActive) return messages;
    if (messages.some((message) => message.id === streamingForActive.id)) {
      return messages.map((message) =>
        message.id === streamingForActive.id
          ? {
              ...message,
              text: streamingForActive.text || message.text,
              isStreaming: true,
              runId: message.runId ?? streamingForActive.runId,
            }
          : message,
      );
    }
    return [...messages, streamingForActive];
  }, [messages, streamingForActive]);

  const { routeLabel } = useMemo(() => {
    const path = location.pathname;
    if (path.startsWith("/ask") || path === "/") {
      return {
        routeLabel: conversationsApi.activeConversation?.title ?? "AskMcNeese",
      };
    }
    if (path.startsWith("/about")) return { routeLabel: "About" };
    if (path.startsWith("/class-planner")) return { routeLabel: "Class Planner" };
    if (path.startsWith("/updates")) return { routeLabel: "Updates" };
    if (path.startsWith("/status")) return { routeLabel: "Usage" };
    if (path.startsWith("/settings")) return { routeLabel: "Settings" };
    if (path.startsWith("/feedback")) return { routeLabel: "Feedback" };
    if (path.startsWith("/acm/panel")) return { routeLabel: "ACM Panel" };
    if (path.startsWith("/acm")) return { routeLabel: "ACM Member Login" };
    return { routeLabel: "AskMcNeese" };
  }, [conversationsApi.activeConversation?.title, location.pathname]);

  // Conversation / page identity for tabs — not a permanent Ask top bar.
  useEffect(() => {
    const path = location.pathname;
    const onAsk = path === "/" || path.startsWith("/ask");
    if (onAsk) {
      document.title =
        routeLabel && routeLabel !== "AskMcNeese"
          ? `${routeLabel} — AskMcNeese`
          : "AskMcNeese";
      return;
    }
    document.title =
      routeLabel && routeLabel !== "AskMcNeese"
        ? `${routeLabel} — AskMcNeese`
        : "AskMcNeese";
  }, [location.pathname, routeLabel]);

  return (
    <Routes>
      <Route
        element={
          <PublicAppShell
            healthStatus={healthStatus}
            sidebarCollapsed={sidebarCollapsed}
            onToggleSidebarCollapsed={toggleSidebarCollapsed}
            setSidebarCollapsed={setSidebarCollapsed}
            desktop={desktop}
            mobileNavOpen={sidebarOpen}
            onMobileNavOpenChange={setSidebarOpen}
            conversations={conversationsApi.conversations}
            activeId={conversationsApi.activeId}
            onSelectConversation={selectConversation}
            onRename={conversationsApi.renameConversation}
            onTogglePin={conversationsApi.togglePin}
            onDelete={conversationsApi.deleteConversation}
            onNewChat={newChat}
            routeLabel={routeLabel}
          />
        }
      >
        <Route path="/" element={<Navigate to="/ask" replace />} />
        <Route
          path="/ask"
          element={
            <ChatPage
              messages={displayedMessages}
              isLoading={isLoading}
              askStatus={askStatus}
              activeRun={activeRun}
              requestVisualState={requestVisualState}
              offline={healthStatus === "offline"}
              sourceScope={sourceScope}
              onSourceScopeChange={setSourceScope}
              webSearchAvailable={capabilities.officialWebSearchAvailable}
              onSend={send}
              onStop={handleStop}
            />
          }
        />
        <Route path="/about" element={<AboutLayout />}>
          <Route
            index
            element={
              <Suspense fallback={<RouteFallback />}>
                <AboutOverview />
              </Suspense>
            }
          />
          <Route path="team" element={<Navigate to="/about" replace />} />
          <Route path="advisor" element={<Navigate to="/about" replace />} />
          <Route path="methodology" element={<Navigate to="/about" replace />} />
          <Route path="roadmap" element={<Navigate to="/about" replace />} />
        </Route>
        <Route
          path="/updates"
          element={
            <Suspense fallback={<RouteFallback />}>
              <UpdatesPage />
            </Suspense>
          }
        />
        <Route
          path="/class-planner"
          element={
            <Suspense fallback={<RouteFallback />}>
              <ClassPlannerPage />
            </Suspense>
          }
        />
        <Route path="/status" element={<SystemStatusPanel />} />
        <Route
          path="/settings"
          element={
            <SettingsPanel
              sidebarCollapsed={sidebarCollapsed}
              onSidebarCollapsedChange={setSidebarCollapsed}
              onClearHistory={() => {
                conversationsApi.clearConversations();
                clearStreaming();
                setMessages([]);
              }}
            />
          }
        />
        <Route path="/feedback" element={<FeedbackPanel />} />
        <Route path="/acm/login" element={<AcmLoginPage />} />
        <Route path="/acm/panel" element={<AcmPanelPage />} />
        <Route path="/acm" element={<Navigate to="/acm/panel" replace />} />
        <Route path="/workspace/login" element={<Navigate to="/acm/login" replace />} />
        <Route path="/__visual__/progress-active" element={<VisualProgressFixture mode="active" />} />
        <Route path="/__visual__/progress-details" element={<VisualProgressFixture mode="details" />} />
        <Route path="/__visual__/progress-complete" element={<VisualProgressFixture mode="complete" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

function toPersistedRunSummary(
  run: AskRun,
  citationFallback?: number,
): NonNullable<ChatMessage["runSummary"]> {
  return {
    runId: run.runId,
    status: run.status === "failed" ? "failed" : run.status === "cancelled" ? "cancelled" : "completed",
    stages: run.stages.map((stage) => ({
      id: stage.id,
      event: stage.event,
      label: stage.label,
      detail: stage.detail,
      status: stage.status,
      elapsedMs: stage.elapsedMs,
      phase: stage.phase,
      kind: stage.kind,
      operationId: stage.operationId,
      sourceTitle: stage.sourceTitle,
      sourceHost: stage.sourceHost,
      sourceUrl: stage.sourceUrl,
      sourceType: stage.sourceType,
      count: stage.count,
    })),
    durationMs: run.completedAt ? run.completedAt - run.startedAt : undefined,
    sourcesFound: run.sourcesFound ?? citationFallback,
    sourcesRead: run.sourcesRead,
    citationsUsed: run.citationsUsed ?? citationFallback,
  };
}

export default function App() {
  return (
    <BrowserRouter>
      <TourProvider>
        <AppRoutes />
      </TourProvider>
    </BrowserRouter>
  );
}
