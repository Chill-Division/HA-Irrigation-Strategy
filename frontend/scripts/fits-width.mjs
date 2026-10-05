/** Whether a page fits its window's width, measured once it has caught up with the window. A page
 * just resized reaches its layout some frames later, and on a busy CI runner more than two: measured
 * too soon, the top bar can still be as wide as the window was (seen in CI on the Reservoir checks,
 * after 390 px). So the page (or a frame) gets up to two seconds to fit. One that still does not
 * overflows for real, and the failure names what sticks out. */
export async function fitsWidth(page, label = "Page has horizontal overflow") {
  const fits = await page
    .waitForFunction(() => document.documentElement.scrollWidth <= innerWidth + 1, null, {
      polling: "raf",
      timeout: 2_000,
    })
    .then(
      () => true,
      () => false,
    );
  if (fits) return;
  // What sticks out: the outermost elements past the window's edge, leaving out any a box of their
  // own clips (a wide table in its scrolling box widens nothing).
  const wide = await page.evaluate(() => {
    const past = (element) => element.getBoundingClientRect().right > innerWidth + 1;
    const clipped = (element) => {
      for (let box = element.parentElement; box; box = box.parentElement)
        if (getComputedStyle(box).overflowX !== "visible" && !past(box)) return true;
      return false;
    };
    return [...document.querySelectorAll("body *")]
      .filter((element) => past(element) && !clipped(element))
      .filter((element) => !element.parentElement || !past(element.parentElement))
      .slice(0, 5)
      .map((element) => [element.tagName.toLowerCase(), ...element.classList].join("."));
  });
  throw new Error(`${label}: ${wide.join(", ") || "the page is wider than the window"}`);
}
