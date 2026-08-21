import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
  /** When true, markdown h1 becomes a section heading instead of the primary title. */
  hasTitle?: boolean;
}

function buildComponents(hasTitle: boolean): Components {
  return {
    h1: ({ children }) =>
      hasTitle ? (
        <h2 className="answerSectionTitle">{children}</h2>
      ) : (
        <h1 className="answerTitle">{children}</h1>
      ),
    h2: ({ children }) => <h2 className="answerSectionTitle">{children}</h2>,
    h3: ({ children }) => <h3 className="answerSubsectionTitle">{children}</h3>,
    h4: ({ children }) => <h4 className="answerSubsectionTitle">{children}</h4>,
    p: ({ children }) => <p className="answerBody">{children}</p>,
    ul: ({ children }) => <ul className="answerList list-disc">{children}</ul>,
    ol: ({ children }) => <ol className="answerList list-decimal">{children}</ol>,
    blockquote: ({ children }) => <blockquote className="answerQuote">{children}</blockquote>,
    strong: ({ children }) => <strong className="answerEmphasis">{children}</strong>,
    small: ({ children }) => <small className="answerMetadata">{children}</small>,
    table: ({ children }) => (
      <div className="overflow-x-auto">
        <table className="answerTable">{children}</table>
      </div>
    ),
    a: ({ children, href }) => (
      <a href={href} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    ),
    img: () => null,
  };
}

export function MarkdownRenderer({
  content,
  className = "",
  hasTitle = false,
}: MarkdownRendererProps) {
  return (
    <div className={`prose-answer ${className}`.trim()}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml components={buildComponents(hasTitle)}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
