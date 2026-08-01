import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import {
  ArrowUp,
  BookOpenCheck,
  Check,
  ChevronDown,
  Globe2,
  Sparkles,
  Square,
  type LucideIcon,
} from "lucide-react";
import { AppIcon } from "../ui/AppIcon";
import type { ComposerState, SourceScope } from "../../types";

/**
 * Keep synchronized with backend AskRequest.question max_length.
 * Raised from 1,000 so students can paste course/policy/degree-audit context.
 */
export const COMPOSER_PROMPT_LIMIT = 4000;
export const COMPOSER_TEXTAREA_MAX_PX = 160;

interface ChatInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  loading: boolean;
  offline: boolean;
  state: ComposerState;
  sourceScope: SourceScope;
  onSourceScopeChange: (scope: SourceScope) => void;
  webSearchAvailable?: boolean;
}

function isBusyState(state: ComposerState, loading: boolean): boolean {
  return (
    loading ||
    state === "submitting" ||
    state === "retrieving" ||
    state === "generating"
  );
}

function isOfflineState(state: ComposerState, offline: boolean): boolean {
  return offline || state === "offline";
}

interface ScopeOption {
  value: SourceScope;
  label: string;
  description: string;
  icon: LucideIcon;
}

/**
 * Adaptive is first and default: the system picks McNeese, web, or both
 * from the query (flowchart Tool Selector). The other two are manual locks.
 */
export const SCOPE_OPTIONS: ScopeOption[] = [
  {
    value: "adaptive",
    label: "Adaptive",
    description: "System decides McNeese, web, or both",
    icon: Sparkles,
  },
  {
    value: "knowledge",
    label: "McNeese only",
    description: "Official campus pages — no outside web",
    icon: BookOpenCheck,
  },
  {
    value: "web",
    label: "Include the web",
    description: "Campus sources plus live web search",
    icon: Globe2,
  },
];

function getScopeOption(scope: SourceScope): ScopeOption {
  return SCOPE_OPTIONS.find((option) => option.value === scope) ?? SCOPE_OPTIONS[0];
}

function getSourceLabel(scope: SourceScope): string {
  if (scope === "knowledge") return "McNeese only";
  if (scope === "web") return "Include the web";
  return "Adaptive";
}

/**
 * Minimal AskMcNeese composer.
 * Write → choose source mode quietly → send/stop.
 * History, settings, refine chips, smoke, and caution live elsewhere.
 */
