import { useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import { AnimatedBeam } from "./AnimatedBeam";
import { ensureGsap, prefersReducedMotion } from "../../lib/gsap";
import type { MethodologyStep } from "../../content/about";

interface MethodologyStoryProps {
  steps: MethodologyStep[];
  intro: string;
}

/**
 * Desktop (≥1024): sticky visual + ScrollTrigger active step (native scroll).
 * No multi-viewport page pin — sticky column only, max story height from step spacing.
 * Mobile / reduced-motion: stacked natural flow; all steps readable in DOM order.
 */
export function MethodologyStory({ steps, intro }: MethodologyStoryProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = useState(0);
  const labels = steps.map((step) => step.title);

  useGSAP(
    () => {
      if (prefersReducedMotion()) return;
      const { gsap, ScrollTrigger } = ensureGsap();
      const root = rootRef.current;
      const progress = progressRef.current;
      if (!root) return;

      const mm = gsap.matchMedia();

      mm.add("(min-width: 1024px)", () => {
        const panels = root.querySelectorAll<HTMLElement>("[data-method-step]");
        const triggers: ScrollTrigger[] = [];

        panels.forEach((panel, index) => {
          triggers.push(
            ScrollTrigger.create({
              trigger: panel,
              start: "top 55%",
              end: "bottom 45%",
              onEnter: () => setActiveStep(index),
              onEnterBack: () => setActiveStep(index),
              onUpdate: (self) => {
                if (!progress) return;
                const base = index / Math.max(panels.length - 1, 1);
                const span = 1 / Math.max(panels.length - 1, 1);
                const value = Math.min(1, Math.max(0, base + self.progress * span * 0.35));
                progress.style.transform = `scaleY(${value})`;
              },
            }),
          );
        });

        return () => {
          triggers.forEach((t) => t.kill());
        };
      });

      mm.add("(max-width: 1023px)", () => {
        const panels = root.querySelectorAll<HTMLElement>("[data-method-step]");
        const triggers = Array.from(panels).map((panel, index) =>
          ScrollTrigger.create({
            trigger: panel,
            start: "top 80%",
            once: true,
            onEnter: () => setActiveStep(index),
          }),
        );
        if (progress) progress.style.transform = "scaleY(1)";
        return () => triggers.forEach((t) => t.kill());
      });

      return () => mm.revert();
    },
    { dependencies: [steps.length], scope: rootRef, revertOnUpdate: true },
  );

  return (
    <div ref={rootRef} className="methodology-story">
      <p className="mb-10 max-w-prose text-lg leading-relaxed text-text-secondary">{intro}</p>

      <div className="grid gap-10 lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] lg:gap-14">
        <div
          data-method-visual
          className="methodology-visual relative rounded-2xl bg-brand-50/70 p-6 lg:sticky lg:top-24 lg:self-start"
        >
          <div
            className="absolute bottom-8 left-3 top-8 hidden w-px bg-border lg:block"
            aria-hidden="true"
          >
            <div
              ref={progressRef}
              className="origin-top h-full w-full bg-brand-600"
              style={{ transform: "scaleY(0)" }}
            />
          </div>
          <p className="mb-4 font-sans text-xs font-semibold uppercase tracking-wide text-brand-700">
            How an answer is prepared
          </p>
          <AnimatedBeam activeStep={activeStep} steps={labels} className="min-h-[260px] lg:min-h-[320px]" />
          <p className="mt-4 font-sans text-sm text-text-secondary" aria-live="polite">
            Current stage:{" "}
            <span className="font-medium text-text-primary">
              {steps[activeStep]?.title ?? steps[0]?.title}
            </span>
          </p>
          <p className="mt-2 font-sans text-xs text-text-muted lg:hidden">
            Scroll through each step below — the diagram updates to match.
          </p>
        </div>

        <ol className="space-y-12 lg:space-y-28">
          {steps.map((step, index) => (
            <li
              key={step.id}
              data-method-step
              className="scroll-mt-28"
              aria-current={index === activeStep ? "step" : undefined}
            >
              <p className="mb-2 font-sans text-xs font-semibold uppercase tracking-wide text-text-muted">
                Step {index + 1}
              </p>
              <h2 className="mb-3 font-editorial text-2xl font-semibold text-text-primary md:text-[1.75rem]">
                {step.title}
              </h2>
              <p className="max-w-prose leading-relaxed text-text-secondary">{step.description}</p>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
