import { motion } from "framer-motion";
import { fadeIn } from "../../lib/motion";
import { useTour } from "../../features/onboarding";
import { BrandLogo } from "../brand/BrandLogo";

interface EmptyStateProps {
  onSuggestion?: (prompt: string) => void;
}

/** Mobile: warm greeting + ask line only. Desktop keeps a light brand frame. */
export function EmptyState(_props: EmptyStateProps) {
  const { showWelcomeGuest, guestAlias } = useTour();
  const greeting = showWelcomeGuest
    ? (guestAlias ? `Welcome, Guest ${guestAlias}` : "Welcome, Guest")
    : "Welcome — glad you’re here.";

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
          <BrandLogo
            variant="horizontal"
            decorative
            eager
            className="ask-welcomeBrandLogo"
          />
        </div>
        <p className={`ask-welcomeGreeting${showWelcomeGuest ? " ask-welcomeGuest" : ""}`}>
          {greeting}
        </p>
        <h1 className="ask-welcomeBrand">What are you trying to figure out?</h1>
        <p className="ask-welcomeIntro">Ask in your own words.</p>
      </div>
    </motion.section>
  );
}
