import { Link } from "react-router-dom";
import { Surface } from "../components/ui/Surface";

export function LoginPage() {
  return (
    <div className="flex min-h-dvh items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <Surface level="content" className="p-8">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            McNeese ACM
          </p>
          <h1 className="mt-2">Internal operations</h1>
          <p className="page-lede">
            Sign in is a visual prototype. Continue to the panel with fixture
            credentials only.
          </p>
          <form
            className="mt-6 space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
            }}
          >
            <div className="acm-field">
              <label className="acm-field__label" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                className="acm-input"
                defaultValue="admin"
                autoComplete="username"
              />
            </div>
            <div className="acm-field">
              <label className="acm-field__label" htmlFor="member">
                Member ID
              </label>
              <input id="member" className="acm-input" defaultValue="123" />
            </div>
            <div className="acm-field">
              <label className="acm-field__label" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="acm-input"
                defaultValue="pass123"
                autoComplete="current-password"
              />
            </div>
            <Link to="/home" className="acm-btn acm-btn--primary w-full no-underline">
              Continue to panel (prototype)
            </Link>
          </form>
          <p className="mt-4 text-center text-xs text-text-muted">
            Demo values are fixture labels, not production accounts.
          </p>
          <p className="mt-4 text-center">
            <Link to="/fixtures" className="text-sm font-semibold">
              Open fixture gallery
            </Link>
          </p>
        </Surface>
      </div>
    </div>
  );
}
