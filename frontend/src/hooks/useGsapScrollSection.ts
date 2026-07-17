import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import { ensureGsap, prefersReducedMotion } from "../lib/gsap";

/**
 * Reveal child sections with GSAP ScrollTrigger once.
 * Animates the outer wrapper only — keep Motion/Anime on descendants.
 */
export function useGsapScrollSection(enabled = true) {
  const containerRef = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      if (!enabled || prefersReducedMotion()) return;
      const { gsap, ScrollTrigger } = ensureGsap();
      const root = containerRef.current;
      if (!root) return;

      const sections = root.querySelectorAll<HTMLElement>("[data-gsap-section]");
      sections.forEach((section) => {
        gsap.fromTo(
          section,
          { opacity: 0, y: 16 },
          {
            opacity: 1,
            y: 0,
            duration: 0.65,
            ease: "power2.out",
            scrollTrigger: {
              trigger: section,
              start: "top 85%",
              once: true,
            },
          },
        );
      });

      return () => {
        ScrollTrigger.getAll().forEach((trigger) => {
          if (trigger.trigger && root.contains(trigger.trigger as Node)) {
            trigger.kill();
          }
        });
      };
    },
    { dependencies: [enabled], scope: containerRef },
  );

  return containerRef;
}
