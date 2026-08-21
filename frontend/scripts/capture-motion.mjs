import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const OUT = path.resolve("../docs/screenshots/motion");
fs.mkdirSync(OUT, { recursive: true });
const BASE = "http://127.0.0.1:4173";

async function shot(page, name) {
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  console.log("wrote", file);
}

async function run() {
  const browser = await chromium.launch();
  const widths = [390, 768, 1280, 1440];
  const routes = [
    ["about", "/about"],
    ["methodology", "/about/methodology"],
    ["team", "/about/team"],
    ["advisor", "/about/advisor"],
    ["roadmap", "/about/roadmap"],
    ["updates", "/updates"],
    ["status", "/status"],
    ["settings", "/settings"],
    ["feedback", "/feedback"],
    ["acm-login", "/acm/login"],
  ];

  for (const width of widths) {
    const context = await browser.newContext({
      viewport: { width, height: width <= 390 ? 844 : 900 },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();

    for (const [name, route] of routes) {
      await page.goto(`${BASE}${route}`, { waitUntil: "networkidle" });
      await page.waitForTimeout(600);
      await shot(page, `${width}-${name}`);
    }

    // Methodology scroll stages (desktop storytelling)
    if (width >= 1280) {
      await page.goto(`${BASE}/about/methodology`, { waitUntil: "networkidle" });
      await page.waitForTimeout(500);
      await shot(page, `${width}-methodology-before`);
      await page.evaluate(() => window.scrollTo(0, Math.floor(document.body.scrollHeight * 0.35)));
      await page.waitForTimeout(500);
      await shot(page, `${width}-methodology-mid`);
      await page.evaluate(() => window.scrollTo(0, Math.floor(document.body.scrollHeight * 0.85)));
      await page.waitForTimeout(500);
      await shot(page, `${width}-methodology-final`);

      await page.goto(`${BASE}/about/roadmap`, { waitUntil: "networkidle" });
      await page.waitForTimeout(400);
      await shot(page, `${width}-roadmap-initial`);
      await page.evaluate(() => window.scrollTo(0, Math.floor(document.body.scrollHeight * 0.45)));
      await page.waitForTimeout(500);
      await shot(page, `${width}-roadmap-mid`);
    }

    // Reduced motion
    if (width === 1280) {
      await context.close();
      const reduced = await browser.newContext({
        viewport: { width: 1280, height: 900 },
        reducedMotion: "reduce",
      });
      const rp = await reduced.newPage();
      await rp.goto(`${BASE}/about/methodology`, { waitUntil: "networkidle" });
      await rp.waitForTimeout(400);
      await shot(rp, `1280-methodology-reduced-motion`);
      await rp.goto(`${BASE}/about/team`, { waitUntil: "networkidle" });
      await rp.waitForTimeout(400);
      await shot(rp, `1280-team-reduced-motion`);
      await reduced.close();
      continue;
    }

    await context.close();
  }

  await browser.close();
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
