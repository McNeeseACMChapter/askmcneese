import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { AmbientSmokePulse } from "../motion/AmbientSmokePulse";
import { fadeIn, staggerContainer, listItem } from "../../lib/motion";

interface EmptyStateProps {
  onSuggestionClick: (text: string) => void;
}

/** Keep ≤3 on phone (Hick) — fourth remains for tablet/desktop grid. */
const suggestions = [
  {
    title: "Apply & deadlines",
    titleFull: "Application steps and deadlines",
    question: "What are the steps to apply to McNeese and when are the deadlines?",
  },
  {
    title: "Aid & scholarships",
    titleFull: "Aid and scholarships",
    question: "How do I apply for financial aid and scholarships at McNeese?",
  },
  {
    title: "Student services",
    titleFull: "Student services",
    question: "What campus services are available to McNeese students?",
  },
  {
    title: "Programs",
    titleFull: "Programs and requirements",
    question: "How do I find degree programs and academic requirements at McNeese?",
  },
];

/**
 * Guest first paint: P0 brand + warm welcome → P2 optional starters → P3 trust.
 * Composer (P1) stays docked — never compete with it.
 * Mobile keeps one greeting, chip starters, and quiet chrome.
 */
export function EmptyState({ onSuggestionClick }: EmptyStateProps) {
  return (
    <motion.section
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="ask-welcome"
      aria-label="Welcome to AskMcNeese"
    >
      <div className="ask-welcomeAtmosphere" aria-hidden="true" />
      <AmbientSmokePulse trigger className="ask-welcomeSmoke left-1/2 top-10 -translate-x-1/2" />

      <div className="ask-welcomeHero">
        <h1 className="ask-welcomeBrand">AskMcNeese</h1>
        <p className="ask-welcomeGreeting">Welcome — you&apos;re in the right place.</p>
        <p className="ask-welcomeSupport">
          Ask anything about campus life. Answers stay grounded in McNeese sources.
        </p>
      </div>

      <div className="ask-welcomeStarters">
        <h2 className="ask-welcomeStartersLabel">Optional places to start</h2>
        <motion.ul
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="ask-welcomeStarterList"
        >
          {suggestions.map((item) => (
            <motion.li key={item.titleFull} variants={listItem} className="ask-welcomeStarterItem">
              <button
                type="button"
                onClick={() => onSuggestionClick(item.question)}
                className="suggestion-row ask-welcomeStarterBtn"
              >
                <span className="ask-welcomeStarterTitleMobile">{item.title}</span>
                <span className="ask-welcomeStarterTitleDesktop">{item.titleFull}</span>
              </button>
            </motion.li>
          ))}
        </motion.ul>
        <p className="ask-welcomeTrust">
          <Link
            to="/about"
            className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          >
            About the team and what AskMcNeese does
          </Link>
        </p>
      </div>
    </motion.section>
  );
}
