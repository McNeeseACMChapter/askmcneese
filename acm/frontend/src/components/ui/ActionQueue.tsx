import { Link } from "react-router-dom";
import type { WorkItem } from "../../data/types";
import { StatusBadge, type StatusTone } from "./StatusBadge";
import { Surface } from "./Surface";
import { ProgressBar } from "../viz/ProgressBar";

export function ActionQueue({
  items,
  title = "Needs your attention",
  subtitle = "Priority work for your current fixture role.",
}: {
  items: WorkItem[];
  title?: string;
  subtitle?: string;
}) {
  return (
    <Surface level="content" className="overflow-hidden">
      <div className="border-b border-[var(--border-subtle)] px-5 py-4">
        <h2>{title}</h2>
        <p className="mt-1 text-sm text-text-secondary">{subtitle}</p>
      </div>
      <ul className="divide-y divide-[var(--border-subtle)]">
        {items.map((item) => (
          <li
            key={item.id}
            className="row-hover flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0 space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-text-primary">{item.title}</p>
                <StatusBadge
                  label={item.status}
                  tone={item.statusTone as StatusTone}
                />
              </div>
              <p className="text-sm text-text-secondary">{item.reason}</p>
              <p className="text-xs text-text-muted">
                {item.parentLabel} · Deadline · {item.deadline}
              </p>
              <ProgressBar value={item.progress} label={`${item.title} progress`} />
            </div>
            <Link
              to={item.href}
              className="acm-btn acm-btn--secondary shrink-0 no-underline"
            >
              {item.actionLabel}
            </Link>
          </li>
        ))}
      </ul>
    </Surface>
  );
}
