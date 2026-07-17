import { useState } from "react";
import { motion } from "framer-motion";
import {
  daysInRole,
  formatDaysInRole,
  orgAdvisor,
  orgBuilders,
  orgManager,
  orgPresident,
  orgUmbrella,
  type OrgPerson,
  type OrgTenure,
} from "../../content/orgChart";
import { useReducedMotion } from "../../hooks/useReducedMotion";

function TenureMeta({ tenure }: { tenure: OrgTenure }) {
  const former = tenure.status === "former";
  const days = daysInRole(tenure);
  return (
    <div className="org-card__meta">
      <span className="org-badge">
        {former ? `Former · ${tenure.label}` : tenure.label}
      </span>
      <span className="org-days" title="Days in this role">
        {formatDaysInRole(days)}
      </span>
    </div>
  );
}
function Photo({
  person,
  variant = "person",
}: {
  person?: Pick<OrgPerson, "name" | "initials" | "photoSrc">;
  variant?: "person" | "org";
}) {
  const [failed, setFailed] = useState(false);
  const src = person?.photoSrc;
  const showImg = Boolean(src) && !failed;

  return (
    <div className="org-photo" aria-hidden={!showImg}>
      {showImg ? (
        <img
          src={src}
          alt=""
          loading="lazy"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="org-photo__initials">
          {variant === "org" ? "ACM" : person?.initials}
        </span>
      )}
    </div>
  );
}

function PersonCard({
  person,
  className = "",
  tabIndex = 0,
}: {
  person: OrgPerson;
  className?: string;
  tabIndex?: number;
}) {
  const former = person.tenure?.status === "former";
  return (
    <article
      className={`org-card ${former ? "org-card--former" : ""} ${className}`.trim()}
      tabIndex={tabIndex}
      aria-label={`${person.name}, ${person.role}${former ? ", former contributor" : ""}`}
    >
      <Photo person={person} />
      <h3 className="org-card__name">{person.name}</h3>
      <p className="org-card__role">{person.role}</p>
      {person.detail ? <p className="org-card__detail">{person.detail}</p> : null}
      {person.tenure ? <TenureMeta tenure={person.tenure} /> : null}
    </article>
  );
}

function MobileRow({
  person,
  umbrella,
}: {
  person?: OrgPerson;
  umbrella?: boolean;
}) {
  if (umbrella) {
    return (
      <div className="org-mobile__row org-mobile__row--umbrella" tabIndex={0}>
        <Photo variant="org" person={{ name: orgUmbrella.title, initials: "ACM", photoSrc: orgUmbrella.logoSrc }} />
        <div className="org-mobile__copy">
          <p className="org-mobile__name">{orgUmbrella.title}</p>
          <p className="org-mobile__role">{orgUmbrella.subtitle}</p>
          <p className="org-mobile__detail">
            {orgPresident.name} · {orgPresident.role}
          </p>
        </div>
      </div>
    );
  }

  if (!person) return null;
  const former = person.tenure?.status === "former";
  return (
    <div
      className={`org-mobile__row ${former ? "org-mobile__row--former" : ""}`}
      tabIndex={0}
      aria-label={`${person.name}, ${person.role}`}
    >
      <Photo person={person} />
      <div className="org-mobile__copy">
        <p className="org-mobile__name">{person.name}</p>
        <p className="org-mobile__role">{person.role}</p>
        {person.detail ? <p className="org-mobile__detail">{person.detail}</p> : null}
        {person.tenure ? <TenureMeta tenure={person.tenure} /> : null}
      </div>
    </div>
  );
}

const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.38,
      delay: 0.06 * i,
      ease: [0.22, 1, 0.36, 1] as const,
    },
  }),
};

/**
 * Chain of command for AskMcNeese.
 * Desktop: CSS tree. Phone: vertical timeline (not shrunk desktop cards).
 */
export function CommandChain() {
  const reduceMotion = useReducedMotion();
  const motionProps = (i: number) =>
    reduceMotion
      ? {}
      : {
          custom: i,
          variants: fadeUp,
          initial: "hidden" as const,
          whileInView: "visible" as const,
          viewport: { once: true, amount: 0.28 },
        };

  return (
    <section className="org-chart" aria-labelledby="org-chart-title">
      <div className="org-chart__atmosphere" aria-hidden="true" />

      <header className="org-chart__intro">
        <p className="org-chart__eyebrow">Chain of command</p>
        <h2 id="org-chart-title" className="org-chart__title">
          Who steers AskMcNeese
        </h2>
      </header>

      {/* Desktop tree */}
      <div className="org-tree">
        <motion.div className="org-tree__tier" {...motionProps(0)}>
          <article className="org-card org-card--umbrella" tabIndex={0} aria-label="McNeese ACM Student Chapter">
            <Photo
              variant="org"
              person={{ name: orgUmbrella.title, initials: "ACM", photoSrc: orgUmbrella.logoSrc }}
            />
            <h3 className="org-card__name">{orgUmbrella.title}</h3>
            <p className="org-card__role">{orgUmbrella.subtitle}</p>
          </article>
          <div className="org-president">
            <p className="org-president__label">Chapter President</p>
            <p className="org-president__name">{orgPresident.name}</p>
          </div>
        </motion.div>

        <div className="org-tree__stem" aria-hidden="true" />

        <motion.div className="org-tree__tier" {...motionProps(1)}>
          <PersonCard person={orgAdvisor} className="org-card--advisor" />
        </motion.div>

        <div className="org-tree__stem" aria-hidden="true" />

        <motion.div className="org-tree__tier" {...motionProps(2)}>
          <PersonCard person={orgManager} className="org-card--manager" />
        </motion.div>

        <div className="org-tree__stem" aria-hidden="true" />

        <motion.div className="org-tree__builders" {...motionProps(3)}>
          {orgBuilders.map((person) => (
            <div key={person.id} className="org-tree__builder">
              <PersonCard person={person} />
            </div>
          ))}
        </motion.div>
      </div>

      {/* Phone timeline */}
      <div className="org-mobile" aria-label="Chain of command">
        <div className="org-mobile__item">
          <MobileRow umbrella />
        </div>
        <div className="org-mobile__item">
          <MobileRow person={orgAdvisor} />
        </div>
        <div className="org-mobile__item">
          <MobileRow person={orgManager} />
        </div>
        {orgBuilders.map((person) => (
          <div key={person.id} className="org-mobile__item">
            <MobileRow person={person} />
          </div>
        ))}
      </div>

      <p className="org-chart__lede">
        McNeese ACM is the umbrella. Academic oversight sits with Dr. Vipin Menon.
        Delivery runs through Prince Pudasaini, with backend and frontend builders on the line.
      </p>
    </section>
  );
}
