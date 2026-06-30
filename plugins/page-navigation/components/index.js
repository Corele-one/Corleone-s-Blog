import { h } from "preact"
import { resolveRelative } from "@quartz-community/utils"

const DEFAULT_OPTIONS = {
  previousLabel: "上一篇",
  nextLabel: "下一篇",
  includeIndex: false,
}

function titleFor(page) {
  const frontmatterTitle = page.frontmatter?.title
  if (frontmatterTitle) return frontmatterTitle

  const path = page.relativePath ?? page.filePath ?? page.slug ?? ""
  const filename = path.split("/").at(-1) ?? page.slug ?? ""
  return decodeURIComponent(filename.replace(/\.md$/, "").replace(/-/g, " "))
}

function parentOf(slug) {
  const parts = slug.split("/")
  parts.pop()
  return parts.join("/")
}

function pageWeight(page) {
  const source = page.relativePath ?? page.filePath ?? page.slug ?? ""
  return source.split("/").at(-1)?.replace(/\.md$/, "").toLocaleLowerCase() ?? ""
}

function isMarkdownPage(page) {
  const path = page.relativePath ?? page.filePath ?? ""
  return path.endsWith(".md")
}

function shouldShowPage(page, options) {
  const slug = page.slug ?? ""
  if (!isMarkdownPage(page)) return false
  if (slug === "404") return false
  if (slug === "tags" || slug.startsWith("tags/")) return false
  if (!options.includeIndex && (slug === "index" || slug.endsWith("/index"))) return false
  return true
}

export function PageNavigation(userOptions = {}) {
  const options = { ...DEFAULT_OPTIONS, ...userOptions }

  function PageNavigationComponent({ fileData, allFiles }) {
    const currentSlug = fileData.slug
    if (!currentSlug) return null
    if (!shouldShowPage(fileData, options)) return null

    const currentParent = parentOf(currentSlug)
    const pages = allFiles
      .filter((page) => {
        const slug = page.slug
        if (!slug || slug === currentSlug) return false
        if (!shouldShowPage(page, options)) return false
        return parentOf(slug) === currentParent
      })
      .sort((a, b) => {
        const byPath = pageWeight(a).localeCompare(pageWeight(b), "zh-CN", {
          numeric: true,
          sensitivity: "base",
        })
        if (byPath !== 0) return byPath
        return titleFor(a).localeCompare(titleFor(b), "zh-CN", { numeric: true })
      })

    const orderedPages = [...pages, fileData].sort((a, b) =>
      pageWeight(a).localeCompare(pageWeight(b), "zh-CN", {
        numeric: true,
        sensitivity: "base",
      }),
    )

    const index = orderedPages.findIndex((page) => page.slug === currentSlug)
    const previous = index > 0 ? orderedPages[index - 1] : undefined
    const next = index >= 0 && index < orderedPages.length - 1 ? orderedPages[index + 1] : undefined

    if (!previous && !next) return null

    const link = (page, direction, label) =>
      page
        ? h(
            "a",
            {
              class: `page-navigation-link ${direction}`,
              href: resolveRelative(currentSlug, page.slug),
            },
            h("span", { class: "page-navigation-label" }, `${label}:`),
            h("span", { class: "page-navigation-title" }, titleFor(page)),
          )
        : h("span", {
            class: `page-navigation-link ${direction} placeholder`,
            "aria-hidden": "true",
          })

    return h(
      "nav",
      { class: "page-navigation", "aria-label": "Page navigation" },
      link(previous, "previous", options.previousLabel),
      link(next, "next", options.nextLabel),
    )
  }

  PageNavigationComponent.css = `
.page-navigation {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 1rem;
  margin: 3rem 0 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--lightgray);
}

.page-navigation-link {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
  color: var(--secondary);
  text-decoration: none;
}

.page-navigation-link.next {
  align-items: flex-end;
  text-align: right;
}

.page-navigation-link:hover .page-navigation-title {
  text-decoration: underline;
}

.page-navigation-label {
  color: var(--gray);
  font-size: 0.85rem;
}

.page-navigation-title {
  overflow-wrap: anywhere;
  font-size: 1rem;
  font-weight: 600;
}

.page-navigation-link.placeholder {
  pointer-events: none;
}

@media all and (max-width: 600px) {
  .page-navigation {
    grid-template-columns: 1fr;
  }

  .page-navigation-link.next {
    align-items: flex-start;
    text-align: left;
  }

  .page-navigation-link.placeholder {
    display: none;
  }
}
`

  return PageNavigationComponent
}
