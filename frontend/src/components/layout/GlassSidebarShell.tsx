import { useEffect, useRef, type ReactNode } from "react";
import { motion } from "framer-motion";
import { PanelLeftClose, X } from "lucide-react";

export interface GlassSidebarShellProps {
  title: string;
  collapsed: boolean;
  isMobile: boolean;
  onToggleCollapsed: () => void;
  onClose: () => void;
  headerAction?: ReactNode;
  children: ReactNode;
  /** Accessible name for the aside */
  ariaLabel?: string;
  collapseLabel?: { expand: string; collapse: string };
}

const spring = {
  type: "spring" as const,
  stiffness: 340,
  damping: 32,
  mass: 0.9,
};

export function GlassSidebarShell({
  title,
  collapsed,
  isMobile,
  onToggleCollapsed,
  onClose,
  headerAction,
  children,
  ariaLabel,
  collapseLabel = { expand: "Expand sidebar", collapse: "Collapse sidebar" },
}: GlassSidebarShellProps) {
  const asideRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  useEffect(() => {
    if (!isMobile) return;
    const root = asideRef.current;
    if (!root) return;

    const selector =
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const focusables = () => Array.from(root.querySelectorAll<HTMLElement>(selector));

    const first = focusables()[0];
    first?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const items = focusables();
      if (!items.length) return;
      const firstEl = items[0];
      const lastEl = items[items.length - 1];
      if (event.shiftKey && document.activeElement === firstEl) {
        event.preventDefault();
        lastEl.focus();
      } else if (!event.shiftKey && document.activeElement === lastEl) {
        event.preventDefault();
        firstEl.focus();
      }
    };

    root.addEventListener("keydown", onKeyDown);
    return () => root.removeEventListener("keydown", onKeyDown);
  }, [isMobile]);

  const widthClass = isMobile
    ? "w-[min(280px,85vw)]"
    : collapsed
      ? "w-sidebar-collapsed"
      : "w-sidebar";

  const header = (
    <div className="flex h-header items-center justify-between gap-1 border-b border-border px-3">
      {!collapsed && (
        <strong className="min-w-0 truncate font-editorial text-lg">{title}</strong>
      )}
      <div className={`flex items-center gap-0.5 ${collapsed ? "w-full justify-center" : "ml-auto"}`}>
        {!isMobile && (
          <button
            type="button"
            onClick={onToggleCollapsed}
            className="flex h-11 w-11 items-center justify-center rounded-xl text-text-secondary transition hover:bg-surface-hover"
            title={collapsed ? collapseLabel.expand : collapseLabel.collapse}
            aria-label={collapsed ? collapseLabel.expand : collapseLabel.collapse}
          >
            <PanelLeftClose
              size={20}
              strokeWidth={1.75}
              className={collapsed ? "rotate-180" : undefined}
            />
          </button>
        )}
        <button
          type="button"
          onClick={onClose}
          className="flex h-11 w-11 items-center justify-center rounded-xl text-text-secondary transition hover:bg-surface-hover"
          aria-label={`Close ${title.toLowerCase()}`}
          title={`Close ${title.toLowerCase()}`}
        >
          <X size={18} strokeWidth={1.75} />
        </button>
      </div>
    </div>
  );

  const body = (
    <>
      {header}
      {headerAction}
      <div className="min-h-0 flex-1 overflow-y-auto scrollbar-thin">{children}</div>
    </>
  );

  if (!isMobile) {
    return (
      <motion.aside
        ref={asideRef}
        role="complementary"
        aria-label={ariaLabel ?? title}
        initial={{ x: 0, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 0, opacity: 0 }}
        transition={spring}
        className={`glass-navigation flex h-full flex-col border-r-0 ${widthClass}`}
      >
        {body}
      </motion.aside>
    );
  }

  return (
    <motion.div
      className="fixed inset-0 z-overlay"
      initial="closed"
      animate="open"
      exit="closed"
      variants={{
        open: { opacity: 1 },
        closed: { opacity: 0 },
      }}
      transition={{ duration: 0.18 }}
    >
      <motion.div
        className="absolute inset-0 bg-black/20 backdrop-blur-[4px]"
        onClick={onClose}
        aria-label={`Close ${title.toLowerCase()}`}
        role="button"
        tabIndex={-1}
      />
      <motion.aside
        ref={asideRef}
        role="complementary"
        aria-label={ariaLabel ?? title}
        variants={{
          open: { x: 0 },
          closed: { x: "-100%" },
        }}
        transition={spring}
        drag="x"
        dragConstraints={{ left: -320, right: 0 }}
        dragElastic={0.08}
        onDragEnd={(_, info) => {
          if (info.offset.x < -72 || info.velocity.x < -400) onClose();
        }}
        className={`glass-navigation absolute inset-y-0 left-0 flex h-full flex-col border-r-0 shadow-float ${widthClass}`}
      >
        {body}
      </motion.aside>
    </motion.div>
  );
}
