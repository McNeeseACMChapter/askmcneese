export interface GoogleFeedbackConfig {
  actionUrl: string;
  categoryEntry: string;
  messageEntry: string;
}

interface FeedbackEnvironment {
  VITE_GOOGLE_FEEDBACK_FORM_ACTION?: string;
  VITE_GOOGLE_FEEDBACK_CATEGORY_ENTRY?: string;
  VITE_GOOGLE_FEEDBACK_MESSAGE_ENTRY?: string;
}

const ASKMCNEESE_GOOGLE_FORM: GoogleFeedbackConfig = {
  actionUrl:
    "https://docs.google.com/forms/d/e/1FAIpQLSdBnSo7B1NGrm5DRYGJnMfvfqL1Q10u1GNeJQXK0GMvJNCBcg/formResponse",
  categoryEntry: "entry.516755088",
  messageEntry: "entry.1067231505",
};

function validEntryName(value: string): boolean {
  return /^entry\.\d+$/.test(value);
}

function validGoogleFormAction(value: string): boolean {
  try {
    const url = new URL(value);
    return (
      url.protocol === "https:" &&
      url.hostname === "docs.google.com" &&
      url.pathname.endsWith("/formResponse")
    );
  } catch {
    return false;
  }
}

export function getGoogleFeedbackConfig(
  environment: FeedbackEnvironment = import.meta.env,
): GoogleFeedbackConfig | null {
  const actionUrl = environment.VITE_GOOGLE_FEEDBACK_FORM_ACTION?.trim() ?? "";
  const categoryEntry = environment.VITE_GOOGLE_FEEDBACK_CATEGORY_ENTRY?.trim() ?? "";
  const messageEntry = environment.VITE_GOOGLE_FEEDBACK_MESSAGE_ENTRY?.trim() ?? "";

  if (!actionUrl && !categoryEntry && !messageEntry) {
    return ASKMCNEESE_GOOGLE_FORM;
  }

  if (
    !validGoogleFormAction(actionUrl) ||
    !validEntryName(categoryEntry) ||
    !validEntryName(messageEntry)
  ) {
    return null;
  }
  return { actionUrl, categoryEntry, messageEntry };
}

/**
 * Submit only the two visible feedback fields. `no-cors` is required because
 * Google Forms does not expose a browser-readable cross-origin response.
 */
export async function submitGoogleFormFeedback(
  config: GoogleFeedbackConfig,
  category: string,
  message: string,
): Promise<void> {
  const payload = new URLSearchParams();
  payload.set(config.categoryEntry, category);
  payload.set(config.messageEntry, message);

  await fetch(config.actionUrl, {
    method: "POST",
    mode: "no-cors",
    credentials: "omit",
    referrerPolicy: "no-referrer",
    headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
    body: payload.toString(),
  });
}
