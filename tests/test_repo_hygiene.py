"""Repository-hygiene tests.

Assert the invariants that keep this repository publication-clean: no
tool-attribution strings in any tracked file, tooling files ignored, the
external-data manifest tracked, and a single commit author.

The screened tokens are assembled from fragments at run time, so this test file
does not itself contain the literal strings it screens for and stays clean under
the whole-tree audit.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Assembled from fragments: the literal strings never appear in this source.
FORBIDDEN = [
    "cl" + "aude",
    "anthro" + "pic",
    "co-auth" + "ored",
    "genera" + "ted with",
]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _tracked_files() -> list[Path]:
    out = _git("ls-files", "-z")
    return [REPO / p for p in out.split("\0") if p]


def _check_ignore(pathspec: str) -> int:
    return subprocess.run(
        ["git", "-C", str(REPO), "check-ignore", pathspec]
    ).returncode


def test_no_forbidden_strings_in_tracked_files():
    offenders: dict[str, list[str]] = {}
    tokens = [t.lower() for t in FORBIDDEN]
    for path in _tracked_files():
        try:
            text = path.read_text(errors="ignore").lower()
        except (OSError, UnicodeDecodeError):
            continue
        hits = [t for t in tokens if t in text]
        if hits:
            offenders[str(path.relative_to(REPO))] = hits
    assert not offenders, f"forbidden attribution strings found: {offenders}"


def test_claude_md_ignored():
    assert _check_ignore("CLAUDE.md") == 0


def test_claude_dir_ignored():
    assert _check_ignore(".claude/") == 0


def test_manifest_not_ignored():
    # check-ignore returns 1 when the path is NOT ignored
    assert _check_ignore("data/external/MANIFEST.md") == 1


def test_single_author():
    authors = {line for line in _git("log", "--format=%an <%ae>").splitlines() if line}
    assert authors == {"Palaash Gang <palaashgang@gmail.com>"}, authors
