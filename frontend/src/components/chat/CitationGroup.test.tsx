import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import {
  CitationGroup,
  dedupeCitations,
  domainInitial,
  normalizeCitationUrl,
} from "./CitationGroup";
import type { Citation } from "../../types";

function cite(partial: Partial<Citation> & Pick<Citation, "id" | "title" | "url">): Citation {
  return partial;
}

describe("normalizeCitationUrl", () => {
  it("normalizes trailing slash and hostname casing", () => {
    expect(normalizeCitationUrl("HTTPS://WWW.McNeese.EDU/admissions/")).toBe(
      "https://www.mcneese.edu/admissions",
    );
  });

  it("returns null for malformed URLs without throwing", () => {
    expect(normalizeCitationUrl("not a url")).toBeNull();
    expect(normalizeCitationUrl("")).toBeNull();
    expect(normalizeCitationUrl(undefined)).toBeNull();
  });
});

describe("dedupeCitations", () => {
  it("keeps same-title citations with different URLs", () => {
    const result = dedupeCitations([
      cite({ id: "1", title: "Admissions", url: "https://www.mcneese.edu/admissions" }),
      cite({ id: "2", title: "Admissions", url: "https://www.mcneese.edu/admissions/transfer" }),
    ]);
    expect(result).toHaveLength(2);
  });

  it("collapses trailing-slash duplicates to the first occurrence", () => {
    const first = cite({ id: "1", title: "Admissions", url: "https://www.mcneese.edu/admissions" });
    const second = cite({ id: "2", title: "Admissions Page", url: "https://www.mcneese.edu/admissions/" });
    const result = dedupeCitations([first, second]);
    expect(result).toHaveLength(1);
    expect(result[0].id).toBe("1");
  });

  it("preserves first occurrence for identical normalized URLs", () => {
    const result = dedupeCitations([
      cite({ id: "a", title: "A", url: "https://www.mcneese.edu/finaid" }),
      cite({ id: "b", title: "B", url: "https://www.mcneese.edu/finaid" }),
    ]);
    expect(result).toEqual([
      cite({ id: "a", title: "A", url: "https://www.mcneese.edu/finaid" }),
    ]);
  });

  it("does not crash on malformed URLs and keeps distinct fallbacks", () => {
    const result = dedupeCitations([
      cite({ id: "1", title: "Broken", url: "not-a-url" }),
      cite({ id: "2", title: "Broken", url: "also-broken" }),
      cite({ id: "3", title: "Broken", url: "not-a-url" }),
    ]);
    expect(result).toHaveLength(2);
    expect(result.map((c) => c.id)).toEqual(["1", "2"]);
  });
});

describe("CitationGroup", () => {
  it("stays collapsed by default and reveals both same-title citations on expand", async () => {
    const user = userEvent.setup();
    render(
      <CitationGroup
        citations={[
          cite({ id: "1", title: "Admissions", url: "https://www.mcneese.edu/admissions" }),
          cite({ id: "2", title: "Admissions", url: "https://www.mcneese.edu/admissions/transfer" }),
        ]}
      />,
    );
    expect(screen.getByRole("button", { name: /Sources/i })).toBeInTheDocument();
    expect(screen.queryByText("Admissions")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Sources/i }));
    await waitFor(() => {
      expect(screen.getAllByText("Admissions")).toHaveLength(2);
    });
  });

  it("exposes a domain initial for compact mobile chips", () => {
    expect(domainInitial("https://www.mcneese.edu/admissions")).toBe("M");
    expect(domainInitial("https://louisiana.gov/aid")).toBe("L");
  });
});
