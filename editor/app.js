"use strict"
const $ = (id) => document.getElementById(id)
const token = document.querySelector('meta[name="editor-token"]').content
let state = null
let page = null
let savedText = ""
let filter = "all"
let busy = false
let previewReady = false
let activeJob = null
let loadingPage = 0

async function api(route, body) {
  const response = await fetch(route, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      "X-Editor-Token": token,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  const value = await response.json()
  if (!response.ok) throw new Error(value.error || "操作失败")
  return value
}
function message(text, error = false) {
  $("message").textContent = text
  $("message").hidden = !text
  $("message").classList.toggle("error", error)
}
function dirty() {
  return page && $("content").value !== savedText
}
function controls() {
  for (const id of ["sync", "build", "publish", "hide", "reset", "remove-selection"])
    $(id).disabled = busy || !state || (["hide", "reset", "remove-selection"].includes(id) && !page)
  $("save").disabled = busy || !page || !dirty()
  $("content").readOnly = busy
  $("hide").disabled ||=
    page?.path === "index.md" || Boolean(page?.hiddenBy && page.hiddenBy !== page.path)
  $("reset").disabled ||= !page?.edited
  $("save-state").textContent = dirty()
    ? "有未保存的修改。保存后，下次同步仍会保留。"
    : "已保存的博客修改会保留，Study 原笔记不变。"
}
function make(tag, text, className) {
  const element = document.createElement(tag)
  if (text !== undefined) element.textContent = text
  if (className) element.className = className
  return element
}
function renderList() {
  const search = $("search").value.toLocaleLowerCase()
  const rows = state.pages.filter(
    (item) =>
      (filter !== "edited" || item.edited || item.conflict) &&
      (filter !== "hidden" || item.hiddenBy) &&
      (item.title + " " + item.path).toLocaleLowerCase().includes(search),
  )
  $("pages").replaceChildren()
  for (const row of rows) {
    const button = make("button", undefined, "page-row")
    button.classList.toggle("selected", page?.path === row.path)
    button.classList.toggle("is-hidden", Boolean(row.hiddenBy))
    button.setAttribute("aria-pressed", String(page?.path === row.path))
    const title = make("strong", row.title)
    if (row.conflict || row.edited || row.hiddenBy)
      title.append(
        make("span", row.conflict ? "需对比" : row.hiddenBy ? "隐藏" : "已编辑", "marker"),
      )
    button.append(title, make("small", row.path))
    button.onclick = () => selectPage(row.path)
    $("pages").append(button)
  }
  $("page-count").textContent =
    `${rows.length} 页 · ${state.pages.filter((x) => !x.hiddenBy).length} 页准备发布`
  $("rules").replaceChildren()
  for (const rule of state.excludedPaths) {
    const line = make("div", undefined, "rule")
    const button = make("button", "恢复")
    button.disabled = busy
    button.onclick = async () => {
      if (!(await leaveEdits())) return
      await operate(async () => {
        const result = await api("/api/rules/restore", { path: rule })
        await reload(true)
        previewReady = false
        message(
          result.syncError
            ? `规则已保存；同步待处理：${result.syncError}`
            : "已恢复。发布后才会出现在网站。",
          Boolean(result.syncError),
        )
      })
    }
    line.append(make("span", rule), button)
    $("rules").append(line)
  }
}
async function reload(reloadCurrent = false) {
  state = await api("/api/pages")
  $("source").textContent = `笔记来源：${state.source}`
  if (reloadCurrent && page) await loadPage(page.path)
  renderList()
  controls()
}
async function leaveEdits() {
  return !dirty() || window.confirm("当前有未保存的修改。放弃这些修改并继续？")
}
async function loadPage(path) {
  const version = ++loadingPage
  const loaded = await api("/api/page?path=" + encodeURIComponent(path))
  if (version !== loadingPage) return
  page = loaded
  savedText = page.content
  $("content").value = page.content
  $("original").value = page.original
  $("page-path").textContent = page.path
  $("page-title").textContent = state.pages.find((x) => x.path === path)?.title || path
  $("conflict").hidden = !page.conflict
  $("original-panel").open = page.conflict
  $("hide").textContent = page.hiddenBy ? "恢复此页" : "隐藏此页"
  $("hide").title =
    page.hiddenBy && page.hiddenBy !== page.path
      ? `此页由 ${page.hiddenBy} 目录规则隐藏`
      : "隐藏只影响网站发布"
  $("badges").replaceChildren()
  for (const [text, warning] of [
    [page.hiddenBy ? "当前隐藏" : "准备发布", Boolean(page.hiddenBy)],
    [page.edited ? "博客专用版本" : "与原笔记一致", false],
    [page.conflict ? "原笔记已更新" : "", true],
  ]) {
    if (text) $("badges").append(make("span", text, "badge" + (warning ? " warning" : "")))
  }
  renderList()
  controls()
  showPreview()
}
async function selectPage(path) {
  if (busy || !(await leaveEdits())) return
  try {
    message("")
    await loadPage(path)
    document.body.classList.remove("show-pages")
  } catch (error) {
    message(error.message, true)
  }
}
async function operate(action) {
  if (busy) return
  busy = true
  controls()
  try {
    await action()
  } catch (error) {
    message(error.message, true)
  } finally {
    busy = false
    controls()
    if (state) renderList()
  }
}
async function change(action) {
  if (!page) return
  if (action !== "save" && !(await leaveEdits())) return
  if (
    action === "reset" &&
    !window.confirm("恢复原笔记内容？当前博客专用版本将被移除，Study 不变。")
  )
    return
  await operate(async () => {
    const result = await api("/api/page", {
      action,
      path: page.path,
      content: $("content").value,
      sourceHash: page.sourceHash,
      revision: page.revision,
    })
    previewReady = false
    await reload(true)
    message(
      result.syncError
        ? `博客选择已保存；同步待处理：${result.syncError}`
        : action === "hide"
          ? "此页已从本地发布副本中移除。点击发布后线上生效。"
          : "已保存。可预览后发布。",
      Boolean(result.syncError),
    )
  })
}
function tab(preview) {
  $("editing").hidden = preview
  $("previewing").hidden = !preview
  $("save-tools").hidden = preview
  $("edit-tab").classList.toggle("active", !preview)
  $("preview-tab").classList.toggle("active", preview)
  if (preview) showPreview()
}
function showPreview() {
  const ready = previewReady && page && !page.hiddenBy
  $("frame-wrap").hidden = !ready
  $("preview-empty").hidden = ready
  $("preview-empty").textContent = page?.hiddenBy
    ? "此页已隐藏，不会生成公开网页。"
    : "点击「本地预览」生成最新网页。保存内容不会自动发布。"
  if (ready) {
    const url =
      state.previewUrl +
      "/" +
      page.previewPath.split("/").map(encodeURIComponent).join("/") +
      "?v=" +
      Date.now()
    $("preview-frame").src = url
    $("open-preview").href = url
  } else $("open-preview").removeAttribute("href")
}
const names = {
  "sync-preview": "同步预览",
  "sync-apply": "应用同步",
  build: "构建本地预览",
  publish: "发布网站",
}
async function runJob(kind, existingId = null) {
  if (busy) return
  if (dirty()) return message("请先保存当前修改，再同步、预览或发布。", true)
  busy = true
  controls()
  $("task-panel").hidden = false
  $("task-panel").open = true
  $("apply-sync").hidden = true
  $("cancel-job").hidden = false
  $("task-title").textContent = names[kind] + " · 正在进行"
  $("task-log").textContent = "正在开始…"
  try {
    const { id } = existingId ? { id: existingId } : await api("/api/jobs", { kind })
    activeJob = id
    let job
    do {
      await new Promise((resolve) => setTimeout(resolve, 900))
      job = await api("/api/jobs/" + id)
      $("task-log").textContent = job.log.replace(/\x1b\[[0-9;]*m/g, "")
      $("task-log").scrollTop = $("task-log").scrollHeight
    } while (job.status === "running")
    const success = job.status === "done"
    $("task-title").textContent =
      names[kind] + (success ? " · 已完成" : job.status === "cancelled" ? " · 已停止" : " · 未完成")
    $("apply-sync").hidden = !(success && kind === "sync-preview")
    if (success && kind === "build") previewReady = true
    if (success && kind === "sync-apply") previewReady = false
    await reload(true)
    if (success && kind === "build") tab(true)
    message(
      success
        ? kind === "sync-preview"
          ? "预览完成。确认变化后，点击「应用这次同步」。"
          : kind === "publish"
            ? "已提交并推送，网站部署进度可在任务记录中查看。"
            : kind === "sync-apply"
              ? "同步已完成，博客编辑与隐藏规则均已保留。"
              : "本地网页已更新，可在预览中检查。"
        : "任务未完成。请查看任务记录；已保存的博客编辑仍然保留。",
      !success,
    )
  } catch (error) {
    message(error.message, true)
  } finally {
    busy = false
    activeJob = null
    $("cancel-job").hidden = true
    controls()
    if (state) renderList()
  }
}
$("search").oninput = () => state && renderList()
document.querySelectorAll("[data-filter]").forEach((button) => {
  button.onclick = () => {
    filter = button.dataset.filter
    document
      .querySelectorAll("[data-filter]")
      .forEach((b) => b.classList.toggle("active", b === button))
    if (state) renderList()
  }
})
$("menu").onclick = () => document.body.classList.toggle("show-pages")
$("content").oninput = controls
$("save").onclick = () => change("save")
$("reset").onclick = () => change("reset")
$("hide").onclick = () => change(page?.hiddenBy ? "show" : "hide")
$("remove-selection").onmousedown = (event) => event.preventDefault()
$("remove-selection").onclick = () => {
  const field = $("content")
  if (field.selectionStart === field.selectionEnd) return message("先在正文中选中想删除的文字。")
  field.setRangeText("", field.selectionStart, field.selectionEnd, "start")
  field.focus()
  controls()
  message("已删除选中的文字。点击「保存博客版本」保留修改。")
}
$("sync").onclick = () => runJob("sync-preview")
$("apply-sync").onclick = () => runJob("sync-apply")
$("build").onclick = () => runJob("build")
$("publish").onclick = () => runJob("publish")
$("cancel-job").onclick = () =>
  activeJob &&
  api("/api/jobs/cancel", {}).then(
    () => message("已请求停止任务。"),
    (error) => message(error.message, true),
  )
$("edit-tab").onclick = () => tab(false)
$("preview-tab").onclick = () => tab(true)
$("preview-current").onclick = showPreview
$("mobile-preview").onclick = () => $("frame-wrap").classList.toggle("mobile")
window.addEventListener("beforeunload", (event) => {
  if (dirty()) {
    event.preventDefault()
    event.returnValue = ""
  }
})
window.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
    event.preventDefault()
    if (dirty() && !busy) change("save")
  }
})
;(async () => {
  try {
    await reload()
    await loadPage("index.md")
    if (state.running) {
      const running = await api("/api/jobs/" + state.running)
      await runJob(running.kind, running.id)
    }
  } catch (error) {
    message(error.message, true)
  }
})()
