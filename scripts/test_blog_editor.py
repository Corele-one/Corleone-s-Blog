import contextlib
from http.server import ThreadingHTTPServer
import io
import json
from pathlib import Path
import shutil
import os
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from blog_editor import Conflict, Studio, handler_for
from blog_publication import load_policy, save_policy
import sync_study as sync


class StudioFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name).resolve()
        self.repo, self.source = base / "blog", base / "Study"
        (self.repo / "site").mkdir(parents=True)
        (self.repo / "site/index.md").write_text("Home")
        (self.repo / "content").mkdir()
        (self.repo / "scripts").mkdir()
        for name in ["sync_study.py", "blog_publication.py"]:
            shutil.copy2(Path(__file__).with_name(name), self.repo / "scripts" / name)
        config = {"include": ["Blog", "Note"], "extensions": [".md", ".pdf"], "excludeNames": ["node_modules"], "sitePages": {"site/index.md": "index.md"}, "legacyPaths": []}
        (self.repo / "sync.config.json").write_text(json.dumps(config))
        for directory in ["Blog", "Note"]:
            (self.source / directory).mkdir(parents=True)
            (self.source / directory / "note.md").write_text("first\n\nremove this paragraph\n\nlast\n")
        self.app = Studio(self.repo, self.source)
        with contextlib.redirect_stdout(io.StringIO()):
            sync.synchronize(self.source, self.repo, apply=True, migrate=True)

    def change(self, action, name="Blog/note.md", **fields):
        page = self.app.page(name)
        return self.app.change({"action": action, "path": name, "sourceHash": page["sourceHash"], "revision": page["revision"], **fields})


class StudioTests(StudioFixture, unittest.TestCase):
    def test_edit_survives_sync_and_never_writes_study(self):
        source_before = (self.source / "Blog/note.md").read_bytes()
        result = self.change("save", content="first\n\nlast\n")
        self.assertIsNone(result["syncError"])
        with contextlib.redirect_stdout(io.StringIO()):
            sync.synchronize(self.source, self.repo, apply=True)
        self.assertEqual((self.repo / "content/Blog/note.md").read_text(), "first\n\nlast\n")
        self.assertEqual((self.source / "Blog/note.md").read_bytes(), source_before)

    def test_hide_last_page_is_intentional_and_survives_sync(self):
        self.change("hide")
        self.assertFalse((self.repo / "content/Blog/note.md").exists())
        with contextlib.redirect_stdout(io.StringIO()):
            sync.synchronize(self.source, self.repo, apply=True)
        self.assertFalse((self.repo / "content/Blog/note.md").exists())
        self.change("show")
        self.assertTrue((self.repo / "content/Blog/note.md").exists())

    def test_changed_source_requires_review_and_rejects_stale_save(self):
        self.change("save", content="blog version")
        stale = self.app.page("Blog/note.md")
        (self.source / "Blog/note.md").write_text("new original")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, "Source changed"):
            sync.synchronize(self.source, self.repo, apply=True)
        with self.assertRaises(Conflict):
            self.app.change({"action": "save", "path": "Blog/note.md", "content": "stale", "sourceHash": stale["sourceHash"], "revision": stale["revision"]})
        self.assertTrue(self.app.page("Blog/note.md")["conflict"])
        self.change("save", content="reviewed blog version")
        self.assertFalse(self.app.page("Blog/note.md")["conflict"])
        self.assertEqual((self.source / "Blog/note.md").read_text(), "new original")

    def test_reset_restores_original_and_removes_override(self):
        self.change("save", content="edited")
        self.change("reset")
        self.assertNotIn("Blog/note.md", load_policy(self.repo)["overrides"])
        self.assertEqual((self.repo / "content/Blog/note.md").read_bytes(), (self.source / "Blog/note.md").read_bytes())

    def test_directory_exclusion_removes_notes_and_resources(self):
        section = self.source / "Note/GenSE"
        section.mkdir()
        (section / "lecture.md").write_text("unfinished")
        (section / "slides.pdf").write_bytes(b"pdf")
        policy = load_policy(self.repo)
        policy["excludedPaths"].append("Note/GenSE")
        save_policy(self.repo, policy)
        self.app.apply_saved()
        self.assertFalse((self.repo / "content/Note/GenSE").exists())
        with self.assertRaisesRegex(ValueError, "目录规则"):
            self.change("show", "Note/GenSE/lecture.md")
        self.app.restore_rule({"path": "Note/GenSE"})
        self.assertTrue((self.repo / "content/Note/GenSE/slides.pdf").exists())

    def test_homepage_cannot_be_hidden_and_secret_never_saved(self):
        with self.assertRaisesRegex(ValueError, "首页"):
            self.change("hide", "index.md")
        with self.assertRaisesRegex(ValueError, "疑似"):
            self.change("save", content="-----BEGIN PRIVATE KEY-----")
        self.assertFalse((self.repo / "overrides/Blog/note.md").exists())

    def test_sync_preview_and_apply_jobs(self):
        (self.source / "Note/new.md").write_text("new")
        for kind in ["sync-preview", "sync-apply"]:
            job_id = self.app.start_job(kind)["id"]
            deadline = time.monotonic() + 10
            while self.app.jobs[job_id]["status"] == "running" and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertEqual(self.app.jobs[job_id]["status"], "done", self.app.jobs[job_id]["log"])
            self.assertEqual((self.repo / "content/Note/new.md").exists(), kind == "sync-apply")

    def test_invalid_page_and_symlink_override_are_rejected(self):
        with self.assertRaises(ValueError):
            self.app.page("../../private.md")
        (self.repo / "overrides").symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.change("save", content="wrong target")

    def test_cancel_stops_the_whole_task_process_group(self):
        stub = '''import signal, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
def stop(*args):
    child.wait(timeout=4)
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
print('ready', flush=True)
while True: time.sleep(.1)
'''
        (self.repo / "scripts/sync_study.py").write_text(stub)
        job_id = self.app.start_job("sync-preview")["id"]
        deadline = time.monotonic() + 10
        while "ready" not in self.app.jobs[job_id]["log"] and time.monotonic() < deadline:
            time.sleep(.02)
        pid = self.app.jobs[job_id]["pid"]
        self.assertIsNotNone(pid)
        self.app.cancel()
        while self.app.jobs[job_id]["status"] == "running" and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertEqual(self.app.jobs[job_id]["status"], "cancelled")
        with self.assertRaises(ProcessLookupError):
            os.killpg(pid, 0)


