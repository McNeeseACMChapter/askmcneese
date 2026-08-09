import { motion, useReducedMotion } from "framer-motion";
import { BrandLogo } from "../../components/brand/BrandLogo";

interface GuestAdmissionProps {
  alias: string;
  mode: "admission" | "bootstrap-error" | "saving";
  message?: string;
  onContinue?: () => void;
  onRetry?: () => void;
}

/** Brand-canvas guest assignment / failure — never a card or modal box. */
export function GuestAdmission({
  alias,
  mode,
  message,
  onContinue,
  onRetry,
}: GuestAdmissionProps) {
  const reduceMotion = useReducedMotion();
  const duration = reduceMotion ? 0 : 0.55;

  return (
    <motion.div
      className="guestAdmission"
      role={mode === "bootstrap-error" ? "alertdialog" : "dialog"}
      aria-modal="true"
      aria-label={mode === "admission" ? "Guest assigned" : "Guest session"}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reduceMotion ? 0 : 0.22 }}
    >
      <div className="guestAdmissionInner">
        <motion.div
          className="guestAdmissionMark"
          initial={reduceMotion ? false : { opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration, ease: [0.22, 1, 0.36, 1] }}
        >
          <BrandLogo variant="mark" decorative eager className="guestAdmissionMarkImg" />
        </motion.div>

        <motion.div
          initial={reduceMotion ? false : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration, delay: reduceMotion ? 0 : 0.12, ease: [0.22, 1, 0.36, 1] }}
        >
          <BrandLogo
            variant="horizontal"
            decorative
            eager
            className="guestAdmissionWordmark"
          />
        </motion.div>

        {mode === "admission" ? (
          <motion.div
            className="guestAdmissionCopy"
            initial={reduceMotion ? false : { opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration, delay: reduceMotion ? 0 : 0.22 }}
          >
            <p className="guestAdmissionEyebrow">You&apos;re in as Guest</p>
            <p className="guestAdmissionAlias" aria-label={`Guest ${alias}`}>
              {alias}
            </p>
            <p className="guestAdmissionNote">
              Your demo activity can stay connected to this browser while you explore.
            </p>
            <button type="button" className="guestAdmissionAction" onClick={onContinue}>
              Continue →
            </button>
          </motion.div>
        ) : null}

        {mode === "bootstrap-error" ? (
          <div className="guestAdmissionCopy">
            <p className="guestAdmissionEyebrow">AskMcNeese</p>
            <p className="guestAdmissionNote">
              {message ?? "We couldn’t start your guest session."}
            </p>
            <button type="button" className="guestAdmissionAction" onClick={onRetry}>
              Try again →
            </button>
          </div>
        ) : null}

        {mode === "saving" ? (
          <div className="guestAdmissionCopy">
            <p className="guestAdmissionNote">{message ?? "Saving your setup…"}</p>
            {onRetry ? (
              <button type="button" className="guestAdmissionAction" onClick={onRetry}>
                Try again →
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}
