import { useState, type FormEvent } from "react";
import { RouteEnter } from "../motion/RouteEnter";
import { Panel } from "./SystemStatusPanel";

export function FeedbackPanel() {
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const query = new URLSearchParams({ subject: subject.trim(), body: body.trim() });
    window.location.href = `mailto:acm@mcneese.edu?${query.toString()}`;
  };

  return (
    <RouteEnter>
    <Panel title="Feedback" description="Share a suggestion or report an issue with the AskMcNeese team.">
      <form onSubmit={submit} className="space-y-4 rounded-xl border border-border bg-surface p-5">
        <label className="block"><span className="mb-1 block text-sm font-semibold">Subject</span><input required value={subject} onChange={(event) => setSubject(event.target.value)} className="w-full rounded-lg border border-border px-3 py-2 focus:border-mcneese-blue focus:outline-none" /></label>
        <label className="block"><span className="mb-1 block text-sm font-semibold">Message</span><textarea required rows={7} value={body} onChange={(event) => setBody(event.target.value)} className="w-full resize-y rounded-lg border border-border px-3 py-2 focus:border-mcneese-blue focus:outline-none" /></label>
        <button className="rounded-lg bg-mcneese-blue px-4 py-2 font-semibold text-white hover:bg-mcneese-dark" type="submit">Open email</button>
      </form>
    </Panel>
    </RouteEnter>
  );
}
