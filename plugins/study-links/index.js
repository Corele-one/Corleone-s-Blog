import { visit } from "unist-util-visit"
import { resolveRelative } from "@quartz-community/utils"
import { resolveStudyLink } from "./resolve.js"

export function StudyLinks() {
  return {
    name: "StudyLinks",
    htmlPlugins(ctx) {
      const slugs = new Set(ctx.allSlugs)
      return [
        () => (tree, file) => {
          visit(tree, "element", (node) => {
            const attribute =
              node.tagName === "a"
                ? "href"
                : ["img", "video", "audio", "iframe"].includes(node.tagName)
                  ? "src"
                  : undefined
            if (attribute && typeof node.properties?.[attribute] === "string") {
              node.properties[attribute] = resolveStudyLink(
                file.data.slug,
                node.properties[attribute],
                slugs,
              )
            }
            if (node.tagName === "object" && typeof node.properties?.data === "string") {
              const target = resolveStudyLink(file.data.slug, node.properties.data, slugs)
              if (target.startsWith("/") && !target.startsWith("//")) {
                node.properties.data = resolveRelative(file.data.slug, target.slice(1))
              }
            }
          })
        },
      ]
    },
  }
}
