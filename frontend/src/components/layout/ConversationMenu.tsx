import { useEffect, useRef, useState, type ReactNode } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { MoreHorizontal, Pencil, Pin, Trash2 } from "lucide-react";
import type { Conversation } from "../../types";

interface ConversationMenuProps {
  conversation: Conversation;
  onRename: () => void;
  onTogglePin: () => void;
  onDelete: () => void;
}

export function ConversationMenu({
  conversation,
  onRename,
  onTogglePin,
  onDelete,
}: ConversationMenuProps) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.stopImmediatePropagation();
        setOpen(false);
      }
    };
    document.addEventListener("keydown", handler, true);
    return () => document.removeEventListener("keydown", handler, true);
  }, [open]);

  return (
    <div ref={menuRef} className="relative flex-shrink-0">
      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          setOpen((value) => !value);
        }}
        className="flex h-11 w-11 items-center justify-center rounded-lg text-text-muted opacity-100 transition hover:bg-surface hover:text-text-primary md:h-7 md:w-7 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100"
        aria-label={`Actions for ${conversation.title}`}
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <MoreHorizontal size={14} strokeWidth={1.75} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            role="menu"
            initial={{ opacity: 0, scale: 0.94, y: -4 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: -4 }}
            transition={{ duration: 0.12 }}
            className="absolute right-0 z-dropdown mt-1 w-36 rounded-xl border border-border bg-surface/90 p-1 shadow-card backdrop-blur-md"
          >
            <MenuButton
              onClick={() => {
                onRename();
                setOpen(false);
              }}
              label="Rename"
              icon={<Pencil size={13} strokeWidth={1.75} />}
            />
            <MenuButton
              onClick={() => {
                onTogglePin();
                setOpen(false);
              }}
              label={conversation.pinned ? "Unpin" : "Pin"}
              icon={<Pin size={13} strokeWidth={1.75} />}
            />
            <div className="my-1 border-t border-border" />
            <MenuButton
              onClick={() => {
                onDelete();
                setOpen(false);
              }}
              label="Delete"
              icon={<Trash2 size={13} strokeWidth={1.75} />}
              danger
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function MenuButton({
  label,
  onClick,
  icon,
  danger = false,
}: {
  label: string;
  onClick: () => void;
  icon: ReactNode;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      role="menuitem"
      className={`flex min-h-11 w-full items-center gap-2 rounded-lg px-2.5 text-left text-sm transition hover:bg-surface-hover md:min-h-0 md:py-1.5 ${
        danger ? "text-error" : "text-text-primary"
      }`}
      onClick={(event) => {
        event.stopPropagation();
        onClick();
      }}
    >
      <span className="flex-shrink-0 opacity-70">{icon}</span>
      {label}
    </button>
  );
}
