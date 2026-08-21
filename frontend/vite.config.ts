/// <reference types="vitest/config" />
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, normalizePath, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const frontendRoot = fileURLToPath(new URL(".", import.meta.url));
const timelineCsvPath = path.resolve(frontendRoot, "../docs/pm/timeline.csv");

/** Load the canonical PM timeline without duplicating it into src/. */
export function canonicalTimelinePlugin(sourcePath = timelineCsvPath): Plugin {
  const virtualId = "virtual:pm-timeline";
  const resolvedId = `\0${virtualId}`;
  const normalizedSourcePath = normalizePath(sourcePath);
  let hotCsv: string | undefined;

  return {
    name: "canonical-pm-timeline",
    resolveId(id) {
      if (id === virtualId || id === "@pm-timeline") return resolvedId;
      return undefined;
    },
    load(id) {
      if (id !== resolvedId) return undefined;
      this.addWatchFile(sourcePath);
      const csv = hotCsv ?? fs.readFileSync(sourcePath, "utf8");
      return {
        code: `export default ${JSON.stringify(csv)};`,
        map: null,
      };
    },
    configureServer(server) {
      server.watcher.add(sourcePath);
    },
    async handleHotUpdate({ file, read, server }) {
      if (normalizePath(file) !== normalizedSourcePath) return undefined;
      hotCsv = await read();
      const timelineModule = server.moduleGraph.getModuleById(resolvedId);
      if (timelineModule) return [timelineModule];
      server.ws.send({ type: "full-reload" });
      return [];
    },
  };
}

export default defineConfig({
  plugins: [react(), canonicalTimelinePlugin()],
  server: {
    port: 5173,
    strictPort: true,
    fs: {
      allow: [frontendRoot, path.dirname(timelineCsvPath)],
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
});
