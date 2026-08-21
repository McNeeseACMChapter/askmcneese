import { motion } from "framer-motion";
import type { ReactNode } from "react";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface BlurFadeProps {
  children: ReactNode;
  className?: string;
  delay?: number;
  yOffset?: number;
}

/** Adapted Magic UI BlurFade — quiet entrance for short editorial copy. */
export function BlurFade({ children, className = "", delay = 0, yOffset = 12 }: BlurFadeProps) {
  const reduced = useReducedMotion();
  if (reduced) {
    return <div className={className}>{children}</div>;
  }
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: yOffset, filter: "blur(6px)" }}
      animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      transition={{ duration: 0.55, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  );
}
