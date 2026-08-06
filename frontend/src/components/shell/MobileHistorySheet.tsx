import { useEffect } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Plus, X } from "lucide-react";
import type { Conversation } from "../../types";

interface MobileHistorySheetProps {
  open: boolean;
  conversations: Conversation[];
  activeId: string | null;
  onClose: () => void;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}

/** Translucent history card for phone — not the desktop sidebar. */
export function MobileHistorySheet({
  open,
  conversations,
  activeId,
  onClose,
  onSelectConversation,
  onNewChat,
}: MobileHistorySheetProps) {
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previous;
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (typeof document === "undefined") return null;

  return createPortal(
    <AnimatePresence>
      {open ? (
        <motion.div
          className="mobile-historyOverlay md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Chat history"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.16 }}
        >
          <button
            type="button"
            className="mobile-historyScrim"
            aria-label="Close history"
            onClick={onClose}
          />
          <motion.div
            className="mobile-historyCard"
            initial={reduceMotion ? false : { y: 40, opacity: 0.85 }}
            animate={{ y: 0, opacity: 1 }}
            exit={reduceMotion ? undefined : { y: 28, opacity: 0 }}
            transition={
              reduceMotion
                ? { duration: 0 }
                : { type: "spring", stiffness: 420, damping: 34 }
            }
          >
            <span className="mobile-historyHandle" aria-hidden="true" />
            <header className="mobile-historyHeader">
              <div>
                <p className="mobile-historyKicker">AskMcNeese</p>
                <h2>History</h2>
              </div>
              <button
                type="button"
                className="mobile-historyClose"
                aria-label="Close history"
                onClick={onClose}
              >
                <X size={19} strokeWidth={1.9} />
              </button>
            </header>

            <button
              type="button"
              className="mobile-historyNew"
              onClick={() => {
                onNewChat();
                onClose();
              }}
            >
              <Plus size={18} strokeWidth={2} aria-hidden />
              <span>New conversation</span>
            </button>

            <ul className="mobile-historyList">
              {conversations.length === 0 ? (
                <li className="mobile-historyEmpty">No conversations yet.</li>
              ) : (
                conversations.map((conversation) => {
                  const selected = conversation.id === activeId;
                  return (
                    <li key={conversation.id}>
                      <button
                        type="button"
                        className={`mobile-historyItem${selected ? " is-selected" : ""}`}
                        aria-current={selected ? "true" : undefined}
                        onClick={() => {
                          onSelectConversation(conversation.id);
                          onClose();
                        }}
                      >
                        <span className="mobile-historyTitle">{conversation.title}</span>
                        <span className="mobile-historyPreview">
                          {conversation.preview || "Empty"}
                        </span>
                      </button>
                    </li>
                  );
                })
              )}
            </ul>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>,
    document.body,
  );
}
