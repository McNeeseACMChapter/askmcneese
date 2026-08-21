import { motion } from "framer-motion";
import { BrandLogo } from "../brand/BrandLogo";

interface SplashScreenProps {
  onComplete: () => void;
}

export function SplashScreen({ onComplete }: SplashScreenProps) {
  return (
    <motion.div
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-gradient-to-br from-mcneese-blue via-mcneese-dark to-mcneese-blue"
      initial={{ opacity: 1 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, ease: "easeInOut" }}
      onAnimationComplete={(definition) => {
        if (definition === "exit") onComplete();
      }}
    >
      {/* Animated background particles */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute h-64 w-64 rounded-full bg-white/5"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
              scale: 0,
            }}
            animate={{
              scale: [0, 1.5, 1],
              opacity: [0, 0.3, 0],
            }}
            transition={{
              duration: 3,
              delay: i * 0.3,
              repeat: Infinity,
              repeatDelay: 2,
            }}
          />
        ))}
      </div>

      {/* Main content */}
      <div className="relative z-10 flex flex-col items-center">
        {/* Approved brand artwork */}
        <motion.div
          initial={{ scale: 0.92, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{
            type: "spring",
            stiffness: 180,
            damping: 18,
            delay: 0.2,
          }}
          className="mb-6 overflow-hidden bg-white shadow-2xl splashBrandLogo"
        >
          <BrandLogo variant="stacked" decorative eager />
        </motion.div>

        {/* Tagline */}
        <motion.p
          className="mb-8 text-lg text-white/70"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.5 }}
        >
          Your campus assistant
        </motion.p>

        {/* Loading bar */}
        <motion.div
          className="h-1 w-48 overflow-hidden rounded-full bg-white/20"
          initial={{ opacity: 0, scaleX: 0 }}
          animate={{ opacity: 1, scaleX: 1 }}
          transition={{ delay: 1.4, duration: 0.3 }}
        >
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-mcneese-gold via-white to-mcneese-gold"
            initial={{ x: "-100%" }}
            animate={{ x: "100%" }}
            transition={{
              duration: 1,
              delay: 1.5,
              ease: "easeInOut",
            }}
            onAnimationComplete={onComplete}
          />
        </motion.div>

        {/* Attribution */}
        <motion.div
          className="mt-12 flex flex-col items-center gap-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8, duration: 0.5 }}
        >
          <motion.div
            className="flex items-center gap-2 text-sm text-white/50"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 2, duration: 0.4 }}
          >
            <span>Built by</span>
          </motion.div>
          <motion.div
            className="flex items-center gap-3"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 2.1, duration: 0.4, type: "spring" }}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10">
              <span className="text-sm font-bold text-mcneese-gold">ACM</span>
            </div>
            <span className="text-lg font-semibold text-white">
              McNeese ACM
            </span>
          </motion.div>
        </motion.div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/20 to-transparent" />
    </motion.div>
  );
}
