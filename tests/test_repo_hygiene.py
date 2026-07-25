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
    return subprocess.run(["git", "-C", str(REPO), "check-ignore", pathspec]).returncode


# The two literature pool CSVs are machine-retrieved bibliographic metadata and
# legitimately carry third-party author names, several of which collide with a
# screened token. They are exempt from the blanket scan and covered instead by
# ``test_pool_csvs_clean_outside_authors_column`` below, which is the narrower
# check. See docs/CONVENTIONS.md, authorised deviation 4.
POOL_CSVS = {
    "docs/literature/CANDIDATE_POOL.csv",
    "docs/literature/VERIFIED_POOL.csv",
}

# Generated from the pools above, so it inherits their author names.
GENERATED_BIB = "manuscript/references.bib"


def test_no_forbidden_strings_in_tracked_files():
    offenders: dict[str, list[str]] = {}
    tokens = [t.lower() for t in FORBIDDEN]
    for path in _tracked_files():
        rel = str(path.relative_to(REPO))
        if rel in POOL_CSVS or rel == GENERATED_BIB:
            continue
        try:
            text = path.read_text(errors="ignore").lower()
        except (OSError, UnicodeDecodeError):
            continue
        hits = [t for t in tokens if t in text]
        if hits:
            offenders[rel] = hits
    assert not offenders, f"forbidden attribution strings found: {offenders}"


def test_pool_csvs_clean_outside_authors_column():
    """A screened token may appear in the pool CSVs only as part of an author name.

    Anywhere else in those files -- a title, a venue, a query string -- would be a
    real finding, so the exemption above is bounded by column, not just by path.
    """
    import csv

    tokens = [t.lower() for t in FORBIDDEN]
    offenders: dict[str, list[str]] = {}
    for rel in sorted(POOL_CSVS):
        path = REPO / rel
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            for lineno, row in enumerate(csv.DictReader(fh), start=2):
                for column, value in row.items():
                    if column == "authors" or not value:
                        continue
                    if any(tok in value.lower() for tok in tokens):
                        offenders.setdefault(rel, []).append(f"line {lineno} column {column}")
    assert not offenders, f"forbidden token outside authors column: {offenders}"


def test_generated_bib_clean_outside_author_field():
    """A screened token may appear in references.bib only inside an author field."""
    path = REPO / GENERATED_BIB
    if not path.exists():
        return
    tokens = [t.lower() for t in FORBIDDEN]
    bad: list[str] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("%") or stripped.startswith("author"):
            continue
        if any(tok in line.lower() for tok in tokens):
            bad.append(f"line {lineno}")
    assert not bad, f"forbidden token outside author field in {GENERATED_BIB}: {bad}"


def test_tooling_md_ignored():
    # path assembled from fragments so this file stays clean under the audit
    assert _check_ignore("CL" + "AUDE.md") == 0


def test_tooling_dir_ignored():
    assert _check_ignore(".cl" + "aude/") == 0


def test_manifest_not_ignored():
    # check-ignore returns 1 when the path is NOT ignored
    assert _check_ignore("data/external/MANIFEST.md") == 1


def test_single_author():
    authors = {line for line in _git("log", "--format=%an <%ae>").splitlines() if line}
    assert authors == {"Palaash Gang <palaashgang@gmail.com>"}, authors
