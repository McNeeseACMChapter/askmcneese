import { motion } from "framer-motion";
import { useReducedMotion } from "../../hooks/useReducedMotion";

interface TextRevealProps {
  text: string;
  className?: string;
  as?: "p" | "h2" | "span";
}

/**
 * Adapted Magic UI TextReveal — one short mission sentence only.
 * Accessible complete phrase; visual word stagger is decorative.
 */
export function TextReveal({ text, className = "", as: Tag = "p" }: TextRevealProps) {
  const reduced = useReducedMotion();
  const words = text.split(" ");

  if (reduced) {
    return <Tag className={className}>{text}</Tag>;
  }

  return (
    <Tag className={className} aria-label={text}>
      <span className="sr-only">{text}</span>
      <span aria-hidden="true" className="inline">
        {words.map((word, index) => (
          <motion.span
            key={`${word}-${index}`}
            className="inline-block whitespace-pre"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.35,
              delay: Math.min(index * 0.035, 0.6),
              ease: [0.16, 1, 0.3, 1],
            }}
          >
            {word}
            {index < words.length - 1 ? " " : ""}
          </motion.span>
        ))}
      </span>
    </Tag>
  );
}
