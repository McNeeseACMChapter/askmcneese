import { useState } from "react";
import { Check, Copy, ThumbsDown, ThumbsUp } from "lucide-react";

interface MessageActionsProps {
  text: string;
}

export function MessageActions({ text }: MessageActionsProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard may be unavailable
    }
  };

  return (
    <div className="mt-5 flex flex-wrap items-center gap-1">
      <ActionButton
        label={copied ? "Copied" : "Copy"}
        onClick={handleCopy}
        icon={
          copied ? (
            <Check size={16} strokeWidth={1.75} className="text-success" />
          ) : (
            <Copy size={16} strokeWidth={1.75} />
          )
        }
      />
      <ActionButton
        label="Helpful"
        pressed={feedback === "up"}
        onClick={() => setFeedback("up")}
        icon={<ThumbsUp size={16} strokeWidth={1.75} />}
      />
      <ActionButton
        label="Not helpful"
        pressed={feedback === "down"}
        onClick={() => setFeedback("down")}
        icon={<ThumbsDown size={16} strokeWidth={1.75} />}
      />
      {feedback && (
        <span className="ml-2 font-sans text-xs text-text-muted">Thanks for the feedback.</span>
      )}
    </div>
  );
}

function ActionButton({
  label,
  icon,
  onClick,
  pressed,
}: {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
  pressed?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={pressed}
      className={`inline-flex min-h-11 items-center gap-1.5 rounded-xl px-3 text-xs font-medium transition duration-fast focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus active:scale-[0.98] ${
        pressed
          ? "bg-brand-50 text-brand-700"
          : "text-text-muted hover:bg-surface-hover hover:text-text-primary"
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
