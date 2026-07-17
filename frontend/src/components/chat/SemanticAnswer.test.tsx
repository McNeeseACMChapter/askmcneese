import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MarkdownRenderer } from "../../lib/markdown";
import { prepareAnswerView } from "../../lib/answerSections";
import { SemanticAnswer } from "./SemanticAnswer";
import type { ChatMessage, StructuredAnswer } from "../../types";

describe("MarkdownRenderer", () => {
  it("renders headings instead of raw hash symbols", () => {
    render(<MarkdownRenderer content={"# Admissions\n\nApply online."} />);
    expect(screen.getByRole("heading", { name: "Admissions" })).toBeInTheDocument();
    expect(screen.queryByText(/# Admissions/)).not.toBeInTheDocument();
  });

  it("maps h1 to section title when a primary title already exists", () => {
    render(<MarkdownRenderer content={"# Extra heading\n\nBody."} hasTitle />);
    expect(screen.getByRole("heading", { name: "Extra heading" })).toHaveClass("answerSectionTitle");
  });

  it("renders lists and emphasis", () => {
    render(<MarkdownRenderer content={"- One\n- Two\n\n**Bold**"} />);
    expect(screen.getByText("One")).toBeInTheDocument();
    expect(screen.getByText("Bold").tagName).toBe("STRONG");
    expect(screen.getByText("Bold")).toHaveClass("answerEmphasis");
  });
});

describe("prepareAnswerView", () => {
  const base: StructuredAnswer = {
    type: "factual",
    contentMarkdown: "The main McNeese phone number is 337-475-5000.",
    keyFacts: [{ label: "Phone", value: "337-475-5000" }],
    importantDates: [],
    requirements: ["Must apply"],
    steps: ["Call the office"],
    warnings: [],
    relatedQuestions: [],
    sources: [],
  };

  it("suppresses key-fact / requirements / single-step cards for simple factual answers", () => {
    const view = prepareAnswerView(base);
    expect(view.showKeyFacts).toBe(false);
    expect(view.showRequirements).toBe(false);
    expect(view.showSteps).toBe(false);
  });

  it("keeps multi-step process sections", () => {
    const view = prepareAnswerView({
      ...base,
      type: "process",
      contentMarkdown: "Change your major in three steps.",
      steps: ["Meet your advisor.", "Submit the form.", "Confirm in Banner."],
      requirements: [],
      keyFacts: [],
    });
    expect(view.showSteps).toBe(true);
  });
});

describe("SemanticAnswer", () => {
  it("renders no-source pattern without empty fact cards", () => {
    const message: ChatMessage = {
      id: "a1",
      role: "assistant",
      text: "I couldn't find relevant information.",
      structured: {
        type: "no_source",
        contentMarkdown: "I couldn't find relevant information.",
        keyFacts: [],
        importantDates: [],
        requirements: [],
        steps: [],
        warnings: [],
        relatedQuestions: [],
        sources: [],
      },
    };
    render(<SemanticAnswer message={message} />);
    expect(screen.getByText(/couldn't find relevant information/i)).toBeInTheDocument();
    expect(screen.queryByText("Key facts")).not.toBeInTheDocument();
    expect(screen.queryByText("Requirements")).not.toBeInTheDocument();
  });

  it("renders date callout only when deadline data exists", () => {
    const message: ChatMessage = {
      id: "a2",
      role: "assistant",
      text: "## Deadline\n\nSubmit by August 1.",
      structured: {
        type: "deadline",
        title: "Deadline",
        contentMarkdown: "## Deadline\n\nSubmit by August 1.",
        keyFacts: [],
        importantDates: [{ label: "Application deadline", value: "August 1" }],
        requirements: [],
        steps: [],
        warnings: [],
        relatedQuestions: [],
        sources: [{ id: "1", title: "Admissions", url: "https://www.mcneese.edu/admissions" }],
      },
    };
    render(<SemanticAnswer message={message} />);
    expect(screen.getByText("Important dates")).toBeInTheDocument();
    expect(screen.getByText("August 1")).toBeInTheDocument();
    expect(screen.getByText(/Sources · 1/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Deadline" })).toHaveClass("answerTitle");
    expect(screen.queryByText("Key facts")).not.toBeInTheDocument();
    expect(screen.queryByText("Requirements")).not.toBeInTheDocument();
    expect(screen.queryByText("Next steps")).not.toBeInTheDocument();
  });

  it("does not render key-fact cards for a simple factual answer", () => {
    const message: ChatMessage = {
      id: "a3",
      role: "assistant",
      text: "The main campus phone number is 337-475-5000.",
      structured: {
        type: "factual",
        contentMarkdown: "The main campus phone number is 337-475-5000.",
        keyFacts: [
          { label: "Phone", value: "337-475-5000" },
          { label: "  ", value: "" },
        ],
        importantDates: [],
        requirements: [],
        steps: [],
        warnings: [],
        relatedQuestions: [],
        sources: [],
      },
    };
    render(<SemanticAnswer message={message} />);
    expect(screen.getByText(/337-475-5000/)).toBeInTheDocument();
    expect(screen.queryByText("Key facts")).not.toBeInTheDocument();
    expect(screen.queryByText("Details")).not.toBeInTheDocument();
    expect(screen.queryByText("Requirements")).not.toBeInTheDocument();
  });

  it("while streaming renders body only without structured sections", () => {
    const message: ChatMessage = {
      id: "stream-1",
      role: "assistant",
      text: "## Partial\n\nStill writing",
      isStreaming: true,
      structured: {
        type: "deadline",
        title: "Should not show",
        contentMarkdown: "## Partial\n\nStill writing",
        keyFacts: [{ label: "X", value: "Y" }],
        importantDates: [{ label: "Due", value: "Tomorrow" }],
        requirements: ["A"],
        steps: [],
        warnings: [],
        relatedQuestions: [],
        sources: [{ id: "1", title: "Admissions", url: "https://www.mcneese.edu/admissions" }],
      },
    };
    render(<SemanticAnswer message={message} />);
    expect(screen.getByText(/Still writing/i)).toBeInTheDocument();
    expect(screen.queryByText("Important dates")).not.toBeInTheDocument();
    expect(screen.queryByText("Official sources")).not.toBeInTheDocument();
    expect(screen.queryByText("Should not show")).not.toBeInTheDocument();
  });
});
