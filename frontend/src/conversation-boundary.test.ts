import { describe, expect, it } from "vitest";
import { canApplyPlannerAction, shouldUseConversationHistory } from "./App";

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
    expect(shouldUseConversationHistory("61066 i want to ragister this calculus course")).toBe(true);
    expect(shouldUseConversationHistory("Put CRNs 61154 and 61200 in Class Planner")).toBe(true);
  });

  it("treats a named degree question as standalone", () => {
    expect(shouldUseConversationHistory("What courses are required for mechanical engineering?")).toBe(false);
  });
});

describe("Class Planner action boundary", () => {
  const base = {
    type: "class_planner_add" as const,
    term_id: "202660",
    sections: [],
  };

  it("requires server confirmation and compatible validation", () => {
    expect(canApplyPlannerAction(base)).toBe(false);
    expect(canApplyPlannerAction({ ...base, confirmed: true })).toBe(false);
    expect(canApplyPlannerAction({
      ...base,
      confirmed: true,
      validation_status: "UNCERTAIN",
    })).toBe(false);
    expect(canApplyPlannerAction({
      ...base,
      confirmed: true,
      validation_status: "COMPATIBLE",
    })).toBe(true);
  });
});
