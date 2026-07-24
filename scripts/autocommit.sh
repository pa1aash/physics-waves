#!/usr/bin/env bash
# Commit-and-push helper. Stages everything, commits with a conventional
# subject derived from the first changed file, and pushes immediately. Invoked
# by file-producing Makefile targets and by the local post-edit automation.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
[ -z "$(git status --porcelain)" ] && exit 0
git add -A
subject="$(git diff --cached --name-only | head -1 | xargs -I{} basename {})"
git commit -q -m "chore: update ${subject}" || exit 0
git push -q origin main || {
  echo "PUSH FAILED — local commit retained. Resolve before continuing." >&2
  exit 1
}
