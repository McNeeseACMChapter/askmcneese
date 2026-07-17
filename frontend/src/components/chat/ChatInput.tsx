import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowUp,
  BookMarked,
  ChevronDown,
  Globe,
  History,
  Settings2,
  Square,
  WandSparkles,
} from "lucide-react";
import { AmbientSmokePulse } from "../motion/AmbientSmokePulse";
import { AppIcon } from "../ui/AppIcon";
import { IconButton } from "../ui/IconButton";
import type { ComposerState, SourceScope } from "../../types";

export const COMPOSER_PROMPT_LIMIT = 1000;
/** Max textarea height before internal scroll (px). */
export const COMPOSER_TEXTAREA_MAX_PX = 112;

const REFINE_CHIPS = [
  {
    id: "context",
    label: "Add student context",
    shortLabel: "Add context",
    text: "Context: I am a [current/prospective/international] student in [program or term].",
  },
  {
    id: "checklist",
    label: "Make it a checklist",
    shortLabel: "Checklist",
    text: "Please answer as a concise step-by-step checklist.",
  },
  {
    id: "deadlines",
    label: "Include deadlines",
    shortLabel: "Include deadlines",
    text: "Include relevant deadlines, dates, and eligibility requirements.",
  },
  {
    id: "contacts",
    label: "Include contacts",
    shortLabel: "Include contacts",
    text: "Include the correct McNeese office, official contact information, and source links.",
  },
] as const;

interface ChatInputProps {
  onSend: (text: string) => void;
  onStop: () => void;
  loading: boolean;
  offline: boolean;
  state: ComposerState;
  sourceScope: SourceScope;
  onSourceScopeChange: (scope: SourceScope) => void;
  webSearchAvailable?: boolean;
  onOpenHistory?: () => void;
  onOpenSettings?: () => void;
}

function isBusyState(state: ComposerState, loading: boolean): boolean {
  if (loading) return true;
  return state === "submitting" || state === "retrieving" || state === "generating";
}

function isOfflineState(state: ComposerState, offline: boolean): boolean {
  return offline || state === "offline";
}

