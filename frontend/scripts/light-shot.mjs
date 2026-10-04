/** The README's screenshots are in the light theme the dashboard opens in. A browser check that runs
 * dark leaves the dashboard following the device (its saved appearance is Home Assistant), so for a
 * screenshot the device is made light, and dark again after, each once the colours have finished
 * easing between themes. */

/** Until the theme's colours have finished easing (at most 2 s), then two frames. */
export async function settled(page) {
  await page.locator("html").evaluate(async () => {
    const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const running = document
      .getAnimations()
      .filter((a) => a.playState === "running" && a.effect?.getTiming().iterations !== Infinity);
    await Promise.race([Promise.all(running.map((a) => a.finished.catch(() => {}))), wait(2000)]);
    for (let frame = 0; frame < 2; frame++)
      await Promise.race([new Promise((resolve) => requestAnimationFrame(resolve)), wait(100)]);
  });
}

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
