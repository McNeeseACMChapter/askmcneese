import * as Toast from "@radix-ui/react-toast";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

export type ToastTone = "success" | "failure" | "warning" | "info";

export interface ToastItem {
  id: string;
  title: string;
  description?: string;
  tone: ToastTone;
  undo?: () => void;
}

interface ToastContextValue {
  push: (toast: Omit<ToastItem, "id">) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const toneBorder: Record<ToastTone, string> = {
  success: "var(--success)",
  failure: "var(--danger)",
  warning: "var(--warning)",
  info: "var(--brand-700)",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const reduce = useReducedMotion();

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((toast: Omit<ToastItem, "id">) => {
    const id = `t-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    setItems((prev) => [...prev, { ...toast, id }]);
  }, []);

  const value = useMemo(() => ({ push, dismiss }), [push, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      <Toast.Provider swipeDirection="right" duration={4200}>
        {children}
        <AnimatePresence>
          {items.map((item) => (
            <Toast.Root
              key={item.id}
              open
              onOpenChange={(open) => {
                if (!open) dismiss(item.id);
              }}
              asChild
            >
              <motion.div
                className="acm-toast"
                style={{ borderLeftColor: toneBorder[item.tone] }}
                initial={reduce ? false : { opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reduce ? undefined : { opacity: 0, y: 8 }}
                transition={{ duration: reduce ? 0 : 0.18 }}
              >
                <div className="acm-toast__body">
                  <Toast.Title className="acm-toast__title">{item.title}</Toast.Title>
                  {item.description ? (
                    <Toast.Description className="acm-toast__desc">
                      {item.description}
                    </Toast.Description>
                  ) : null}
                </div>
                {item.undo ? (
                  <button
                    type="button"
                    className="acm-toast__undo"
                    onClick={() => {
                      item.undo?.();
                      dismiss(item.id);
                    }}
                  >
                    Undo
                  </button>
                ) : null}
                <Toast.Close className="acm-toast__close" aria-label="Dismiss">
                  ×
                </Toast.Close>
              </motion.div>
            </Toast.Root>
          ))}
        </AnimatePresence>
        <Toast.Viewport className="acm-toast-viewport" />
      </Toast.Provider>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast requires ToastProvider");
  return ctx;
}