/**
 * Docked glass input pill — AskMcNeese composer.
 * Preserves App.send → useAsk → POST /ask SSE contract.
 * Mobile: lightweight floating surface (no internal header chrome).
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
  onOpenHistory,
  onOpenSettings,
}: ChatInputProps) {
  const navigate = useNavigate();
  const [value, setValue] = useState("");
  const [smokeKey, setSmokeKey] = useState(0);
  const [showRefineChips, setShowRefineChips] = useState(false);
  const [stopping, setStopping] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const busy = isBusyState(state, loading);
  const isOffline = isOfflineState(state, offline);
  const overLimit = value.length > COMPOSER_PROMPT_LIMIT;
  const trimmed = value.trim();
  const canSubmit = Boolean(trimmed) && !busy && !isOffline && !overLimit;
  const showCharCount = value.length >= 800;
  const charCountUrgent = value.length >= 950;
  const sourceShortLabel =
    sourceScope === "adaptive" ? "Smart" : sourceScope === "knowledge" ? "Knowledge" : "Campus live";

  useEffect(() => {
    const element = textareaRef.current;
    if (!element) return;
    const mobile =
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 640px)").matches;
    const maxPx = mobile ? (value.trim() ? 96 : 38) : COMPOSER_TEXTAREA_MAX_PX;
    element.style.height = "auto";
    const next = Math.min(Math.max(element.scrollHeight, mobile && !value.trim() ? 38 : 0), maxPx);
    element.style.height = `${next || (mobile ? 38 : element.scrollHeight)}px`;
    element.style.overflowY = element.scrollHeight > maxPx ? "auto" : "hidden";
  }, [value]);

  useEffect(() => {
    if (!webSearchAvailable && (sourceScope === "web" || sourceScope === "adaptive")) {
      onSourceScopeChange("knowledge");
    }
  }, [webSearchAvailable, sourceScope, onSourceScopeChange]);

  useEffect(() => {
    if (!busy) setStopping(false);
  }, [busy]);

  useEffect(() => {
    if (busy) setShowRefineChips(false);
  }, [busy]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const text = value.trim();
    if (!text || busy || isOffline || text.length > COMPOSER_PROMPT_LIMIT || value.length > COMPOSER_PROMPT_LIMIT) {
      return;
    }
    setSmokeKey((k) => k + 1);
    setShowRefineChips(false);
    onSend(text);
    setValue("");
  };

  const keys = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      if (!canSubmit) return;
      event.currentTarget.form?.requestSubmit();
    }
  };

  const applyChip = (snippet: string) => {
    if (busy || isOffline) return;
    if (value.includes(snippet)) {
      textareaRef.current?.focus();
      setShowRefineChips(false);
      return;
    }
    const next = value.trim().length === 0 ? snippet : `${value.replace(/\s+$/, "")}\n${snippet}`;
    const clipped = next.length > COMPOSER_PROMPT_LIMIT ? next.slice(0, COMPOSER_PROMPT_LIMIT) : next;
    setValue(clipped);
    setShowRefineChips(false);
    requestAnimationFrame(() => textareaRef.current?.focus());
  };

  const handleOpenHistory = () => {
    onOpenHistory?.();
  };

  const handleOpenSettings = () => {
    if (onOpenSettings) {
      onOpenSettings();
      return;
    }
    navigate("/settings");
  };

  const handleStop = () => {
    if (stopping) return;
    setStopping(true);
    onStop();
  };

  const webUnavailableTitle = webSearchAvailable
    ? undefined
    : "Web search is currently unavailable from the AskMcNeese API.";

  const scopeLabel =
    sourceScope === "adaptive"
      ? "Smart"
      : sourceScope === "knowledge"
        ? "McNeese Knowledge"
        : "Campus live";
  const shellClass = [
    "composerGlass",
    "composerPill",
    isOffline ? "composerGlassOffline" : "",
    overLimit ? "composerGlassInvalid" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="composerShell composerDock shrink-0">
      <div className="composerFade" aria-hidden="true" />
      <AmbientSmokePulse
        trigger={smokeKey}
        className="composerSmokePulse bottom-10 left-1/2 -translate-x-1/2"
      />
      <form
        onSubmit={submit}
        className="composerDockInner relative z-10 mx-auto w-full"
        style={{
          width: "min(calc(100% - (2 * var(--page-gutter))), var(--composer-max-width))",
          maxWidth: "var(--composer-max-width)",
        }}
      >
        <div className={shellClass}>
          <div className="composerBar">
            <label className="composerSourceControl">
              <span className="composerSourceIcon" aria-hidden="true">
                {sourceScope === "knowledge" ? (
                  <AppIcon icon={BookMarked} size={14} />
                ) : (
                  <AppIcon icon={Globe} size={14} />
                )}
              </span>
              <span className="composerSourceLabel">Sources</span>
              <span className="composerSourceShort" aria-hidden="true">
                {sourceShortLabel}
              </span>
              <span className="composerSourceChevron" aria-hidden="true">
                <AppIcon icon={ChevronDown} size={13} />
              </span>
              <select
                value={sourceScope}
                onChange={(event) => onSourceScopeChange(event.target.value as SourceScope)}
                disabled={busy || isOffline}
                className="composerSourceSelect"
                aria-label="Source scope"
                title={webUnavailableTitle}
              >
                <option
                  value="adaptive"
                  disabled={!webSearchAvailable}
                  title={webUnavailableTitle}
                >
                  {webSearchAvailable ? "Smart" : "Smart (unavailable)"}
                </option>
                <option value="knowledge">McNeese Knowledge</option>
                <option value="web" disabled={!webSearchAvailable} title={webUnavailableTitle}>
                  {webSearchAvailable ? "Campus live" : "Campus live (unavailable)"}
                </option>
              </select>
              <span className="sr-only">{scopeLabel}</span>
            </label>

            <div className="composerPromptArea">
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(event) => setValue(event.target.value)}
                onKeyDown={keys}
                rows={1}
                maxLength={COMPOSER_PROMPT_LIMIT}
                disabled={isOffline}
                placeholder={isOffline ? "AskMcNeese is offline" : "Ask about McNeese…"}
                aria-label="AskMcNeese question"
                aria-describedby="composer-caution composer-shortcuts composer-char-status"
                aria-invalid={overLimit || undefined}
                title="Press Enter to send. Press Shift+Enter for a new line."
                className="composerInput composerTextarea"
              />
            </div>

            <div className="composerToolbarEnd">
              <IconButton
                type="button"
                label="Refine question"
                tooltip="Show ways to refine your question"
                size="sm"
                aria-pressed={showRefineChips}
                disabled={busy || isOffline}
                onClick={() => setShowRefineChips((open) => !open)}
                className="composerRefineButton"
              >
                <AppIcon icon={WandSparkles} size={15} className="text-brand-700" />
              </IconButton>

              {showCharCount && (
                <span
                  id="composer-char-status"
                  className={`composerCharacterCount ${charCountUrgent ? "composerCharacterCountUrgent" : ""}`}
                  role={overLimit || charCountUrgent ? "status" : undefined}
                  aria-live={charCountUrgent ? "polite" : undefined}
                >
                  {value.length} / {COMPOSER_PROMPT_LIMIT}
                </span>
              )}
              {!showCharCount && <span id="composer-char-status" className="sr-only" />}

              {busy ? (
                <button
                  type="button"
                  onClick={handleStop}
                  disabled={stopping}
                  className="composerPrimaryAction composerPrimaryActionStop"
                  aria-label="Stop response"
                  title="Stop generating response"
                >
                  <AppIcon icon={Square} size={13} className="text-white" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!canSubmit}
                  title="Press Enter to send · Shift+Enter for a new line"
                  className="composerPrimaryAction"
                  aria-label="Send question"
                >
                  <AppIcon icon={ArrowUp} size={15} className="text-white" />
                </button>
              )}
            </div>
          </div>

          {showRefineChips && !busy && (
            <div className="composerSuggestions" role="group" aria-label="Question refinements">
              {REFINE_CHIPS.map((chip) => (
                <button
                  key={chip.id}
                  type="button"
                  className="composerSuggestionChip"
                  disabled={isOffline}
                  aria-label={chip.label}
                  onClick={() => applyChip(chip.text)}
                >
                  <span className="composerChipLabelFull" aria-hidden="true">
                    {chip.label}
                  </span>
                  <span className="composerChipLabelShort" aria-hidden="true">
                    {chip.shortLabel}
                  </span>
                </button>
              ))}
            </div>
          )}

          <div className="composerUtilityActions" data-testid="composer-utilities">
            <IconButton
              type="button"
              label="Open conversation history"
              tooltip="Conversation history"
              size="sm"
              onClick={handleOpenHistory}
              className="composerUtilityButton"
            >
              <AppIcon icon={History} size={16} />
            </IconButton>
            <IconButton
              type="button"
              label="Open settings"
              tooltip="Settings"
              size="sm"
              onClick={handleOpenSettings}
              className="composerUtilityButton"
            >
              <AppIcon icon={Settings2} size={16} />
            </IconButton>
          </div>
        </div>

        {overLimit && (
          <p className="composerValidationError" role="alert">
            Questions are limited to {COMPOSER_PROMPT_LIMIT} characters.
          </p>
        )}

        <p
          id="composer-caution"
          className="composerCaution mt-2 px-2 text-center font-sans text-[12px] leading-snug text-text-muted"
        >
          <span className="hidden sm:inline">
            AskMcNeese can make mistakes. Verify deadlines, requirements, and policies in the cited
            McNeese source.
          </span>
          <span className="sm:hidden">Verify important details in the cited McNeese source.</span>
        </p>
        <p id="composer-shortcuts" className="sr-only">
          Press Enter to send. Press Shift plus Enter for a new line.
        </p>
      </form>
    </div>
  );
}
