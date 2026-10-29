import { test } from "node:test"
import assert from "node:assert/strict"
import { resolveStudyLink } from "../plugins/study-links/resolve.js"

test("relative project links stay relative to their note", () => {
  const source = "research/project/edge.llm/code/snapdragonnpu/00-roadmap"
  const slugs = new Set(["research/project/edge.llm/scope"])
  assert.equal(
    resolveStudyLink(source, "../../SCOPE#example", slugs),
    "/research/project/edge.llm/scope#example",
  )
})

test("nearby note wins over a folder with the same name", () => {
  const slugs = new Set(["note/me/反馈/index"])
  assert.equal(resolveStudyLink("note/me/反馈/分析", "反馈", slugs), "/note/me/反馈/index")
})

test("vault-root paths and folder indexes remain valid", () => {
  const slugs = new Set(["note/index", "research/project/index"])
  assert.equal(resolveStudyLink("blog/index", "Note/index", slugs), "/note/index")
  assert.equal(
    resolveStudyLink("blog/index", "Research/Project/", slugs),
    "/research/project/index",
  )
})

test("external links, anchors, and absent targets are left intact", () => {
  for (const target of ["https://example.com", "mailto:a@example.com", "#section", "missing.png"]) {
    assert.equal(resolveStudyLink("note/example", target, new Set()), target)
  }
})

test("generated hashtag URLs resolve from nested notes", () => {
  assert.equal(
    resolveStudyLink("research/project/edge.llm/plan", "../../../tags/26049", new Set()),
    "/tags/26049",
  )
})

test("a unique same-name folder index or nested SVG is resolved", () => {
  const slugs = new Set(["note/me/运算放大器/index", "note/cs/assets/diagram.svg"])
  assert.equal(
    resolveStudyLink("note/me/运算放大器/反馈/分析", "运算放大器", slugs),
    "/note/me/运算放大器/index",
  )
  assert.equal(
    resolveStudyLink("note/cs/example", "diagram.svg", slugs),
    "/note/cs/assets/diagram.svg",
  )
})

test("dots in note titles preserve the exact emitted filename on Linux", () => {
  const slugs = new Set(["note/cs/gense/lec1.intro"])
  assert.equal(
    resolveStudyLink("index", "Note/CS/GenSE/Lec1.Intro", slugs),
    "/note/cs/gense/lec1.intro",
  )
})
