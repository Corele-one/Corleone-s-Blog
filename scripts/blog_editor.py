#!/usr/bin/env python3
"""Local Blog Studio: publication editing, Study sync, preview and publishing."""
import argparse
import contextlib
import fcntl
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer, SimpleHTTPRequestHandler
import io
import json
import os
import re
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import threading
from urllib.parse import parse_qs, unquote, urlsplit
import webbrowser

import sync_study as sync
from blog_publication import atomic_write, fingerprint, hidden_by, load_policy, override_path, save_policy, scoped_path

ROOT = Path(__file__).resolve().parents[1]


def preview_path(name):
    parts = re.sub(r"\s", "-", name[:-3].replace("&", "-and-").replace("%", "-percent").replace("?", "").replace("#", "")).lower().split("/")
    if parts[-1] == "_index" or len(parts) > 1 and parts[-1] == parts[-2]:
        parts[-1] = "index"
    return "/".join(parts) + ".html"


class Conflict(ValueError):
    pass


class Studio:
    def __init__(self, repo, source):
        self.repo, self.source = repo.resolve(), source.resolve()
        self.token = secrets.token_urlsafe(32)
        self.mutex = threading.RLock()
        self.jobs = {}
        self.running = None
        self.preview_url = ""

    def catalog(self):
        config = json.loads((self.repo / "sync.config.json").read_text())
        pages = {}
        for folder in config["include"]:
            base = self.source / folder
            if not base.is_dir():
                continue
            if any(p.is_symlink() for p in [base, *base.parents]):
                raise ValueError("笔记目录不能包含符号链接")
            for directory, dirs, names in os.walk(base, followlinks=False):
                parent = Path(directory)
                dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in config["excludeNames"] and not (parent / d).is_symlink())
                for name in sorted(names):
                    path = parent / name
                    if path.suffix == ".md" and not name.startswith(".") and not path.is_symlink():
                        pages[path.relative_to(self.source).as_posix()] = path
        for source, destination in config["sitePages"].items():
            scoped_path(destination, config)
            original = self.repo / source
            if any(p.is_symlink() for p in [original, *original.parents]):
                raise ValueError("站点说明不能包含符号链接")
            pages[destination] = original
        return pages

    def revision(self, name, original, policy):
        entry = policy["overrides"].get(name)
        replacement = override_path(self.repo, name)
        value = {"source": fingerprint(original), "entry": entry, "rules": policy["excludedPaths"],
                 "replacement": fingerprint(replacement) if replacement.exists() else None}
        return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

    def state(self):
        with self.mutex:
            policy = load_policy(self.repo)
            rows = []
            for name, original in sorted(self.catalog().items()):
                entry = policy["overrides"].get(name)
                rows.append({"path": name, "title": original.stem if name != "index.md" else "网站首页",
                             "hiddenBy": hidden_by(name, policy), "edited": entry is not None,
                             "conflict": bool(entry and entry["baseHash"] != fingerprint(original))})
            return {"pages": rows, "excludedPaths": policy["excludedPaths"], "source": str(self.source),
                    "previewUrl": self.preview_url, "running": self.running}

    def page(self, name):
        with self.mutex:
            catalog = self.catalog()
            if name not in catalog:
                raise ValueError("页面不在分享目录内")
            original = catalog[name]
            policy = load_policy(self.repo)
            entry = policy["overrides"].get(name)
            source_text = original.read_text()
            text = override_path(self.repo, name).read_text() if entry else source_text
            return {"path": name, "content": text, "original": source_text,
                    "previewPath": preview_path(name),
                    "sourceHash": fingerprint(original), "revision": self.revision(name, original, policy),
                    "hiddenBy": hidden_by(name, policy), "edited": entry is not None,
                    "conflict": bool(entry and entry["baseHash"] != fingerprint(original))}

    @contextlib.contextmanager
    def editing(self):
        with self.mutex:
            if self.running:
                raise Conflict("任务正在运行，请完成后再编辑")
            lock_file = self.repo / ".local/study-sync/lock"
            lock_file.parent.mkdir(parents=True, exist_ok=True)
            with lock_file.open("a") as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise Conflict("另一个同步进程正在运行")
                yield

    def apply_saved(self):
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                sync.synchronize(self.source, self.repo, apply=True)
            return {"saved": True, "syncError": None}
        except (ValueError, OSError) as error:
            # Keep the user's saved draft when an unrelated source conflict blocks sync.
            return {"saved": True, "syncError": str(error)}

    def change(self, body):
        name = body.get("path")
        action = body.get("action")
        with self.editing():
            current = self.page(name)
            if body.get("revision") != current["revision"] or body.get("sourceHash") != current["sourceHash"]:
                raise Conflict("页面或原笔记已发生变化，请重新载入后再保存")
            policy = load_policy(self.repo)
            target = override_path(self.repo, name)
            if action == "save":
                text = body.get("content")
                if not isinstance(text, str) or len(text.encode()) > 2_000_000:
                    raise ValueError("内容必须是小于 2 MB 的 Markdown")
                for label, pattern in sync.SECRET_PATTERNS.items():
                    if pattern.search(text):
                        raise ValueError(f"检测到疑似 {label}，请移除后再保存；不会显示其值")
                old_text = target.read_bytes() if target.exists() else None
                atomic_write(target, text.encode())
                policy["overrides"][name] = {"baseHash": current["sourceHash"]}
                try:
                    save_policy(self.repo, policy)
                except BaseException:
                    if old_text is None:
                        target.unlink(missing_ok=True)
                    else:
                        atomic_write(target, old_text)
                    raise
            elif action == "reset":
                policy["overrides"].pop(name, None)
                save_policy(self.repo, policy)
                target.unlink(missing_ok=True)
            elif action == "hide":
                if name == "index.md":
                    raise ValueError("首页不能隐藏，可以编辑首页内容")
                if not hidden_by(name, policy):
                    policy["excludedPaths"].append(name)
                save_policy(self.repo, policy)
            elif action == "show":
                if current["hiddenBy"] and current["hiddenBy"] != name:
                    raise ValueError("这页由目录规则隐藏，请在左下角恢复对应目录")
                policy["excludedPaths"] = [p for p in policy["excludedPaths"] if p != name]
                save_policy(self.repo, policy)
            else:
                raise ValueError("不支持的编辑动作")
            return self.apply_saved()

    def restore_rule(self, body):
        with self.editing():
            name = body.get("path")
            policy = load_policy(self.repo)
            if name not in policy["excludedPaths"]:
                raise Conflict("隐藏规则已变化，请刷新列表")
            policy["excludedPaths"].remove(name)
            save_policy(self.repo, policy)
            return self.apply_saved()

    def start_job(self, kind):
        sync_command = [sys.executable, "scripts/sync_study.py"]
        commands = {
            "sync-preview": [sync_command + ["--verbose"]],
            "sync-apply": [sync_command + ["--apply"]],
            "build": [sync_command + ["--apply"], ["npm", "run", "build"], ["npm", "run", "verify:site"]],
            "publish": [["bash", "publish.sh"]],
        }
        if kind not in commands:
            raise ValueError("不支持的任务")
        with self.mutex:
            if self.running:
                raise Conflict("已有任务在运行")
            job_id = secrets.token_hex(8)
            job = {"id": job_id, "kind": kind, "status": "running", "log": "", "code": None, "pid": None, "cancelled": False}
            self.jobs[job_id] = job
            self.running = job_id

        def run():
            code = 0
            try:
                env = dict(os.environ, STUDY_DIR=str(self.source), npm_config_cache=os.environ.get("npm_config_cache", "/private/tmp/my-blog-npm-cache"))
                for command in commands[kind]:
                    if job["cancelled"]:
                        break
                    with self.mutex:
                        process = subprocess.Popen(command, cwd=self.repo, env=env, stdout=subprocess.PIPE,
                                                   stderr=subprocess.STDOUT, text=True, bufsize=1, start_new_session=True)
                        job["pid"] = process.pid
                    for line in process.stdout:
                        with self.mutex:
                            job["log"] = (job["log"] + line)[-300_000:]
                    process.stdout.close()
                    code = process.wait()
                    with self.mutex:
                        job["pid"] = None
                    if code:
                        break
            except Exception as error:
                code = 1
                job["log"] += str(error) + "\n"
            finally:
                with self.mutex:
                    job["code"] = code
                    job["status"] = "cancelled" if job["cancelled"] else "done" if code == 0 else "failed"
                    self.running = None
        threading.Thread(target=run, daemon=True).start()
        return {"id": job_id}

    def cancel(self):
        with self.mutex:
            if self.running:
                job = self.jobs[self.running]
                job["cancelled"] = True
                if job["pid"]:
                    try:
                        os.killpg(job["pid"], signal.SIGTERM)
                    except ProcessLookupError:
                        pass
        return {"ok": True}


