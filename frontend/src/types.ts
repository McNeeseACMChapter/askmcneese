export type ChatRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  /** Sprint 1 only shows clearly-labeled demo content, never real answers. */
  isDemo?: boolean;
  /** Retrieved source chunks for assistant replies (Sprint 2). */
  citations?: RetrievedChunk[];
}

export type HealthStatus = "checking" | "online" | "offline";

/** Trust tier denormalized from source_registry (see docs/db_schema.md). */
export type TrustTier = "High" | "Medium" | "Low";

/** One retrieved chunk returned by POST /ask (matches crawler/chunker metadata). */
export interface RetrievedChunk {
  chunk_id: string;
  chunk_index: number;
  text: string;
  source_url: string;
  title: string;
  category: string;
  trust_tier: TrustTier;
  last_checked_date: string;
}

/** Payload sent to POST /ask. */
export interface AskCommand {
  question: string;
}

/** Successful POST /ask response (Sprint 2 — retrieval only, no LLM answer). */
export interface AskResponse {
  query_id: string;
  question_text: string;
  chunks: RetrievedChunk[];
  num_results: number;
  latency_ms: number;
}
