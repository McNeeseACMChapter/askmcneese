export type ChatRole = "user" | "assistant";

export interface Citation {
  id: string;
  title: string;
  url: string;
  snippet?: string;
}

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  isDemo?: boolean;
  isStreaming?: boolean;
  citations?: Citation[];
  timestamp?: Date;
}

export interface Conversation {
  id: string;
  title: string;
  preview: string;
  updatedAt: Date;
  messages: ChatMessage[];
}

export type HealthStatus = "checking" | "online" | "offline";

export interface AskResponse {
  question: string;
  answer: string;
  chunks: Array<{
    chunk_id: string;
    text: string;
    source_url: string;
    title: string;
    category?: string;
    score?: number;
  }>;
  num_results: number;
  query_id?: string;
  model?: string;
  tokens_used?: number;
  retrieval_ms: number;
  generation_ms?: number;
  total_ms: number;
}

export interface PipelineStep {
  step: string;
  status: "started" | "completed" | "failed";
  message: string;
  duration_ms?: number;
}

export interface StreamEvent {
  event: "step" | "chunk" | "citations" | "done" | "error";
  data: Record<string, unknown>;
}
