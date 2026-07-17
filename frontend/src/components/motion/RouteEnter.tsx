import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface RouteEnterProps {
  children: ReactNode;
  className?: string;
}

/** Short Motion entrance for operational / editorial routes. */
export function RouteEnter({ children, className = "" }: RouteEnterProps) {
  const reduced = useReducedMotion();
  if (reduced) {
    return <div className={className}>{children}</div>;
  }
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: [0.2, 0, 0, 1] }}
    >
      {children}
    </motion.div>
  );
}
