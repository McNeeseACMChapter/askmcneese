import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AboutOverview } from "./pages/about/AboutOverview";
import { AnimatedMetric } from "./components/motion/AnimatedMetric";
import { AppIcon } from "./components/ui/AppIcon";
import { MethodologyStory } from "./components/motion/MethodologyStory";
import { StaggerGroup } from "./components/motion/StaggerGroup";
import { LottieScene } from "./components/motion/LottieScene";
import { UpdatesPage } from "./pages/UpdatesPage";
import { methodologyContent } from "./content/about";
import { ArrowRight, Check } from "lucide-react";
import * as gsapLib from "./lib/gsap";

vi.mock("framer-motion", async () => {
  const React = await import("react");
  const passthrough =
    (tag: string) =>
    ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) =>
      React.createElement(tag, props, children);
  return {
    motion: {
      div: passthrough("div"),
      p: passthrough("p"),
      span: passthrough("span"),
      article: passthrough("article"),
      button: passthrough("button"),
      ul: passthrough("ul"),
      li: passthrough("li"),
      section: passthrough("section"),
      a: passthrough("a"),
      h1: passthrough("h1"),
    },
    AnimatePresence: ({ children }: React.PropsWithChildren) => children,
    LayoutGroup: ({ children }: React.PropsWithChildren) => children,
    useMotionValue: (initial: number) => ({
      set: vi.fn(),
      get: () => initial,
    }),
    useMotionValueEvent: () => undefined,
    animate: (_from: number, to: number, opts?: { onUpdate?: (n: number) => void; onComplete?: () => void }) => {
      opts?.onUpdate?.(to);
      opts?.onComplete?.();
      return { stop: vi.fn() };
    },
  };
});

vi.mock("animejs", () => ({
  animate: vi.fn(),
  stagger: (n: number) => n,
}));

vi.mock("@gsap/react", () => ({
  useGSAP: (fn: () => void | (() => void)) => {
    const cleanup = fn();
    return typeof cleanup === "function" ? cleanup : undefined;
  },
}));

vi.mock("./lib/gsap", async () => {
  const triggers: Array<{ kill: () => void; trigger?: unknown }> = [];
  const ScrollTrigger = {
    create: (config: Record<string, unknown>) => {
      const t = { kill: vi.fn(), trigger: config.trigger };
      triggers.push(t);
      return t;
    },
    getAll: () => triggers,
    refresh: vi.fn(),
  };
  return {
    ensureGsap: () => ({
      gsap: {
        fromTo: vi.fn(),
        matchMedia: () => ({
          add: (_q: string, cb: () => void | (() => void)) => {
            const cleanup = cb();
            return typeof cleanup === "function" ? cleanup : undefined;
          },
          revert: vi.fn(),
        }),
      },
      ScrollTrigger,
    }),
    prefersReducedMotion: () => false,
    isDesktopScrollStory: () => true,
    gsap: {},
    ScrollTrigger,
  };
});

