import { useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { Menu } from "lucide-react";
import { BrandLogo } from "../brand/BrandLogo";
import { UnifiedSidebar, type SidebarMode } from "./UnifiedSidebar";
import { MobileTopNavigation } from "./MobileNavigation";
import { MobileHistorySheet } from "./MobileHistorySheet";
import { useTour } from "../../features/onboarding";
import type { Conversation, HealthStatus } from "../../types";

interface PublicAppShellProps {
  healthStatus: HealthStatus;
  sidebarCollapsed: boolean;
  onToggleSidebarCollapsed: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  desktop: boolean;
  mobileNavOpen: boolean;
  onMobileNavOpenChange: (open: boolean) => void;
  conversations: Conversation[];
  activeId: string | null;
  onSelectConversation: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onTogglePin: (id: string) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
  routeLabel: string;
}

function modeFromPath(pathname: string): SidebarMode {
  if (pathname.startsWith("/ask") || pathname === "/") return "ask";
  if (pathname.startsWith("/class-planner")) return "planner";
  if (pathname.startsWith("/about")) return "about";
  if (pathname.startsWith("/updates")) return "updates";
  if (pathname.startsWith("/status")) return "status";
  return "other";
}

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia(query).matches : false,
  );
  useEffect(() => {
    const media = window.matchMedia(query);
    const change = () => setMatches(media.matches);
    change();
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, [query]);
  return matches;
}

