import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"
import { parse, serialize } from "parse5"

function filesIn(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const name = path.join(directory, entry.name)
    return entry.isDirectory() ? filesIn(name) : [name]
  })
}

export function cleanSite(root, basePath = "/Corleone-s-Blog") {
  const files = new Set(
    filesIn(root).map((file) => path.relative(root, file).split(path.sep).join("/")),
  )
  const removed = []
  function exists(from, href) {
    if (!href || /^(?:[a-z][a-z\d+.-]*:|#|\/\/)/i.test(href)) return true
    try {
      let target = decodeURIComponent(new URL(href, "https://local.invalid/" + from).pathname)
      if (basePath && (target === basePath || target.startsWith(basePath + "/")))
        target = target.slice(basePath.length)
      target = target.replace(/^\//, "").replace(/\/$/, "")
      return [target, target + ".html", target ? target + "/index.html" : "index.html"].some(
        (name) => files.has(name),
      )
    } catch {
      return false
    }
  }
  for (const file of files) {
    if (!file.endsWith(".html")) continue
    const original = fs.readFileSync(path.join(root, file), "utf8")
    const document = parse(original)
    let changed = false
    function visit(parent) {
      const result = []
      for (const node of parent.childNodes ?? []) {
        const attribute =
          node.tagName === "a"
            ? "href"
            : node.tagName === "object"
              ? "data"
              : ["img", "iframe", "video", "audio", "source", "embed"].includes(node.tagName)
                ? "src"
                : undefined
        const target = node.attrs?.find((item) => item.name === attribute)?.value
        if (target && !exists(file, target)) {
          removed.push({ page: file, target, kind: node.tagName === "a" ? "link" : "media" })
          changed = true
          if (node.tagName === "a") {
            visit(node)
            for (const child of node.childNodes ?? []) {
              child.parentNode = parent
              result.push(child)
            }
          }
          continue
        }
        visit(node)
        result.push(node)
      }
      if (parent.childNodes) parent.childNodes = result
    }
    visit(document)
    if (changed) fs.writeFileSync(path.join(root, file), serialize(document))
  }
  const indexFile = path.join(root, "static/contentIndex.json")
  if (fs.existsSync(indexFile)) {
    const index = JSON.parse(fs.readFileSync(indexFile, "utf8"))
    const normalize = (slug) => slug.replace(/(^|\/)index$/, "").replace(/\/$/, "")
    const nodes = new Set(Object.keys(index).map(normalize))
    for (const page of Object.values(index)) {
      if (Array.isArray(page.links))
        page.links = page.links.filter((slug) => nodes.has(normalize(slug)))
    }
    fs.writeFileSync(indexFile, JSON.stringify(index))
  }
  return removed
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
  const removed = cleanSite(path.join(repo, "public"))
  const report = path.join(repo, ".local/study-sync/pruned-links.json")
  fs.mkdirSync(path.dirname(report), { recursive: true })
  fs.writeFileSync(report, JSON.stringify(removed, null, 2) + "\n")
  console.log(`Removed ${removed.length} unavailable links/media; dangling graph edges removed.`)
}
