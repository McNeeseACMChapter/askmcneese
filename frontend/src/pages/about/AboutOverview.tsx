import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowDown,
  ArrowRight,
  Check,
  ExternalLink,
  Quote,
  Search,
  ShieldCheck,
} from "lucide-react";
import { CommandChain } from "../../components/about/CommandChain";
import { BrandLogo } from "../../components/brand/BrandLogo";
import { AppIcon } from "../../components/ui/AppIcon";
import { processStages } from "../../content/about";

const campusQuestions = [
  "How do I transfer credits?",
  "Where can I find tutoring?",
  "When does registration open?",
  "Who can help with financial aid?",
];

const principles = [
  {
    label: "Campus-first",
    title: "McNeese context goes in before an answer comes out.",
  },
  {
    label: "Evidence-visible",
    title: "The source trail stays attached, not buried behind confidence.",
  },
  {
    label: "Human-shaped",
    title: "Students build for the questions campus life actually creates.",
  },
];

export function AboutOverview() {
  const [activeStage, setActiveStage] = useState(0);

  return (
    <div className="about-experience">
      <section className="about-cinematic" aria-labelledby="about-title">
        <div className="about-cinematic__media" aria-hidden="true">
          <img
            src="/about/media/campus-clock.jpg"
            alt=""
            width="1200"
            height="1200"
          />
          <span className="about-cinematic__wash" />
          <span className="about-cinematic__grain" />
        </div>

        <div className="about-cinematic__content">
          <div className="about-cinematic__brandPanel" aria-hidden="true">
            <BrandLogo
              variant="horizontal"
              decorative
              eager
              className="about-cinematic__brandLogo"
            />
          </div>
          <p className="about-kicker about-kicker--gold">Student-built · Source-grounded</p>
          <h1 id="about-title">
            Answers should feel
            <em>closer to home.</em>
          </h1>
          <p className="about-cinematic__lede">
            AskMcNeese turns the campus information already around us into a
            clear path forward—with the original sources still in view.
          </p>
          <div className="about-cinematic__actions">
            <Link to="/ask" className="about-action about-action--gold">
              Ask McNeese <ArrowRight aria-hidden="true" />
            </Link>
            <a href="#story" className="about-action about-action--ghost">
              Why we built it
            </a>
          </div>
        </div>

        <div className="about-cinematic__artifact" aria-label="Example of a source-grounded AskMcNeese answer">
          <div className="about-artifact__question">
            <span>AskMcNeese / 01</span>
            <p>What do I need to apply as a transfer student?</p>
          </div>
          <div className="about-artifact__signal" aria-hidden="true">
            <span /><span /><span />
          </div>
          <div className="about-artifact__answer">
            <span><ShieldCheck /> Answer grounded in McNeese sources</span>
            <p>Start with an application and official transcripts from each college attended.</p>
            <a href="https://www.mcneese.edu/admissions/" target="_blank" rel="noreferrer">
              Undergraduate Admissions <ExternalLink />
            </a>
          </div>
        </div>

        <a className="about-cinematic__scroll" href="#story" aria-label="Continue to the AskMcNeese story">
          <span>Discover the story</span>
          <ArrowDown aria-hidden="true" />
        </a>
      </section>

      <section id="story" className="about-manifesto" aria-labelledby="about-what-title">
        <div className="about-manifesto__orbit" aria-hidden="true">
          <span>Catalog</span><span>Policies</span><span>Services</span><span>Departments</span>
        </div>
        <div className="about-manifesto__copy">
          <p className="about-kicker">The reason</p>
          <h2 id="about-what-title">What AskMcNeese does</h2>
          <p className="about-manifesto__statement">
            Campus knowledge is everywhere.
            <strong> Clarity shouldn’t be.</strong>
          </p>
          <p className="about-manifesto__body">
            The answer may live in a catalog, an office page, a policy, or a
            student-service portal. AskMcNeese follows those scattered threads,
            brings the useful parts together, and leaves a visible trail back.
          </p>
        </div>
        <div className="about-manifesto__quote">
          <Quote aria-hidden="true" />
          <p>Not another chatbot. A better doorway into McNeese.</p>
        </div>
      </section>

      <div className="about-question-river" aria-hidden="true">
        <div className="about-question-river__track">
          {[...campusQuestions, ...campusQuestions].map((question, index) => (
            <span key={`${question}-${index}`}>
              <i /> {question}
            </span>
          ))}
        </div>
      </div>

      <section className="about-principles-editorial" aria-labelledby="about-principles-title">
        <header>
          <p className="about-kicker">A different kind of campus assistant</p>
          <h2 id="about-principles-title">Built for trust before spectacle.</h2>
        </header>
        <ol>
          {principles.map((principle, index) => (
            <li key={principle.label}>
              <span>0{index + 1}</span>
              <div>
                <p>{principle.label}</p>
                <h3>{principle.title}</h3>
              </div>
              <Check aria-hidden="true" />
            </li>
          ))}
        </ol>
      </section>

      <section id="how-it-works" className="about-method" aria-labelledby="about-method-title">
        <div className="about-method__backdrop" aria-hidden="true">HOW</div>
        <header className="about-method__header">
          <p className="about-kicker about-kicker--gold">Open the answer</p>
          <h2 id="about-method-title">Five moves. Nothing hidden.</h2>
          <p>
            Explore the path from a campus question to an answer you can verify.
          </p>
        </header>

        <div className="about-method__accordion">
          {processStages.map((stage, index) => {
            const open = activeStage === index;
            return (
              <div className={`about-method__item ${open ? "is-open" : ""}`} key={stage.id}>
                <button
                  type="button"
                  aria-expanded={open}
                  aria-controls={`about-stage-${stage.id}`}
                  onClick={() => setActiveStage(index)}
                >
                  <span className="about-method__index">0{index + 1}</span>
                  <span className="about-method__label">{stage.title}</span>
                  <span className="about-method__plus" aria-hidden="true" />
                </button>
                <div
                  id={`about-stage-${stage.id}`}
                  className="about-method__panel"
                  aria-hidden={!open}
                >
                  <div className="about-method__panel-inner">
                    <span className="about-method__icon">
                      <AppIcon icon={stage.icon} size={31} />
                    </span>
                    <div>
                      <p className="about-method__panel-label">Stage 0{index + 1}</p>
                      <h3>{stage.title}</h3>
                      <p>{stage.description}</p>
                    </div>
                    <div className="about-method__trace" aria-hidden="true">
                      <span /><span /><span /><i />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <CommandChain />

      <section className="about-closer" aria-labelledby="about-closer-title">
        <div className="about-closer__line" aria-hidden="true" />
        <div>
          <p className="about-kicker about-kicker--gold">Your question is the beginning</p>
          <h2 id="about-closer-title">Find the answer.<br />Keep the source.</h2>
        </div>
        <Link to="/ask" className="about-closer__ask">
          <span>
            <small>Ask in your own words</small>
            What do you need to know?
          </span>
          <i><Search aria-hidden="true" /></i>
        </Link>
      </section>
    </div>
  );
}