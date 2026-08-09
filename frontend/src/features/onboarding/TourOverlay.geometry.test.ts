import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { annotationLayout, tetherPath, TourOverlay, type SpotlightRect } from "./TourOverlay";
import { TOUR_STEPS } from "./tourSteps";

function setViewport(width: number, height: number) {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
  Object.defineProperty(window, "innerHeight", { configurable: true, value: height });
}

const box = { top: 0, left: 0, width: 330, height: 180 } as DOMRect;

describe("walkthrough annotation geometry", () => {
  beforeEach(() => setViewport(1280, 720));

  it("keeps a working skip control inside every walkthrough card", () => {
    const onSkip = vi.fn();
    class ResizeObserverStub {
      observe() {}
      disconnect() {}
      unobserve() {}
    }
    vi.stubGlobal("ResizeObserver", ResizeObserverStub);
    render(React.createElement(TourOverlay, {
      open: true,
      phase: "active",
      step: TOUR_STEPS[1],
      stepNumber: 2,
      stepCount: TOUR_STEPS.length,
      isMobile: false,
      rect: { top: 80, left: 20, width: 48, height: 48 },
      interactiveTarget: true,
      drawerOpen: false,
      readingMode: false,
      showAck: false,
      onAck: vi.fn(),
      onSkip,
      onTargetClick: vi.fn(),
    }));

    fireEvent.click(screen.getByRole("button", { name: "Skip walkthrough" }));
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it("places a desktop card fully outside a target when side space exists", () => {
    const target: SpotlightRect = { top: 120, left: 100, width: 400, height: 400 };
    const layout = annotationLayout(target, false, box);
    expect(layout.placement).toBe("side-right");
    expect(Number(layout.style.left)).toBeGreaterThanOrEqual(target.left + target.width + 24);
  });

  it("places the mobile card below a top target without overlap", () => {
    setViewport(390, 844);
    const target: SpotlightRect = { top: 70, left: 16, width: 56, height: 56 };
    const mobileBox = { ...box, width: 320, height: 210 } as DOMRect;
    const layout = annotationLayout(target, true, mobileBox);
    expect(layout.placement).toBe("dock-top");
    expect(Number(layout.style.top)).toBeGreaterThanOrEqual(target.top + target.height + 18);
    expect(Number(layout.style.left)).toBeGreaterThanOrEqual(14);
  });

  it("does not draw a misleading connector through an overlapping card", () => {
    const target: SpotlightRect = { top: 100, left: 100, width: 240, height: 180 };
    const overlapping = { top: 160, left: 260, width: 368, height: 200 } as DOMRect;
    expect(tetherPath(target, overlapping)).toBeNull();
  });

  it("ends the pointer immediately outside the spotlight boundary", () => {
    const target: SpotlightRect = { top: 100, left: 700, width: 80, height: 80 };
    const card = { top: 100, left: 300, width: 330, height: 180 } as DOMRect;
    const tether = tetherPath(target, card);
    expect(tether).not.toBeNull();
    expect(tether!.beadX).toBeLessThan(target.left);
    expect(tether!.beadX).toBeGreaterThan(target.left - 12);
    expect(tether!.beadY).toBeGreaterThanOrEqual(target.top);
    expect(tether!.beadY).toBeLessThanOrEqual(target.top + target.height);
  });
});