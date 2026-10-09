/** The integration's and the controller app's brand images: pictures of the dashboard's own mark
 * (the blue tile in the menu's top-left corner), drawn in its light theme's colours and font, so
 * all three always match. Home Assistant 2026.3+ serves `custom_components/crop_steering/brand/`
 * for the integration and HACS shows its icon; the Supervisor shows the app's icon.png and
 * logo.png. There are no dark_ variants: Home Assistant falls back to these, and the blue tile and
 * wordmark read on a dark card as well as on a light one.
 *
 * Run from frontend/ after `npm run build`:  node scripts/make-brand-images.mjs */
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = new URL("../../", import.meta.url);
const html = await readFile(new URL("addons/f2_control/www/public/dashboard.html", root));
const server = createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(html);
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  viewport: { width: 2600, height: 600 },
  colorScheme: "light",
});
await page.goto(`http://127.0.0.1:${server.address().port}/dashboard.html?demo#/overview`);
const glyph = await page
  .locator(".desktop-sidebar .brand-mark svg")
  .evaluate((svg) => svg.outerHTML);
await page.evaluate(() => {
  document.getElementById("root").hidden = true;
  for (const element of [document.documentElement, document.body])
    element.style.background = "transparent";
});

/** The tile `height` px square, its glyph and corners in the menu's proportions (23 and 10 of
 * 38 px), and with `wordmark` the name beside it in the tile's blue. */
async function draw(file, height, wordmark = false) {
  const stage = await page.evaluateHandle(
    ({ glyph, height, wordmark }) => {
      document.getElementById("brand-stage")?.remove();
      const stage = document.createElement("div");
      stage.id = "brand-stage";
      stage.style.cssText = `position:fixed;left:0;top:0;display:flex;align-items:center;gap:${height / 4}px;height:${height}px`;
      const tile = document.createElement("span");
      tile.className = "brand-mark";
      tile.style.cssText = `width:${height}px;height:${height}px;border-radius:${(height * 10) / 38}px`;
      tile.innerHTML = glyph;
      for (const side of ["width", "height"])
        tile.firstElementChild.setAttribute(side, String((height * 23) / 38));
      stage.append(tile);
      if (wordmark) {
        // As the menu writes it: the initials, PHASE, heavier than the word after them.
        const name = document.createElement("span");
        const initials = document.createElement("b");
        initials.textContent = "PHASE";
        initials.style.cssText = "font-weight:800;letter-spacing:0.02em";
        name.append(initials, " Steering");
        name.style.cssText = `font-size:${height * 0.44}px;font-weight:500;letter-spacing:-0.02em;color:var(--primary);white-space:nowrap`;
        stage.append(name);
      }
      document.body.append(stage);
      return stage;
    },
    { glyph, height, wordmark },
  );
  await stage.screenshot({ path: fileURLToPath(new URL(file, root)), omitBackground: true });
  console.log(file);
}

const brand = "custom_components/crop_steering/brand/";
await draw(`${brand}icon.png`, 256);
await draw(`${brand}icon@2x.png`, 512);
await draw(`${brand}logo.png`, 256, true);
await draw(`${brand}logo@2x.png`, 512, true);
await draw("addons/f2_control/icon.png", 256);
await draw("addons/f2_control/logo.png", 256, true);
await browser.close();
server.close();
