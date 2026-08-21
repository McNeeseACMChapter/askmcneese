import type { AppView } from "../../types";

interface NavRailProps {
  activeView: AppView;
  onViewChange: (view: AppView) => void;
  onNewChat: () => void;
  onHistory: () => void;
}

const items: Array<{ view: AppView; label: string; path: string }> = [
  { view: "status", label: "Status", path: "M4 19h16M6 16l3-4 3 2 5-7" },
  { view: "settings", label: "Settings", path: "M12 15.5a3.5 3.5 0 100-7 3.5 3.5 0 000 7zM19.4 15a1.7 1.7 0 00.34 1.88l.06.06-2.12 2.12-.06-.06a1.7 1.7 0 00-1.88-.34 1.7 1.7 0 00-1.03 1.56V20h-3v-.08a1.7 1.7 0 00-1.03-1.56 1.7 1.7 0 00-1.88.34l-.06.06-2.12-2.12.06-.06A1.7 1.7 0 007 14.7a1.7 1.7 0 00-1.56-1.03H5v-3h.44A1.7 1.7 0 007 9.64a1.7 1.7 0 00-.34-1.88L6.6 7.7l2.12-2.12.06.06a1.7 1.7 0 001.88.34A1.7 1.7 0 0011.7 4.4V4h3v.4a1.7 1.7 0 001.03 1.56 1.7 1.7 0 001.88-.34l.06-.06 2.12 2.12-.06.06a1.7 1.7 0 00-.34 1.88 1.7 1.7 0 001.56 1.03H20v3h-.08A1.7 1.7 0 0019.4 15z" },
  { view: "feedback", label: "Feedback", path: "M21 15a4 4 0 01-4 4H8l-5 3V7a4 4 0 014-4h10a4 4 0 014 4v8z" },
];

function Icon({ path }: { path: string }) {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
      <path strokeLinecap="round" strokeLinejoin="round" d={path} />
    </svg>
  );
}

export function NavRail({ activeView, onViewChange, onNewChat, onHistory }: NavRailProps) {
  const base = "flex h-10 w-10 items-center justify-center rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-focus";
  return (
    <nav className="fixed inset-x-0 bottom-0 z-header flex h-14 items-center justify-around border-t border-white/10 bg-brand-950 px-2 text-white md:static md:h-full md:w-nav-rail md:flex-col md:justify-start md:gap-2 md:border-r md:border-t-0 md:py-3" aria-label="Primary">
      <button className={`${base} bg-white/10 hover:bg-white/20`} onClick={onNewChat} title="New chat" aria-label="New chat">
        <Icon path="M12 5v14M5 12h14" />
      </button>
      <button className={`${base} hover:bg-white/10`} onClick={onHistory} title="History" aria-label="Focus history search">
        <Icon path="M3 12a9 9 0 109-9 9.8 9.8 0 00-6.4 2.4L3 8m0-5v5h5" />
      </button>
      <div className="my-1 hidden h-px w-8 bg-white/15 md:block" />
      {items.map((item) => (
        <button
          key={item.view}
          className={`${base} ${activeView === item.view ? "bg-white text-brand-900" : "hover:bg-white/10"}`}
          onClick={() => onViewChange(item.view)}
          title={item.label}
          aria-label={item.label}
          aria-current={activeView === item.view ? "page" : undefined}
        >
          <Icon path={item.path} />
        </button>
      ))}
    </nav>
  );
}
