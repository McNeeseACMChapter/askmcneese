import type { HTMLAttributes, ReactNode } from "react";

interface GsapSectionProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
}

/** Outer GSAP ScrollTrigger target — do not put Framer Motion transform on this node. */
export function GsapSection({ children, className = "", ...rest }: GsapSectionProps) {
  return (
    <section data-gsap-section className={className} {...rest}>
      {children}
    </section>
  );
}
