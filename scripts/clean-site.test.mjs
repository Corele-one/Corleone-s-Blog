import { test } from "node:test"
import assert from "node:assert/strict"
import fs from "node:fs"
import os from "node:os"
import path from "node:path"
import { cleanSite } from "./clean_site.mjs"

test("missing links become plain text, missing media disappear, and graph edges are pruned", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "blog-clean-"))
  try {
    fs.mkdirSync(path.join(root, "note"))
    fs.mkdirSync(path.join(root, "static"))
    fs.writeFileSync(
      path.join(root, "index.html"),
      '<html><body><a href="note/good">Good</a><a href="note/absent"><b>Keep these words</b></a><img src="missing.png"><object data="missing.svg"></object><a href="https://example.com">Web</a></body></html>',
    )
    fs.writeFileSync(path.join(root, "note/good.html"), '<a href="../">Home</a>')
    fs.writeFileSync(
      path.join(root, "static/contentIndex.json"),
      JSON.stringify({
        index: { links: ["note/good", "note/absent"] },
        "note/good": { links: [] },
      }),
    )
    const removed = cleanSite(root)
    assert.equal(removed.length, 3)
    const html = fs.readFileSync(path.join(root, "index.html"), "utf8")
    assert.ok(html.includes("Keep these words"))
    assert.ok(!html.includes("note/absent"))
    assert.ok(!html.includes("missing.png"))
    assert.ok(!html.includes("missing.svg"))
    assert.ok(html.includes('href="note/good"'))
    assert.deepEqual(
      JSON.parse(fs.readFileSync(path.join(root, "static/contentIndex.json"))).index.links,
      ["note/good"],
    )
    assert.deepEqual(cleanSite(root), [])
  } finally {
    fs.rmSync(root, { recursive: true, force: true })
  }
})
