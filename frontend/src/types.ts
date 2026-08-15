export type ChatRole = "user" | "assistant";

export interface Citation {
  id: string;
  title: string;
  url: string;
  citationLabel?: string;
  retrievalMethod?: string;
  pageFetched?: boolean;
  lastVerified?: string;
  provider?: string;
  verifiedLive?: boolean;
}

export interface AnswerFact {
  label: string;
  value: string;
}

export interface PlannerAction {
  type: "class_planner_add";
  term_id: string;
  sections: Array<Record<string, unknown> & { id: string; termId: string }>;
  source?: "validated_class_planner";
  confirmed?: boolean;
  validation_status?: "COMPATIBLE" | "CONFLICTING" | "UNCERTAIN";
}

export interface TaskState {
  schema_version: 1;
  task_type: string;
  status: "active" | "awaiting_input" | "blocked" | "completed" | "ready_for_confirmation";
  domain?: string;
  term?: string;
  subject?: string;
  constraint_course?: string;
  constraint_section?: string;
  pending_field?: string;
  pending_fields?: string[];
  query_anchor?: string;
  selected_crns?: string[];
  candidate_crns?: string[];
}

export interface ReleaseDecision {
  status: "CAN_RELEASE" | "CAN_RELEASE_PARTIAL" | "BLOCKED";
  reasons: string[];
  evidence_passed: boolean;
  partial_allowed: boolean;
  failure_stage?: string | null;
  unsupported_material_claims?: string[];
}

export interface ClaimSupport {
  claim_id: string;
  claim_type: string;
  value: string;
  status: "SUPPORTED" | "DERIVED" | "UNSUPPORTED" | "CONFLICTED";
  evidence_ids: string[];
  derivation?: string | null;
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
  actions?: PlannerAction[];
  taskState?: TaskState;
  releaseDecision?: ReleaseDecision;
  claimLedger?: ClaimSupport[];
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
      detail?: string;
      status: "active" | "completed" | "failed" | "cancelled";
      elapsedMs?: number;
      phase?: LiveTrailPhase;
      kind?: LiveTrailKind;
      operationId?: string;
      sourceTitle?: string;
      sourceHost?: string;
      sourceUrl?: string;
      sourceType?: string;
      count?: number;
    }>;
    durationMs?: number;
    sourcesFound?: number;
    sourcesRead?: number;
    citationsUsed?: number;
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
  actions?: PlannerAction[] | null;
  task_state?: TaskState | null;
  release_decision?: ReleaseDecision | null;
  claim_ledger?: ClaimSupport[] | null;
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


export type LiveTrailPhase = "understand" | "search" | "verify" | "compose";
export type LiveTrailKind = "milestone" | "operation" | "evidence";

export interface LiveTrailMetadata {
  schema_version?: number;
  event_id?: string;
  phase?: LiveTrailPhase;
  kind?: LiveTrailKind;
  operation_id?: string;
  operation_status?: "started" | "completed" | "failed" | "cancelled";
  source_id?: string;
  source_title?: string;
  source_host?: string;
  source_url?: string;
  source_type?: "knowledge" | "official" | "companion" | "web";
  sources_found?: number;
  sources_read?: number;
  num_results?: number;
  result_count?: number;
  citation_count?: number;
  mode?: string;
  duration_ms?: number;
  status?: string;
  channel?: string;
  provider?: string;
  skill?: string;
  source_preview?: string;
}

export interface ActivityEvent {
  requestId: string;
  runId?: string;
  event: string;
  message: string;
  elapsedMs?: number;
  metadata?: LiveTrailMetadata & Record<string, string | number | boolean | null>;
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
