import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  History,
  Info,
  MessageCircleQuestion,
  MessageSquareText,
  MoreHorizontal,
  Newspaper,
  Settings2,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

/**
 * Phone primary (4): Ask · About · History · More
 * Updates / Status live under More (not competing for thumb/eye on Ask).
 * About is a single page (team + what it does) — no About sub-routes in More.
 */
const primaryItems: readonly {
  to: string;
  label: string;
  icon: LucideIcon;
  end: boolean;
}[] = [
  { to: "/ask", label: "Ask", icon: MessageCircleQuestion, end: true },
  { to: "/about", label: "About", icon: Info, end: false },
] as const;

const moreItems = [
  { to: "/updates", label: "Updates", icon: Newspaper },
  { to: "/status", label: "Status", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings2 },
  { to: "/feedback", label: "Feedback", icon: MessageSquareText },
  { to: "/acm/login", label: "ACM Portal", icon: null },
] as const;

interface MobileTopNavigationProps {
  onOpenHistory: () => void;
}

function pathIsActive(pathname: string, to: string, end: boolean): boolean {
  if (to === "/ask") {
    return pathname === "/ask" || pathname === "/";
  }
  if (to === "/about") {
    return pathname === "/about" || pathname.startsWith("/about/");
  }
  if (end) return pathname === to;
  return pathname === to || pathname.startsWith(`${to}/`);
}

export function MobileTopNavigation({ onOpenHistory }: MobileTopNavigationProps) {
  const location = useLocation();
  const reduceMotion = useReducedMotion();
  const [moreOpen, setMoreOpen] = useState(false);

  useEffect(() => {
    setMoreOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!moreOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMoreOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [moreOpen]);

  const moreRouteActive = moreItems.some((item) =>
    pathIsActive(location.pathname, item.to, true),
  );

  const spring = reduceMotion
    ? { duration: 0 }
    : { type: "spring" as const, stiffness: 420, damping: 34 };

  return (
    <>
      <motion.nav
        className="mobile-top-nav md:hidden"
        aria-label="Primary mobile navigation"
        initial={reduceMotion ? false : { y: -16, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 380, damping: 32 }}
      >
        <div className="mobile-top-nav__capsule" role="presentation">
          {primaryItems.map(({ to, label, icon: Icon, end }) => {
            const active = pathIsActive(location.pathname, to, end);
            return (
              <Link
                key={to}
                to={to}
                aria-label={label}
                aria-current={active ? "page" : undefined}
                className="mobile-nav-item"
                data-active={active ? "true" : "false"}
              >
                {active && (
                  <motion.span
                    layoutId="mobile-active-nav-pill"
                    className="mobile-active-nav-pill"
                    transition={spring}
                    aria-hidden
                  />
                )}
                <motion.span
                  className="mobile-nav-item__icon"
                  animate={reduceMotion ? undefined : { scale: active ? 1.06 : 1 }}
                  transition={spring}
                >
                  <Icon size={18} strokeWidth={active ? 2 : 1.75} aria-hidden />
                </motion.span>
                <span className="mobile-nav-item__label">{label}</span>
              </Link>
            );
          })}

          <button
            type="button"
            className="mobile-nav-item"
            data-active="false"
            aria-label="History"
            onClick={onOpenHistory}
          >
            <span className="mobile-nav-item__icon">
              <History size={18} strokeWidth={1.75} aria-hidden />
            </span>
            <span className="mobile-nav-item__label">History</span>
          </button>

          <button
            type="button"
            className="mobile-nav-item"
            data-active={moreRouteActive ? "true" : "false"}
            data-open={moreOpen ? "true" : "false"}
            aria-label="More"
            aria-expanded={moreOpen}
            aria-haspopup="dialog"
            onClick={() => setMoreOpen(true)}
          >
            {moreRouteActive && (
              <motion.span
                layoutId="mobile-active-nav-pill"
                className="mobile-active-nav-pill"
                transition={spring}
                aria-hidden
              />
            )}
            <span className="mobile-nav-item__icon">
              <MoreHorizontal size={18} strokeWidth={moreRouteActive || moreOpen ? 2 : 1.75} aria-hidden />
            </span>
            <span className="mobile-nav-item__label">More</span>
          </button>
        </div>
      </motion.nav>

      <AnimatePresence>
        {moreOpen && (
          <motion.div
            className="fixed inset-0 z-modal md:hidden"
            role="dialog"
            aria-modal="true"
            aria-label="More"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduceMotion ? 0 : 0.16 }}
          >
            <button
              type="button"
              className="absolute inset-0 bg-black/40"
              aria-label="Close more menu"
              onClick={() => setMoreOpen(false)}
            />
            <motion.div
              className="glass-interactive absolute inset-x-0 bottom-0 rounded-t-2xl border border-[var(--glass-border)] p-4 pb-[calc(1rem+env(safe-area-inset-bottom,0px))] shadow-float"
              initial={reduceMotion ? false : { y: 24 }}
              animate={{ y: 0 }}
              exit={reduceMotion ? undefined : { y: 24 }}
              transition={spring}
            >
              <div className="mb-3 flex items-center justify-between">
                <h2 className="font-editorial text-xl text-text-primary">More</h2>
                <button
                  type="button"
                  className="flex h-11 w-11 items-center justify-center rounded-xl hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
                  aria-label="Close"
                  onClick={() => setMoreOpen(false)}
                >
                  <X size={20} strokeWidth={1.75} />
                </button>
              </div>
              <ul className="space-y-1">
                {moreItems.map(({ to, label, icon: Icon }) => (
                  <li key={to}>
                    <NavLink
                      to={to}
                      onClick={() => setMoreOpen(false)}
                      aria-label={label}
                      className={({ isActive }) =>
                        `flex min-h-12 items-center gap-3 rounded-xl px-3 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus ${
                          isActive
                            ? "mobile-more-link-active"
                            : "text-text-secondary hover:bg-surface-hover"
                        }`
                      }
                    >
                      {Icon ? <Icon size={20} strokeWidth={1.75} aria-hidden /> : null}
                      {label}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

/** @deprecated Prefer MobileTopNavigation */
export const MobileNavigation = MobileTopNavigation;
