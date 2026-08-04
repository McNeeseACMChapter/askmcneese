import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";
import { IconButton } from "./IconButton";

interface DrawerProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  variant?: "sheet" | "side";
}

export function Drawer({ open, title, onClose, children, variant = "sheet" }: DrawerProps) {
  const reduce = useReducedMotion();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open ? (
        <div className="acm-more-sheet" role="dialog" aria-modal="true" aria-label={title}>
          <button
            type="button"
            className="acm-more-sheet__backdrop"
            aria-label="Close"
            onClick={onClose}
          />
          <motion.div
            className={"acm-more-sheet__panel surface-interactive" + (variant === "side" ? " acm-drawer--side" : "")}
            initial={reduce ? false : variant === "side" ? { x: "100%" } : { y: "100%" }}
            animate={variant === "side" ? { x: 0 } : { y: 0 }}
            exit={reduce ? undefined : variant === "side" ? { x: "100%" } : { y: "100%" }}
            transition={
              reduce
                ? { duration: 0 }
                : { duration: 0.28, ease: [0.2, 0, 0, 1] }
            }
          >
            <div className="mb-3 flex items-center justify-between">
              <h2>{title}</h2>
              <IconButton label="Close drawer" onClick={onClose}>
                <X size={18} strokeWidth={1.75} aria-hidden />
              </IconButton>
            </div>
            {children}
          </motion.div>
        </div>
      ) : null}
    </AnimatePresence>
  );
}
