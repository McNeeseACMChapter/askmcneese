import type {
  AnswerType,
  AskResponse,
  ChatMessage,
  Citation,
  StructuredAnswer,
} from "../types";

const ANSWER_TYPES = new Set<AnswerType>([
  "factual",
  "deadline",
  "process",
  "comparison",
  "location",
  "no_source",
  "partial",
  "backend_failure",
  "clarification",
  "conversational",
]);

function citationsFromResponse(response: AskResponse): Citation[] {
  if (response.sources?.length) return response.sources;
  return (response.chunks ?? []).map((chunk) => ({
    id: chunk.chunk_id,
    title: chunk.title,
    url: chunk.source_url,
    snippet: chunk.text.slice(0, 200),
  }));
}

function inferredType(response: AskResponse, content: string): AnswerType {
  if (response.answer_type && ANSWER_TYPES.has(response.answer_type)) return response.answer_type;
  if (!content) return "backend_failure";
  if ((response.num_results ?? 0) === 0) return "no_source";
  return "factual";
}

export function normalizeAskResponse(response: AskResponse): StructuredAnswer {
  const content = response.content_markdown ?? response.answer ?? response.text ?? "";
  return {
    type: inferredType(response, content),
    title: response.title ?? undefined,
    summary: response.summary ?? undefined,
    contentMarkdown: content,
    keyFacts: response.key_facts ?? [],
    importantDates: response.important_dates ?? [],
    requirements: response.requirements ?? [],
    steps: response.steps ?? [],
    warnings: response.warnings ?? [],
    relatedQuestions: response.related_questions ?? [],
    confidence: response.confidence,
    sources: citationsFromResponse(response),
  };
}

export function normalizeChatMessage(message: ChatMessage): StructuredAnswer {
  if (message.structured) {
    return {
      ...message.structured,
      contentMarkdown: message.structured.contentMarkdown || message.text,
      sources: message.structured.sources.length
        ? message.structured.sources
        : message.citations ?? [],
    };
  }
  return {
    type: message.isError ? "backend_failure" : "factual",
    contentMarkdown: message.text,
    keyFacts: [],
    importantDates: [],
    requirements: [],
    steps: [],
    warnings: [],
    relatedQuestions: [],
    confidence: message.confidence,
    sources: message.citations ?? [],
  };
}
