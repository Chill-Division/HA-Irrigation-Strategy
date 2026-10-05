/** Waits until nothing on the page is easing any more (at most 5 s), then two frames, so a check
 * measures what stays. Waiting for the changes running now is not enough: at reduced motion every
 * element eases every property for 0.01 ms, and an element added while its parent's colour is
 * changing starts its own change only as the parent's ends. Text in a page just loaded dark turns
 * light a level a frame, and CI read some still dark on dark. */
export async function settled(page) {
  await page.locator("html").evaluate(async () => {
    const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const frame = () =>
      Promise.race([new Promise((resolve) => requestAnimationFrame(resolve)), wait(100)]);
    const end = performance.now() + 5000;
    for (let still = 0; still < 2 && performance.now() < end;) {
      const running = document
        .getAnimations()
        .filter((a) => a.playState === "running" && a.effect?.getTiming().iterations !== Infinity);
      still = running.length ? 0 : still + 1;
      if (running.length)
        await Promise.race([
          Promise.all(running.map((a) => a.finished.catch(() => {}))),
          wait(end - performance.now()),
        ]);
      await frame();
    }
  });
}
