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
    <div className="messageActions" aria-label="Answer actions">
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
        <span className="messageActionsFeedback">Thanks for the feedback.</span>
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
      className={`messageAction${pressed ? " messageAction--pressed" : ""}`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}
