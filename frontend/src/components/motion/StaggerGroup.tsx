import { useEffect, useRef } from "react";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface StaggerGroupProps {
  children: React.ReactNode;
  className?: string;
  itemSelector?: string;
}

function revealImmediately(items: NodeListOf<HTMLElement>) {
  items.forEach((el) => {
    el.style.opacity = "1";
    el.style.transform = "none";
  });
}

/**
 * Anime.js viewport stagger for repeated sibling cards/rows.
 * Parent may use GSAP; children animated here must not also receive GSAP transforms.
 */
export function StaggerGroup({
  children,
  className = "",
  itemSelector = "[data-stagger-item]",
}: StaggerGroupProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const playedRef = useRef(false);
  const reduced = useReducedMotion();

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const items = root.querySelectorAll<HTMLElement>(itemSelector);
    if (!items.length) return;

    if (reduced || typeof IntersectionObserver === "undefined") {
      revealImmediately(items);
      return;
    }

    items.forEach((el) => {
      el.style.opacity = "0";
      el.style.transform = "translateY(12px) scale(0.985)";
    });

    const play = () => {
      if (playedRef.current) return;
      playedRef.current = true;
      void import("animejs").then(({ animate, stagger }) => {
        animate(items, {
          opacity: [0, 1],
          translateY: [12, 0],
          scale: [0.985, 1],
          delay: stagger(55),
          duration: 480,
          ease: "outCubic",
        });
      });
    };

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (!entry?.isIntersecting) return;
        play();
        observer.disconnect();
      },
      { threshold: 0.12 },
    );

    observer.observe(root);

    const failSafe = window.setTimeout(() => {
      if (!playedRef.current) {
        revealImmediately(items);
        playedRef.current = true;
        observer.disconnect();
      }
    }, 2500);

    return () => {
      observer.disconnect();
      window.clearTimeout(failSafe);
    };
  }, [itemSelector, reduced]);

  return (
    <div ref={rootRef} className={className}>
      {children}
    </div>
  );
}
