import { motion } from "framer-motion";
import { ArrowRight, BookOpenCheck } from "lucide-react";
import { fadeIn } from "../../lib/motion";
import { BrandLogo } from "../brand/BrandLogo";
import { AppIcon } from "../ui/AppIcon";

const STARTERS = [
  {
    number: "01",
    label: "Choose a program",
    detail: "Compare majors and requirements",
    prompt: "Help me compare programs I can study at McNeese.",
  },
  {
    number: "02",
    label: "Plan the next step",
    detail: "Applications, registration, and deadlines",
    prompt: "What should I do next to apply to McNeese?",
  },
  {
    number: "03",
    label: "Find the right office",
    detail: "Financial aid, advising, and student support",
    prompt: "Which McNeese office can help with financial aid?",
  },
] as const;

interface EmptyStateProps {
  onSuggestion?: (prompt: string) => void;
}

/** A campus-first welcome that explains the product before asking for trust. */
export function EmptyState({ onSuggestion }: EmptyStateProps) {
  return (
    <motion.section
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="ask-welcome"
      aria-label="Welcome to AskMcNeese"
    >
      <div className="ask-welcomeMedia" aria-hidden="true">
        <div className="ask-welcomeMediaImage" />
        <p className="ask-welcomeMediaCaption">McNeese State University · Lake Charles</p>
      </div>

      <div className="ask-welcomeHero">
        <div className="ask-welcomeLogoPanel" aria-hidden="true">
          <BrandLogo
            variant="horizontal"
            decorative
            eager
            className="ask-welcomeBrandLogo"
          />
        </div>
        <p className="ask-welcomeEyebrow">McNeese information, brought together</p>
        <h1 className="ask-welcomeBrand">What are you trying to figure out?</h1>
        <p className="ask-welcomeIntro">
          Ask in your own words. AskMcNeese will look through campus information,
          show what it used, and point you toward the page or office that owns the decision.
        </p>

        <div className="ask-welcomeStarters" aria-label="Ways to begin">
          {STARTERS.map(({ number, label, detail, prompt }) => (
            <button
              key={prompt}
              type="button"
              className="ask-welcomeStarter"
              onClick={() => onSuggestion?.(prompt)}
            >
              <span className="ask-welcomeStarterNumber" aria-hidden="true">{number}</span>
              <span className="ask-welcomeStarterCopy">
                <strong>{label}</strong>
                <span>{detail}</span>
              </span>
              <AppIcon icon={ArrowRight} size={17} className="ask-welcomeStarterArrow" />
            </button>
          ))}
        </div>

        <div className="ask-welcomeTrust">
          <AppIcon icon={BookOpenCheck} size={16} aria-hidden />
          <p>
            <strong>A guide, not the final authority.</strong>
            The cited McNeese page or office has the last word on requirements and deadlines.
          </p>
        </div>
      </div>
    </motion.section>
  );
}