import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import {
  ArrowRight,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Globe2,
  Mail,
  MapPin,
  Network,
  Pause,
  Play,
  Quote,
  UsersRound,
  Waypoints,
} from "lucide-react";
import { FaFacebookF, FaGithub, FaInstagram, FaLinkedinIn } from "react-icons/fa6";
import {
  orgAdvisor,
  orgBuilders,
  orgManager,
  orgPresident,
  orgUmbrella,
  daysInRole,
  formatDaysInRole,
  type OrgPerson,
} from "../../content/orgChart";
import { useReducedMotion } from "../../hooks/useReducedMotion";

const STORY_DURATION_MS = 7200;

const memberStories: Record<string, { discipline: string; statement: string; signal: string }> = {
  "vipin-menon": {
    discipline: "Academic direction",
    statement: "Keeps the product vision responsible, useful, and aligned with the standards a campus information tool should earn.",
    signal: "Guide",
  },
  "prince-pudasaini": {
    discipline: "Product and delivery",
    statement: "Owns the product thesis end to end—turning an ambitious campus idea into sharp priorities, uncompromising standards, and a system built to lead rather than follow.",
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

const contributorPool = [orgAdvisor, orgManager, ...orgBuilders];
const contributorOrder = ["prince-pudasaini", "evan-weber", "ziyan", "vipin-menon", "landon-peurta"];
const contributors = contributorOrder
  .map((id) => contributorPool.find((person) => person.id === id))
  .filter((person): person is OrgPerson => Boolean(person));

type MemberPortrait = { src: string; width: number; height: number; objectPosition: string };

const memberPortraits: Partial<Record<string, MemberPortrait>> = {
  "prince-pudasaini": {
    src: "/about/media/prince-pudasaini.jpeg",
    width: 1536,
    height: 2048,
    objectPosition: "50% 28%",
  },
  "evan-weber": {
    src: "/about/media/evan-weber.jpg",
    width: 1200,
    height: 1451,
    objectPosition: "50% 18%",
  },
};

type TeamLinkKind = "email" | "github" | "portfolio" | "linkedin" | "facebook" | "instagram";
type TeamLink = { kind: TeamLinkKind; label: string; href: string; iconOnly?: boolean };

// No personal contact or social URLs are published without explicit approval.
// These verified project/chapter channels keep every profile useful without fabrication.
const projectContactLinks: TeamLink[] = [
  { kind: "email", label: "acm@mcneese.edu", href: "mailto:acm@mcneese.edu" },
  { kind: "github", label: "GitHub", href: "https://github.com/McNeeseACMChapter/askmcneese", iconOnly: true },
  { kind: "portfolio", label: "Portfolio", href: "/ask", iconOnly: true },
];

const chapterSocialLinks: TeamLink[] = [
  { kind: "linkedin", label: "LinkedIn", href: "https://www.linkedin.com/company/mcneese-acm-student-chapter", iconOnly: true },
  { kind: "facebook", label: "McNeese on Facebook", href: "https://www.facebook.com/McNeeseStateU/", iconOnly: true },
  { kind: "instagram", label: "Instagram", href: "https://www.instagram.com/mcneeseacm/", iconOnly: true },
];

function TeamLinkButton({ link, active }: { link: TeamLink; active: boolean }) {
  const Icon = link.kind === "email" ? Mail
    : link.kind === "github" ? FaGithub
    : link.kind === "portfolio" ? Globe2
    : link.kind === "linkedin" ? FaLinkedinIn
    : link.kind === "facebook" ? FaFacebookF
    : FaInstagram;
  const external = link.href.startsWith("http");

  return (
    <a
      href={link.href}
      target={external ? "_blank" : undefined}
      rel={external ? "noopener noreferrer" : undefined}
      tabIndex={active ? undefined : -1}
      aria-label={link.label}
      title={link.label}
      className={link.iconOnly ? "is-iconOnly" : undefined}
    >
      <Icon aria-hidden="true" />
      <span>{link.label}</span>
    </a>
  );
}

function statusLabel(person: OrgPerson) {
  if (!person.tenure) return "Contributor";
  return person.tenure.status === "former"
    ? `Former · ${person.tenure.label}`
    : person.tenure.label;
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
  const reducedMotion = useReducedMotion();
  const [activeId, setActiveId] = useState(orgManager.id);
  const [playbackIntent, setPlaybackIntent] = useState<"playing" | "paused">(
    () => reducedMotion ? "paused" : "playing",
  );
  const [stageVisible, setStageVisible] = useState(false);
  const [pageVisible, setPageVisible] = useState(
    () => typeof document === "undefined" || document.visibilityState !== "hidden",
  );
  const trackRef = useRef<HTMLDivElement>(null);
  const stickyRef = useRef<HTMLDivElement>(null);
  const scrollFrameRef = useRef<number | null>(null);
  const programmaticScrollRef = useRef<{ index: number; until: number } | null>(null);
  const pointerStartRef = useRef<{ x: number; y: number; id: number } | null>(null);

  const activeIndex = Math.max(0, contributors.findIndex((person) => person.id === activeId));
  const activePerson = contributors[activeIndex];
  const isActuallyPlaying = playbackIntent === "playing" && stageVisible && pageVisible && !reducedMotion;

  const scrollToIndex = useCallback((index: number, behavior: ScrollBehavior = "smooth") => {
    const track = trackRef.current;
    const sticky = stickyRef.current;
    if (!track || !sticky || typeof window === "undefined") return;
    if (window.navigator.userAgent.toLowerCase().includes("jsdom")) return;

    const clamped = Math.max(0, Math.min(contributors.length - 1, index));
    const resolvedBehavior = reducedMotion ? "auto" : behavior;
    programmaticScrollRef.current = {
      index: clamped,
      until: Date.now() + (resolvedBehavior === "smooth" ? 2400 : 240),
    };
    const root = findScrollRoot(track);
    const trackRect = track.getBoundingClientRect();
    const stickyTop = Number.parseFloat(window.getComputedStyle(sticky).top) || 0;
    const range = Math.max(0, track.offsetHeight - sticky.offsetHeight);
    const ratio = contributors.length > 1 ? clamped / (contributors.length - 1) : 0;

    if (root === window) {
      const trackTop = trackRect.top + window.scrollY;
      window.scrollTo({ top: Math.max(0, trackTop - stickyTop + range * ratio), behavior: resolvedBehavior });
    } else {
      const scrollElement = root as HTMLElement;
      const rootRect = scrollElement.getBoundingClientRect();
      const trackTop = scrollElement.scrollTop + trackRect.top - rootRect.top;
      scrollElement.scrollTo({ top: Math.max(0, trackTop - stickyTop + range * ratio), behavior: resolvedBehavior });
    }
  }, [reducedMotion]);

  const selectIndex = useCallback((index: number, options?: { pause?: boolean; behavior?: ScrollBehavior }) => {
    const clamped = Math.max(0, Math.min(contributors.length - 1, index));
    programmaticScrollRef.current = { index: clamped, until: Date.now() + 2600 };
    setActiveId(contributors[clamped].id);
    if (options?.pause !== false) setPlaybackIntent("paused");
    window.requestAnimationFrame(() => {
      scrollToIndex(clamped, options?.behavior ?? "smooth");
    });
  }, [scrollToIndex]);

  useEffect(() => {
    const sticky = stickyRef.current;
    if (!sticky || typeof IntersectionObserver === "undefined") {
      setStageVisible(true);
      return;
    }
    const observer = new IntersectionObserver(
      ([entry]) => setStageVisible(entry.isIntersecting && entry.intersectionRatio >= 0.55),
      { threshold: [0, 0.55, 0.82] },
    );
    observer.observe(sticky);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const onVisibilityChange = () => setPageVisible(document.visibilityState !== "hidden");
    document.addEventListener("visibilitychange", onVisibilityChange);
    return () => document.removeEventListener("visibilitychange", onVisibilityChange);
  }, []);

  useEffect(() => {
    if (reducedMotion) setPlaybackIntent("paused");
  }, [reducedMotion]);

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

      const programmatic = programmaticScrollRef.current;
      if (programmatic && Date.now() < programmatic.until) {
        const targetId = contributors[programmatic.index].id;
        setActiveId((current) => current === targetId ? current : targetId);
        return;
      }
      programmaticScrollRef.current = null;

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
    if (!isActuallyPlaying) return;
    if (activeIndex >= contributors.length - 1) {
      setPlaybackIntent("paused");
      return;
    }
    const timer = window.setTimeout(() => {
      selectIndex(activeIndex + 1, { pause: false, behavior: "smooth" });
    }, STORY_DURATION_MS);
    return () => window.clearTimeout(timer);
  }, [activeIndex, isActuallyPlaying, selectIndex]);

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

  const isInteractiveTarget = (target: EventTarget | null) =>
    target instanceof HTMLElement && !!target.closest("button, a, input, select, textarea, summary, [role='tab']");

  const handleStagePointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.button !== 0 || isInteractiveTarget(event.target)) return;
    pointerStartRef.current = { x: event.clientX, y: event.clientY, id: event.pointerId };
  };

  const handleStagePointerUp = (event: ReactPointerEvent<HTMLDivElement>) => {
    const start = pointerStartRef.current;
    pointerStartRef.current = null;
    if (!start || start.id !== event.pointerId || isInteractiveTarget(event.target)) return;
    const distance = Math.hypot(event.clientX - start.x, event.clientY - start.y);
    const selection = typeof window !== "undefined" ? window.getSelection()?.toString().trim() : "";
    if (distance > 8 || selection) {
      programmaticScrollRef.current = null;
      setPlaybackIntent("paused");
      return;
    }
    setPlaybackIntent((current) => current === "playing" ? "paused" : "playing");
  };

  const togglePlayback = () => {
    if (playbackIntent === "playing") {
      setPlaybackIntent("paused");
      return;
    }
    if (activeIndex === contributors.length - 1) {
      selectIndex(0, { pause: false, behavior: "auto" });
    }
    setPlaybackIntent("playing");
  };

  const storyTrackStyle = {
    "--story-track-height": `${contributors.length * 45 + 75}svh`,
    "--story-duration": `${STORY_DURATION_MS}ms`,
  } as CSSProperties;

  return (
    <section className="about-people" aria-labelledby="about-team-title">
      <div className="about-people__prologue">
        <div className="about-people__media">
          <div className="about-people__word" aria-hidden="true">ACM</div>
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
          <p className="about-kicker">The team behind AskMcNeese</p>
          <h2 id="about-team-title">Built by people who know this campus.</h2>
          <p>
            AskMcNeese is a student-led ACM project shaped through engineering
            work, campus context, and faculty guidance. Every contributor owns a
            clear part of making campus answers more useful.
          </p>
          <div className="about-people__promise">
            <span><MapPin aria-hidden="true" />One campus</span>
            <span><UsersRound aria-hidden="true" />Five contributors</span>
            <span><Waypoints aria-hidden="true" />Shared responsibility</span>
          </div>
        </header>
      </div>

      <div
        className="about-member-stage"
        onPointerDown={handleStagePointerDown}
        onPointerUp={handleStagePointerUp}
        onPointerCancel={() => { pointerStartRef.current = null; }}
        onWheelCapture={() => {
          programmaticScrollRef.current = null;
          setPlaybackIntent("paused");
        }}
        onFocusCapture={() => setPlaybackIntent("paused")}
      >
        <div className="about-member-stage__heading">
          <p className="about-kicker about-kicker--gold">Meet the team</p>
          <p>Scroll to move through the story, or use the controls.</p>
        </div>

        <div ref={trackRef} className="about-member-storyTrack" style={storyTrackStyle}>
          <div ref={stickyRef} className="about-member-storySticky">
            <div className="about-member-storyNav" aria-label="Team story controls">
              <div className="about-member-storyPosition" aria-live={isActuallyPlaying ? "off" : "polite"}>
                <span>Story {String(activeIndex + 1).padStart(2, "0")} / {String(contributors.length).padStart(2, "0")}</span>
                <strong>{activePerson.name}</strong>
              </div>

              <nav className="about-member-storyProgress" aria-label="Choose a team member">
                {contributors.map((person, index) => (
                  <button
                    key={person.id}
                    type="button"
                    className={`${index < activeIndex ? "is-complete" : ""}${index === activeIndex ? " is-active" : ""}${isActuallyPlaying && index === activeIndex ? " is-playing" : ""}`.trim()}
                    onClick={() => selectIndex(index)}
                    aria-label={`Show ${person.name}`}
                    aria-current={index === activeIndex ? "step" : undefined}
                  >
                    <span />
                  </button>
                ))}
              </nav>

              <div className="about-member-storyActions">
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
                  className="about-member-storyPlay"
                  onClick={togglePlayback}
                  aria-label={playbackIntent === "playing" ? "Pause team story" : "Play team story"}
                  aria-pressed={playbackIntent === "playing"}
                >
                  {playbackIntent === "playing" ? <Pause aria-hidden="true" /> : <Play aria-hidden="true" />}
                  <span>{playbackIntent === "playing" ? "Pause" : "Play"}</span>
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

              <div className="about-member-deck">
                {contributors.map((person, index) => {
                  const story = memberStories[person.id];
                  const portrait = memberPortraits[person.id];
                  const offset = index - activeIndex;
                  const state = offset === 0 ? "active" : offset < 0 ? "past" : "future";
                  const active = state === "active";
                  const tenureDays = person.tenure ? formatDaysInRole(daysInRole(person.tenure)) : null;
                  const cardStyle = {
                    "--story-card-offset": Math.abs(offset),
                    "--story-card-index": index,
                  } as CSSProperties;

                  return (
                    <article
                      key={person.id}
                      id={`about-member-panel-${person.id}`}
                      className="about-member-profile about-teamCard"
                      role="tabpanel"
                      aria-labelledby={`about-member-tab-${person.id}`}
                      aria-hidden={!active}
                      data-story-state={state}
                      style={cardStyle}
                      data-person={person.id}
                    >
                      <div className="about-teamCard__shell">
                        <div className="about-teamCard__media" data-has-portrait={portrait ? "true" : "false"}>
                          {portrait ? (
                            <img
                              src={portrait.src}
                              alt={`Portrait of ${person.name}`}
                              width={portrait.width}
                              height={portrait.height}
                              loading="lazy"
                              style={{ objectPosition: portrait.objectPosition }}
                            />
                          ) : (
                            <div
                              className="about-teamCard__portraitFallback"
                              role="img"
                              aria-label={`${person.name} monogram`}
                            >
                              <span>{person.initials}</span>
                              <small>AskMcNeese team</small>
                            </div>
                          )}
                          <span className="about-teamCard__mediaIndex" aria-hidden="true">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                        </div>

                        <div className="about-teamCard__content">
                          <header className="about-teamCard__identity">
                            <p className="about-teamCard__discipline">{story.discipline}</p>
                            <h3>{person.name}</h3>
                            <p className="about-teamCard__role">{person.role}</p>
                          </header>

                          <div className="about-teamCard__responsibility">
                            <span>What they do</span>
                            <p>{person.detail ?? story.statement}</p>
                          </div>

                          <div className="about-teamCard__perspective">
                            <Quote aria-hidden="true" />
                            <div>
                              <span>Contribution perspective</span>
                              <p>{story.statement}</p>
                            </div>
                          </div>

                          <div className="about-teamCard__connections" aria-label={`${person.name} project contact and chapter social links`}>
                            <div className="about-teamCard__linkGroup">
                              <p>Contact</p>
                              <div>
                                {projectContactLinks.map((link) => (
                                  <TeamLinkButton key={link.kind} link={link} active={active} />
                                ))}
                              </div>
                            </div>
                            <div className="about-teamCard__linkGroup">
                              <p>Social profiles</p>
                              <div>
                                {chapterSocialLinks.map((link) => (
                                  <TeamLinkButton key={link.kind} link={link} active={active} />
                                ))}
                              </div>
                            </div>
                          </div>

                          <footer className="about-teamCard__footer">
                            <div className="about-teamCard__tenure">
                              <CalendarDays aria-hidden="true" />
                              <span>
                                <strong>{statusLabel(person)}</strong>
                              </span>
                            </div>
                            {tenureDays ? (
                              <div className="about-teamCard__counter">
                                <Clock3 aria-hidden="true" />
                                <strong>{tenureDays}</strong>
                                <span>{person.tenure?.status === "former" ? "contributed" : "contributing"}</span>
                              </div>
                            ) : null}
                            <span className="about-teamCard__position">
                              {String(index + 1).padStart(2, "0")} / {String(contributors.length).padStart(2, "0")}
                            </span>
                          </footer>
                        </div>
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
