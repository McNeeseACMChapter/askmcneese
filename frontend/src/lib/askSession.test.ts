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

  it("never replaces another turn's provisional assistant", () => {
    const older: ChatMessage = {
      id: "a-old",
      role: "assistant",
      text: "",
      isStreaming: true,
    };
    const response: ChatMessage = {
      id: "a-new",
      role: "assistant",
      text: "New answer",
    };
    expect(mergeAskResult([user, older], response)).toEqual([user, older, response]);
  });

  it("preserves 100 sequential user-assistant turn pairs without duplicates", () => {
    let messages: ChatMessage[] = [];
    for (let index = 0; index < 100; index += 1) {
      const userTurn: ChatMessage = {
        id: `u-${index}`,
        role: "user",
        text: `Question ${index}`,
      };
      const pending: ChatMessage = {
        id: `a-${index}`,
        role: "assistant",
        text: "",
        isStreaming: true,
      };
      messages = [...messages, userTurn, pending];
      messages = mergeAskResult(messages, {
        ...pending,
        text: `Answer ${index}`,
        isStreaming: false,
      });
    }
    expect(messages).toHaveLength(200);
    for (let index = 0; index < 100; index += 1) {
      expect(messages[index * 2].id).toBe(`u-${index}`);
      expect(messages[index * 2 + 1].id).toBe(`a-${index}`);
      expect(messages[index * 2 + 1].isStreaming).toBe(false);
    }
  });

  it("preserves turn ownership under out-of-order and replayed final responses", () => {
    let messages: ChatMessage[] = [];
    for (let index = 0; index < 20; index += 1) {
      messages.push(
        { id: `u-random-${index}`, role: "user", text: `Question ${index}` },
        { id: `a-random-${index}`, role: "assistant", text: "", isStreaming: true },
      );
    }
    const completionOrder = [7, 1, 18, 3, 12, 0, 19, 5, 14, 8, 2, 16, 4, 11, 6, 17, 9, 15, 10, 13];
    for (const index of completionOrder) {
      const response: ChatMessage = {
        id: `a-random-${index}`,
        role: "assistant",
        text: `Answer ${index}`,
        isStreaming: false,
      };
      messages = mergeAskResult(messages, response);
      messages = mergeAskResult(messages, response);
    }
    expect(messages).toHaveLength(40);
    for (let index = 0; index < 20; index += 1) {
      expect(messages[index * 2].id).toBe(`u-random-${index}`);
      expect(messages[index * 2 + 1].id).toBe(`a-random-${index}`);
      expect(messages[index * 2 + 1].text).toBe(`Answer ${index}`);
    }
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
