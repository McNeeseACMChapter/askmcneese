import { describe, expect, it } from "vitest";
import {
  createAssistantErrorMessage,
  mergeAskResult,
  shouldIgnoreStreamUpdate,
  streamingMessageForActiveConversation,
  updateStreamingText,
  type StreamingAssistantState,
} from "./askSession";
import type { ChatMessage } from "../types";

const user: ChatMessage = {
  id: "u1",
  role: "user",
  text: "Hello",
  timestamp: new Date(),
};

describe("mergeAskResult", () => {
  it("appends a successful or error assistant message", () => {
    const error = createAssistantErrorMessage("Request failed");
    expect(mergeAskResult([user], error)).toEqual([user, error]);
  });

  it("leaves messages unchanged on abort (null response)", () => {
    expect(mergeAskResult([user], null)).toEqual([user]);
  });
});

describe("createAssistantErrorMessage", () => {
  it("uses a safe fallback when text is empty", () => {
    expect(createAssistantErrorMessage("").isError).toBe(true);
    expect(createAssistantErrorMessage("").text).toMatch(/couldn’t complete/i);
  });
});

describe("streaming provisional state", () => {
  it("updates one provisional message without duplicating", () => {
    let state: StreamingAssistantState = null;
    state = updateStreamingText(state, "r1", "c1", "Partial 1");
    state = updateStreamingText(state, "r1", "c1", "Partial 1 Partial 2");
    expect(state?.message.id).toBe("stream-r1");
    expect(state?.message.text).toBe("Partial 1 Partial 2");
    expect(state?.message.isStreaming).toBe(true);
  });

  it("keeps empty provisional messages visible for live-activity attachment", () => {
    const state = updateStreamingText(null, "r1", "c1", "", "a-stable");
    expect(streamingMessageForActiveConversation(state, "c1")?.id).toBe("a-stable");
    expect(streamingMessageForActiveConversation(state, "c1")?.text).toBe("");
  });

  it("ignores stale request updates", () => {
    const state = updateStreamingText(null, "r1", "c1", "Old");
    expect(shouldIgnoreStreamUpdate(state, "r0", "c1", "r1")).toBe(true);
    expect(shouldIgnoreStreamUpdate(state, "r1", "c1", "r1")).toBe(false);
  });
});
