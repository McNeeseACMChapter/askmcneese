import { motion, AnimatePresence } from "framer-motion";
import { sidebarVariants, overlayVariants, listItem, staggerContainer } from "../../lib/motion";
import type { Conversation } from "../../types";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string | null) => void;
  onNewChat: () => void;
  onDelete: (id: string) => void;
  isMobile: boolean;
}

export function Sidebar({
  isOpen,
  onClose,
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  isMobile,
}: SidebarProps) {
  const groupedConversations = groupByDate(conversations);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") onClose();
  };

  const sidebarContent = (
    <motion.aside
      variants={sidebarVariants}
      initial="closed"
      animate="open"
      exit="closed"
      className={`flex h-full w-[280px] flex-col border-r border-border bg-surface ${
        isMobile ? "fixed inset-y-0 left-0 z-50 shadow-float" : ""
      }`}
      onKeyDown={handleKeyDown}
    >
      <div className="flex items-center justify-between border-b border-border p-4">
        <h2 className="text-sm font-semibold text-text-primary">History</h2>
        <div className="flex items-center gap-1">
          <button
            onClick={onNewChat}
            className="rounded-lg p-1.5 text-text-secondary hover:bg-gray-100 hover:text-mcneese-blue focus:outline-none focus:ring-2 focus:ring-mcneese-blue/30"
            aria-label="New chat"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
          </button>
          {isMobile && (
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-text-secondary hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-mcneese-blue/30"
              aria-label="Close sidebar"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto scrollbar-thin p-2" aria-label="Chat history">
        {conversations.length === 0 ? (
          <p className="px-3 py-8 text-center text-sm text-text-muted">
            No conversations yet
          </p>
        ) : (
          <motion.div variants={staggerContainer} initial="hidden" animate="visible">
            {Object.entries(groupedConversations).map(([group, convs]) => (
              <div key={group} className="mb-4">
                <p className="mb-1 px-3 text-xs font-medium uppercase tracking-wide text-text-muted">
                  {group}
                </p>
                {convs.map((conv) => (
                  <motion.div key={conv.id} variants={listItem}>
                    <button
                      onClick={() => {
                        onSelect(conv.id);
                        if (isMobile) onClose();
                      }}
                      className={`group relative mb-0.5 flex w-full items-start gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                        activeId === conv.id
                          ? "bg-mcneese-blue/10 text-mcneese-blue"
                          : "text-text-primary hover:bg-gray-100"
                      }`}
                    >
                      <svg
                        className={`mt-0.5 h-4 w-4 flex-shrink-0 ${
                          activeId === conv.id ? "text-mcneese-blue" : "text-text-muted"
                        }`}
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                        />
                      </svg>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{conv.title}</p>
                        <p className="truncate text-xs text-text-muted">{conv.preview || "Empty"}</p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(conv.id);
                        }}
                        className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-text-muted opacity-0 transition-opacity hover:bg-red-100 hover:text-red-600 focus:opacity-100 group-hover:opacity-100"
                        aria-label={`Delete ${conv.title}`}
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </button>
                  </motion.div>
                ))}
              </div>
            ))}
          </motion.div>
        )}
      </nav>

      <div className="border-t border-border p-4">
        <p className="text-center text-[11px] text-text-muted">Built by McNeese ACM</p>
      </div>
    </motion.aside>
  );

  if (!isMobile) {
    return isOpen ? sidebarContent : null;
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            variants={overlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
            aria-hidden="true"
          />
          {sidebarContent}
        </>
      )}
    </AnimatePresence>
  );
}

function groupByDate(conversations: Conversation[]): Record<string, Conversation[]> {
  const groups: Record<string, Conversation[]> = {};
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const weekAgo = new Date(today.getTime() - 7 * 86400000);

  conversations.forEach((conv) => {
    const date = new Date(conv.updatedAt);
    let group: string;

    if (date >= today) {
      group = "Today";
    } else if (date >= yesterday) {
      group = "Yesterday";
    } else if (date >= weekAgo) {
      group = "Previous 7 Days";
    } else {
      group = "Older";
    }

    if (!groups[group]) groups[group] = [];
    groups[group].push(conv);
  });

  return groups;
}
