/** The README's screenshots are in the light theme the dashboard opens in. A browser check that runs
 * dark leaves the dashboard following the device (its saved appearance is Home Assistant), so for a
 * screenshot the device is made light, and dark again after, each once the colours have finished
 * easing between themes. */
import { settled } from "./settled.mjs";

/** `target` (the page or a part of it) screenshotted with `options` in the light theme, the page then
 * dark again as its checks run. */
export async function lightShot(page, target, options) {
  await page.emulateMedia({ colorScheme: "light" });
  await page.waitForFunction(() => !document.documentElement.classList.contains("dark"));
  await settled(page);
  await target.screenshot(options);
  await page.emulateMedia({ colorScheme: "dark" });
  await page.waitForFunction(() => document.documentElement.classList.contains("dark"));
  await settled(page);
}
