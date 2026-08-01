import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ACM_DEMO, isAcmDemoLogin } from "../acm/demoCredentials";
import { getAcmPanelUrl } from "../acm/panelUrl";
import { saveAcmSession } from "../acm/session";
import { BrandLogo } from "../components/brand/BrandLogo";
import { RouteEnter } from "../components/motion/RouteEnter";

/**
 * ACM member verification gate (Ask :5173).
 * On success, hands off to the ACM Panel app (:5174).
 * Demo credentials prefilled from askmcneese/acm/auth/demo-credentials.json.
 */
export function AcmLoginPage() {
  const [email, setEmail] = useState<string>(ACM_DEMO.email);
  const [memberId, setMemberId] = useState<string>(ACM_DEMO.memberId);
  const [password, setPassword] = useState<string>(ACM_DEMO.password);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !isAcmDemoLogin({
        email,
        memberId,
        password,
      })
    ) {
      setError("Those demo credentials do not match. Use admin / 123 / pass123.");
      return;
    }
    saveAcmSession({
      email: email.trim(),
      memberId: memberId.trim(),
      role: "admin",
      at: Date.now(),
    });
    setError(null);
    window.location.assign(getAcmPanelUrl("/home"));
  }

  return (
    <RouteEnter>
      <main className="acm-login">
        <div className="acm-login__shell">
          <header className="acm-login__intro">
            <div className="acm-login__brandPanel" aria-hidden="true">
              <BrandLogo
                variant="horizontal"
                decorative
                eager
                className="acm-login__brandLogo"
              />
            </div>
            <p className="acm-login__eyebrow">McNeese ACM · AskMcNeese</p>
            <h1 className="acm-login__title">ACM Member Login</h1>
            <p className="acm-login__lede">
              AskMcNeese is the chapter’s campus Q&amp;A platform—answers grounded in approved
              McNeese sources. This page is the member gate: verified ACM members sign in here to
              reach the ACM Panel.
            </p>
          </header>

          <form className="acm-login__form" onSubmit={handleSubmit} noValidate={false}>
            <h2 className="acm-login__formTitle">Member verification</h2>
            <p className="acm-login__formHint">
              Demo prefilled: email <strong>admin</strong>, member ID <strong>123</strong>, password{" "}
              <strong>pass123</strong>. Design home: <code>askmcneese/acm/</code>.
            </p>

            <label className="acm-login__field">
              <span className="acm-login__label">Email</span>
              <input
                type="text"
                name="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError(null);
                }}
                placeholder="admin"
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
                  setError(null);
                }}
                placeholder="123"
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
                  setError(null);
                }}
                placeholder="pass123"
                className="acm-login__input"
              />
            </label>

            <button type="submit" className="acm-login__submit">
              Verify &amp; log in
            </button>

            {error ? (
              <p className="acm-login__ack acm-login__ack--error" role="alert">
                {error}
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
