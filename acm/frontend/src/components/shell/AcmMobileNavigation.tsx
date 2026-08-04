import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { MoreHorizontal, X } from "lucide-react";
import { pathActive, routeManifest } from "../../routes/manifest";
import { usePrototype } from "../../state/PrototypeContext";

const ICON = 18;
const STROKE = 1.75;

export function AcmMobileNavigation() {
  const location = useLocation();
  const reduce = useReducedMotion();
  const { user } = usePrototype();
  const [moreOpen, setMoreOpen] = useState(false);

  useEffect(() => {
    setMoreOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!moreOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMoreOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [moreOpen]);

  const primary = routeManifest.filter((r) => r.showInMobilePrimary);
  const moreItems = routeManifest.filter((r) => {
    if (!r.showInMobileMore) return false;
    if (r.requiredPermission === "admin" && !user.canViewAdmin) return false;
    if (r.requiredPermission === "audit" && !user.canViewAudit) return false;
    return true;
  });

  const moreActive = moreItems.some((item) =>
    pathActive(location.pathname, item.path, item.end),
  );

  return (
    <>
      <nav className="acm-mobile-nav" aria-label="Primary mobile navigation">
        <div className="acm-mobile-nav__capsule">
          {primary.map((item) => {
            const Icon = item.icon;
            const active = pathActive(location.pathname, item.path, item.end);
            return (
              <Link
                key={item.path}
                to={item.path}
                className="acm-mobile-nav__item"
                data-active={active ? "true" : "false"}
                aria-current={active ? "page" : undefined}
              >
                <Icon size={ICON} strokeWidth={STROKE} aria-hidden />
                {item.label}
              </Link>
            );
          })}
          <button
            type="button"
            className="acm-mobile-nav__item"
            data-active={moreOpen || moreActive ? "true" : "false"}
            aria-expanded={moreOpen}
            aria-controls="acm-more-sheet"
            onClick={() => setMoreOpen(true)}
          >
            <MoreHorizontal size={ICON} strokeWidth={STROKE} aria-hidden />
            More
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {moreOpen ? (
          <div
            id="acm-more-sheet"
            className="acm-more-sheet md:hidden"
            role="dialog"
            aria-modal="true"
            aria-label="More navigation"
          >
            <button
              type="button"
              className="acm-more-sheet__backdrop"
              aria-label="Close more menu"
              onClick={() => setMoreOpen(false)}
            />
            <motion.div
              className="acm-more-sheet__panel surface-interactive"
              initial={reduce ? false : { y: "100%" }}
              animate={{ y: 0 }}
              exit={reduce ? undefined : { y: "100%" }}
              transition={
                reduce ? { duration: 0 } : { duration: 0.28, ease: [0.2, 0, 0, 1] }
              }
            >
              <div className="acm-more-sheet__handle" aria-hidden />
              <div className="mb-3 flex items-center justify-between">
                <h2>More</h2>
                <button
                  type="button"
                  className="acm-icon-btn"
                  aria-label="Close"
                  onClick={() => setMoreOpen(false)}
                >
                  <X size={18} strokeWidth={1.75} aria-hidden />
                </button>
              </div>
              <div className="acm-more-sheet__grid">
                {moreItems.map((item) => {
                  const Icon = item.icon;
                  const active = pathActive(location.pathname, item.path, item.end);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className="acm-more-sheet__link"
                      aria-current={active ? "page" : undefined}
                      onClick={() => setMoreOpen(false)}
                    >
                      <Icon size={ICON} strokeWidth={STROKE} aria-hidden />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </motion.div>
          </div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
