#!/bin/bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export npm_config_cache="${npm_config_cache:-/private/tmp/my-blog-npm-cache}"

if ! git diff --cached --quiet; then
  echo "There are staged changes. Commit or unstage them before publishing."
  exit 1
fi

python3 scripts/sync_study.py --apply
npm run build
npm run verify:site

python3 <<'PY'
import json
from pathlib import Path
import subprocess

name = '.study-sync-manifest.json'
current = json.loads(Path(name).read_text())['files']
result = subprocess.run(['git', 'show', f'HEAD:{name}'], capture_output=True, text=True)
if result.returncode:
    raise SystemExit('Commit the sync setup before using the daily publish command.')
previous = json.loads(result.stdout)['files']
paths = [f':(literal)content/{key}' for key in sorted(set(current) | set(previous))]
paths.append(f':(literal){name}')
paths.append(':(literal)publication.json')
policy = json.loads(Path('publication.json').read_text())
old_policy = subprocess.run(['git', 'show', 'HEAD:publication.json'], capture_output=True, text=True)
old_overrides = json.loads(old_policy.stdout)['overrides'] if old_policy.returncode == 0 else {}
paths.extend(f':(literal)overrides/{key}' for key in sorted(set(policy['overrides']) | set(old_overrides)))
subprocess.run(
    ['git', 'add', '-A', '--pathspec-from-file=-', '--pathspec-file-nul'],
    input=('\0'.join(paths) + '\0').encode(), check=True,
)
PY
if ! git diff --cached --quiet; then
  git commit -m "content: sync Study notes $(date '+%Y-%m-%d')"
fi

if [ "$(git rev-list --count '@{upstream}..HEAD')" -eq 0 ]; then
  echo "No new commits to publish."
  exit 0
fi

git -c http.version=HTTP/1.1 push --progress
echo "Pushed. Follow deployment: https://github.com/Corele-one/Corleone-s-Blog/actions"
