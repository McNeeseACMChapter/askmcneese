export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  /** Sprint 1 only shows clearly-labeled demo content, never real answers. */
  isDemo?: boolean;
}

export type HealthStatus = "checking" | "online" | "offline";
