import { chromium } from "playwright";
import fs from "fs";

const out =
  "c:/Users/prinx/OneDrive/Desktop/Summer 2026/AskMcNeese Program/askmcneese/frontend/artifacts/composer-mobile";
const docs =
  "c:/Users/prinx/OneDrive/Desktop/Summer 2026/AskMcNeese Program/askmcneese/docs/pm/sprint3/artifacts/composer-mobile";
fs.mkdirSync(out, { recursive: true });
fs.mkdirSync(docs, { recursive: true });

const browser = await chromium.launch();
const viewports = [
  { name: "390", width: 390, height: 844 },
  { name: "430", width: 430, height: 932 },
  { name: "768", width: 768, height: 1024 },
  { name: "1280", width: 1280, height: 800 },
];

for (const vp of viewports) {
  const page = await browser.newPage({
    viewport: { width: vp.width, height: vp.height },
  });
  await page.goto("http://127.0.0.1:4173/ask", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });
  await page.waitForTimeout(1000);
  await page.locator(".composerGlass").waitFor({ state: "visible" });

  const full = `${out}/ask-${vp.name}-full.png`;
  const crop = `${out}/ask-${vp.name}-composer.png`;
  await page.screenshot({ path: full });
  await page.locator(".composerGlass").screenshot({ path: crop });
  fs.copyFileSync(full, `${docs}/ask-${vp.name}-full.png`);
  fs.copyFileSync(crop, `${docs}/ask-${vp.name}-composer.png`);

  if (vp.name === "390") {
    await page.locator('textarea[aria-label="AskMcNeese question"]').click();
    await page.waitForTimeout(250);
    const focused = `${out}/ask-390-focused.png`;
    await page.screenshot({ path: focused });
    fs.copyFileSync(focused, `${docs}/ask-390-focused.png`);
    const headerDisplay = await page
      .locator(".composerHeader")
      .evaluate((el) => getComputedStyle(el).display);
    console.log("390 header display:", headerDisplay);
  }
  if (vp.name === "1280") {
    const headerDisplay = await page
      .locator(".composerHeader")
      .evaluate((el) => getComputedStyle(el).display);
    console.log("1280 header display:", headerDisplay);
  }

  console.log("captured", vp.name, fs.statSync(full).size);
  await page.close();
}

await browser.close();
console.log("done");
