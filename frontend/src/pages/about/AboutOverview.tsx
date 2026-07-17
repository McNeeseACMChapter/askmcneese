import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { CommandChain } from "../../components/about/CommandChain";
import { AppIcon } from "../../components/ui/AppIcon";
import { aboutPurpose } from "../../content/about";

/**
 * Single About page: team chain of command, then a short “what it does.”
 */
export function AboutOverview() {
  return (
    <div className="space-y-14 md:space-y-16">
      <CommandChain />

      <section aria-labelledby="about-what-title" className="mx-auto max-w-prose">
        <h2
          id="about-what-title"
          className="mb-4 text-center font-editorial text-[var(--type-section-title)] font-semibold text-text-primary"
        >
          {aboutPurpose.heading}
        </h2>
        <div className="space-y-4">
          {aboutPurpose.paragraphs.map((paragraph) => (
            <p key={paragraph.slice(0, 48)} className="leading-relaxed text-text-secondary">
              {paragraph}
            </p>
          ))}
        </div>
        <p className="mt-8 text-center">
          <Link
            to="/ask"
            className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-brand-700 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus"
          >
            Ask a question
            <AppIcon icon={ArrowRight} size={16} />
          </Link>
        </p>
      </section>
    </div>
  );
}
