import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type MouseEvent as ReactMouseEvent,
} from "react";
import {
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Network,
  Pause,
  Play,
  UsersRound,
} from "lucide-react";
import {
  orgAdvisor,
  orgBuilders,
  orgManager,
  orgPresident,
  orgUmbrella,
  type OrgPerson,
} from "../../content/orgChart";

const STORY_DURATION_MS = 7200;

const memberStories: Record<string, { discipline: string; statement: string; signal: string }> = {
  "vipin-menon": {
    discipline: "Academic direction",
    statement: "Keeps the product vision responsible, useful, and aligned with the standards a campus information tool should earn.",
    signal: "Guide",
  },
  "prince-pudasaini": {
    discipline: "Product and delivery",
    statement: "Turns the idea into a working program—setting direction, shaping sprints, and connecting every delivery lane.",
    signal: "Lead",
  },
  "landon-peurta": {
    discipline: "Backend foundation",
    statement: "Helped establish the early backend track through the first two sprints and the project's initial delivery foundation.",
    signal: "Build",
  },
  ziyan: {
    discipline: "Backend systems",
    statement: "Carries current backend ownership forward, connecting retrieval, services, and the systems behind every answer.",
    signal: "Systems",
  },
  "evan-weber": {
    discipline: "Product experience",
    statement: "Shapes the interface people touch—the Ask experience, application shell, and client-side delivery.",
    signal: "Experience",
  },
};

const contributors = [orgAdvisor, orgManager, ...orgBuilders];

const memberPortraits: Partial<Record<string, string>> = {
  "prince-pudasaini": "/about/media/prince-pudasaini.jpeg",
};

function statusLabel(person: OrgPerson) {
  if (!person.tenure) return "Contributor";
  return person.tenure.status === "former"
    ? `Former · ${person.tenure.label}`
    : person.tenure.label;
}

