import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const root = path.join(repo, "public")
const config = JSON.parse(fs.readFileSync(path.join(repo, "sync.config.json"), "utf8"))
const landingPages = new Set(
  Object.values(config.sitePages).map((name) => name.replace(/\.md$/, ".html")),
)

function walk(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const name = path.join(directory, entry.name)
    return entry.isDirectory() ? walk(name) : name.endsWith(".html") ? [name] : []
  })
}

function exists(from, href) {
  href = href.replaceAll("&amp;", "&")
  if (/^(?:[a-z][a-z\d+.-]*:|#|\/\/)/i.test(href)) return true
  let target
  try {
    let raw = decodeURIComponent(href.split("#")[0].split("?")[0])
    if (raw === "/Corleone-s-Blog" || raw.startsWith("/Corleone-s-Blog/")) {
      raw = path.join(root, raw.slice("/Corleone-s-Blog".length))
    }
    if (!raw) return true
    target = path.resolve(path.dirname(from), raw)
  } catch {
    return false
  }
  if (target !== root && !target.startsWith(root + path.sep)) return false
  return [target, target + ".html", path.join(target, "index.html")].some(
    (candidate) => fs.existsSync(candidate) && fs.statSync(candidate).isFile(),
  )
}

const failures = []
const noteLinks = []
let count = 0
for (const file of walk(root)) {
  count++
  const relative = path.relative(root, file)
  const html = fs.readFileSync(file, "utf8")
  const navs = html.match(/<nav class="page-navigation"[\s\S]*?<\/nav>/g) ?? []
  for (const nav of navs) {
    for (const [, href] of nav.matchAll(/href="([^"]+)"/g)) {
      if (!exists(file, href))
        failures.push({ page: relative, target: href, kind: "page navigation" })
    }
  }
  const articles = html.match(/<article\b[^>]*>[\s\S]*?<\/article>/g) ?? []
  for (const article of articles) {
    for (const [, attribute, href] of article.matchAll(/\b(href|src|data)="([^"]+)"/g)) {
      if (!exists(file, href)) {
        const item = {
          page: relative,
          target: href,
          kind: attribute === "href" ? "note link" : "media",
        }
        ;(landingPages.has(relative) ? failures : noteLinks).push(item)
      }
    }
  }
}
for (const landing of landingPages) {
  if (!fs.existsSync(path.join(root, landing)))
    failures.push({ page: landing, kind: "missing landing page" })
}
const report = { pages: count, failures, sourceNoteIssues: noteLinks }
const local = path.join(repo, ".local", "study-sync")
fs.mkdirSync(local, { recursive: true })
fs.writeFileSync(path.join(local, "site-check.json"), JSON.stringify(report, null, 2) + "\n")
console.log(
  "Checked " +
    count +
    " HTML pages. Navigation failures: " +
    failures.length +
    ". Source note issues: " +
    noteLinks.length +
    ".",
)
if (noteLinks.length) {
  console.log(
    "Source note issues are recorded in .local/study-sync/site-check.json; correct the originals in Study.",
  )
}
if (failures.length) {
  for (const failure of failures) console.error(JSON.stringify(failure))
  process.exitCode = 1
}
