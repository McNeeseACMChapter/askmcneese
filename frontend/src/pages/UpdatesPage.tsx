import { useMemo, useState } from "react";
import { LayoutGroup, motion } from "framer-motion";
import { BlurFade } from "../components/motion/BlurFade";
import { RouteEnter } from "../components/motion/RouteEnter";
import { StaggerGroup } from "../components/motion/StaggerGroup";
import { UpdateCard } from "../components/updates/UpdateCard";
import {
  featuredUpdateSlug,
  updates,
  type UpdateCategory,
  type UpdateItem,
} from "../content/updates";
import { useReducedMotion } from "../hooks/useReducedMotion";

const categories: Array<UpdateCategory | "All"> = [
  "All",
  "Product",
  "Engineering",
  "Design",
  "Reliability",
  "Release",
];

export function UpdatesPage() {
  const reduced = useReducedMotion();
  const [activeCategory, setActiveCategory] = useState<UpdateCategory | "All">("All");

  const featured = useMemo(
    () => updates.find((u) => u.slug === featuredUpdateSlug) ?? updates[0],
    [],
  );

  const filtered = useMemo(() => {
    const sorted = [...updates].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
    );
    if (activeCategory === "All") return sorted.filter((u) => u.slug !== featured.slug);
    return sorted.filter((u) => u.category === activeCategory && u.slug !== featured.slug);
  }, [activeCategory, featured.slug]);

  return (
    <RouteEnter>
      <main className="w-full">
        <div className="mx-auto w-full max-w-4xl px-[var(--page-gutter)] py-8 md:py-12">
          <header className="mb-12">
            <BlurFade>
              <h1 className="font-editorial text-[var(--type-page-title)] font-semibold text-text-primary">
                Project updates
              </h1>
            </BlurFade>
            <p className="mt-4 max-w-prose text-lg leading-relaxed text-text-secondary">
              Real milestones from AskMcNeese development—streaming stabilization, citation fixes,
              activity alignment, and the visual product overhaul.
            </p>
          </header>

          <section id="latest" aria-labelledby="featured-update-title" className="mb-12 scroll-mt-24">
            <p
              id="featured-update-title"
              className="mb-4 text-sm font-medium uppercase tracking-wide text-brand-700"
            >
              Featured update
            </p>
            <UpdateCard update={featured} featured />
          </section>

          <section id="releases" aria-labelledby="updates-feed-title" className="scroll-mt-24">
            <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
              <h2
                id="updates-feed-title"
                className="font-editorial text-xl font-semibold text-text-primary"
              >
                All updates
              </h2>
              <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by category">
                {categories.map((category) => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => setActiveCategory(category)}
                    className={`min-h-9 rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus ${
                      activeCategory === category
                        ? "bg-brand-700 text-white"
                        : "text-text-secondary hover:bg-brand-50/60 hover:text-text-primary"
                    }`}
                    aria-pressed={activeCategory === category}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            <LayoutGroup>
              <StaggerGroup className="divide-y divide-[var(--border-subtle)]" itemSelector="[data-stagger-item]">
                {filtered.length === 0 ? (
                  <p className="py-6 text-sm text-text-muted">No updates in this category yet.</p>
                ) : (
                  filtered.map((update: UpdateItem) => (
                    <motion.div
                      key={update.slug}
                      data-stagger-item
                      layout={!reduced}
                      initial={false}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.22, ease: [0.2, 0, 0, 1] }}
                    >
                      <UpdateCard update={update} />
                    </motion.div>
                  ))
                )}
              </StaggerGroup>
            </LayoutGroup>
          </section>

          <section
            id="development"
            className="mt-12 scroll-mt-24 border-t border-[var(--border-subtle)] pt-10"
          >
            <h2 className="font-editorial text-xl font-semibold text-text-primary">Development</h2>
            <p className="mt-2 max-w-prose text-sm leading-relaxed text-text-secondary">
              Active work focuses on the public visual system, route clarity, and preserving the
              stabilized Ask SSE lifecycle. Engineering notes live in the repository change logs under{" "}
              <code className="text-xs">docs/</code>.
            </p>
          </section>

          <section id="limitations" className="mt-10 scroll-mt-24">
            <h2 className="font-editorial text-xl font-semibold text-text-primary">
              Known limitations
            </h2>
            <ul className="mt-3 max-w-prose list-disc space-y-2 pl-5 text-sm leading-relaxed text-text-secondary">
              <li>
                Answers depend on indexed approved sources; gaps in the knowledge base produce partial
                or no-source responses.
              </li>
              <li>Helpful / not helpful controls are client-side only until a feedback API ships.</li>
              <li>
                Authentication, student personalization, and ACM workspace remain future roadmap
                items—not available in this release.
              </li>
            </ul>
          </section>
        </div>
      </main>
    </RouteEnter>
  );
}
