import type { Variants, Transition } from "framer-motion";

export const springFast: Transition = {
  type: "spring",
  stiffness: 500,
  damping: 30,
};

export const springNormal: Transition = {
  type: "spring",
  stiffness: 300,
  damping: 25,
};

export const springGentle: Transition = {
  type: "spring",
  stiffness: 200,
  damping: 20,
};

export const easeFast: Transition = {
  duration: 0.15,
  ease: [0.4, 0, 0.2, 1],
};

export const easeNormal: Transition = {
  duration: 0.25,
  ease: [0.4, 0, 0.2, 1],
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: easeFast },
  exit: { opacity: 0, transition: easeFast },
};

export const slideUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: springNormal },
  exit: { opacity: 0, y: -8, transition: easeFast },
};

export const slideInRight: Variants = {
  hidden: { opacity: 0, x: 20 },
  visible: { opacity: 1, x: 0, transition: springNormal },
  exit: { opacity: 0, x: 20, transition: easeFast },
};

export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0, transition: springNormal },
  exit: { opacity: 0, x: -20, transition: easeFast },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: springFast },
  exit: { opacity: 0, scale: 0.95, transition: easeFast },
};

export const sidebarVariants: Variants = {
  open: {
    x: 0,
    transition: springNormal,
  },
  closed: {
    x: "-100%",
    transition: springNormal,
  },
};

export const overlayVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.02,
    },
  },
};

export const listItem: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: springGentle },
};

export const buttonHover = {
  scale: 1.02,
  transition: { duration: 0.15 },
};

export const buttonTap = {
  scale: 0.98,
};

export const pillHover = {
  scale: 1.03,
  transition: { duration: 0.12 },
};

export const pillTap = {
  scale: 0.97,
};