class HttpTests(StudioFixture, unittest.TestCase):
    def test_http_auth_host_origin_and_path_scope(self):
        editor = self.repo / "editor"
        editor.mkdir()
        (editor / "index.html").write_text("EDITOR_TOKEN_PLACEHOLDER")
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.app))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base, timeout=5) as response:
            self.assertEqual(response.read().decode(), self.app.token)
        for headers in [{}, {"X-Editor-Token": self.app.token, "Origin": "https://example.com"}, {"X-Editor-Token": self.app.token, "Host": "attacker.invalid"}]:
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(base + "/api/pages", headers=headers), timeout=5)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
        headers = {"X-Editor-Token": self.app.token}
        with urlopen(Request(base + "/api/pages", headers=headers), timeout=5) as response:
            self.assertEqual(len(json.load(response)["pages"]), 3)
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(base + "/api/page?path=../../private.md", headers=headers), timeout=5)
        self.assertEqual(error.exception.code, 400)
        error.exception.close()
        page = self.app.page("Blog/note.md")
        body = json.dumps({"action": "save", "path": page["path"], "revision": page["revision"], "sourceHash": page["sourceHash"], "content": "edited over HTTP"}).encode()
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(base + "/api/page", data=body, headers={"Content-Type": "application/json"}), timeout=5)
        self.assertEqual(error.exception.code, 403)
        error.exception.close()
        self.assertFalse((self.repo / "overrides/Blog/note.md").exists())
        with urlopen(Request(base + "/api/page", data=body, headers={**headers, "Content-Type": "application/json"}), timeout=5) as response:
            self.assertTrue(json.load(response)["saved"])
        self.assertEqual((self.repo / "content/Blog/note.md").read_text(), "edited over HTTP")
        self.assertIn("remove this paragraph", (self.source / "Blog/note.md").read_text())


if __name__ == "__main__":
    unittest.main()
