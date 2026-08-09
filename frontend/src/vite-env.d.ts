/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_CLASS_DATA_MODE?: "mock" | "staging" | "live";
  readonly VITE_CLASS_TERM_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
