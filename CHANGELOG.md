# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- Full git-history audit for operator-supplied binaries. Confirmed **no
  copyrighted PDF or template file was ever committed or pushed**: five
  independent scans (added-in-history, reflog, reachable large blobs, dangling
  blobs, and literature/template commit touches) traced 21 literature and
  Springer-template PDF blobs that the former blanket `git add -A` autocommit had
  written to the local object store as **loose, never-committed, never-reachable**
  objects — never transmitted to GitHub. Purged locally via
  `git reflog expire --expire=now --all` and `git gc --prune=now --aggressive`
  (126 MiB of loose objects → 0), and re-verified clean. No history rewrite or
  force-push was required.

### Changed

- Hardened `scripts/autocommit.sh`: replaced the blanket `git add -A` with
  tracked-file updates (`git add -u`) plus new files only under a
  source-directory whitelist (`configs`, `docs`, `src`, `tests`, `scripts`,
  `theory`, `.github`), and added a `.git/AUTOCOMMIT_OFF` escape hatch. Binaries
  in `data/`, `figures/`, `manuscript/` and `logs/` can no longer reach the index
  through the background hook.

## [0.1.0] — 2026-07-24

### Added

- Repository initialised: structure, licences, environment specification, and
  external data acquisition.
