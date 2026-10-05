/** Package one canonical, self-contained application for all supported delivery paths. */
import { readFile, writeFile, mkdir, readdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL("../../", import.meta.url));
const addon = path.join(root, "addons/f2_control/www/public"),
  integration = path.join(root, "custom_components/crop_steering/www");
const html = (await readFile(new URL("../dist/index.html", import.meta.url), "utf8")).replace(
  /^[\t ]+$/gm,
  "",
);
if (/<script[^>]+src=/.test(html) || /<link[^>]+rel="stylesheet"/.test(html))
  throw new Error("Primary dashboard must inline scripts and styles.");
if (/url\(["']?https?:\/\//.test(html))
  throw new Error("Dashboard fonts/assets must not depend on external network requests.");
// The page the app's sidebar entry opens (ingress serves index.html for "/"). It keeps the query and
// the hash, and opens Overview when there is no hash.
const entry =
  '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Crop Steering</title></head><body><p>Opening Crop Steering…</p><noscript><a href="./dashboard.html">Open dashboard</a> · JavaScript is required.</noscript><script>\n' +
  'location.replace("./dashboard.html"+location.search+(location.hash||"#/overview"));\n' +
  "</script></body></html>\n";
// The licences of the packages the dashboard is built from travel with it (vite.config.ts).
const licences = await readFile(
  new URL("../dist/THIRD_PARTY_LICENSES.txt", import.meta.url),
  "utf8",
);
const pages = new Map([
  [addon, { "dashboard.html": html, "index.html": entry, "THIRD_PARTY_LICENSES.txt": licences }],
  [integration, { "dashboard.html": html, "THIRD_PARTY_LICENSES.txt": licences }],
]);
for (const [folder, files] of pages) {
  await mkdir(folder, { recursive: true });
  // A page an earlier build wrote and this one does not would otherwise stay committed, and
  // CI's check that the committed build matches a fresh one cannot see a file left over.
  for (const name of await readdir(folder))
    if (name.endsWith(".html") && !(name in files)) await rm(path.join(folder, name));
  for (const [name, content] of Object.entries(files))
    await writeFile(path.join(folder, name), content);
}
console.log(
  "Packaged " +
    Math.round(Buffer.byteLength(html) / 1024) +
    " KiB native dashboard in integration and add-on.",
);
