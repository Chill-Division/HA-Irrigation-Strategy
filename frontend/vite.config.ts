import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath, URL } from "node:url";

const RULE = "=".repeat(80);
// Tailwind's plugin writes its CSS, its reset included, into the bundle without the package being
// one of the build's modules.
const ALSO_BUNDLED = ["tailwindcss"];

/** THIRD_PARTY_LICENSES.txt: the licence of every npm package the dashboard is built from, which
 * scripts/package.mjs ships beside it, since their licences ask that it travels with every copy.
 * Sorted and undated, so the build stays the same byte for byte (CI compares the committed
 * dashboard with a fresh build). */
function thirdPartyLicences(): Plugin {
  return {
    name: "third-party-licences",
    apply: "build",
    generateBundle() {
      const packages = new Map<string, { title: string; text: string }>();
      const add = (dir: string) => {
        const pkg = JSON.parse(readFileSync(path.join(dir, "package.json"), "utf8"));
        const key = `${pkg.name}@${pkg.version}`;
        if (packages.has(key)) return;
        const kind =
          typeof pkg.license === "string" ? pkg.license : (pkg.license?.type ?? "see the package");
        const file = readdirSync(dir)
          .sort()
          .find((name) => /^(licen[cs]e|copying)(\.|-|$)/i.test(name));
        const repository =
          typeof pkg.repository === "string" ? pkg.repository : pkg.repository?.url;
        const text = file
          ? readFileSync(path.join(dir, file), "utf8").replace(/\r\n?/g, "\n").trim()
          : `The package carries no licence file. Its licence is ${kind}${repository ? `: ${repository}` : "."}`;
        packages.set(key, { title: `${pkg.name} ${pkg.version} (${kind})`, text });
      };
      for (const raw of this.getModuleIds()) {
        const id = raw.replace(/^\0/, "").split("?")[0].replace(/\\/g, "/");
        const at = id.lastIndexOf("/node_modules/");
        if (at < 0) continue;
        const parts = id.slice(at + "/node_modules/".length).split("/");
        add(
          id.slice(0, at) +
            "/node_modules/" +
            parts.slice(0, parts[0].startsWith("@") ? 2 : 1).join("/"),
        );
      }
      for (const name of ALSO_BUNDLED)
        add(fileURLToPath(new URL(`./node_modules/${name}`, import.meta.url)));
      const entries = [...packages.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
      const source =
        "Third-party software in the PHASE Steering dashboard\n\n" +
        "The dashboard (dashboard.html) is built from these open-source packages, each used under its\n" +
        "licence, which follows its name. PHASE Steering itself is under the MIT licence in LICENSE.\n" +
        entries.map(([, { title, text }]) => `\n${RULE}\n${title}\n${RULE}\n\n${text}\n`).join("");
      this.emitFile({ type: "asset", fileName: "THIRD_PARTY_LICENSES.txt", source });
    },
  };
}

export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss(), viteSingleFile(), thirdPartyLicences()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  build: { target: "es2022", reportCompressedSize: true },
});
