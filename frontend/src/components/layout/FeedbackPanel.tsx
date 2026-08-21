import { useState, type FormEvent } from "react";
import { CheckCircle2, Send } from "lucide-react";
import {
  getGoogleFeedbackConfig,
  submitGoogleFormFeedback,
} from "../../features/feedback/googleForm";
import { RouteEnter } from "../motion/RouteEnter";
import { Panel } from "./SystemStatusPanel";

const CATEGORIES = [
  ["incorrect", "Incorrect answer"],
  ["missing", "Missing information"],
  ["experience", "Confusing experience"],
  ["idea", "Feature idea"],
] as const;

export function FeedbackPanel() {
  const [category, setCategory] = useState<(typeof CATEGORIES)[number][0]>("incorrect");
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const googleForm = getGoogleFeedbackConfig();

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (sending || !googleForm) return;
    if (body.trim().length < 10) {
      setError("Please enter at least 10 characters so the team can understand what happened.");
      return;
    }
    setSending(true);
    setError(null);
    try {
      const categoryLabel = CATEGORIES.find(([value]) => value === category)?.[1] ?? category;
      await submitGoogleFormFeedback(googleForm, categoryLabel, body.trim());
      setSubmitted(true);
      setBody("");
    } catch {
      setError("We couldn’t send this feedback to Google Forms. Please try again.");
    } finally {
      setSending(false);
    }
  };

  return (
    <RouteEnter>
      <Panel
        title="Feedback"
        description="Flag an incorrect answer, missing campus information, or a product issue."
      >
        {submitted ? (
          <div className="rounded-2xl border border-success/30 bg-success/5 p-5" role="status">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 text-success" size={20} aria-hidden />
              <div>
                <p className="font-semibold">Feedback sent</p>
                <p className="mt-1 text-sm text-text-secondary">
                  The category and message were submitted to the AskMcNeese Google Form.
                </p>
                <button
                  type="button"
                  className="mt-4 text-sm font-semibold text-mcneese-blue hover:underline"
                  onClick={() => setSubmitted(false)}
                >
                  Send another note
                </button>
              </div>
            </div>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-5 rounded-2xl border border-border bg-surface p-5">
            <fieldset>
              <legend className="mb-2 text-sm font-semibold">What should we review?</legend>
              <div className="grid gap-2 sm:grid-cols-2">
                {CATEGORIES.map(([value, label]) => (
                  <label
                    key={value}
                    className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-border px-3 py-2 text-sm has-[:checked]:border-mcneese-blue has-[:checked]:bg-brand-soft"
                  >
                    <input
                      type="radio"
                      name="feedback-category"
                      value={value}
                      checked={category === value}
                      onChange={() => setCategory(value)}
                      className="accent-mcneese-blue"
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <label className="block">
              <span className="mb-1 block text-sm font-semibold">What happened?</span>
              <span id="feedback-message-guidance" className="mb-2 block text-xs text-text-muted">
                Include the question you asked and what you expected. Do not include private student information.
              </span>
              <textarea
                id="feedback-message"
                required
                maxLength={4000}
                rows={7}
                value={body}
                aria-describedby="feedback-message-guidance feedback-message-count"
                onChange={(event) => {
                  setBody(event.target.value);
                  if (error) setError(null);
                }}
                className="w-full resize-y rounded-xl border border-border px-3 py-3 focus:border-mcneese-blue focus:outline-none"
              />
              <span id="feedback-message-count" className="mt-1 block text-right text-xs text-text-muted">
                {body.trim().length} / 4000 · minimum 10 characters
              </span>
            </label>

            {error ? <p className="text-sm text-error" role="alert">{error}</p> : null}
            {!googleForm ? (
              <p className="text-sm text-error" role="status">
                The AskMcNeese Google Form has not been connected yet.
              </p>
            ) : null}

            <div className="flex items-center justify-between gap-4">
              <p className="text-xs text-text-muted">
                Only the selected category and message are sent. No guest identity,
                conversation history, or browser data is included.
              </p>
              <button
                className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-mcneese-blue px-4 py-2 font-semibold text-white hover:bg-mcneese-dark disabled:opacity-55"
                type="submit"
                disabled={!googleForm || sending}
              >
                <Send size={16} aria-hidden />
                {sending ? "Sending…" : "Submit"}
              </button>
            </div>
          </form>
        )}
      </Panel>
    </RouteEnter>
  );
}