describe("Motion", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: query.includes("prefers-reduced-motion") ? false : true,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("methodology content remains available for story components", () => {
    render(<MethodologyStory steps={methodologyContent.steps} intro="Intro copy" />);
    for (const step of methodologyContent.steps) {
      expect(screen.getByRole("heading", { name: step.title })).toBeInTheDocument();
    }
    expect(screen.getByText("Intro copy")).toBeInTheDocument();
  });

  it("MethodologyStory keeps all steps in reading order", () => {
    render(<MethodologyStory steps={methodologyContent.steps} intro="Intro copy" />);
    const items = document.querySelectorAll("[data-method-step]");
    expect(items).toHaveLength(methodologyContent.steps.length);
    expect(screen.getByText("Intro copy")).toBeInTheDocument();
  });

  it("AnimatedMetric exposes the final formatted value", async () => {
    const { rerender } = render(<AnimatedMetric value={10} format={(n) => String(Math.round(n))} />);
    expect(screen.getByLabelText("10")).toBeInTheDocument();
    rerender(<AnimatedMetric value={42} format={(n) => String(Math.round(n))} />);
    await waitFor(() => {
      expect(screen.getByLabelText("42")).toBeInTheDocument();
    });
  });

  it("AnimatedMetric jumps immediately under reduced motion", () => {
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: query.includes("prefers-reduced-motion"),
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    );
    render(<AnimatedMetric value={99} />);
    expect(screen.getByLabelText("99")).toBeInTheDocument();
  });

  it("About page shows team chain and what it does", () => {
    render(
      <MemoryRouter>
        <AboutOverview />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /Who steers AskMcNeese/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /What AskMcNeese does/i })).toBeInTheDocument();
    expect(screen.getAllByText(/Prince Pudasaini/i).length).toBeGreaterThan(0);
  });

  it("updates remain visible without Anime.js execution", () => {
    render(
      <MemoryRouter>
        <UpdatesPage />
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { name: /Built in public/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Explore the work behind the product/i })).toBeInTheDocument();
  });

  it("LottieScene shows accessible fallback when asset is missing", () => {
    render(<LottieScene label="Methodology diagram" />);
    expect(screen.getByRole("img", { name: /Methodology diagram/i })).toBeInTheDocument();
    expect(screen.getByText(/approved Lottie asset not provided/i)).toBeInTheDocument();
  });

  it("AppIcon renders Lucide icons only", () => {
    const { container } = render(
      <>
        <AppIcon icon={ArrowRight} />
        <AppIcon icon={Check} />
      </>,
    );
    expect(container.querySelectorAll("svg")).toHaveLength(2);
  });

  it("StaggerGroup reveals items when IntersectionObserver is unavailable", () => {
    const original = window.IntersectionObserver;
    // @ts-expect-error test deletion
    delete window.IntersectionObserver;
    render(
      <StaggerGroup>
        <div data-stagger-item>Card A</div>
        <div data-stagger-item>Card B</div>
      </StaggerGroup>,
    );
    expect(screen.getByText("Card A")).toBeVisible();
    expect(screen.getByText("Card B")).toBeVisible();
    window.IntersectionObserver = original;
  });

  it("gsap ensure module is importable for route cleanup patterns", () => {
    const api = gsapLib.ensureGsap();
    expect(api.ScrollTrigger).toBeTruthy();
    expect(typeof api.ScrollTrigger.create).toBe("function");
  });
});

describe("ask route code splitting", () => {
  it("ChatPage source does not import Methodology/GSAP/Lottie", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const chatPath = path.resolve(__dirname, "components/chat/ChatPage.tsx");
    const chat = fs.readFileSync(chatPath, "utf8");
    expect(chat).not.toMatch(/MethodologyStory|lottie-web|@gsap\/react|from ["']gsap/);
  });

  it("App lazy-loads About overview route", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const app = fs.readFileSync(path.resolve(__dirname, "App.tsx"), "utf8");
    expect(app).toMatch(/lazy\(\(\) =>[\s\S]*AboutOverview/);
    expect(app).not.toMatch(/import \{ AboutOverview \}/);
    expect(app).not.toMatch(/AboutMethodology|AboutRoadmap|AboutAdvisor|AboutTeam/);
  });

  it("production components do not import banned icon libraries", async () => {
    const fs = await import("node:fs");
    const path = await import("node:path");
    const walk = (dir: string, acc: string[] = []) => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) walk(full, acc);
        else if (/\.(tsx|ts)$/.test(entry.name) && !entry.name.includes(".test.")) acc.push(full);
      }
      return acc;
    };
    const files = walk(path.resolve(__dirname));
    const banned = /@heroicons|fontawesome|@fortawesome|material-symbols|@mui\/icons|@tabler\/icons/;
    const offenders = files.filter((file) => banned.test(fs.readFileSync(file, "utf8")));
    expect(offenders).toEqual([]);
  });
});
