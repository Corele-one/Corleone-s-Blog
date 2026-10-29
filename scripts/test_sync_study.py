"""Exercise mirror safety using isolated temporary Study and blog trees."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("sync_study", Path(__file__).with_name("sync_study.py"))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name).resolve()
        self.repo, self.study = base / "blog", base / "Study"
        (self.repo / "content/Old").mkdir(parents=True)
        (self.repo / "content/Old/old.md").write_text("legacy")
        (self.repo / "site").mkdir()
        (self.repo / "site/index.md").write_text("site home")
        (self.repo / "content/handwritten.md").write_text("keep this")
        for name in ["Blog", "Note", "Research/Project"]:
            folder = self.study / name
            folder.mkdir(parents=True)
            (folder / "note.md").write_text(f"{name} note")
        config = {
            "include": ["Blog", "Note", "Research/Project"],
            "extensions": [".md", ".pdf", ".png"],
            "excludeNames": ["node_modules"],
            "sitePages": {"site/index.md": "index.md"},
            "legacyPaths": ["Old"],
        }
        (self.repo / "sync.config.json").write_text(json.dumps(config))

    def run_sync(self, **options):
        with contextlib.redirect_stdout(io.StringIO()):
            return sync.synchronize(self.study, self.repo, **options)

    def initialize(self):
        self.run_sync(apply=True, migrate=True)

    def test_preview_migration_and_idempotency(self):
        original = {str(p): p.read_bytes() for p in self.study.rglob("*") if p.is_file()}
        self.run_sync(migrate=True)
        self.assertTrue((self.repo / "content/Old/old.md").exists())
        self.assertFalse((self.repo / sync.MANIFEST).exists())
        self.initialize()
        self.assertFalse((self.repo / "content/Old").exists())
        self.assertEqual((self.repo / "content/handwritten.md").read_text(), "keep this")
        self.assertEqual(self.run_sync(check=True), 0)
        self.assertEqual(original, {str(p): p.read_bytes() for p in self.study.rglob("*") if p.is_file()})

    def test_source_move_and_deletion(self):
        self.initialize()
        (self.study / "Note/note.md").rename(self.study / "Note/renamed.md")
        self.assertEqual(self.run_sync(check=True), 1)
        self.run_sync(apply=True)
        self.assertFalse((self.repo / "content/Note/note.md").exists())
        self.assertTrue((self.repo / "content/Note/renamed.md").exists())
        self.assertEqual(self.run_sync(check=True), 0)

    def test_missing_or_empty_root_never_deletes_content(self):
        self.initialize()
        (self.study / "Note/note.md").unlink()
        with self.assertRaisesRegex(ValueError, "No publishable files"):
            self.run_sync(apply=True)
        self.assertTrue((self.repo / "content/Note/note.md").exists())
        (self.study / "Note").rmdir()
        with self.assertRaisesRegex(ValueError, "Missing directory"):
            self.run_sync(apply=True)

    def test_local_edit_is_preserved(self):
        self.initialize()
        path = self.repo / "content/Note/note.md"
        path.write_text("local work")
        with self.assertRaisesRegex(ValueError, "Local edit"):
            self.run_sync(apply=True)
        self.assertEqual(path.read_text(), "local work")

    def test_missing_destination_is_recreated(self):
        self.initialize()
        (self.repo / "content/Note/note.md").unlink()
        self.run_sync(apply=True)
        self.assertTrue((self.repo / "content/Note/note.md").exists())

    def test_hidden_and_outside_scope_files_are_excluded(self):
        hidden = self.study / "Note/.claude"
        hidden.mkdir()
        (hidden / "private.md").write_text("private")
        (self.study / "Note/.env").write_text("secret")
        (self.study / "Note/executable.bin").write_bytes(b"binary")
        (self.study / "private.md").write_text("outside scope")
        self.initialize()
        files = json.loads((self.repo / sync.MANIFEST).read_text())["files"]
        self.assertEqual(len(files), 4)

    def test_source_symlink_rejected(self):
        (self.study / "Note/link.md").symlink_to(self.study / "Blog/note.md")
        with self.assertRaisesRegex(ValueError, "Source symlink"):
            self.run_sync(apply=True, migrate=True)

    def test_destination_symlink_rejected(self):
        self.initialize()
        (self.repo / "content/Note/note.md").unlink()
        (self.repo / "content/Note/note.md").symlink_to(self.study / "Note/note.md")
        with self.assertRaisesRegex(ValueError, "Symlink in destination"):
            self.run_sync(apply=True)

    def test_possible_secret_stops_before_migration(self):
        (self.study / "Note/note.md").write_text("-----BEGIN PRIVATE KEY-----")
        with self.assertRaisesRegex(ValueError, "value suppressed"):
            self.run_sync(apply=True, migrate=True)
        self.assertTrue((self.repo / "content/Old/old.md").exists())

    def test_site_index_collision_is_explicit(self):
        config = json.loads((self.repo / "sync.config.json").read_text())
        config["sitePages"]["site/index.md"] = "Note/note.md"
        (self.repo / "sync.config.json").write_text(json.dumps(config))
        with self.assertRaisesRegex(ValueError, "conflicts with site page"):
            self.run_sync(migrate=True)

    def test_transaction_rolls_back_on_write_failure(self):
        from unittest.mock import patch
        self.initialize()
        before = (self.repo / sync.MANIFEST).read_bytes()
        (self.study / "Blog/note.md").write_text("updated blog")
        (self.study / "Note/note.md").write_text("updated note")
        real_replace = sync.os.replace
        writes = 0

        def fail_second(source, target):
            nonlocal writes
            writes += 1
            if writes == 2:
                raise OSError("simulated write failure")
            return real_replace(source, target)

        with patch.object(sync.os, "replace", side_effect=fail_second):
            with self.assertRaisesRegex(OSError, "simulated"):
                self.run_sync(apply=True)
        self.assertEqual((self.repo / "content/Blog/note.md").read_text(), "Blog note")
        self.assertEqual((self.repo / "content/Note/note.md").read_text(), "Note note")
        self.assertEqual((self.repo / sync.MANIFEST).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
