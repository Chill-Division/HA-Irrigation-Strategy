/** Graphical room telemetry against the isolated compiled demo. */
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { readFile, mkdir, writeFile } from "node:fs/promises";
import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
const html = await readFile(new URL("../../addons/f2_control/www/public/dashboard.html", import.meta.url));
const out = new URL("../../output/playwright/", import.meta.url);
const file = (name) => new URL(name, out).pathname.replace(/^\/([A-Za-z]:)/, "$1");
// The README's screenshots.
const img = (name) =>
  new URL(`../../img/${name}`, import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
await mkdir(out, { recursive: true });
const server = createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(html);
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({
  headless: true,
  ...(process.platform === "win32" ? { channel: "chrome" } : {}),
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1080 },
  colorScheme: "dark",
});
const errors = [],
  forbidden = [];
async function open(target) {
  const page = await target.newPage();
  page.on("pageerror", (e) => errors.push(e.message));
  await page.route("**/*", (route) => {
    if (
      !route.request().url().startsWith(origin) ||
      new URL(route.request().url()).pathname.startsWith("/api/")
    ) {
      forbidden.push(route.request().url());
      return route.abort();
    }
    return route.continue();
  });
  return page;
}
const page = await open(context);
try {
  await page.goto(`${origin}/dashboard.html?demo=1#/overview`);
  const tank = page.locator("[data-tank-status]");
  await tank.waitFor();
  // The reservoir's own level, as the controller works it out: 640 mm between 125 (full) and 850
  // (empty) is 29%, ahead of the room's level sensor in % (42).
  assert.equal(await tank.locator("[data-tank-level]").getAttribute("data-tank-level"), "29");
  assert.equal(await tank.locator("[data-pump-state]").getAttribute("data-pump-state"), "on");
  assert.match(await tank.innerText(), /17.6 °C/);
  assert.doesNotMatch(await tank.innerText(), /mS\/cm|\bpH\b/, "no tank EC or pH any more");
  assert.ok(await tank.locator("time").getAttribute("datetime"));
  assert.ok(await page.locator('[data-last-irrigation="1"]:visible').getAttribute("datetime"));
  // The tank and its first reading sit as far below the heading as the tank sits from the left.
  const inset = await tank.evaluate((panel) => {
    const box = panel.getBoundingClientRect();
    const heading = panel.querySelector(".panel-heading").getBoundingClientRect();
    const drawing = panel.querySelector(".tank-vessel svg").getBoundingClientRect();
    const first = panel.querySelector(".tank-quality > div").getBoundingClientRect();
    return {
      left: Math.round(drawing.left - box.left),
      top: Math.round(drawing.top - heading.bottom),
      readingTop: Math.round(first.top - heading.bottom),
    };
  });
  assert.ok(
    Math.abs(inset.top - inset.left) <= 2,
    `tank inset: top ${inset.top}, left ${inset.left}`,
  );
  assert.ok(
    Math.abs(inset.readingTop - inset.left) <= 2,
    `first reading inset: top ${inset.readingTop}, left ${inset.left}`,
  );
  await tank.screenshot({ path: file("tank-status.png") });
  await tank.screenshot({ path: img("tank-status.png") });
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    assert.ok(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1),
      `no horizontal overflow at ${width}`,
    );
    const audit = await new AxeBuilder({ page }).include("[data-tank-status]").analyze();
    assert.deepEqual(
      audit.violations.map((v) => ({ id: v.id, impact: v.impact })),
      [],
    );
  }
  await page.screenshot({ path: file("tank-status-mobile.png"), fullPage: true });

  // The Overview stays two screens at most at 1440×800, zones beside the tank, and Map sensors
  // on the tank heading's line.
  await page.setViewportSize({ width: 1440, height: 800 });
  const layout = await page.evaluate(() => {
    const box = (selector) => document.querySelector(selector).getBoundingClientRect();
    // A live Overview has no demo banner: the room it takes here is not counted.
    const banner = document.querySelector(".demo-banner");
    const demo = banner
      ? banner.nextElementSibling.getBoundingClientRect().top - banner.getBoundingClientRect().top
      : 0;
    // Each zone's line on the grow day wraps so it can be read whole: what it adds is not counted.
    const wrapped = [...document.querySelectorAll(".timeline-zone-line")].reduce(
      (sum, line) =>
        sum + line.getBoundingClientRect().height - parseFloat(getComputedStyle(line).lineHeight),
      0,
    );
    return {
      height: document.documentElement.scrollHeight - demo - wrapped,
      window: innerHeight,
      zonesTop: box(".overview-grid > .panel").top,
      tankTop: box("[data-tank-status]").top,
      mapTop: box("[data-tank-status] .tank-actions button").top,
      titleBottom: box("[data-tank-status] .panel-heading h2").bottom,
    };
  });
  assert.ok(
    layout.height <= 2 * layout.window,
    `Overview is ${layout.height}px tall without the demo banner and the zone lines' wrapping, in a ${layout.window}px window`,
  );
  assert.equal(layout.zonesTop, layout.tankTop, "zones and tank share a row");
  assert.ok(layout.mapTop < layout.titleBottom, "the tank's action shares the title's line");

  // Light theme: the panel stays accessible.
  const lightContext = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    colorScheme: "light",
  });
  const light = await open(lightContext);
  await light.goto(`${origin}/dashboard.html?demo=1#/overview`);
  await light.locator("[data-tank-status]").waitFor();
  const audit = await new AxeBuilder({ page: light }).include("[data-tank-status]").analyze();
  assert.deepEqual(
    audit.violations.map((v) => ({ id: v.id, nodes: v.nodes.map((n) => n.target) })),
    [],
    "tank panel accessibility, light",
  );
  await lightContext.close();

  await page.goto(`${origin}/dashboard.html?demo=1&room=room%3Af1_#/overview`);
  await page.waitForFunction(
    () => document.querySelector("[data-tank-level]")?.getAttribute("data-tank-level") === "72",
  );
  assert.equal(await page.locator("[data-pump-state]").getAttribute("data-pump-state"), "off");
  assert.deepEqual(errors, []);
  assert.deepEqual(forbidden, []);
  const checks = [
    "graphical mapped tank readings, no tank EC or pH",
    "zone event timestamps",
    "mobile layout and accessibility, light and dark",
    "Overview two screens at most, zones beside the tank, Map sensors on the heading's line",
    "room isolation",
  ];
  await writeFile(
    new URL("tank-status-verification.json", out),
    JSON.stringify({ checks, errors, forbidden }, null, 2),
  );
  console.log(
    `${checks.length} tank/zone browser checks passed; no console errors or external/API requests.`,
  );
} finally {
  await browser.close();
  await new Promise((resolve) => server.close(resolve));
}
