import "@testing-library/jest-dom/vitest";
import { createElement, type CSSProperties } from "react";
import { vi } from "vitest";

/** jsdom has no real canvas — stub ECharts so route tests stay stable. */
vi.mock("echarts-for-react", () => ({
  default: ({ style, option }: { style?: CSSProperties; option?: unknown }) =>
    createElement("div", {
      "data-testid": "echarts-stub",
      "data-has-option": option ? "true" : "false",
      style: {
        height: style?.height ?? 200,
        width: style?.width ?? "100%",
        background: "rgba(14,76,146,0.06)",
      },
      role: "img",
      "aria-label": "Chart",
    }),
}));
