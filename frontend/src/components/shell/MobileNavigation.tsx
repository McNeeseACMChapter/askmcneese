import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Link, NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  History,
  Info,
  Menu,
  MessageSquareText,
  Newspaper,
  Settings2,
  BarChart3,
  X,
} from "lucide-react";
import { BrandLogo } from "../brand/BrandLogo";

const moreLinks = [
  { to: "/about", label: "About", icon: Info },
  { to: "/updates", label: "Updates", icon: Newspaper },
  { to: "/status", label: "Usage", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: Settings2 },
  { to: "/feedback", label: "Feedback", icon: MessageSquareText },
] as const;

interface MobileTopNavigationProps {
  onOpenHistory: () => void;
}

function pathIsActive(pathname: string, to: string, end: boolean): boolean {
  if (to === "/ask") return pathname === "/ask" || pathname === "/";
  if (to === "/about") return pathname === "/about" || pathname.startsWith("/about/");
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
    const previousOverflow = document.body.style.overflow;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMoreOpen(false);
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [moreOpen]);

  const moreRouteActive = moreLinks.some((item) =>
    pathIsActive(location.pathname, item.to, true),
  );
  const askActive = pathIsActive(location.pathname, "/ask", true);

  const spring = reduceMotion
    ? { duration: 0 }
    : { type: "spring" as const, stiffness: 420, damping: 34 };

  const moreSheet =
    typeof document !== "undefined"
      ? createPortal(
          <AnimatePresence>
            {moreOpen ? (
              <motion.div
                className="mobile-moreOverlay md:hidden"
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
                  className="mobile-moreScrim"
                  aria-label="Close more menu"
                  onClick={() => setMoreOpen(false)}
                />
                <motion.div
                  className="mobile-moreSheet"
                  initial={reduceMotion ? false : { y: 32 }}
                  animate={{ y: 0 }}
                  exit={reduceMotion ? undefined : { y: 32 }}
                  transition={spring}
                >
                  <span className="mobile-moreHandle" aria-hidden="true" />
                  <div className="mobile-moreHeader">
                    <div>
                      <p className="mobile-moreKicker">AskMcNeese</p>
                      <h2>Menu</h2>
                    </div>
                    <button
                      type="button"
                      className="mobile-moreClose"
                      aria-label="Close"
                      onClick={() => setMoreOpen(false)}
                    >
                      <X size={19} strokeWidth={1.9} />
                    </button>
                  </div>
                  <ul className="mobile-moreList">
                    <li>
                      <button
                        type="button"
                        className="mobile-moreLink"
                        aria-label="History"
                        onClick={() => {
                          setMoreOpen(false);
                          onOpenHistory();
                        }}
                      >
                        <span className="mobile-moreLinkIcon" aria-hidden="true">
                          <History size={19} strokeWidth={1.8} />
                        </span>
                        <span>History</span>
                      </button>
                    </li>
                    {moreLinks.map(({ to, label, icon: Icon }) => (
                      <li key={to}>
                        <NavLink
                          to={to}
                          onClick={() => setMoreOpen(false)}
                          aria-label={label}
                          className={({ isActive }) =>
                            `mobile-moreLink${isActive ? " mobile-more-link-active" : ""}`
                          }
                        >
                          <span className="mobile-moreLinkIcon" aria-hidden="true">
                            <Icon size={19} strokeWidth={1.8} />
                          </span>
                          <span>{label}</span>
                        </NavLink>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              </motion.div>
            ) : null}
          </AnimatePresence>,
          document.body,
        )
      : null;

  return (
    <>
      <motion.nav
        className="mobile-top-nav md:hidden"
        aria-label="Primary mobile navigation"
        initial={reduceMotion ? false : { y: -12, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={
          reduceMotion
            ? { duration: 0 }
            : { type: "spring", stiffness: 380, damping: 32 }
        }
      >
        <div className="mobile-header" role="presentation">
          <Link
            to="/ask"
            aria-label="Ask"
            aria-current={askActive ? "page" : undefined}
            className="mobile-headerBrand"
            data-active={askActive ? "true" : "false"}
          >
            <span className="mobile-headerBrand__mark" aria-hidden="true">
              <BrandLogo
                variant="mark"
                decorative
                eager
                className="mobile-headerBrand__markImage"
              />
            </span>
            <span className="mobile-headerBrand__copy">
              <span className="mobile-headerBrand__name">AskMcNeese</span>
              <span className="mobile-headerBrand__tagline">Campus guide</span>
            </span>
          </Link>

          <div className="mobile-headerActions">
            <button
              type="button"
              className="mobile-headerIconButton mobile-headerMenuButton"
              data-active={moreRouteActive ? "true" : "false"}
              data-open={moreOpen ? "true" : "false"}
              aria-label="Menu"
              aria-expanded={moreOpen}
              aria-haspopup="dialog"
              onClick={() => setMoreOpen(true)}
            >
              <Menu
                size={20}
                strokeWidth={moreRouteActive || moreOpen ? 2.1 : 1.8}
                aria-hidden="true"
              />
            </button>
          </div>
        </div>
      </motion.nav>
      {moreSheet}
    </>
  );
}

/** @deprecated Prefer MobileTopNavigation */
export const MobileNavigation = MobileTopNavigation;
