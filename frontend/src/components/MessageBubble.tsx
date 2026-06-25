import type { ChatMessage, RetrievedChunk } from "../types";

function CitationBlock({ chunk, index }: { chunk: RetrievedChunk; index: number }) {
  return (
    <li className="border-l-2 border-mcneese-gold pl-3">
      <p className="whitespace-pre-wrap">{chunk.text.trim()}</p>
      <p className="mt-1.5 text-xs text-gray-500">
        <span className="font-semibold text-gray-600">[{index + 1}]</span>{" "}
        <a
          href={chunk.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-mcneese-blue underline decoration-mcneese-blue/30 underline-offset-2 hover:decoration-mcneese-blue"
        >
          {chunk.title}
        </a>
        {chunk.category && (
          <>
            {" · "}
            <span>{chunk.category}</span>
          </>
        )}
        {chunk.last_checked_date && (
          <>
            {" · "}
            <span>checked {chunk.last_checked_date}</span>
          </>
        )}
      </p>
    </li>
  );
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const hasCitations = !isUser && message.citations && message.citations.length > 0;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm leading-relaxed shadow-sm ${
          isUser
            ? "rounded-br-sm bg-mcneese-blue text-white"
            : "rounded-bl-sm border border-gray-200 bg-white text-gray-800"
        }`}
      >
        {message.isDemo && !isUser && (
          <span className="mb-1 block text-[10px] font-bold uppercase tracking-wide text-mcneese-gold">
            Demo
          </span>
        )}

        {hasCitations ? (
          <div className="space-y-3">
            {message.text && <p>{message.text}</p>}
            <ul className="space-y-3">
              {message.citations!.map((chunk, index) => (
                <CitationBlock key={chunk.chunk_id} chunk={chunk} index={index} />
              ))}
            </ul>
          </div>
        ) : (
          message.text
        )}
      </div>
    </div>
  );
}
