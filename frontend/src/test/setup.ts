import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

class IntersectionObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() {
    return [];
  }
}

if (typeof window !== "undefined") {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  if (typeof window.IntersectionObserver === "undefined") {
    // @ts-expect-error test polyfill
    window.IntersectionObserver = IntersectionObserverStub;
  }

  window.scrollTo = () => undefined;
}
