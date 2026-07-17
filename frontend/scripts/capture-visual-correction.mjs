import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const OUT = path.resolve("../docs/screenshots/visual-correction");
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

  for (const width of widths) {
    const context = await browser.newContext({
      viewport: { width, height: width <= 390 ? 844 : 900 },
      deviceScaleFactor: 1,
    });
    const page = await context.newPage();

    await page.goto(`${BASE}/ask`, { waitUntil: "networkidle" });
    await page.waitForTimeout(700);
    await shot(page, `${width}-empty-ask`);

    await page.goto(`${BASE}/__visual__/progress-active`, { waitUntil: "networkidle" });
    await page.waitForTimeout(500);
    await shot(page, `${width}-progress-compact`);

    await page.goto(`${BASE}/__visual__/progress-details`, { waitUntil: "networkidle" });
    await page.waitForTimeout(700);
    await shot(page, `${width}-progress-expanded`);

    await page.goto(`${BASE}/__visual__/progress-complete`, { waitUntil: "networkidle" });
    await page.waitForTimeout(700);
    await shot(page, `${width}-answer-sources-expanded`);

    if (width <= 768) {
      await page.goto(`${BASE}/ask`, { waitUntil: "networkidle" });
      const more = page.getByRole("button", { name: /More navigation/i });
      if (await more.count()) {
        await more.click();
        await page.waitForTimeout(400);
        await shot(page, `${width}-mobile-more`);
      }
    }

    await page.goto(`${BASE}/about`, { waitUntil: "networkidle" });
    await page.waitForTimeout(500);
    await shot(page, `${width}-about`);

    await page.goto(`${BASE}/updates`, { waitUntil: "networkidle" });
    await page.waitForTimeout(500);
    await shot(page, `${width}-updates`);

    await page.goto(`${BASE}/acm/login`, { waitUntil: "networkidle" });
    await page.waitForTimeout(500);
    await shot(page, `${width}-acm-portal`);

    await context.close();
  }

  await browser.close();
  console.log("done");
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
