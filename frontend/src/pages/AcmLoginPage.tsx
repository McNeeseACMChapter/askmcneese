import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { RouteEnter } from "../components/motion/RouteEnter";

/**
 * ACM member verification gate — UI only.
 * Submit acknowledges the form; it does not authenticate or navigate.
 */
export function AcmLoginPage() {
  const [email, setEmail] = useState("");
  const [memberId, setMemberId] = useState("");
  const [password, setPassword] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitted(true);
  }

  return (
    <RouteEnter>
      <main className="acm-login">
        <div className="acm-login__shell">
          <header className="acm-login__intro">
            <p className="acm-login__eyebrow">McNeese ACM · AskMcNeese</p>
            <h1 className="acm-login__title">ACM Member Login</h1>
            <p className="acm-login__lede">
              AskMcNeese is the chapter’s campus Q&amp;A platform—answers grounded in approved
              McNeese sources. This page is the member gate: verified ACM members sign in here to
              reach chapter tools and project access.
            </p>
          </header>

          <form className="acm-login__form" onSubmit={handleSubmit} noValidate={false}>
            <h2 className="acm-login__formTitle">Member verification</h2>
            <p className="acm-login__formHint">
              Use your chapter-approved credentials. Sign-in verifies membership only—no session is
              created in this build.
            </p>

            <label className="acm-login__field">
              <span className="acm-login__label">McNeese email</span>
              <input
                type="email"
                name="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setSubmitted(false);
                }}
                placeholder="you@mcneese.edu"
                className="acm-login__input"
              />
            </label>

            <label className="acm-login__field">
              <span className="acm-login__label">ACM member ID</span>
              <input
                type="text"
                name="memberId"
                autoComplete="off"
                required
                value={memberId}
                onChange={(e) => {
                  setMemberId(e.target.value);
                  setSubmitted(false);
                }}
                placeholder="Chapter member ID"
                className="acm-login__input"
              />
            </label>

            <label className="acm-login__field">
              <span className="acm-login__label">Password</span>
              <input
                type="password"
                name="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setSubmitted(false);
                }}
                placeholder="••••••••"
                className="acm-login__input"
              />
            </label>

            <button type="submit" className="acm-login__submit">
              Verify &amp; log in
            </button>

            {submitted ? (
              <p className="acm-login__ack" role="status">
                Verification form received. Member login is not connected yet—nothing further
                happens after this step.
              </p>
            ) : null}
          </form>

          <p className="acm-login__footer">
            <Link to="/about" className="acm-login__link">
              About the team
            </Link>
            <span aria-hidden="true"> · </span>
            <Link to="/ask" className="acm-login__link">
              Back to Ask
            </Link>
          </p>
        </div>
      </main>
    </RouteEnter>
  );
}
