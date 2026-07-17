import { useEffect, useState } from "react";
import type { ActivityEvent } from "../../types";

interface ActivityTimelineProps {
  events: ActivityEvent[];
  complete?: boolean;
  disconnected?: boolean;
}

export function ActivityTimeline({
  events,
  complete = false,
  disconnected = false,
}: ActivityTimelineProps) {
  const [expanded, setExpanded] = useState(!complete);
  useEffect(() => {
    if (complete) setExpanded(false);
  }, [complete]);

  const current = events[events.length - 1];
  if (!current && !disconnected) return null;

  return (
    <div className="activityBubble w-full" role="status">
      <div className="flex items-center justify-between gap-3">
        <p className="activityBubbleText flex items-center gap-2">
          {!complete && !disconnected && (
            <span className="typingDots" aria-hidden="true">
              <span className="typingDot active" />
              <span className="typingDot" />
              <span className="typingDot" />
            </span>
          )}
          {disconnected ? "Connection interrupted — try again." : current?.message}
        </p>
        {events.length > 1 && (
          <button
            type="button"
            className="activityBubbleMeta shrink-0 text-[var(--chat-accent)]"
            onClick={() => setExpanded((value) => !value)}
            aria-expanded={expanded}
          >
            {expanded ? "Hide activity" : "View activity"}
          </button>
        )}
      </div>
      {expanded && (
        <ol className="mt-3 space-y-2 border-t border-[var(--glass-border)] pt-3">
          {events.map((event, index) => (
            <li key={`${event.event}-${index}`} className="activityBubbleMeta flex items-center gap-2">
              <span
                className={
                  index < events.length - 1 || complete
                    ? "text-success"
                    : "text-[var(--chat-accent)]"
                }
              >
                {index < events.length - 1 || complete ? "✓" : "•"}
              </span>
              <span className="flex-1 text-text-secondary">{event.message}</span>
              {event.elapsedMs !== undefined && (
                <span className="text-text-muted">{event.elapsedMs} ms</span>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
