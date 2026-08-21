import { describe, expect, it } from "vitest";
import {
  CANONICAL_STEP_COUNT,
  normalizeStepId,
  resolveStep,
  TOUR_STEPS,
} from "./tourSteps";

describe("tourSteps", () => {
  it("uses one canonical sequence on every viewport", () => {
    expect(TOUR_STEPS).toHaveLength(CANONICAL_STEP_COUNT);
    expect(CANONICAL_STEP_COUNT).toBe(14);
    expect(TOUR_STEPS.at(-1)?.id).toBe("complete");
    expect(TOUR_STEPS.some((step) => step.id === "menu")).toBe(false);
  });

  it("maps mobile Ask to the brand/logo target without changing step count", () => {
    const ask = TOUR_STEPS.find((step) => step.id === "ask");
    expect(ask).toBeTruthy();
    expect(resolveStep(ask!, true).targetId).toBe("logo");
    expect(resolveStep(ask!, false).targetId).toBe("ask");
  });

  it("normalizes legacy step ids for resume", () => {
    expect(normalizeStepId("menu")).toBe("class_planner");
    expect(normalizeStepId("about_scroll")).toBe("about");
    expect(normalizeStepId("about_reading")).toBe("about");
  });

  it("defines completeRoute for action-driven navigation steps", () => {
    const updates = TOUR_STEPS.find((step) => step.id === "updates");
    const usage = TOUR_STEPS.find((step) => step.id === "usage");
    expect(updates?.completeRoute).toBe("/updates");
    expect(usage?.completeRoute).toBe("/status");
    expect(updates?.actionHint).toMatch(/Tap Updates/i);
  });
});