export function PublicAppShell(props: PublicAppShellProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const mode = modeFromPath(location.pathname);
  const isAskRoute =
    location.pathname === "/" || location.pathname.startsWith("/ask");
  const mdUp = useMediaQuery("(min-width: 768px)");
  const isPhone = !mdUp;
  const useDocumentScroll = isPhone && !isAskRoute;
  const [historyOpen, setHistoryOpen] = useState(false);
  const { active: tourActive, step: tourStep } = useTour();

  useEffect(() => {
    if (tourActive && tourStep?.id !== "conversations") setHistoryOpen(false);
  }, [tourActive, tourStep?.id]);

  useEffect(() => {
    document.documentElement.classList.toggle("mobile-document-scroll", useDocumentScroll);
    document.body.classList.toggle("mobile-document-scroll", useDocumentScroll);
    return () => {
      document.documentElement.classList.remove("mobile-document-scroll");
      document.body.classList.remove("mobile-document-scroll");
    };
  }, [useDocumentScroll]);

  const showRouteHeader = mdUp && !(props.desktop && isAskRoute);

  const handleNewChat = () => {
    props.onNewChat();
    if (location.pathname !== "/ask") navigate("/ask");
  };

  const shellClass = [
    "app-shell",
    "public-shell",
    "relative",
    "flex",
    useDocumentScroll ? "public-shell--document-scroll min-h-[100dvh]" : "h-[100dvh]",
    "text-text-primary",
    useDocumentScroll ? "overflow-visible" : "overflow-hidden",
    props.desktop && isAskRoute ? "public-shell--ask-desktop" : "",
    showRouteHeader && !props.desktop ? "public-shell--tablet" : "",
    showRouteHeader && props.desktop ? "public-shell--contextual" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={shellClass}>
      <div className="app-atmosphere" aria-hidden="true" />

      {props.desktop && (
        <UnifiedSidebar
          mode={mode}
          collapsed={
            props.sidebarCollapsed
            && !(tourActive && tourStep?.id === "conversations")
          }
          onToggleCollapsed={props.onToggleSidebarCollapsed}
          isMobile={false}
          mobileOpen={false}
          onMobileClose={() => undefined}
          conversations={props.conversations}
          activeId={props.activeId}
          onSelectConversation={(id) => {
            props.onSelectConversation(id);
            if (location.pathname !== "/ask") navigate("/ask");
          }}
          onRename={props.onRename}
          onTogglePin={props.onTogglePin}
          onDelete={props.onDelete}
          onNewChat={handleNewChat}
        />
      )}

      {!props.desktop && !isPhone && props.mobileNavOpen ? (
        <UnifiedSidebar
          mode={mode}
          collapsed={false}
          onToggleCollapsed={() => undefined}
          isMobile
          mobileOpen={props.mobileNavOpen}
          onMobileClose={() => props.onMobileNavOpenChange(false)}
          conversations={props.conversations}
          activeId={props.activeId}
          onSelectConversation={(id) => {
            props.onSelectConversation(id);
            if (location.pathname !== "/ask") navigate("/ask");
            props.onMobileNavOpenChange(false);
          }}
          onRename={props.onRename}
          onTogglePin={props.onTogglePin}
          onDelete={props.onDelete}
          onNewChat={handleNewChat}
        />
      ) : null}

      {isPhone ? (
        <MobileHistorySheet
          open={historyOpen}
          conversations={props.conversations}
          activeId={props.activeId}
          onClose={() => setHistoryOpen(false)}
          onSelectConversation={(id) => {
            props.onSelectConversation(id);
            if (location.pathname !== "/ask") navigate("/ask");
          }}
          onNewChat={handleNewChat}
          onRename={props.onRename}
          onDelete={props.onDelete}
        />
      ) : null}

      <div
        data-tour-scroll-root
        className={`public-shellMain relative z-[1] flex min-h-0 min-w-0 flex-1 flex-col pt-[var(--mobile-top-nav-offset)] ${
          isAskRoute ? "" : useDocumentScroll ? "overflow-visible" : "overflow-y-auto"
        }`}
      >
        <MobileTopNavigation onOpenHistory={() => setHistoryOpen(true)} />

        {showRouteHeader ? (
          <header
            className={`route-header sticky top-0 z-header flex items-center justify-between px-[var(--page-gutter)] ${
              props.desktop
                ? "route-header--contextual h-16"
                : "route-header--tablet h-[52px] md:h-14"
            }`}
          >
            <div className="flex min-w-0 items-center gap-3">
              {!props.desktop && (
                <button
                  type="button"
                  onClick={() => props.onMobileNavOpenChange(true)}
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-text-secondary hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
                  aria-label="Open navigation"
                >
                  <Menu size={20} strokeWidth={1.75} />
                </button>
              )}
              {!props.desktop ? (
                <BrandLogo
                  variant="mark"
                  decorative
                  eager
                  className="route-headerBrandMark"
                />
              ) : null}
              {props.desktop ? (
                <p className="truncate font-sans text-[15px] font-semibold text-text-primary md:text-[16px]">
                  {props.routeLabel}
                </p>
              ) : (
                <div className="min-w-0">
                  {isAskRoute ? (
                    <>
                      <p className="font-editorial text-xl font-semibold leading-none text-brand-900">
                        AskMcNeese
                      </p>
                      {props.routeLabel !== "AskMcNeese" ? (
                        <p className="mt-1 truncate font-sans text-sm font-semibold text-text-secondary">
                          {props.routeLabel}
                        </p>
                      ) : null}
                    </>
                  ) : (
                    <p className="truncate font-sans text-[15px] font-semibold text-text-primary">
                      {props.routeLabel}
                    </p>
                  )}
                </div>
              )}
            </div>
          </header>
        ) : null}

        {isAskRoute && props.routeLabel !== "AskMcNeese" ? (
          <h1 className="sr-only">{props.routeLabel}</h1>
        ) : null}

        {props.healthStatus === "offline" && (
          <div className="bg-danger-soft px-4 py-2 text-center text-xs text-error">
            AskMcNeese is offline right now. Check your connection and try again shortly.
          </div>
        )}

        <div className={`flex flex-1 flex-col ${isAskRoute ? "min-h-0 overflow-hidden" : useDocumentScroll ? "min-h-[100svh]" : ""}`}>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
