import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { useTour } from "../../features/onboarding";
import { fadeIn } from "../../lib/motion";
import { BrandLogo } from "../brand/BrandLogo";

interface EmptyStateProps {
  onSuggestion?: (prompt: string) => void;
}

const VERIFIED_STARTERS = [
  {
    label: "Plan classes",
    detail: "Find Fall 2026 sections and check time conflicts",
    prompt: "Can you find all CSCI courses offered in Fall 2026 that do not conflict with Calculus II?",
  },
  {
    label: "Find an office",
    detail: "Get a location, contact, and published hours",
    prompt: "Where is the Office of the Registrar, and what time does it close today?",
  },
  {
    label: "Handle a student task",
    detail: "Follow verified steps for IDs, advising, and campus services",
    prompt: "I lost my McNeese ID card. Where do I get a replacement and how much does it cost?",
  },
  {
    label: "Check a deadline or form",
    detail: "Use official dates, policies, and action links",
    prompt: "How do I appeal a parking citation?",
  },
] as const;

export function EmptyState({ onSuggestion }: EmptyStateProps) {
  const { guestAlias } = useTour();
  const greeting = guestAlias ? `Welcome, ${guestAlias}.` : "Welcome to AskMcNeese.";


  return (
    <motion.section
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="ask-welcome"
      aria-label="Welcome to AskMcNeese"
      data-tour-id="home-banner"
    >
      <div className="ask-welcomeMedia" aria-hidden="true">
        <div className="ask-welcomeMediaImage" />
        <p className="ask-welcomeMediaCaption">McNeese State University · Lake Charles</p>
      </div>

      <div className="ask-welcomeHero">
        <div className="ask-welcomeLogoPanel" aria-hidden="true">
          <BrandLogo variant="horizontal" decorative eager className="ask-welcomeBrandLogo" />
        </div>
        <p className="ask-welcomeGreeting">
          {greeting}
        </p>
        <h1 className="ask-welcomeBrand">Ask McNeese in your own words.</h1>
        <p className="ask-welcomeIntro">
          Ask about classes, deadlines, forms, offices, or student services. You do not need the official wording.
        </p>

        <div className="ask-welcomeStarters" aria-label="Useful question examples">
          {VERIFIED_STARTERS.map((starter, index) => (
            <button
              key={starter.label}
              type="button"
              className="ask-welcomeStarter"
              onClick={() => onSuggestion?.(starter.prompt)}
            >
              <span className="ask-welcomeStarterNumber" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="ask-welcomeStarterCopy">
                <strong>{starter.label}</strong>
                <span>{starter.detail}</span>
              </span>
              <ArrowRight className="ask-welcomeStarterArrow" size={17} aria-hidden="true" />
            </button>
          ))}
        </div>

        <div className="ask-welcomeTrust">
          <ShieldCheck size={17} aria-hidden="true" />
          <p>
            <strong>Guidance with sources.</strong>
            AskMcNeese cannot access personal records, make university decisions, or register you for classes.
          </p>
        </div>
      </div>
    </motion.section>
  );
}
