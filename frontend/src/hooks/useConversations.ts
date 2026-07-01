import { useState, useCallback } from "react";
import type { Conversation, ChatMessage } from "../types";

const STORAGE_KEY = "askmcneese_conversations";

function generateId(): string {
  return `conv-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function loadConversations(): Conversation[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    return parsed.map((c: Conversation) => ({
      ...c,
      updatedAt: new Date(c.updatedAt),
      messages: c.messages.map((m: ChatMessage) => ({
        ...m,
        timestamp: m.timestamp ? new Date(m.timestamp) : undefined,
      })),
    }));
  } catch {
    return [];
  }
}

function saveConversations(conversations: Conversation[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>(loadConversations);
  const [activeId, setActiveId] = useState<string | null>(null);

  const activeConversation = conversations.find((c) => c.id === activeId) ?? null;

  const createConversation = useCallback((): Conversation => {
    const newConv: Conversation = {
      id: generateId(),
      title: "New Chat",
      preview: "",
      updatedAt: new Date(),
      messages: [],
    };
    setConversations((prev) => {
      const updated = [newConv, ...prev];
      saveConversations(updated);
      return updated;
    });
    setActiveId(newConv.id);
    return newConv;
  }, []);

  const updateConversation = useCallback(
    (id: string, messages: ChatMessage[]) => {
      setConversations((prev) => {
        const updated = prev.map((c) => {
          if (c.id !== id) return c;
          const firstUserMsg = messages.find((m) => m.role === "user");
          const lastMsg = messages[messages.length - 1];
          return {
            ...c,
            title: firstUserMsg?.text.slice(0, 40) || "New Chat",
            preview: lastMsg?.text.slice(0, 60) || "",
            updatedAt: new Date(),
            messages,
          };
        });
        saveConversations(updated);
        return updated;
      });
    },
    []
  );

  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => {
      const updated = prev.filter((c) => c.id !== id);
      saveConversations(updated);
      return updated;
    });
    if (activeId === id) {
      setActiveId(null);
    }
  }, [activeId]);

  const selectConversation = useCallback((id: string | null) => {
    setActiveId(id);
  }, []);

  return {
    conversations,
    activeConversation,
    activeId,
    createConversation,
    updateConversation,
    deleteConversation,
    selectConversation,
  };
}
