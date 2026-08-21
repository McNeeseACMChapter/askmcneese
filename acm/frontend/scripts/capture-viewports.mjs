/**
 * Captures prototype screenshots into artifacts/visual/.
 * Run: npm run capture:viewports
 * Requires preview server (ACM_BASE_URL, default http://127.0.0.1:4173)
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dirname, "..", "artifacts", "visual");
const base = process.env.ACM_BASE_URL ?? "http://127.0.0.1:4173";

const viewports = [
  { name: "375x812", width: 375, height: 812 },
  { name: "430x932", width: 430, height: 932 },
  { name: "768x1024", width: 768, height: 1024 },
  { name: "1024x768", width: 1024, height: 768 },
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1920x1080", width: 1920, height: 1080 },
];

const routes = [
  { path: "/home", slug: "home" },
  { path: "/my-work", slug: "my-work" },
  { path: "/projects", slug: "projects" },
  { path: "/projects/proj-ask-2", slug: "project-detail" },
  { path: "/meetings", slug: "meetings" },
  { path: "/events", slug: "events" },
  { path: "/members", slug: "members" },
  { path: "/governance", slug: "governance" },
  { path: "/sga", slug: "sga" },
  { path: "/finance", slug: "finance" },
  { path: "/communications", slug: "communications" },
  { path: "/documents", slug: "documents" },
  { path: "/reports", slug: "reports" },
  { path: "/notifications", slug: "notifications" },
  { path: "/administration", slug: "administration" },
  { path: "/audit", slug: "audit" },
  { path: "/approvals/ap-role-001", slug: "approval" },
  { path: "/profile", slug: "profile" },
];

await mkdir(outDir, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage();

for (const vp of viewports) {
  await page.setViewportSize({ width: vp.width, height: vp.height });
  for (const route of routes) {
    await page.goto(`${base}${route.path}`, { waitUntil: "networkidle", timeout: 60000 });
    const file = path.join(outDir, `${route.slug}-${vp.name}.png`);
    await page.screenshot({ path: file, fullPage: true });
    console.log("wrote", file);
  }
}

// Shell states at desktop
await page.setViewportSize({ width: 1440, height: 900 });
await page.goto(`${base}/home`, { waitUntil: "networkidle" });
await page.screenshot({
  path: path.join(outDir, "shell-expanded-1440x900.png"),
  fullPage: false,
});

const collapse = page
  .locator(
    '[aria-label*="Collapse" i], [aria-label*="Expand" i], button[aria-label*="sidebar" i]',
  )
  .first();
if ((await collapse.count()) > 0) {
  await collapse.click({ force: true });
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(outDir, "shell-collapsed-1440x900.png"),
    fullPage: false,
  });
}

// Mobile More sheet
await page.setViewportSize({ width: 375, height: 812 });
await page.goto(`${base}/home`, { waitUntil: "networkidle" });
const more = page.locator(".acm-mobile-nav__item[aria-controls='acm-more-sheet']");
if ((await more.count()) > 0) {
  await more.click({ force: true });
  await page.waitForTimeout(400);
  await page.screenshot({
    path: path.join(outDir, "mobile-more-375x812.png"),
    fullPage: false,
  });
}

await browser.close();
console.log("done");
