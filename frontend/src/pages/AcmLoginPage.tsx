import { Link } from "react-router-dom";
import { BrandLogo } from "../components/brand/BrandLogo";
import { RouteEnter } from "../components/motion/RouteEnter";

/**
 * Production-safe boundary for the separate ACM Panel.
 *
 * AskMcNeese does not own an ACM identity service, so this route must never
 * simulate authentication or expose shared credentials.
 */
export function AcmLoginPage() {
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
            <h1 className="acm-login__title">ACM Member Access</h1>
            <p className="acm-login__lede">
              The ACM Panel is a separate system and is not authenticated by AskMcNeese.
            </p>
          </header>

          <section className="acm-login__form" aria-labelledby="acm-access-status">
            <h2 id="acm-access-status" className="acm-login__formTitle">
              Secure sign-in unavailable
            </h2>
            <p className="acm-login__formHint">
              Member access will remain closed until the ACM Panel is connected to a
              real identity service. AskMcNeese does not accept demonstration or shared
              credentials in production.
            </p>
          </section>

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
