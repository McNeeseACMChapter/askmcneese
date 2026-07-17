import { Outlet, useLocation } from "react-router-dom";
import { useEffect } from "react";

/** Thin shell for the single About page — no section sub-nav. */
export function AboutLayout() {
  const location = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <main className="w-full">
      <div className="mx-auto w-full max-w-5xl px-[var(--page-gutter)] py-8 md:py-12">
        <Outlet />
      </div>
    </main>
  );
}
