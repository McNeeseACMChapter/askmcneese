import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { UserRound } from "lucide-react";
import { BrandLogo } from "../../components/brand/BrandLogo";

interface GuestAdmissionProps {
  alias: string;
  mode: "admission" | "bootstrap-error" | "saving";
  message?: string;
  onStart?: () => void;
  onSkip?: () => void;
  onRetry?: () => void;
}

export function GuestAdmission({
  alias,
  mode,
  message,
  onStart,
  onSkip,
  onRetry,
}: GuestAdmissionProps) {
  const reduceMotion = useReducedMotion();
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    if (mode !== "admission" || !onStart) return;
    const timer = window.setInterval(() => {
      setCountdown((current) => {
        if (current <= 1) {
          window.clearInterval(timer);
          onStart();
          return 0;
        }
        return current - 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [mode, onStart]);

  return (
    <motion.div
      className="guestAdmission"
      role={mode === "bootstrap-error" ? "alertdialog" : "dialog"}
      aria-modal="true"
      aria-label={mode === "admission" ? "Walkthrough choice" : "Guest session"}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reduceMotion ? 0 : 0.2 }}
    >
      <motion.div
        className="guestAdmissionCard"
        initial={reduceMotion ? false : { opacity: 0, y: 12, scale: 0.985 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: reduceMotion ? 0 : 0.42, ease: [0.22, 1, 0.36, 1] }}
      >
        <BrandLogo variant="mark" decorative eager className="guestAdmissionMarkImg" />

        {mode === "admission" ? (
          <>
            <div className="guestAvatar" aria-hidden="true">
              <span className="guestAvatarMesh" />
              <UserRound size={30} strokeWidth={1.8} />
            </div>
            <p className="guestAdmissionEyebrow">This browser is signed in as</p>
            <h1 className="guestAdmissionAlias">{alias}</h1>
            <p className="guestAdmissionNote">
              Take the guided walkthrough now, or skip directly to AskMcNeese.
              Your guest identity and beta allowance stay with this browser.
            </p>
            <div className="guestAdmissionCountdown" aria-live="polite">
              <span style={{ transform: "scaleX(" + countdown / 5 + ")" }} />
              <p>Walkthrough starts in {countdown} second{countdown === 1 ? "" : "s"}</p>
            </div>
            <div className="guestAdmissionChoices">
              <button type="button" className="guestAdmissionAction is-primary" onClick={onStart}>
                Start walkthrough
              </button>
              <button type="button" className="guestAdmissionAction is-secondary" onClick={onSkip}>
                Skip for now
              </button>
            </div>
          </>
        ) : null}

        {mode === "bootstrap-error" ? (
          <div className="guestAdmissionCopy">
            <p className="guestAdmissionEyebrow">AskMcNeese</p>
            <p className="guestAdmissionNote">
              {message ?? "We couldn’t start your guest session."}
            </p>
            <button type="button" className="guestAdmissionAction is-primary" onClick={onRetry}>
              Try again
            </button>
          </div>
        ) : null}

        {mode === "saving" ? (
          <div className="guestAdmissionCopy">
            <p className="guestAdmissionNote">{message ?? "Saving your setup…"}</p>
            {onRetry ? (
              <button type="button" className="guestAdmissionAction is-primary" onClick={onRetry}>
                Try again
              </button>
            ) : null}
          </div>
        ) : null}
      </motion.div>
    </motion.div>
  );
}
