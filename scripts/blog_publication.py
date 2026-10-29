"""Blog-only publication choices. Never writes to the original Study vault."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile


def fingerprint(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def valid_path(value):
    if not isinstance(value, str):
        raise ValueError("Invalid publication path")
    path = PurePosixPath(value)
    if not value or path.is_absolute() or str(path) != value or any(p.startswith(".") for p in path.parts):
        raise ValueError("Unsafe publication path")
    return value


def scoped_path(value, config):
    valid_path(value)
    roots = config["include"]
    if value not in config["sitePages"].values() and not any(value == r or value.startswith(r + "/") for r in roots):
        raise ValueError("Path is outside the blog's sharing scope")
    return value


def load_policy(repo):
    path = repo / "publication.json"
    policy = json.loads(path.read_text()) if path.exists() else {"version": 1, "excludedPaths": [], "overrides": {}}
    if not isinstance(policy, dict) or policy.get("version") != 1 or not isinstance(policy.get("excludedPaths"), list) or not isinstance(policy.get("overrides"), dict):
        raise ValueError("Unsupported publication settings")
    config = json.loads((repo / "sync.config.json").read_text())
    for name in policy["excludedPaths"]:
        scoped_path(name, config)
        if name == "index.md":
            raise ValueError("The homepage cannot be hidden")
    for name, entry in policy["overrides"].items():
        scoped_path(name, config)
        if not isinstance(entry, dict) or not name.endswith(".md") or not isinstance(entry.get("baseHash"), str) or len(entry["baseHash"]) != 64:
            raise ValueError("Invalid blog override metadata")
    return policy


def hidden_by(name, policy):
    return next((p for p in policy["excludedPaths"] if name == p or name.startswith(p + "/")), None)


def override_path(repo, name):
    target = repo / "overrides" / valid_path(name)
    if any(p.is_symlink() for p in [target, *target.parents]):
        raise ValueError("Symlinks are not allowed in blog overrides")
    return target


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save_policy(repo, policy):
    atomic_write(repo / "publication.json", (json.dumps(policy, ensure_ascii=False, indent=2) + "\n").encode())


def apply_policy(repo, desired, policy):
    published = {}
    for name, original in desired.items():
        if hidden_by(name, policy):
            continue
        entry = policy["overrides"].get(name)
        if entry:
            if fingerprint(original) != entry["baseHash"]:
                raise ValueError(f"Source changed beneath blog edits: {name}. Review it in Blog Studio before syncing.")
            replacement = override_path(repo, name)
            if not replacement.is_file():
                raise ValueError(f"Missing blog override: {name}")
            published[name] = replacement
        else:
            published[name] = original
    return published
