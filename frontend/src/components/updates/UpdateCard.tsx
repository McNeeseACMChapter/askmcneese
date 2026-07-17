import type { UpdateItem } from "../../content/updates";

interface UpdateCardProps {
  update: UpdateItem;
  featured?: boolean;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export function UpdateCard({ update, featured = false }: UpdateCardProps) {
  return (
    <article
      className={`group -mx-4 rounded-xl px-4 py-5 transition-colors hover:bg-brand-50/50 md:-mx-6 md:px-6 ${
        featured ? "md:py-8" : ""
      }`}
    >
      <header className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-text-muted">
        <time dateTime={update.date}>{formatDate(update.date)}</time>
        <span aria-hidden="true">·</span>
        <span className="font-medium text-brand-700">{update.category}</span>
      </header>

      <h2
        className={`font-editorial font-semibold text-text-primary ${
          featured ? "text-2xl md:text-3xl" : "text-xl"
        }`}
      >
        {update.title}
      </h2>
      <p
        className={`mt-2 leading-relaxed text-text-secondary ${
          featured ? "text-lg" : "text-base"
        }`}
      >
        {update.summary}
      </p>
    </article>
  );
}
