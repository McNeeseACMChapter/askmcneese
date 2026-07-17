import { useMemo, useState, type KeyboardEvent } from "react";
import { AnimatePresence } from "framer-motion";
import {
  Check,
  MessageSquare,
  Pin,
  Plus,
  Search,
} from "lucide-react";
import type { Conversation } from "../../types";
import { ConversationMenu } from "./ConversationMenu";
import { GlassSidebarShell } from "./GlassSidebarShell";

interface SidebarProps {
  isOpen: boolean;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onClose: () => void;
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onTogglePin: (id: string) => void;
  onDelete: (id: string) => void;
  isMobile: boolean;
  onNewChat?: () => void;
}

export function Sidebar(props: SidebarProps) {
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const filtered = useMemo(() => {
    const matches = props.conversations.filter((item) =>
      `${item.title} ${item.preview}`.toLowerCase().includes(search.toLowerCase())
    );
    return [...matches].sort(
      (a, b) =>
        Number(Boolean(b.pinned)) - Number(Boolean(a.pinned)) ||
        b.updatedAt.getTime() - a.updatedAt.getTime()
    );
  }, [props.conversations, search]);

  const headerAction = (
    <>
      {props.onNewChat ? collapsedNewChat(props.collapsed, props.onNewChat) : null}
      {!props.collapsed && (
        <div className="px-3 py-2">
          <label className="relative flex items-center">
            <span className="sr-only">Search conversations</span>
            <Search
              size={13}
              strokeWidth={1.75}
              className="pointer-events-none absolute left-3 text-text-muted"
              aria-hidden
            />
            <input
              id="history-search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search history"
              className="w-full rounded-xl border border-border bg-white/40 py-2 pl-8 pr-3 text-sm backdrop-blur-sm transition placeholder:text-text-muted focus:bg-white/70 focus:outline-none focus:ring-2 focus:ring-mcneese-blue/30 dark:bg-white/5 dark:focus:bg-white/10"
            />
          </label>
        </div>
      )}
    </>
  );

  return (
    <AnimatePresence>
      {props.isOpen && (
        <GlassSidebarShell
          key="history-sidebar"
          title="History"
          collapsed={props.collapsed}
          isMobile={props.isMobile}
          onToggleCollapsed={props.onToggleCollapsed}
          onClose={props.onClose}
          ariaLabel="Conversation history"
          collapseLabel={{ expand: "Expand history", collapse: "Collapse history" }}
          headerAction={headerAction}
        >
          <nav className="p-2" aria-label="Conversation history">
            {props.collapsed
              ? filtered.slice(0, 8).map((conversation) => (
                  <button
                    key={conversation.id}
                    type="button"
                    onClick={() => props.onSelect(conversation.id)}
                    title={conversation.title}
                    className={`mb-1 flex h-10 w-full items-center justify-center rounded-xl transition-colors ${
                      props.activeId === conversation.id
                        ? "bg-primary-subtle text-mcneese-blue"
                        : "text-text-secondary hover:bg-surface-hover"
                    }`}
                    aria-label={conversation.title}
                    aria-current={props.activeId === conversation.id ? "true" : undefined}
                  >
                    <MessageSquare size={16} strokeWidth={1.75} aria-hidden />
                  </button>
                ))
              : Object.entries(groupByDate(filtered)).map(([group, conversations]) => (
                  <section key={group} className="mb-3 [&:first-child>div]:mt-0">
                    <div className="mb-1 mt-3 flex items-center gap-2 px-1">
                      <div className="h-px flex-1 bg-border" />
                      <span className="px-1 text-[10px] font-semibold uppercase tracking-widest text-text-muted">
                        {group}
                      </span>
                      <div className="h-px flex-1 bg-border" />
                    </div>
                    {conversations.map((conversation) => {
                      const isActive = props.activeId === conversation.id;
                      return (
                        <div
                          key={conversation.id}
                          className={`group relative mb-0.5 cursor-pointer rounded-xl transition-colors ${
                            isActive ? "bg-primary-subtle" : "hover:bg-surface-hover"
                          }`}
                        >
                          {isActive && (
                            <div
                              className="absolute bottom-2 left-0 top-2 w-[3px] rounded-full bg-mcneese-blue"
                              aria-hidden
                            />
                          )}
                          <div className="flex items-center gap-2 px-3 py-2.5 pl-4">
                            <MessageSquare
                              size={14}
                              strokeWidth={1.75}
                              className={`flex-shrink-0 ${
                                isActive ? "text-mcneese-blue" : "text-text-muted"
                              }`}
                              aria-hidden
                            />
                            <button
                              type="button"
                              onClick={() => props.onSelect(conversation.id)}
                              className="min-w-0 flex-1 text-left"
                              aria-current={isActive ? "true" : undefined}
                            >
                              {editingId === conversation.id ? (
                                <RenameInput
                                  conversation={conversation}
                                  onSave={(title) => {
                                    props.onRename(conversation.id, title);
                                    setEditingId(null);
                                  }}
                                  onCancel={() => setEditingId(null)}
                                />
                              ) : (
                                <>
                                  <span className="flex items-center gap-1.5 truncate text-sm font-medium leading-tight">
                                    {conversation.title}
                                    {conversation.pinned && (
                                      <Pin
                                        size={10}
                                        strokeWidth={2}
                                        className="flex-shrink-0 text-mcneese-blue"
                                        aria-label="Pinned"
                                      />
                                    )}
                                  </span>
                                  <span className="mt-0.5 block truncate text-[11px] leading-tight text-text-muted">
                                    {conversation.preview || "Empty conversation"}
                                  </span>
                                </>
                              )}
                            </button>
                            <ConversationMenu
                              conversation={conversation}
                              onRename={() => setEditingId(conversation.id)}
                              onTogglePin={() => props.onTogglePin(conversation.id)}
                              onDelete={() => props.onDelete(conversation.id)}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </section>
                ))}
            {!filtered.length && !props.collapsed && (
              <p className="p-4 text-center text-sm text-text-muted">No conversations found.</p>
            )}
          </nav>
        </GlassSidebarShell>
      )}
    </AnimatePresence>
  );
}

function collapsedNewChat(collapsed: boolean, onNewChat: () => void) {
  if (collapsed) {
    return (
      <div className="flex justify-center border-b border-border py-2">
        <button
          type="button"
          onClick={onNewChat}
          className="flex h-10 w-10 items-center justify-center rounded-xl bg-mcneese-blue/10 text-mcneese-blue transition hover:bg-mcneese-blue/20"
          title="New conversation"
          aria-label="New conversation"
        >
          <Plus size={18} strokeWidth={1.75} />
        </button>
      </div>
    );
  }

  return (
    <div className="border-b border-border px-3 py-2">
      <button
        type="button"
        onClick={onNewChat}
        className="flex h-10 w-full items-center justify-center gap-2 rounded-xl bg-mcneese-blue/10 text-sm font-medium text-mcneese-blue transition hover:bg-mcneese-blue/20"
      >
        <Plus size={15} strokeWidth={2} />
        New conversation
      </button>
    </div>
  );
}

function RenameInput({
  conversation,
  onSave,
  onCancel,
}: {
  conversation: Conversation;
  onSave: (title: string) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(conversation.title);

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    event.stopPropagation();
    if (event.key === "Enter") {
      event.preventDefault();
      onSave(value);
    }
    if (event.key === "Escape") {
      event.preventDefault();
      onCancel();
    }
  };

  return (
    <div className="flex items-center gap-1">
      <input
        autoFocus
        value={value}
        onClick={(event) => event.stopPropagation()}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        className="min-w-0 flex-1 rounded-lg border border-mcneese-blue px-2 py-0.5 text-sm focus:outline-none"
        aria-label="Conversation name"
      />
      <button
        type="button"
        onClick={(event) => {
          event.stopPropagation();
          onSave(value);
        }}
        className="flex h-6 w-6 items-center justify-center rounded text-mcneese-blue hover:bg-primary-subtle"
        aria-label="Save rename"
      >
        <Check size={13} strokeWidth={2} />
      </button>
    </div>
  );
}

function groupByDate(conversations: Conversation[]): Record<string, Conversation[]> {
  const groups: Record<string, Conversation[]> = {};
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const yesterday = new Date(today.getTime() - 86400000);
  const weekAgo = new Date(today.getTime() - 604800000);
  conversations.forEach((conversation) => {
    const label = conversation.pinned
      ? "Pinned"
      : conversation.updatedAt >= today
        ? "Today"
        : conversation.updatedAt >= yesterday
          ? "Yesterday"
          : conversation.updatedAt >= weekAgo
            ? "Previous 7 days"
            : "Older";
    (groups[label] ??= []).push(conversation);
  });
  return groups;
}
