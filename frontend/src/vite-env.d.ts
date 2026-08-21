/// <reference types="vite/client" />

declare module "virtual:pm-timeline" {
  const content: string;
  export default content;
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_CLASS_DATA_MODE?: "staging" | "live";
  readonly VITE_CLASS_TERM_ID?: string;
  readonly VITE_GOOGLE_FEEDBACK_FORM_ACTION?: string;
  readonly VITE_GOOGLE_FEEDBACK_CATEGORY_ENTRY?: string;
  readonly VITE_GOOGLE_FEEDBACK_MESSAGE_ENTRY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
