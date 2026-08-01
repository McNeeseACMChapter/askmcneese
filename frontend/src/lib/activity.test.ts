import { beforeEach, describe, expect, it } from "vitest";
import {
  mapActivityPayload,
  mapLegacyStep,
  sanitizeActivityMessage,
} from "../lib/activity";
import { normalizeAskResponse, normalizeChatMessage } from "../lib/answerModel";
import type { ChatMessage } from "../types";

describe("activity sanitization", () => {
  it("maps activity payload and strips sensitive metadata", () => {
    const event = mapActivityPayload({
      request_id: "q-1",
      event: "retrieval.started",
      message: "Searching trusted McNeese sources",
      elapsed_ms: 12,
      metadata: {
        sources_found: 2,
        secret_path: "C:\\Users\\secret\\db",
        mode: "knowledge_base",
        skill: "kb_retrieve",
      },
    });
    expect(event.requestId).toBe("q-1");
    expect(event.event).toBe("retrieval.started");
    expect(event.message).toBe("Searching trusted McNeese sources");
    expect(event.metadata).toEqual({
      sources_found: 2,
      mode: "knowledge_base",
      skill: "kb_retrieve",
    });
  });

  it("prefers backend-safe messages when present", () => {
    const event = mapActivityPayload({
      event: "answer.generating",
      message: "Writing your answer from 3 sources",
    });
    expect(event.message).toBe("Writing your answer from 3 sources");
  });

  it("uses trust-calibrated fallbacks when message is missing", () => {
    expect(sanitizeActivityMessage("", "query.analyzing")).toBe(
      "Understanding what you need",
    );
    expect(sanitizeActivityMessage(null, "retrieval.source_found")).toBe(
      "Reading a relevant source",
    );
    expect(sanitizeActivityMessage(undefined, "answer.completed")).toBe("Answer ready");
  });

  it("replaces sensitive messages with request.failed fallback", () => {
    expect(sanitizeActivityMessage("API_KEY=abc /.env failed", "request.failed")).toBe(
      "The request could not finish",
    );
  });

  it("uses a safe generic fallback for unknown events", () => {
    expect(sanitizeActivityMessage("", "custom.unknown")).toBe("Working on your answer");
  });

  it("maps legacy steps into activity events", () => {
    const event = mapLegacyStep(
      { step: "generation", status: "started", message: "Generating answer..." },
      "q-2",
    );
    expect(event.event).toBe("answer.started");
    expect(event.requestId).toBe("q-2");
  });

  it("normalizes top-level phase/kind into metadata", () => {
    const event = mapActivityPayload({
      request_id: "q-1",
      event: "retrieval.source_found",
      message: "Reading a relevant source",
      phase: "search",
      kind: "evidence",
      source_title: "Academic Calendar",
      source_host: "mcneese.edu",
    });
    expect(event.metadata?.phase).toBe("search");
    expect(event.metadata?.kind).toBe("evidence");
    expect(event.metadata?.source_title).toBe("Academic Calendar");
  });
});

describe("answer normalization", () => {
  it("preserves legacy answer field", () => {
    const structured = normalizeAskResponse({
      question: "When is the deadline?",
      answer: "## Deadline\n\nAugust 1.",
      num_results: 2,
      answer_type: "deadline",
      important_dates: [{ label: "Deadline", value: "August 1" }],
    });
    expect(structured.contentMarkdown).toContain("August 1");
    expect(structured.importantDates).toHaveLength(1);
  });

  it("handles empty sources without inventing citations", () => {
    const structured = normalizeAskResponse({
      question: "q",
      answer: "No sources.",
      num_results: 0,
    });
    expect(structured.sources).toEqual([]);
  });

  it("uses chat message structured payload when present", () => {
    const message: ChatMessage = {
      id: "1",
      role: "assistant",
      text: "Apply then wait.",
      structured: {
        type: "process",
        contentMarkdown: "Apply then wait.",
        keyFacts: [],
        importantDates: [],
        requirements: [],
        steps: ["Apply", "Wait"],
        warnings: [],
        relatedQuestions: [],
        sources: [],
      },
    };
    expect(normalizeChatMessage(message).steps).toEqual(["Apply", "Wait"]);
  });
});

describe("sidebar storage key", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("uses askmcneese_conversations key namespace", () => {
    expect(localStorage.getItem("askmcneese_conversations")).toBeNull();
  });
});
