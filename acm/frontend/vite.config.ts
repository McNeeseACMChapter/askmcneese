/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // Ask owns 5173. Avoid 5174–52xx — Windows Hyper-V often excludes those.
    port: 3100,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api/acm": {
        target: "http://127.0.0.1:3101",
        changeOrigin: false,
      },
    },
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: true,
  },
});
