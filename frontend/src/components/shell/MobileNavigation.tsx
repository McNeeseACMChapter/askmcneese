import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link, NavLink, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  CalendarDays,
  ChevronRight,
  History,

  Menu,
  MessageSquareText,
  Newspaper,
  Settings2,
  BarChart3,
  X,
} from "lucide-react";
import { useTour } from "../../features/onboarding";
import { BrandLogo } from "../brand/BrandLogo";

const moreLinks = [
  { to: "/class-planner", label: "Class Planner", icon: CalendarDays, tourId: "class-planner" },
  { to: "/updates", label: "Updates", icon: Newspaper, tourId: "updates" },
  { to: "/status", label: "Usage", icon: BarChart3, tourId: "usage" },
  { to: "/settings", label: "Settings", icon: Settings2, tourId: "settings" },
  { to: "/feedback", label: "Feedback", icon: MessageSquareText, tourId: "feedback" },
] as const;

interface MobileTopNavigationProps {
  onOpenHistory: () => void;
}

interface MenuRouteItemProps {
  item: (typeof moreLinks)[number];
  onSelect: (tourId: string) => void;
}

function MenuRouteItem({ item, onSelect }: MenuRouteItemProps) {
  const { to, label, icon: Icon, tourId } = item;
  return (
    <li className="mobile-moreItem">
      <NavLink
        to={to}
        data-tour-id={tourId}
        onClick={() => onSelect(tourId)}
        aria-label={label}
        className={({ isActive }) =>
          `mobile-moreLink${isActive ? " mobile-more-link-active" : ""}`
        }
      >
        <span className="mobile-moreLinkIcon" aria-hidden="true">
          <Icon size={20} strokeWidth={1.8} />
        </span>
        <span className="mobile-moreLinkLabel">{label}</span>
        <ChevronRight className="mobile-moreLinkArrow" size={18} strokeWidth={1.8} aria-hidden="true" />
      </NavLink>
    </li>
  );
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
  const { openMobileMenu, notifyMobileMenuOpen, notifyTargetActivated } = useTour();
  const [moreOpen, setMoreOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const menuSheetRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const closeMenu = useCallback((restoreFocus = false) => {
    setMoreOpen(false);
    if (restoreFocus) menuButtonRef.current?.focus();
  }, []);

  useEffect(() => {
    setMoreOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (openMobileMenu) setMoreOpen(true);
  }, [openMobileMenu]);

  useEffect(() => {
    notifyMobileMenuOpen(moreOpen);
  }, [moreOpen, notifyMobileMenuOpen]);

  useEffect(() => {
    if (!moreOpen) return;
    const previousOverflow = document.body.style.overflow;
    const sheet = menuSheetRef.current;
    const focusable = sheet
      ? Array.from(sheet.querySelectorAll<HTMLElement>('button, a[href]'))
      : [];
    closeButtonRef.current?.focus();

    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMenu(true);
        return;
      }
      if (event.key !== "Tab" || focusable.length < 2) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [closeMenu, moreOpen]);

  const moreRouteActive = moreLinks.some((item) =>
    pathIsActive(location.pathname, item.to, true),
  );
  const askActive = pathIsActive(location.pathname, "/ask", true);
  const aboutActive = pathIsActive(location.pathname, "/about", false);

  const sheetTransition = reduceMotion
    ? { duration: 0 }
    : { duration: 0.2, ease: "easeOut" as const };

  const moreSheet =
    typeof document !== "undefined"
      ? createPortal(
          <AnimatePresence>
            {moreOpen ? (
              <motion.div
                className="mobile-moreOverlay md:hidden"
                role="dialog"
                aria-modal="true"
                aria-labelledby="mobile-more-title"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: reduceMotion ? 0 : 0.16 }}
              >
                <button
                  type="button"
                  className="mobile-moreScrim"
                  aria-label="Dismiss menu"
                  onClick={() => closeMenu(true)}
                />
                <motion.div
                  ref={menuSheetRef}
                  className="mobile-moreSheet"
                  initial={reduceMotion ? false : { x: 36, opacity: 0.7 }}
                  animate={{ x: 0 }}
                  exit={reduceMotion ? undefined : { x: 36, opacity: 0.7 }}
                  transition={sheetTransition}
                >
                  <div className="mobile-moreHeader">
                    <h2 id="mobile-more-title">Menu</h2>
                    <button
                      ref={closeButtonRef}
                      type="button"
                      className="mobile-moreClose"
                      aria-label="Close menu"
                      onClick={() => closeMenu(true)}
                    >
                      <X size={19} strokeWidth={1.9} />
                    </button>
                  </div>
                  <nav className="mobile-moreNav" aria-label="App sections">
                    <section className="mobile-moreSection" aria-labelledby="mobile-more-main-title">
                      <h3 id="mobile-more-main-title" className="mobile-moreSectionTitle">Main</h3>
                      <ul className="mobile-moreList">
                        <li className="mobile-moreItem">
                          <button
                            type="button"
                            className="mobile-moreLink"
                            aria-label="History"
                            data-tour-id="conversations"
                            onClick={() => {
                              notifyTargetActivated("conversations");
                              setMoreOpen(false);
                              onOpenHistory();
                            }}
                          >
                            <span className="mobile-moreLinkIcon" aria-hidden="true">
                              <History size={20} strokeWidth={1.8} />
                            </span>
                            <span className="mobile-moreLinkLabel">History</span>
                            <ChevronRight className="mobile-moreLinkArrow" size={18} strokeWidth={1.8} aria-hidden="true" />
                          </button>
                        </li>
                        {moreLinks.slice(0, 3).map((item) => (
                          <MenuRouteItem
                            key={item.to}
                            item={item}
                            onSelect={(tourId) => {
                              notifyTargetActivated(tourId);
                              setMoreOpen(false);
                            }}
                          />
                        ))}
                      </ul>
                    </section>
                    <section className="mobile-moreSection" aria-labelledby="mobile-more-support-title">
                      <h3 id="mobile-more-support-title" className="mobile-moreSectionTitle">Support</h3>
                      <ul className="mobile-moreList">
                        {moreLinks.slice(3).map((item) => (
                          <MenuRouteItem
                            key={item.to}
                            item={item}
                            onSelect={(tourId) => {
                              notifyTargetActivated(tourId);
                              setMoreOpen(false);
                            }}
                          />
                        ))}
                      </ul>
                    </section>
                  </nav>
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
            data-tour-id="logo"
            onClick={() => {
              notifyTargetActivated("logo");
              notifyTargetActivated("ask");
            }}
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
            <NavLink
              to="/about"
              aria-label="About"
              className="mobile-headerAbout"
              data-active={aboutActive ? "true" : "false"}
              data-tour-id="about"
              onClick={() => notifyTargetActivated("about")}
            >

              <span>About</span>
            </NavLink>
            <button
              ref={menuButtonRef}
              type="button"
              className="mobile-headerIconButton mobile-headerMenuButton"
              data-active={moreRouteActive ? "true" : "false"}
              data-open={moreOpen ? "true" : "false"}
              data-tour-id="menu"
              aria-label="Menu"
              aria-expanded={moreOpen}
              aria-haspopup="dialog"
              onClick={() => {
                setMoreOpen(true);
                notifyTargetActivated("menu");
              }}
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
