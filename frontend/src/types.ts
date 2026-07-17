export type ChatRole = "user" | "assistant";

export interface Citation {
  id: string;
  title: string;
  url: string;
  snippet?: string;
}

export interface AnswerFact {
  label: string;
  value: string;
}

export type AnswerType =
  | "factual"
  | "deadline"
  | "process"
  | "comparison"
  | "location"
  | "no_source"
  | "partial"
  | "backend_failure"
  | "clarification"
  | "conversational";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  isDemo?: boolean;
  isStreaming?: boolean;
  isError?: boolean;
  citations?: Citation[];
  timestamp?: Date;
  model?: string;
  confidence?: "high" | "medium" | "low";
  structured?: StructuredAnswer;
  /** Stable ask-run id for turn-owned live activity (not persisted as live). */
  runId?: string;
  /** Compact completed-run summary attached to this assistant turn. */
  runSummary?: {
    runId: string;
    status: "completed" | "failed" | "cancelled";
    stages: Array<{
      id: string;
      event: string;
      label: string;
      status: "active" | "completed" | "failed";
      elapsedMs?: number;
    }>;
    durationMs?: number;
    sourcesFound?: number;
  };
}

export interface Conversation {
  id: string;
  title: string;
  preview: string;
  updatedAt: Date;
  messages: ChatMessage[];
  pinned?: boolean;
}

export type HealthStatus = "checking" | "online" | "offline";
export type AppView = "chat" | "status" | "settings" | "feedback";
export type SourceScope = "adaptive" | "knowledge" | "web";
export type ComposerState =
  | "idle"
  | "focused"
  | "multiline"
  | "submitting"
  | "retrieving"
  | "generating"
  | "stopped"
  | "failed"
  | "offline";

export interface BackendChunk {
  chunk_id: string;
  text: string;
  source_url: string;
  title: string;
  category?: string;
  score?: number;
}

export interface AskResponse {
  question: string;
  answer?: string;
  text?: string;
  chunks?: BackendChunk[];
  num_results?: number;
  query_id?: string;
  model?: string;
  tokens_used?: number;
  retrieval_ms?: number;
  generation_ms?: number;
  total_ms?: number;
  answer_type?: AnswerType;
  title?: string | null;
  summary?: string | null;
  content_markdown?: string | null;
  key_facts?: AnswerFact[] | null;
  important_dates?: AnswerFact[] | null;
  requirements?: string[] | null;
  steps?: string[] | null;
  warnings?: string[] | null;
  related_questions?: string[] | null;
  confidence?: "high" | "medium" | "low";
  sources?: Citation[] | null;
}

export interface PipelineStep {
  step: string;
  status: "started" | "completed" | "failed";
  message: string;
  duration_ms?: number;
}

export interface StreamEvent {
  event: "activity" | "step" | "chunk" | "citations" | "done" | "error";
  data: Record<string, unknown>;
}

export interface ActivityEvent {
  requestId: string;
  runId?: string;
  event: string;
  message: string;
  elapsedMs?: number;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface StructuredAnswer {
  type: AnswerType;
  title?: string;
  summary?: string;
  contentMarkdown: string;
  keyFacts: AnswerFact[];
  importantDates: AnswerFact[];
  requirements: string[];
  steps: string[];
  warnings: string[];
  relatedQuestions: string[];
  confidence?: "high" | "medium" | "low";
  sources: Citation[];
}
