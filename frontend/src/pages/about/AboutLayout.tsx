import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";

export function AboutLayout() {
  const location = useLocation();

  useEffect(() => {
    const shellScroller = document.querySelector<HTMLElement>(".public-shellMain");
    if (shellScroller) shellScroller.scrollTop = 0;
    if (document.scrollingElement) document.scrollingElement.scrollTop = 0;
  }, [location.pathname]);

  return (
    <main className="about-page">
      <div className="about-page__inner">
        <Outlet />
      </div>
    </main>
  );
}