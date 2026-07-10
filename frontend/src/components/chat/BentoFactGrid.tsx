import { motion } from "framer-motion";

export interface BentoFact {
  label: string;
  value: string;
  icon?: "calendar" | "info" | "clock" | "location" | "dollar";
}

interface BentoFactGridProps {
  facts: BentoFact[];
}

export function BentoFactGrid({ facts }: BentoFactGridProps) {
  if (facts.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
      {facts.map((fact, index) => (
        <BentoFactCard key={`${fact.label}-${index}`} fact={fact} index={index} />
      ))}
    </div>
  );
}

interface BentoFactCardProps {
  fact: BentoFact;
  index: number;
}

function BentoFactCard({ fact, index }: BentoFactCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
      className="group relative rounded-xl border border-border bg-surface-sunken p-3 transition-all hover:border-mcneese-blue/30 hover:shadow-soft"
    >
      <div className="flex items-start gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-subtle flex-shrink-0">
          <FactIcon type={fact.icon || "info"} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium uppercase tracking-wide text-text-muted truncate">
            {fact.label}
          </p>
          <p className="text-sm font-semibold text-text-primary mt-0.5 leading-tight">
            {fact.value}
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function FactIcon({ type }: { type: "calendar" | "info" | "clock" | "location" | "dollar" }) {
  const iconClass = "h-4 w-4 text-mcneese-blue";

  switch (type) {
    case "calendar":
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      );
    case "clock":
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case "location":
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      );
    case "dollar":
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case "info":
    default:
      return (
        <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
  }
}
