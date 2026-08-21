interface Step {
  id: string;
  label: string;
  done?: boolean;
  current?: boolean;
}

export function LifecycleStepper({ steps, label }: { steps: Step[]; label: string }) {
  return (
    <ol className="acm-stepper" aria-label={label}>
      {steps.map((step, i) => (
        <li
          key={step.id}
          className={`acm-stepper__item${step.done ? " is-done" : ""}${step.current ? " is-current" : ""}`}
        >
          <span className="acm-stepper__dot" aria-hidden>
            {step.done ? "✓" : i + 1}
          </span>
          <span className="acm-stepper__label">{step.label}</span>
        </li>
      ))}
    </ol>
  );
}