def handler_for(studio):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, status, data, content_type="application/json; charset=utf-8"):
            data = json.dumps(data, ensure_ascii=False).encode() if not isinstance(data, bytes) else data
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def allowed_host(self):
            return self.headers.get("Host") in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

        def authorized(self):
            origin = self.headers.get("Origin")
            allowed_origins = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
            return self.allowed_host() and (not origin or origin in allowed_origins) and hmac.compare_digest(self.headers.get("X-Editor-Token", ""), studio.token)

        def do_GET(self):
            if not self.allowed_host():
                return self.respond(403, {"error": "Host rejected"})
            route = urlsplit(self.path)
            if route.path in {"/", "/app.js", "/style.css"}:
                name, kind = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}[route.path]
                data = (studio.repo / "editor" / name).read_text()
                if name == "index.html":
                    data = data.replace("EDITOR_TOKEN_PLACEHOLDER", studio.token)
                return self.respond(200, data.encode(), kind + "; charset=utf-8")
            if not self.authorized():
                return self.respond(403, {"error": "请从本机启动器重新打开客户端"})
            try:
                if route.path == "/api/pages":
                    return self.respond(200, studio.state())
                if route.path == "/api/page":
                    return self.respond(200, studio.page(parse_qs(route.query).get("path", [""])[0]))
                if route.path.startswith("/api/jobs/"):
                    with studio.mutex:
                        job = studio.jobs.get(route.path.rsplit("/", 1)[1])
                        if job:
                            return self.respond(200, {k: v for k, v in job.items() if k != "pid"})
                return self.respond(404, {"error": "Not found"})
            except (ValueError, OSError) as error:
                return self.respond(400, {"error": str(error)})

        def do_POST(self):
            if not self.authorized():
                return self.respond(403, {"error": "Request rejected"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 2_100_000:
                    raise ValueError("请求内容过大或为空")
                body = json.loads(self.rfile.read(length))
                routes = {"/api/page": studio.change, "/api/rules/restore": studio.restore_rule,
                          "/api/jobs": lambda b: studio.start_job(b.get("kind")), "/api/jobs/cancel": lambda b: studio.cancel()}
                action = routes.get(urlsplit(self.path).path)
                if not action:
                    return self.respond(404, {"error": "Not found"})
                return self.respond(200, action(body))
            except Conflict as error:
                return self.respond(409, {"error": str(error)})
            except (ValueError, OSError, KeyError, TypeError) as error:
                return self.respond(400, {"error": str(error)})
    return Handler


def preview_handler(root):
    class Preview(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, *args):
            pass

        def list_directory(self, path):
            self.send_error(404)
            return None

        def do_GET(self):
            if self.headers.get("Host") not in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}:
                return self.send_error(403)
            route = urlsplit(self.path)
            target = unquote(route.path)
            if target == "/Corleone-s-Blog" or target.startswith("/Corleone-s-Blog/"):
                target = target[len("/Corleone-s-Blog"):]
            # Quartz uses extensionless page URLs. Preview them like Pages does.
            candidate = (root / target.lstrip("/")).resolve()
            if candidate != root.resolve() and root.resolve() not in candidate.parents:
                return self.send_error(404)
            if any(p.is_symlink() for p in [root / target.lstrip("/"), *(root / target.lstrip("/")).parents]):
                return self.send_error(404)
            if not candidate.exists() and candidate.with_suffix(candidate.suffix + ".html").is_file():
                target += ".html"
            self.path = target or "/"
            return super().do_GET()
    return Preview


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(os.environ.get("STUDY_DIR", str(Path.home() / "Documents/Study"))))
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    runtime = ROOT / ".local/blog-studio"
    runtime.mkdir(parents=True, exist_ok=True)
    instance_lock = (runtime / "instance.lock").open("a")
    try:
        fcntl.flock(instance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        running = json.loads((runtime / "instance.json").read_text())
        print(f"Blog Studio 已经在运行：{running['url']}", flush=True)
        if not args.no_open:
            webbrowser.open(running["url"])
        return
    studio = Studio(ROOT, args.source)
    preview = ThreadingHTTPServer(("127.0.0.1", 0), preview_handler(ROOT / "public"))
    studio.preview_url = f"http://127.0.0.1:{preview.server_port}"
    threading.Thread(target=preview.serve_forever, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(studio))
    url = f"http://127.0.0.1:{server.server_port}"
    atomic_write(runtime / "instance.json", json.dumps({"url": url}).encode())
    print(f"Blog Studio 已启动：{url}\n关闭此终端窗口即可退出。", flush=True)
    if not args.no_open:
        webbrowser.open(url)
    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, stop)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        studio.cancel()
        server.server_close()
        preview.shutdown()
        preview.server_close()
        (runtime / "instance.json").unlink(missing_ok=True)
        instance_lock.close()


if __name__ == "__main__":
    main()
