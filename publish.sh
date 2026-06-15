#!/bin/bash
set -e

git add content/ quartz.config.yaml

if ! git diff --cached --quiet; then
  git commit -m "content: update notes $(date '+%Y-%m-%d')"
fi

if [ "$(git rev-list --count '@{upstream}..HEAD')" -eq 0 ]; then
  echo "No changes to publish."
  exit 0
fi

# GitHub connections through some local proxies are more reliable over HTTP/1.1.
git -c http.version=HTTP/1.1 push
echo "Published. Check https://corele-one.github.io/Corleone-s-Blog in a few minutes."
