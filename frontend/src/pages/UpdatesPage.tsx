import { useMemo, useState } from "react";
import { LayoutGroup, motion } from "framer-motion";
import {
  ArrowRight,
  BookOpenCheck,
  Database,
  MessageSquareText,
  Search,
  ShieldCheck,
} from "lucide-react";
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

const systemFlow = [
  { label: "Find", detail: "Search governed campus sources", icon: Search },
  { label: "Verify", detail: "Keep evidence attached", icon: ShieldCheck },
  { label: "Answer", detail: "Explain the useful next step", icon: MessageSquareText },
  { label: "Improve", detail: "Store feedback for review", icon: Database },
] as const;

const betaCapabilities = [
  "Source-grounded McNeese questions",
  "Live Fall 2026 class search and schedule building",
  "Persistent guest identity and feedback",
] as const;

const canvasPlan = [
  "Connect a Canvas account only with student consent",
  "Bring enrolled courses, due dates, and course materials into one view",
  "Keep campus-wide answers separate from private student data",
] as const;

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
        <div className="mx-auto w-full max-w-5xl px-[var(--page-gutter)] py-8 md:py-12">
          <header className="updatesHero">
            <BlurFade>
              <p className="updatesEyebrow">Development record</p>
              <h1><span className="sr-only">Project updates: </span>What changed, what works, and what comes next.</h1>
            </BlurFade>
            <p>
              A visual record of the public beta. Every item below reflects the current product;
              future work is marked as planned.
            </p>
          </header>

          <section className="updatesSystem" aria-labelledby="updates-system-title">
            <div className="updatesSectionHeading">
              <p>Current answer path</p>
              <h2 id="updates-system-title">From a question to an accountable answer</h2>
            </div>
            <ol className="updatesFlow">
              {systemFlow.map(({ label, detail, icon: Icon }, index) => (
                <li key={label}>
                  <div className="updatesFlowIcon"><Icon size={20} aria-hidden="true" /></div>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{label}</strong>
                  <p>{detail}</p>
                  {index < systemFlow.length - 1 ? <ArrowRight aria-hidden="true" /> : null}
                </li>
              ))}
            </ol>
          </section>

          <section className="updatesReleaseGrid" aria-label="Release status">
            <article className="updatesReleaseCard updatesReleaseCard--live">
              <p className="updatesReleaseState"><span /> Public beta now</p>
              <h2>Useful campus work in one place</h2>
              <ul>
                {betaCapabilities.map((capability) => <li key={capability}>{capability}</li>)}
              </ul>
            </article>
            <article className="updatesReleaseCard updatesReleaseCard--planned">
              <p className="updatesReleaseState"><BookOpenCheck size={16} /> Version 2.0 concept</p>
              <h2>Canvas-connected student context</h2>
              <ul>
                {canvasPlan.map((item) => <li key={item}>{item}</li>)}
              </ul>
              <p className="updatesPlanNotice">
                Planned, not available in the beta. Scope and timing may change as privacy,
                permissions, and production testing are completed.
              </p>
            </article>
          </section>

          <section id="latest" aria-labelledby="featured-update-title" className="mb-12 scroll-mt-24">
            <p id="featured-update-title" className="updatesFeedLabel">Latest documented change</p>
            <UpdateCard update={featured} featured />
          </section>

          <section id="releases" aria-labelledby="updates-feed-title" className="scroll-mt-24">
            <div className="updatesFeedHeader">
              <div>
                <p className="updatesFeedLabel">Change log</p>
                <h2 id="updates-feed-title"><span className="sr-only">All updates: </span>Development updates</h2>
              </div>
              <div className="updatesFilters" role="group" aria-label="Filter by category">
                {categories.map((category) => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => setActiveCategory(category)}
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

          <section id="limitations" className="updatesLimitations">
            <p className="updatesFeedLabel">Beta boundary</p>
            <h2>What the current release does not promise</h2>
            <ul>
              <li>Answers remain limited by the quality and freshness of available sources.</li>
              <li>Class data is currently published for the active supported term only.</li>
              <li>Canvas data, sign-in, and personalized academic records are not in this beta.</li>
            </ul>
          </section>
        </div>
      </main>
    </RouteEnter>
  );
}