function prefersReducedMotion() {
  return typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

type StoryScrollRoot = Window | HTMLElement;

function findScrollRoot(element: HTMLElement): StoryScrollRoot {
  let parent = element.parentElement;
  while (parent && parent !== document.body) {
    const overflowY = window.getComputedStyle(parent).overflowY;
    if (/(auto|scroll|overlay)/.test(overflowY) && parent.scrollHeight > parent.clientHeight) {
      return parent;
    }
    parent = parent.parentElement;
  }
  return window;
}

export function CommandChain() {
  const [activeId, setActiveId] = useState(orgManager.id);
  const [autoPlay, setAutoPlay] = useState(!prefersReducedMotion());
  const [stageVisible, setStageVisible] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);
  const stickyRef = useRef<HTMLDivElement>(null);
  const scrollFrameRef = useRef<number | null>(null);

  const activeIndex = Math.max(0, contributors.findIndex((person) => person.id === activeId));
  const activePerson = contributors[activeIndex];

  const scrollToIndex = useCallback((index: number, behavior: ScrollBehavior = "smooth") => {
    const track = trackRef.current;
    const sticky = stickyRef.current;
    if (!track || !sticky || typeof window === "undefined") return;
    if (window.navigator.userAgent.toLowerCase().includes("jsdom")) return;

    const clamped = Math.max(0, Math.min(contributors.length - 1, index));
    const root = findScrollRoot(track);
    const trackRect = track.getBoundingClientRect();
    const stickyTop = Number.parseFloat(window.getComputedStyle(sticky).top) || 0;
    const range = Math.max(0, track.offsetHeight - sticky.offsetHeight);
    const ratio = contributors.length > 1 ? clamped / (contributors.length - 1) : 0;

    if (root === window) {
      const trackTop = trackRect.top + window.scrollY;
      window.scrollTo({ top: Math.max(0, trackTop - stickyTop + range * ratio), behavior });
    } else {
      const scrollElement = root as HTMLElement;
      const rootRect = scrollElement.getBoundingClientRect();
      const trackTop = scrollElement.scrollTop + trackRect.top - rootRect.top;
      scrollElement.scrollTo({ top: Math.max(0, trackTop - stickyTop + range * ratio), behavior });
    }
  }, []);

  const selectIndex = useCallback((index: number, options?: { pause?: boolean; behavior?: ScrollBehavior }) => {
    const clamped = Math.max(0, Math.min(contributors.length - 1, index));
    setActiveId(contributors[clamped].id);
    if (options?.pause !== false) setAutoPlay(false);
    scrollToIndex(clamped, options?.behavior ?? "smooth");
  }, [scrollToIndex]);

  useEffect(() => {
    const sticky = stickyRef.current;
    if (!sticky || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver(
      ([entry]) => setStageVisible(entry.isIntersecting && entry.intersectionRatio >= 0.55),
      { threshold: [0, 0.55, 0.82] },
    );
    observer.observe(sticky);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const track = trackRef.current;
    if (!track) return;
    const scrollRoot = findScrollRoot(track);

    const updateFromScroll = () => {
      scrollFrameRef.current = null;
      const track = trackRef.current;
      const sticky = stickyRef.current;
      if (!track || !sticky) return;

      const stickyTop = Number.parseFloat(window.getComputedStyle(sticky).top) || 0;
      const rect = track.getBoundingClientRect();
      const range = Math.max(1, track.offsetHeight - sticky.offsetHeight);
      const progress = Math.max(0, Math.min(1, (stickyTop - rect.top) / range));
      const nextIndex = Math.round(progress * (contributors.length - 1));
      setActiveId((current) => current === contributors[nextIndex].id ? current : contributors[nextIndex].id);

    };

    const onScroll = () => {
      if (scrollFrameRef.current !== null) return;
      scrollFrameRef.current = window.requestAnimationFrame(updateFromScroll);
    };

    updateFromScroll();
    scrollRoot.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      scrollRoot.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (scrollFrameRef.current !== null) window.cancelAnimationFrame(scrollFrameRef.current);
    };
  }, [stageVisible]);

  useEffect(() => {
    if (!autoPlay || !stageVisible || prefersReducedMotion()) return;
    if (activeIndex >= contributors.length - 1) {
      setAutoPlay(false);
      return;
    }
    const timer = window.setTimeout(() => {
      selectIndex(activeIndex + 1, { pause: false, behavior: "smooth" });
    }, STORY_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [activeIndex, autoPlay, selectIndex, stageVisible]);

  const moveTabFocus = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const direction = event.key === "ArrowDown" || event.key === "ArrowRight" ? 1
      : event.key === "ArrowUp" || event.key === "ArrowLeft" ? -1
      : 0;
    const nextIndex = event.key === "Home" ? 0
      : event.key === "End" ? contributors.length - 1
      : direction ? (index + direction + contributors.length) % contributors.length
      : index;

    if (nextIndex === index && !["Home", "End"].includes(event.key)) return;
    event.preventDefault();
    selectIndex(nextIndex);
    const tabs = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>("[role='tab']");
    tabs?.[nextIndex]?.focus();
  };

  const handleStageClick = (event: ReactMouseEvent<HTMLDivElement>) => {
    const target = event.target as HTMLElement;
    if (target.closest("button, a, input, select, textarea, summary, [role='tab']")) return;
    setAutoPlay((current) => !current);
  };
  const storyTrackStyle = {
    "--story-track-height": `${contributors.length * 68 + 86}svh`,
  } as CSSProperties;

  return (
    <section className="about-people" aria-labelledby="about-team-title">
      <div className="about-people__prologue">
        <div className="about-people__media">
          <div className="about-people__word" aria-hidden="true">HUMAN</div>
          <div className="about-people__halo" aria-hidden="true" />
          <img
            src="/about/media/mcneese-student.png"
            alt=""
            aria-hidden="true"
            width="554"
            height="610"
            loading="lazy"
          />
          <p>Made on campus.<br />Made for campus.</p>
        </div>

        <header className="about-people__intro">
          <p className="about-kicker">The humans behind the answers</p>
          <h2 id="about-team-title">Built by people who know this campus.</h2>
          <p>
            AskMcNeese is not an anonymous product dropped onto McNeese. It is
            a student-led ACM project shaped through engineering work, campus
            context, and faculty guidance.
          </p>
          <div className="about-people__promise">
            <span>One campus</span>
            <span>Five contributors</span>
            <span>Shared responsibility</span>
          </div>
        </header>
      </div>

      <div className="about-member-stage" onClick={handleStageClick}>
        <div className="about-member-stage__backdrop" aria-hidden="true" />
        <div className="about-member-stage__heading">
          <p className="about-kicker about-kicker--gold">Meet the team</p>
          <p>Scroll to move through the story, or use the controls.</p>
        </div>

        <div ref={trackRef} className="about-member-storyTrack" style={storyTrackStyle}>
          <div ref={stickyRef} className="about-member-storySticky">
            <div className="about-member-storyNav" aria-label="Team story controls">
              <div className="about-member-storyPosition" aria-live="polite">
                <span>Story {String(activeIndex + 1).padStart(2, "0")} / {String(contributors.length).padStart(2, "0")}</span>
                <strong>{activePerson.name}</strong>
              </div>

              <div
                className="about-member-storyProgress"
                role="progressbar"
                aria-label="Team story progress"
                aria-valuemin={1}
                aria-valuemax={contributors.length}
                aria-valuenow={activeIndex + 1}
              >
                {contributors.map((person, index) => (
                  <button
                    key={person.id}
                    type="button"
                    className={`${index < activeIndex ? "is-complete" : ""}${index === activeIndex ? " is-active" : ""}${autoPlay && index === activeIndex ? " is-playing" : ""}`.trim()}
                    onClick={() => selectIndex(index)}
                    aria-label={`Show ${person.name}`}
                    aria-current={index === activeIndex ? "step" : undefined}
                  >
                    <span />
                  </button>
                ))}
              </div>

              <div className="about-member-storyActions">
                <button
                  type="button"
                  className="about-member-storyPlay"
                  onClick={() => setAutoPlay((current) => !current)}
                  aria-label={autoPlay ? "Pause team story" : "Play team story"}
                >
                  {autoPlay ? <Pause aria-hidden="true" /> : <Play aria-hidden="true" />}
                  <span>{autoPlay ? "Pause" : "Play"}</span>
                </button>
                <button
                  type="button"
                  onClick={() => selectIndex(activeIndex - 1)}
                  disabled={activeIndex === 0}
                  aria-label="Previous contributor"
                >
                  <ChevronLeft aria-hidden="true" />
                </button>
                <button
                  type="button"
                  onClick={() => selectIndex(activeIndex + 1)}
                  disabled={activeIndex === contributors.length - 1}
                  aria-label="Next contributor"
                >
                  <ChevronRight aria-hidden="true" />
                </button>
              </div>
            </div>

            <div className="about-member-stage__layout">
              <div className="about-member-tabs" role="tablist" aria-label="AskMcNeese contributors" aria-orientation="vertical">
                {contributors.map((person, index) => {
                  const selected = person.id === activeId;
                  const former = person.tenure?.status === "former";
                  return (
                    <button
                      key={person.id}
                      id={`about-member-tab-${person.id}`}
                      type="button"
                      role="tab"
                      aria-selected={selected}
                      aria-controls={`about-member-panel-${person.id}`}
                      tabIndex={selected ? 0 : -1}
                      className={selected ? "is-active" : ""}
                      onClick={() => selectIndex(index)}
                      onKeyDown={(event) => moveTabFocus(event, index)}
                    >
                      <span className="about-member-tab__number">0{index + 1}</span>
                      <span className="about-member-tab__identity">
                        <strong>{person.name}</strong>
                        <small>{person.role}</small>
                      </span>
                      {former ? <span className="about-member-tab__status is-former">Former · {person.tenure?.label}</span> : null}
                      <ArrowRight aria-hidden="true" />
                    </button>
                  );
                })}
              </div>

              <div className="about-member-deck" aria-live="polite">
                {contributors.map((person, index) => {
                  const story = memberStories[person.id];
                  const portrait = memberPortraits[person.id];
                  const offset = index - activeIndex;
                  const state = offset === 0 ? "active" : offset < 0 ? "past" : "future";
                  const cardStyle = {
                    "--story-card-offset": Math.abs(offset),
                    "--story-card-index": index,
                  } as CSSProperties;

                  return (
                    <article
                      key={person.id}
                      id={`about-member-panel-${person.id}`}
                      className={`about-member-profile${portrait ? " about-member-profile--has-portrait" : ""}`}
                      role="tabpanel"
                      aria-labelledby={`about-member-tab-${person.id}`}
                      aria-hidden={state !== "active"}
                      data-story-state={state}
                      style={cardStyle}
                    >
                      <div className="about-member-profile__monogram" aria-hidden="true">{person.initials}</div>
                      {portrait ? (
                        <figure className="about-member-profile__portrait">
                          <img
                            src={portrait}
                            alt={`Portrait of ${person.name}`}
                            width="1365"
                            height="2048"
                            loading="lazy"
                          />
                        </figure>
                      ) : null}
                      <div className="about-member-profile__signal" aria-hidden="true">
                        <span>{story.signal}</span><i /><i /><i />
                      </div>
                      <p className="about-member-profile__discipline">{story.discipline}</p>
                      <h3>{person.name}</h3>
                      <p className="about-member-profile__role">{person.role}</p>
                      <p className="about-member-profile__statement">{story.statement}</p>
                      <div className="about-member-profile__footer">
                        <span>{statusLabel(person)}</span>
                        <span>{String(index + 1).padStart(2, "0")} / {String(contributors.length).padStart(2, "0")}</span>
                      </div>
                    </article>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="about-governance-wrap">
        <details className="about-governance-disclosure">
          <summary>
            <span className="about-governance-disclosure__icon"><Network aria-hidden="true" /></span>
            <span>
              <small>Student-led · Faculty-guided</small>
              <h3>Who steers AskMcNeese</h3>
            </span>
            <span className="about-governance-disclosure__action">
              View responsibility flow <ArrowRight aria-hidden="true" />
            </span>
          </summary>
          <div className="about-governance-flow" aria-label="AskMcNeese governance structure">
            <div>
              <img src={orgUmbrella.logoSrc} alt="" />
              <span><strong>{orgUmbrella.title}</strong><small>{orgUmbrella.subtitle}</small></span>
            </div>
            <i aria-hidden="true" />
            <div>
              <span className="about-governance-flow__initials">{orgPresident.initials}</span>
              <span><strong>{orgPresident.name}</strong><small>{orgPresident.role}</small></span>
            </div>
            <i aria-hidden="true" />
            <div>
              <span className="about-governance-flow__initials">{orgAdvisor.initials}</span>
              <span><strong>{orgAdvisor.name}</strong><small>{orgAdvisor.role}</small></span>
            </div>
            <i aria-hidden="true" />
            <div>
              <span className="about-governance-flow__initials">{orgManager.initials}</span>
              <span><strong>{orgManager.name}</strong><small>{orgManager.role}</small></span>
            </div>
            <i aria-hidden="true" />
            <div>
              <span className="about-governance-flow__initials"><UsersRound aria-hidden="true" /></span>
              <span><strong>Project builders</strong><small>Frontend and backend delivery</small></span>
            </div>
          </div>
        </details>
      </div>
    </section>
  );
}