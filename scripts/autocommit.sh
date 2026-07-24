#!/usr/bin/env bash
# Commit-and-push helper. Invoked by file-producing Makefile targets and by the
# local post-edit automation.
#
# Staging policy: stage modifications (and deletions) of files git ALREADY
# tracks, plus NEW files only inside an explicit whitelist of source-controlled
# directories. Never a blanket `git add -A` / `git add .` — that is how
# operator-supplied binaries (the literature PDFs, the Springer Nature template)
# entered the index before their directories had gitignore rules. A tree-wide
# `git add --intent-to-add .` is avoided for the same reason: it would record
# intent-to-add entries for every untracked file anywhere, which the next run's
# `git add -u` would then stage — reintroducing the blanket-add one run later.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# Escape hatch for sessions that need exact, hand-written commit subjects and
# controlled grouping (e.g. the numbered Session 00-series multi-phase builds):
#   touch .git/AUTOCOMMIT_OFF   # at session start
#   rm -f .git/AUTOCOMMIT_OFF   # at session end
[ -f .git/AUTOCOMMIT_OFF ] && exit 0

# 1. Modifications and deletions of already-tracked files, anywhere in the tree.
git add -u

# 2. New files, but ONLY inside directories meant to hold source-controlled
#    content. data/, figures/, manuscript/ and logs/ are deliberately EXCLUDED:
#    they hold operator-supplied or generated binaries that must only ever be
#    committed through an explicit, reviewed commit in a numbered session.
for dir in configs docs src tests scripts theory .github; do
  [ -d "$dir" ] && git add "$dir"
done

[ -z "$(git diff --cached --name-only)" ] && exit 0

subject_file="$(git diff --cached --name-only | head -1 | xargs -I{} basename {})"
git commit -q -m "chore: update ${subject_file}" || exit 0
git push -q origin main || {
  echo "PUSH FAILED — local commit retained. Resolve before continuing." >&2
  exit 1
}
