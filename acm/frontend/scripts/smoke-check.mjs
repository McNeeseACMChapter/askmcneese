import { chromium } from "playwright";

const base = process.env.ACM_BASE_URL ?? "http://127.0.0.1:5173";

const routes = [
  "/home",
  "/my-work",
  "/projects",
  "/projects?view=board",
  "/projects?view=timeline",
  "/projects/proj-ask-2",
  "/meetings",
  "/events",
  "/members",
  "/governance",
  "/sga",
  "/finance",
  "/communications",
  "/documents",
  "/reports",
  "/notifications",
  "/administration",
  "/audit",
  "/profile",
  "/approvals/ap-role-001",
  "/approvals/ap-proj-001",
];

const browser = await chromium.launch();
const page = await browser.newPage();
let hadError = false;

page.on("console", (msg) => {
  if (msg.type() === "error") {
    console.log(`[console.error] ${msg.text()}`);
    hadError = true;
  }
});
page.on("pageerror", (err) => {
  console.log(`[pageerror] ${err.message}`);
  hadError = true;
});

for (const route of routes) {
  try {
    const res = await page.goto(`${base}${route}`, { waitUntil: "networkidle", timeout: 15000 });
    const status = res ? res.status() : "no-response";
    const h1 = await page.locator("h1").first().textContent().catch(() => "(no h1)");
    console.log(`OK ${route} -> status=${status} h1="${h1?.trim()}"`);
  } catch (err) {
    console.log(`FAIL ${route} -> ${err.message}`);
    hadError = true;
  }
}

await browser.close();
if (hadError) {
  console.log("SMOKE_CHECK: ISSUES FOUND");
  process.exit(1);
} else {
  console.log("SMOKE_CHECK: ALL CLEAR");
}
