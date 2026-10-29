#!/usr/bin/env python3
"""Read-only Study -> content mirror. Default is a dry run; no network required."""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from blog_publication import apply_policy, hidden_by, load_policy

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ".study-sync-manifest.json"
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "API token": re.compile(r"\bsk-[A-Za-z0-9_-]{25,}"),
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def relative(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or str(path) != value:
        raise ValueError(f"Unsafe relative path: {value}")
    return value


def safe_target(content, name):
    target = content / relative(name)
    if content.is_symlink() or any(p.is_symlink() for p in [target, *target.parents] if p != content.parent):
        raise ValueError(f"Symlink in destination: {name}")
    if target.exists() and not target.is_file():
        raise ValueError(f"Expected a file at destination: {name}")
    return target


def collect(source, repo, config):
    policy = load_policy(repo)
    desired = {}
    skipped = Counter()
    counts = Counter()
    for folder in config["include"]:
        base = source / relative(folder)
        if not base.is_dir() or any(p.is_symlink() for p in [base, *base.parents]):
            raise ValueError(f"Missing directory or symlink in source: {folder}")
        before = len(desired)
        source_count = 0
        for directory, dirs, names in os.walk(base, followlinks=False):
            parent = Path(directory)
            allowed_dirs = []
            for name in sorted(dirs):
                if name.startswith(".") or name in config["excludeNames"]:
                    skipped["hidden/cache directories"] += 1
                elif (parent / name).is_symlink():
                    raise ValueError(f"Source symlink: {(parent / name).relative_to(source)}")
                else:
                    allowed_dirs.append(name)
            dirs[:] = allowed_dirs
            for name in sorted(names):
                path = parent / name
                if name.startswith("."):
                    skipped["hidden files"] += 1
                    continue
                if path.is_symlink():
                    raise ValueError(f"Source symlink: {path.relative_to(source)}")
                if path.suffix.lower() not in config["extensions"]:
                    skipped["unsupported extensions"] += 1
                    continue
                if path.stat().st_size >= 100 * 1024 * 1024:
                    raise ValueError(f"File exceeds GitHub's 100 MiB limit: {path.relative_to(source)}")
                key = path.relative_to(source).as_posix()
                source_count += 1
                if hidden_by(key, policy):
                    skipped["unpublished files"] += 1
                    continue
                if path.suffix.lower() in {".md", ".svg", ".canvas", ".base", ".excalidraw"}:
                    text = path.read_text(encoding="utf-8")
                    for rule, pattern in SECRET_PATTERNS.items():
                        if pattern.search(text):
                            raise ValueError(f"Possible {rule} in {key}; value suppressed. Review before sharing.")
                desired[key] = path
                counts[folder] += 1
        if source_count == 0:
            raise ValueError(f"No publishable files in {folder}; refusing to erase a directory.")
    for origin, destination in config["sitePages"].items():
        relative(origin)
        relative(destination)
        site_source = repo / origin
        if any(p.is_symlink() for p in [site_source, *site_source.parents]):
            raise ValueError(f"Site source symlink: {origin}")
        if destination in desired:
            raise ValueError(f"Source note conflicts with site page: {destination}. Update sitePages first.")
        desired[destination] = repo / origin
    desired = apply_policy(repo, desired, policy)
    for name in policy["overrides"]:
        if name in desired:
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(desired[name].read_text()):
                    raise ValueError(f"Possible {label} in blog override {name}; value suppressed.")
    # Quartz slugs are case-sensitive on Pages but the Mac filesystem may not be.
    casefolded = {}
    for key in desired:
        folded = key.casefold()
        if folded in casefolded:
            raise ValueError(f"Case-colliding paths: {casefolded[folded]} and {key}")
        casefolded[folded] = key
    return desired, counts, skipped


def synchronize(source, repo, *, apply=False, check=False, migrate=False, verbose=False):
    config = json.loads((repo / "sync.config.json").read_text())
    content = repo / "content"
    if source == content or source in content.parents or content in source.parents:
        raise ValueError("Study and content must be separate directory trees.")
    desired, counts, skipped = collect(source, repo, config)
    hashes = {key: digest(path) for key, path in desired.items()}
    manifest = repo / MANIFEST
    previous = {}
    if manifest.exists():
        if migrate:
            raise ValueError("Migration already completed; omit --migrate-legacy.")
        stored = json.loads(manifest.read_text())
        if stored.get("version") != 1:
            raise ValueError("Unsupported sync manifest version.")
        previous = stored["files"]
    elif not migrate:
        raise ValueError("First sync requires --migrate-legacy (preview it before --apply).")
    else:
        # One-time, explicit removal of known old categories, never arbitrary content.
        for name in [*config["legacyPaths"], "index.md"]:
            entry = content / relative(name)
            if entry.is_symlink():
                raise ValueError(f"Legacy symlink: {name}")
            paths = entry.rglob("*") if entry.is_dir() else [entry]
            for path in paths:
                if path.is_symlink():
                    raise ValueError(f"Legacy symlink: {path.relative_to(content)}")
                if path.is_file():
                    previous[path.relative_to(content).as_posix()] = digest(path)
    added, changed, removed = [], [], []
    for key in sorted(set(previous) | set(hashes)):
        target = safe_target(content, key)
        current = digest(target) if target.exists() else None
        old, new = previous.get(key), hashes.get(key)
        if current is not None and current != old and current != new:
            raise ValueError(f"Local edit or unmanaged file at content/{key}; move it to Study or restore it first.")
        if new is None:
            if current is not None:
                removed.append(key)
        elif current != new:
            (added if current is None else changed).append(key)
    next_manifest = {"version": 1, "files": dict(sorted(hashes.items()))}
    manifest_text = json.dumps(next_manifest, ensure_ascii=False, indent=2) + "\n"
    manifest_changed = not manifest.exists() or manifest.read_text() != manifest_text
    for folder, count in counts.items():
        print(f"  {folder}: {count} files")
    print(f"Plan: +{len(added)} ~{len(changed)} -{len(removed)}; {sum(p.suffix == '.md' for p in desired.values())} Markdown pages including site navigation.")
    if skipped:
        print("Excluded: " + ", ".join(f"{n} {k}" for k, n in skipped.items()))
    for label, paths in [("ADD", added), ("UPDATE", changed), ("DELETE", removed)]:
        for key in paths if verbose else paths[:10]:
            print(f"  {label} {key}")
        if not verbose and len(paths) > 10:
            print(f"  ... {len(paths) - 10} more ({label}; --verbose lists all)")
    pending = bool(added or changed or removed or manifest_changed)
    if check:
        print("Sync is current." if not pending else "Sync is pending.")
        return 1 if pending else 0
    if not apply or not pending:
        print("Dry run; no content changed." if not apply else "Already up to date.")
        return 0
    local = repo / ".local" / "study-sync"
    local.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="transaction-", dir=local) as temporary:
        transaction = Path(temporary)
        # Snapshot everything before touching content. A changing source aborts here.
        for key in added + changed:
            staged = transaction / "new" / key
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(desired[key], staged)
            if digest(staged) != hashes[key]:
                raise ValueError(f"Source changed during sync: {key}; run again.")
        for key in changed + removed:
            backup = transaction / "old" / key
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(content / key, backup)
        old_manifest = manifest.read_bytes() if manifest.exists() else None
        try:
            for key in added + changed:
                target = content / key
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(transaction / "new" / key, target)
            for key in removed:
                (content / key).unlink()
            staged_manifest = transaction / "manifest.json"
            staged_manifest.write_text(manifest_text)
            os.replace(staged_manifest, manifest)
        except BaseException:
            for key in added:
                (content / key).unlink(missing_ok=True)
            for key in changed + removed:
                shutil.copy2(transaction / "old" / key, content / key)
            if old_manifest is None:
                manifest.unlink(missing_ok=True)
            else:
                manifest.write_bytes(old_manifest)
            raise
    for directory in sorted(content.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if directory.is_dir() and not directory.is_symlink() and not any(directory.iterdir()):
            directory.rmdir()
    print("Applied. Study originals were read only; no commit or push performed.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(os.environ.get("STUDY_DIR", str(Path.home() / "Documents/Study"))))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="apply the previewed changes")
    mode.add_argument("--check", action="store_true", help="exit 1 when sync is needed")
    parser.add_argument("--migrate-legacy", action="store_true", help="one-time migration from old content layout")
    parser.add_argument("--verbose", action="store_true", help="list every changed path")
    args = parser.parse_args()
    try:
        if args.apply:
            local = ROOT / ".local" / "study-sync"
            local.mkdir(parents=True, exist_ok=True)
            with (local / "lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return synchronize(args.source.resolve(), ROOT, apply=True, migrate=args.migrate_legacy, verbose=args.verbose)
        return synchronize(args.source.resolve(), ROOT, check=args.check, migrate=args.migrate_legacy, verbose=args.verbose)
    except (OSError, ValueError, KeyError) as error:
        print(f"Sync stopped: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
