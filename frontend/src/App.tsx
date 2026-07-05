import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Header } from "./components/layout/Header";
import { Sidebar } from "./components/layout/Sidebar";
import { ChatPage } from "./components/chat/ChatPage";
import { SplashScreen } from "./components/feedback/SplashScreen";
import { useHealth } from "./hooks/useHealth";
import { useAsk } from "./hooks/useAsk";
import { useConversations } from "./hooks/useConversations";
import type { ChatMessage } from "./types";

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia(query).matches : false
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [query]);

  return matches;
}

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const { status, version } = useHealth();
  const { ask, isLoading: isAskLoading, status: askStatus, pipeline } = useAsk();
  const {
    conversations,
    activeConversation,
    activeId,
    createConversation,
    updateConversation,
    deleteConversation,
    selectConversation,
  } = useConversations();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const isMobile = !useMediaQuery("(min-width: 768px)");

  useEffect(() => {
    if (activeConversation) {
      setMessages(activeConversation.messages);
    } else {
      setMessages([]);
    }
  }, [activeConversation]);

  useEffect(() => {
    if (isDesktop) {
      setSidebarOpen(true);
    }
  }, [isDesktop]);

  const handleSend = useCallback(
    async (text: string) => {
      let convId = activeId;

      if (!convId) {
        const newConv = createConversation();
        convId = newConv.id;
      }

      const userMsg: ChatMessage = {
        id: `u-${Date.now()}`,
        role: "user",
        text,
        timestamp: new Date(),
      };

      const newMessages = [...messages, userMsg];
      setMessages(newMessages);
      updateConversation(convId, newMessages);
      setIsSending(true);

      try {
        // Send prior turns so the backend can resolve persona/context.
        const history = messages.map((m) => ({ role: m.role, content: m.text }));
        const response = await ask(text, undefined, history);
        const finalMessages = [...newMessages, response];
        setMessages(finalMessages);
        updateConversation(convId, finalMessages);
      } catch (error) {
        const errorMsg: ChatMessage = {
          id: `e-${Date.now()}`,
          role: "assistant",
          text: "Sorry, something went wrong. Please try again.",
          timestamp: new Date(),
        };
        const finalMessages = [...newMessages, errorMsg];
        setMessages(finalMessages);
        updateConversation(convId, finalMessages);
      } finally {
        setIsSending(false);
      }
    },
    [activeId, ask, createConversation, messages, updateConversation]
  );

  const handleNewChat = useCallback(() => {
    selectConversation(null);
    setMessages([]);
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [isMobile, selectConversation]);

  const handleSelectConversation = useCallback(
    (id: string | null) => {
      selectConversation(id);
    },
    [selectConversation]
  );

  return (
    <>
      <AnimatePresence mode="wait">
        {showSplash && (
          <SplashScreen onComplete={() => setShowSplash(false)} />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {!showSplash && (
          <motion.div
            className="flex h-full bg-background"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          >
            <Sidebar
              isOpen={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
              conversations={conversations}
              activeId={activeId}
              onSelect={handleSelectConversation}
              onNewChat={handleNewChat}
              onDelete={deleteConversation}
              isMobile={!isDesktop}
            />

            <div className="flex min-w-0 flex-1 flex-col h-full">
              <Header
                status={status}
                version={version}
                onMenuClick={() => setSidebarOpen(true)}
                showMenuButton={!isDesktop || !sidebarOpen}
              />

              {status === "offline" && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="border-b border-red-200 bg-red-50 px-4 py-2 text-center text-xs text-red-700"
                >
                  <span className="font-medium">Backend offline</span> — Start the API with{" "}
                  <code className="rounded bg-red-100 px-1 py-0.5">uvicorn app.main:app</code>
                </motion.div>
              )}

              <div className="flex-1 min-h-0 flex flex-col">
                <ChatPage
                  messages={messages}
                  isLoading={isSending || isAskLoading}
                  askStatus={askStatus}
                  pipeline={pipeline}
                  onSend={handleSend}
                />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