export function ChatInput({
  onSend,
  onStop,
  loading,
  offline,
  state,
  sourceScope,
  onSourceScopeChange,
  webSearchAvailable = true,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const [stopping, setStopping] = useState(false);
  const [scopeMenuOpen, setScopeMenuOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scopeControlRef = useRef<HTMLDivElement>(null);
  const scopeTriggerRef = useRef<HTMLButtonElement>(null);
  const scopeOptionRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const busy = isBusyState(state, loading);
  const isOffline = isOfflineState(state, offline);
  const trimmed = value.trim();
  const canSubmit = Boolean(trimmed) && !busy && !isOffline;
  const showCharCount = value.length >= COMPOSER_PROMPT_LIMIT * 0.85;
  const charCountUrgent = value.length >= COMPOSER_PROMPT_LIMIT * 0.95;

  const sourceLabel = getSourceLabel(sourceScope);
  const SourceIcon = getScopeOption(sourceScope).icon;
  const scopeDisabled = busy || isOffline || !webSearchAvailable;

  const closeScopeMenu = useCallback((refocus = false) => {
    setScopeMenuOpen(false);
    if (refocus) scopeTriggerRef.current?.focus();
  }, []);

  useEffect(() => {
    if (!scopeMenuOpen) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!scopeControlRef.current?.contains(event.target as Node)) {
        closeScopeMenu();
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [scopeMenuOpen, closeScopeMenu]);

  useEffect(() => {
    if (scopeMenuOpen) {
      const selected = SCOPE_OPTIONS.findIndex((o) => o.value === sourceScope);
      scopeOptionRefs.current[Math.max(selected, 0)]?.focus();
    }
  }, [scopeMenuOpen, sourceScope]);

  const selectScope = (scope: SourceScope) => {
    onSourceScopeChange(scope);
    closeScopeMenu(true);
  };

  const handleScopeMenuKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      closeScopeMenu(true);
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const focused = scopeOptionRefs.current.findIndex(
        (el) => el === document.activeElement,
      );
      const delta = event.key === "ArrowDown" ? 1 : -1;
      const next =
        (focused + delta + SCOPE_OPTIONS.length) % SCOPE_OPTIONS.length;
      scopeOptionRefs.current[next]?.focus();
    }
  };

  useEffect(() => {
    const element = textareaRef.current;
    if (!element) return;

    const isMobile =
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 640px)").matches;
    const maxHeight = isMobile ? 120 : COMPOSER_TEXTAREA_MAX_PX;
    const minHeight = isMobile ? 36 : 42;

    element.style.height = "0px";
    const nextHeight = Math.min(
      Math.max(element.scrollHeight, minHeight),
      maxHeight,
    );

    element.style.height = `${nextHeight}px`;
    element.style.overflowY = element.scrollHeight > maxHeight ? "auto" : "hidden";
  }, [value]);

  useEffect(() => {
    if (!webSearchAvailable && sourceScope !== "knowledge") {
      onSourceScopeChange("knowledge");
    }
  }, [webSearchAvailable, sourceScope, onSourceScopeChange]);

  useEffect(() => {
    if (!busy) setStopping(false);
  }, [busy]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!canSubmit) return;

    onSend(trimmed);
    setValue("");

    requestAnimationFrame(() => {
      if (textareaRef.current) {
        textareaRef.current.style.height = "42px";
      }
    });
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      if (canSubmit) event.currentTarget.form?.requestSubmit();
    }
  };

  const handleStop = () => {
    if (stopping) return;
    setStopping(true);
    onStop();
  };

  const frameClassName = [
    "composerFrame",
    isOffline ? "composerFrame--offline" : "",
    busy ? "composerFrame--busy" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="composerDock shrink-0">
      <form
        onSubmit={submit}
        className="composerDockInner mx-auto w-full"
        aria-label="Ask McNeese"
      >
        <div className={frameClassName} data-state={state}>
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            maxLength={COMPOSER_PROMPT_LIMIT}
            disabled={isOffline}
            placeholder={isOffline ? "AskMcNeese is offline" : "What do you need to find?"}
            aria-label="AskMcNeese question"
            aria-describedby="composer-shortcuts composer-char-status"
            title="Press Enter to send. Press Shift+Enter for a new line."
            className="composerTextarea"
          />

          <div className="composerFooter">
            <div
              ref={scopeControlRef}
              className="composerScopeControl"
              data-scope={sourceScope}
              data-disabled={scopeDisabled || undefined}
              onKeyDown={handleScopeMenuKeyDown}
            >
              <button
                ref={scopeTriggerRef}
                type="button"
                className="composerScopeTrigger"
                aria-label="Choose source mode"
                aria-haspopup="listbox"
                aria-expanded={scopeMenuOpen}
                data-value={sourceScope}
                disabled={scopeDisabled}
                onClick={() => setScopeMenuOpen((open) => !open)}
                title={
                  webSearchAvailable
                    ? `Source mode: ${sourceLabel}`
                    : "Live web search is unavailable; using McNeese sources."
                }
              >
                <span className="composerScopeIcon" aria-hidden="true">
                  <AppIcon icon={SourceIcon} size={15} />
                </span>
                <span className="composerScopeText">{sourceLabel}</span>
                <span
                  className="composerScopeChevron"
                  data-open={scopeMenuOpen || undefined}
                  aria-hidden="true"
                >
                  <AppIcon icon={ChevronDown} size={13} />
                </span>
              </button>

              {scopeMenuOpen && (
                <div
                  className="composerScopeMenu"
                  role="listbox"
                  aria-label="Source modes"
                >
                  <p className="composerScopeMenuHeading">How should AskMcNeese look?</p>
                  {SCOPE_OPTIONS.map((option, index) => {
                    const selected = option.value === sourceScope;
                    const recommended = option.value === "adaptive";
                    return (
                      <button
                        key={option.value}
                        ref={(el) => {
                          scopeOptionRefs.current[index] = el;
                        }}
                        type="button"
                        role="option"
                        aria-selected={selected}
                        className="composerScopeOption"
                        data-selected={selected || undefined}
                        data-recommended={recommended || undefined}
                        onClick={() => selectScope(option.value)}
                      >
                        <span className="composerScopeOptionIcon" aria-hidden="true">
                          <AppIcon icon={option.icon} size={16} />
                        </span>
                        <span className="composerScopeOptionBody">
                          <span className="composerScopeOptionLabelRow">
                            <span className="composerScopeOptionLabel">
                              {option.label}
                            </span>
                            {recommended && (
                              <span className="composerScopeOptionBadge">Default</span>
                            )}
                          </span>
                          <span className="composerScopeOptionDescription">
                            {option.description}
                          </span>
                        </span>
                        <span
                          className="composerScopeOptionCheck"
                          aria-hidden="true"
                        >
                          {selected && <AppIcon icon={Check} size={15} />}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="composerActions">
              <span
                id="composer-char-status"
                className={`composerCharacterCount ${
                  showCharCount ? "composerCharacterCount--visible" : ""
                } ${charCountUrgent ? "composerCharacterCount--urgent" : ""}`}
                aria-live={charCountUrgent ? "polite" : undefined}
              >
                {showCharCount
                  ? `${value.length.toLocaleString()} / ${COMPOSER_PROMPT_LIMIT.toLocaleString()}`
                  : ""}
              </span>

              {busy ? (
                <button
                  type="button"
                  onClick={handleStop}
                  disabled={stopping}
                  className="composerPrimaryAction composerPrimaryAction--stop"
                  aria-label={stopping ? "Stopping response" : "Stop response"}
                  title="Stop response"
                >
                  <AppIcon icon={Square} size={12} />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="composerPrimaryAction"
                  aria-label="Send question"
                  title="Send question"
                >
                  <AppIcon icon={ArrowUp} size={16} />
                </button>
              )}
            </div>
          </div>
        </div>

        <p id="composer-shortcuts" className="sr-only">
          Press Enter to send. Press Shift plus Enter for a new line.
        </p>
      </form>
    </div>
  );
}
