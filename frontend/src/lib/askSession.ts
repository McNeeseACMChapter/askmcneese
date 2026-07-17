import type { ChatMessage } from "../types";

export type StreamingAssistantState = {
  requestId: string;
  conversationId: string;
  message: ChatMessage;
} | null;

const SAFE_ERROR_FALLBACK = "I couldn’t complete that request. Please try again.";

/** Merge a completed ask result into the pending conversation messages. */
export function mergeAskResult(
  pending: ChatMessage[],
  response: ChatMessage | null,
): ChatMessage[] {
  if (!response) return pending;
  // Replace provisional assistant with the same id when present.
  const index = pending.findIndex(
    (message) => message.id === response.id || (message.isStreaming && message.role === "assistant"),
  );
  if (index >= 0) {
    const next = [...pending];
    next[index] = { ...response, isStreaming: false };
    return next;
  }
  return [...pending, response];
}

export function createAssistantErrorMessage(text?: string | null): ChatMessage {
  const safe =
    typeof text === "string" && text.trim()
      ? text.trim().slice(0, 300)
      : SAFE_ERROR_FALLBACK;
  return {
    id: `e-${Date.now()}`,
    role: "assistant",
    text: safe,
    isError: true,
    isStreaming: false,
    timestamp: new Date(),
  };
}

export function createStreamingAssistantMessage(
  requestId: string,
  text: string,
  assistantMessageId?: string,
): ChatMessage {
  return {
    id: assistantMessageId ?? `stream-${requestId}`,
    role: "assistant",
    text,
    isStreaming: true,
    timestamp: new Date(),
    runId: undefined,
  };
}

export function updateStreamingText(
  state: StreamingAssistantState,
  requestId: string,
  conversationId: string,
  fullText: string,
  assistantMessageId?: string,
): StreamingAssistantState {
  if (!state || state.requestId !== requestId || state.conversationId !== conversationId) {
    return {
      requestId,
      conversationId,
      message: createStreamingAssistantMessage(requestId, fullText, assistantMessageId),
    };
  }
  return {
    ...state,
    message: {
      ...state.message,
      text: fullText,
      isStreaming: true,
    },
  };
}

/**
 * Return the provisional assistant for the active conversation.
 * Empty text is allowed so live activity can attach before the first token.
 */
export function streamingMessageForActiveConversation(
  state: StreamingAssistantState,
  activeConversationId: string | null,
): ChatMessage | null {
  if (!state || !activeConversationId) return null;
  if (state.conversationId !== activeConversationId) return null;
  return state.message;
}

export function shouldIgnoreStreamUpdate(
  state: StreamingAssistantState,
  requestId: string,
  conversationId: string,
  activeRequestId: string | null,
): boolean {
  if (activeRequestId !== requestId) return true;
  if (state && state.requestId !== requestId) return true;
  if (state && state.conversationId !== conversationId) return true;
  return false;
}

/** Seed a provisional assistant immediately on submit (before first chunk). */
export function seedStreamingAssistant(
  requestId: string,
  conversationId: string,
  assistantMessageId: string,
): StreamingAssistantState {
  return {
    requestId,
    conversationId,
    message: createStreamingAssistantMessage(requestId, "", assistantMessageId),
  };
}
