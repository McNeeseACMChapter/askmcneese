import { describe, expect, it } from "vitest";
import { INITIAL_TOUR_STATE, tourReducer, type TourMachineState } from "./tourMachine";

function started(stepId: string, pathname: string, isMobile = false): TourMachineState {
  const entering = tourReducer(INITIAL_TOUR_STATE, {
    type: "START",
    stepId,
    pathname,
    isMobile,
  });
  return tourReducer(entering, { type: "ENTERED", pathname, isMobile });
}

describe("tourReducer", () => {
  it("starts the walkthrough at the requested persisted step", () => {
    const state = started("usage", "/status");
    expect(state.stepIndex).toBe(8);
    expect(state.phase).toBe("TOUR_ACTIVE");
  });

  it("advances a same-route desktop target exactly once", () => {
    const ask = started("ask", "/ask");
    const advanced = tourReducer(ask, {
      type: "TARGET",
      targetId: "ask",
      pathname: "/ask",
      isMobile: false,
    });
    expect(advanced.stepIndex).toBe(2);
    expect(advanced.phase).toBe("TOUR_ACTIVE");

    const staleDuplicate = tourReducer(advanced, {
      type: "TARGET",
      targetId: "ask",
      pathname: "/ask",
      isMobile: false,
    });
    expect(staleDuplicate).toEqual(advanced);
  });

  it("requires the mobile menu before a hidden destination can activate", () => {
    const state = started("class_planner", "/ask", true);
    expect(state.phase).toBe("DRAWER_SUBSTATE");

    const ignored = tourReducer(state, {
      type: "TARGET",
      targetId: "class-planner",
      pathname: "/ask",
      isMobile: true,
    });
    expect(ignored).toEqual(state);

    const open = tourReducer(state, {
      type: "MENU_CHANGED",
      open: true,
      pathname: "/ask",
      isMobile: true,
    });
    expect(open.phase).toBe("TOUR_ACTIVE");
  });

  it("waits for route arrival after a mobile destination click", () => {
    let state = started("class_planner", "/ask", true);
    state = tourReducer(state, {
      type: "MENU_CHANGED",
      open: true,
      pathname: "/ask",
      isMobile: true,
    });
    state = tourReducer(state, {
      type: "TARGET",
      targetId: "class-planner",
      pathname: "/ask",
      isMobile: true,
    });
    expect(state.phase).toBe("ROUTE_TRANSITION");
    expect(state.awaitedRoute).toBe("/class-planner");

    state = tourReducer(state, {
      type: "ROUTE_CHANGED",
      pathname: "/class-planner",
      isMobile: true,
    });
    expect(state.stepIndex).toBe(4);
    expect(state.phase).toBe("TOUR_ACTIVE");
  });

  it("does not let drawer closure overwrite an in-flight route transition", () => {
    const transitioning: TourMachineState = {
      ...started("usage", "/updates", true),
      phase: "ROUTE_TRANSITION",
      menuOpen: true,
      awaitedRoute: "/status",
    };
    const closed = tourReducer(transitioning, {
      type: "MENU_CHANGED",
      open: false,
      pathname: "/updates",
      isMobile: true,
    });
    expect(closed.phase).toBe("ROUTE_TRANSITION");
    expect(closed.awaitedRoute).toBe("/status");
  });

  it("enters guided reading only after About route arrives", () => {
    let state = started("about", "/class-planner");
    expect(state.phase).toBe("TOUR_ACTIVE");
    state = tourReducer(state, {
      type: "TARGET",
      targetId: "about",
      pathname: "/class-planner",
      isMobile: false,
    });
    expect(state.phase).toBe("ROUTE_TRANSITION");

    state = tourReducer(state, {
      type: "ROUTE_CHANGED",
      pathname: "/about",
      isMobile: false,
    });
    expect(state.stepIndex).toBe(6);
    expect(state.phase).toBe("GUIDED_READING");
  });

  it("does not release About before the final reading event", () => {
    const about = started("about", "/about");
    const partial = tourReducer(about, {
      type: "READ_PROGRESS",
      progress: 2,
      complete: false,
      pathname: "/about",
      isMobile: false,
    });
    expect(partial.stepIndex).toBe(6);
    expect(partial.phase).toBe("GUIDED_READING");
  });

  it("releases About deterministically at the real end", () => {
    const about = started("about", "/about");
    const done = tourReducer(about, {
      type: "READ_PROGRESS",
      progress: 3,
      complete: true,
      pathname: "/about",
      isMobile: false,
    });
    expect(done.stepIndex).toBe(7);
    expect(done.phase).toBe("TOUR_ACTIVE");
  });

  it("maps browser Back to the nearest earlier walkthrough step", () => {
    const usage = started("usage", "/status");
    const back = tourReducer(usage, {
      type: "ROUTE_CHANGED",
      pathname: "/updates",
      isMobile: false,
    });
    expect(back.stepIndex).toBe(7);
    expect(back.phase).toBe("TOUR_ACTIVE");
  });

  it("uses the real mobile History target and then owns navigation to Ask", () => {
    let state = started("conversations", "/status", true);
    expect(state.phase).toBe("DRAWER_SUBSTATE");
    state = tourReducer(state, {
      type: "MENU_CHANGED",
      open: true,
      pathname: "/status",
      isMobile: true,
    });
    state = tourReducer(state, {
      type: "TARGET",
      targetId: "conversations",
      pathname: "/status",
      isMobile: true,
    });
    expect(state.stepIndex).toBe(10);
    expect(state.phase).toBe("ROUTE_TRANSITION");
    expect(state.desiredRoute).toBe("/ask");
  });

  it("keeps desktop Conversations as an acknowledgement step", () => {
    const conversations = started("conversations", "/ask");
    const next = tourReducer(conversations, {
      type: "ACK",
      pathname: "/ask",
      isMobile: false,
    });
    expect(next.stepIndex).toBe(10);
    expect(next.phase).toBe("TOUR_ACTIVE");
  });

  it("reconciles cleanly when the viewport crosses the mobile breakpoint", () => {
    const desktop = started("updates", "/about", false);
    const mobile = tourReducer(desktop, {
      type: "ROUTE_CHANGED",
      pathname: "/about",
      isMobile: true,
    });
    expect(mobile.phase).toBe("DRAWER_SUBSTATE");

    const desktopAgain = tourReducer(mobile, {
      type: "ROUTE_CHANGED",
      pathname: "/about",
      isMobile: false,
    });
    expect(desktopAgain.phase).toBe("TOUR_ACTIVE");
  });

  it("finishes through explicit completing, exiting, and completed states", () => {
    let state = started("complete", "/feedback");
    state = tourReducer(state, { type: "COMPLETE_REQUEST" });
    expect(state.phase).toBe("TOUR_COMPLETING");
    state = tourReducer(state, { type: "COMPLETE_SUCCESS" });
    expect(state.phase).toBe("TOUR_EXITING");
    state = tourReducer(state, { type: "COMPLETE_EXITED" });
    expect(state.phase).toBe("COMPLETED");
  });
});
