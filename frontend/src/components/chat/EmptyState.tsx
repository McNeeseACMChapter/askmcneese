import { motion } from "framer-motion";
import { useTour } from "../../features/onboarding";
import { fadeIn } from "../../lib/motion";
import { BrandLogo } from "../brand/BrandLogo";

interface EmptyStateProps {
  onSuggestion?: (prompt: string) => void;
}

export function EmptyState(_props: EmptyStateProps) {
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
        <h1 className="ask-welcomeBrand">Find McNeese information.</h1>
        <p className="ask-welcomeIntro">
          Ask about university dates, policies, programs, people, offices, forms, and current opportunities.
        </p>

      </div>
    </motion.section>
  );
}
