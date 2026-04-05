import { mkdir, readFile, readdir, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { marked } from "marked";

const root = process.cwd();
const contentDir = path.join(root, "content");
const publicDir = path.join(root, "public");

async function walk(dir) {
  const out = [];
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...(await walk(full)));
    } else {
      out.push(full);
    }
  }
  return out;
}

async function build() {
  await rm(publicDir, { recursive: true, force: true });
  await mkdir(publicDir, { recursive: true });

  let files = [];
  try {
    const contentStat = await stat(contentDir);
    if (contentStat.isDirectory()) {
      files = await walk(contentDir);
    }
  } catch {
    // Keep empty site if no content exists yet.
  }

  const links = [];
  for (const file of files) {
    const rel = path.relative(contentDir, file);
    const out = path.join(publicDir, rel.replace(/\.md$/i, ".html"));
    const outDir = path.dirname(out);
    await mkdir(outDir, { recursive: true });

    if (file.endsWith(".md")) {
      const src = await readFile(file, "utf8");
      const html = marked.parse(src);
      await writeFile(out, `<!doctype html><html><body>${html}</body></html>`, "utf8");
      links.push(`<li><a href="${rel.replace(/\.md$/i, ".html")}">${rel}</a></li>`);
    }
  }

  await writeFile(
    path.join(publicDir, "index.html"),
    `<!doctype html><html><body><h1>SmartWiki2 Published Wiki</h1><ul>${links.join("")}</ul></body></html>`,
    "utf8"
  );
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
