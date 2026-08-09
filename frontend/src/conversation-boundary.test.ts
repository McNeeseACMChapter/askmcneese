import { describe, expect, it } from "vitest";
import { shouldUseConversationHistory } from "./App";

describe("conversation history boundary", () => {
  it("does not funnel an independent new topic through the previous answer", () => {
    expect(shouldUseConversationHistory("Who is Dr. Vipin Menon?" )).toBe(false);
    expect(shouldUseConversationHistory("What student jobs are available now?")).toBe(false);
    expect(shouldUseConversationHistory("When does Summer 2026 end?")).toBe(false);
  });

  it("keeps history only for prompts that explicitly depend on it", () => {
    expect(shouldUseConversationHistory("What about parking there?")).toBe(true);
    expect(shouldUseConversationHistory("Tell me more about that")).toBe(true);
    expect(shouldUseConversationHistory("How many 400 level courses do I need?")).toBe(true);
  });

  it("treats a named degree question as standalone", () => {
    expect(shouldUseConversationHistory("What courses are required for mechanical engineering?")).toBe(false);
  });
});