import { useCallback, useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Check, MoreHorizontal, Pencil, Plus, Trash2, X } from "lucide-react";
import type { Conversation } from "../../types";

interface MobileHistorySheetProps {
  open: boolean;
  conversations: Conversation[];
  activeId: string | null;
  onClose: () => void;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}

interface SwipeSession {
  id: string;
  startX: number;
  startY: number;
  startedRevealed: boolean;
  moved: boolean;
}

const ACTION_RAIL_WIDTH = 128;
const REVEAL_THRESHOLD = 48;
const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value));

/** Phone-first conversation history with explicit and swipe-revealed actions. */
export function MobileHistorySheet({
  open,
  conversations,
  activeId,
  onClose,
  onSelectConversation,
  onNewChat,
  onRename,
  onDelete,
}: MobileHistorySheetProps) {
  const reduceMotion = useReducedMotion();
  const cardRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const swipeSessionRef = useRef<SwipeSession | null>(null);
  const suppressSelectionRef = useRef(false);
  const [revealedId, setRevealedId] = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState(0);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [deleteCandidate, setDeleteCandidate] = useState<Conversation | null>(null);
  const revealedIdRef = useRef(revealedId);
  const editingIdRef = useRef(editingId);
  const deleteCandidateRef = useRef(deleteCandidate);
  revealedIdRef.current = revealedId;
  editingIdRef.current = editingId;
  deleteCandidateRef.current = deleteCandidate;

  const resetTransientState = useCallback(() => {
    setRevealedId(null);
    setDraggingId(null);
    setDragOffset(0);
    setEditingId(null);
    setDraftTitle("");
    setDeleteCandidate(null);
    swipeSessionRef.current = null;
  }, []);

  useEffect(() => {
    if (!open) {
      resetTransientState();
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (deleteCandidateRef.current) setDeleteCandidate(null);
      else if (editingIdRef.current) setEditingId(null);
      else if (revealedIdRef.current) setRevealedId(null);
      else onClose();
    };

    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [onClose, open, resetTransientState]);

  useEffect(() => {
    if (revealedId && !conversations.some(({ id }) => id === revealedId)) {
      setRevealedId(null);
    }
  }, [conversations, revealedId]);

  const startRename = (conversation: Conversation) => {
    setDeleteCandidate(null);
    setRevealedId(null);
    setEditingId(conversation.id);
    setDraftTitle(conversation.title);
  };

  const saveRename = (conversation: Conversation) => {
    const nextTitle = draftTitle.trim();
    if (nextTitle && nextTitle !== conversation.title) {
      onRename(conversation.id, nextTitle);
    }
    setEditingId(null);
    setDraftTitle("");
  };

  const handlePointerDown = (
    event: ReactPointerEvent<HTMLDivElement>,
    conversationId: string,
  ) => {
    if (editingId || event.pointerType === "mouse") return;
    swipeSessionRef.current = {
      id: conversationId,
      startX: event.clientX,
      startY: event.clientY,
      startedRevealed: revealedId === conversationId,
      moved: false,
    };
    setDraggingId(conversationId);
    setDragOffset(revealedId === conversationId ? -ACTION_RAIL_WIDTH : 0);
    event.currentTarget.setPointerCapture?.(event.pointerId);
  };

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const session = swipeSessionRef.current;
    if (!session || session.id !== draggingId) return;
    const deltaX = event.clientX - session.startX;
    const deltaY = event.clientY - session.startY;
    if (Math.abs(deltaX) > 8 && Math.abs(deltaX) > Math.abs(deltaY)) {
      session.moved = true;
      event.preventDefault();
      const base = session.startedRevealed ? -ACTION_RAIL_WIDTH : 0;
      setDragOffset(clamp(base + deltaX, -ACTION_RAIL_WIDTH, 0));
    }
  };

  const handlePointerEnd = (event: ReactPointerEvent<HTMLDivElement>) => {
    const session = swipeSessionRef.current;
    if (!session || session.id !== draggingId) return;
    const deltaX = event.clientX - session.startX;
    const base = session.startedRevealed ? -ACTION_RAIL_WIDTH : 0;
    const finalOffset = clamp(base + deltaX, -ACTION_RAIL_WIDTH, 0);
    setRevealedId(finalOffset <= -REVEAL_THRESHOLD ? session.id : null);
    setDraggingId(null);
    setDragOffset(0);
    swipeSessionRef.current = null;
    if (session.moved) {
      suppressSelectionRef.current = true;
      window.setTimeout(() => {
        suppressSelectionRef.current = false;
      }, 0);
    }
  };

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
          <button type="button" className="mobile-historyScrim" aria-label="Close history" onClick={onClose} />
          <motion.div
            ref={cardRef}
            className="mobile-historyCard"
            initial={reduceMotion ? false : { y: 40, opacity: 0.85 }}
            animate={{ y: 0, opacity: 1 }}
            exit={reduceMotion ? undefined : { y: 28, opacity: 0 }}
            transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 420, damping: 34 }}
          >
            <header className="mobile-historyHeader">
              <div>
                <h2>History</h2>
                <p>Continue a conversation or manage it.</p>
              </div>
              <button ref={closeButtonRef} type="button" className="mobile-historyClose" aria-label="Close history" onClick={onClose}>
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
                  const revealed = revealedId === conversation.id;
                  const editing = editingId === conversation.id;
                  const offset = draggingId === conversation.id ? dragOffset : revealed ? -ACTION_RAIL_WIDTH : 0;
                  return (
                    <li key={conversation.id} className="mobile-historyRow"
                      data-revealed={revealed ? "true" : "false"}
                      data-dragging={draggingId === conversation.id ? "true" : "false"}>
                      <div
                        className="mobile-historyActions"
                        aria-label={`Actions for ${conversation.title}`}
                        aria-hidden={!revealed}
                      >
                        <button
                          type="button"
                          className="mobile-historyAction mobile-historyAction--rename"
                          aria-label={`Rename ${conversation.title}`}
                          tabIndex={revealed ? 0 : -1}
                          onClick={() => startRename(conversation)}
                        >
                          <Pencil size={17} strokeWidth={1.9} aria-hidden="true" />
                          <span>Rename</span>
                        </button>
                        <button
                          type="button"
                          className="mobile-historyAction mobile-historyAction--delete"
                          aria-label={`Delete ${conversation.title}`}
                          tabIndex={revealed ? 0 : -1}
                          onClick={() => {
                            setRevealedId(null);
                            setDeleteCandidate(conversation);
                          }}
                        >
                          <Trash2 size={17} strokeWidth={1.9} aria-hidden="true" />
                          <span>Delete</span>
                        </button>
                      </div>

                      <div
                        className={`mobile-historyItemSurface${selected ? " is-selected" : ""}${draggingId === conversation.id ? " is-dragging" : ""}`}
                        style={{ transform: `translate3d(${offset}px, 0, 0)` }}
                        onPointerDown={(event) => handlePointerDown(event, conversation.id)}
                        onPointerMove={handlePointerMove}
                        onPointerUp={handlePointerEnd}
                        onPointerCancel={handlePointerEnd}
                      >
                        {editing ? (
                          <form
                            className="mobile-historyRenameForm"
                            onSubmit={(event) => {
                              event.preventDefault();
                              saveRename(conversation);
                            }}
                          >
                            <label className="sr-only" htmlFor={`mobile-history-rename-${conversation.id}`}>Conversation title</label>
                            <input
                              id={`mobile-history-rename-${conversation.id}`}
                              value={draftTitle}
                              onChange={(event) => setDraftTitle(event.target.value)}
                              autoFocus
                              maxLength={100}
                            />
                            <button type="submit" aria-label="Save conversation title">
                              <Check size={17} strokeWidth={2} aria-hidden="true" />
                            </button>
                            <button
                              type="button"
                              aria-label="Cancel rename"
                              onClick={() => {
                                setEditingId(null);
                                setDraftTitle("");
                              }}
                            >
                              <X size={17} strokeWidth={2} aria-hidden="true" />
                            </button>
                          </form>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="mobile-historyItemMain"
                              aria-current={selected ? "true" : undefined}
                              onClick={() => {
                                if (suppressSelectionRef.current) return;
                                if (revealed) {
                                  setRevealedId(null);
                                  return;
                                }
                                onSelectConversation(conversation.id);
                                onClose();
                              }}
                            >
                              <span className="mobile-historyTitle">{conversation.title}</span>
                              <span className="mobile-historyPreview">{conversation.preview || "Empty"}</span>
                            </button>
                            <button
                              type="button"
                              className="mobile-historyOptions"
                              aria-label={`Options for ${conversation.title}`}
                              aria-expanded={revealed}
                              onClick={() => setRevealedId(revealed ? null : conversation.id)}
                            >
                              <MoreHorizontal size={19} strokeWidth={1.9} aria-hidden="true" />
                            </button>
                          </>
                        )}
                      </div>
                    </li>
                  );
                })
              )}
            </ul>

            <AnimatePresence>
              {deleteCandidate ? (
                <motion.div
                  className="mobile-historyConfirm"
                  role="alertdialog"
                  aria-modal="true"
                  aria-labelledby="mobile-history-confirm-title"
                  aria-describedby="mobile-history-confirm-copy"
                  initial={reduceMotion ? false : { opacity: 0, y: 10, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={reduceMotion ? undefined : { opacity: 0, y: 8, scale: 0.98 }}
                  transition={{ duration: reduceMotion ? 0 : 0.16 }}
                >
                  <div className="mobile-historyConfirmPanel">
                    <span className="mobile-historyConfirmIcon" aria-hidden="true">
                      <Trash2 size={20} strokeWidth={1.9} />
                    </span>
                    <h3 id="mobile-history-confirm-title">Delete conversation?</h3>
                    <p id="mobile-history-confirm-copy">“{deleteCandidate.title}” will be permanently removed.</p>
                    <div className="mobile-historyConfirmActions">
                      <button type="button" autoFocus onClick={() => setDeleteCandidate(null)}>Keep it</button>
                      <button
                        type="button"
                        className="is-danger"
                        onClick={() => {
                          onDelete(deleteCandidate.id);
                          setDeleteCandidate(null);
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>,
    document.body,
  );
}
