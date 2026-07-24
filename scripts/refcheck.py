"""make refcheck: verify that every \\cite key resolves to a bibliography entry
with a live DOI.

For a given ``.tex`` file (default ``theory/derivations.tex``), extract every
``\\cite{...}`` key, look each up in ``manuscript/references.bib``, confirm a
``doi`` field is present, and — network permitting — resolve it with an HTTP HEAD
against ``https://doi.org/<doi>``. With no argument, summarise across every
``.tex`` file in ``theory/`` and ``manuscript/``.

Flags a genuine inconsistency (non-zero exit) for: a citation key with no
bibliography entry, an entry missing a DOI, or a DOI that fails to resolve. A DOI
that cannot be checked because the network is unavailable is reported but does
not fail the run. ``manuscript/references.bib`` does not exist until Session L4;
until then this reports "nothing to check" and exits 0.

Usage:
    python scripts/refcheck.py [file.tex] [--no-doi]
"""

from __future__ import annotations

import argparse
import glob
import re
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "manuscript" / "references.bib"

_CITE = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
_ENTRY = re.compile(r"@\w+\s*\{\s*([^,\s]+)\s*,(.*?)\n\s*\}", re.DOTALL)
_DOI = re.compile(r"doi\s*=\s*[{\"]\s*([^}\"]+?)\s*[}\"]", re.IGNORECASE)


def cite_keys(texfile: Path) -> set[str]:
    text = texfile.read_text(errors="ignore")
    keys: set[str] = set()
    for m in _CITE.finditer(text):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                keys.add(k)
    return keys


def parse_bib(bibfile: Path) -> dict[str, str | None]:
    """Map each bib key to its DOI (or None if the entry has no doi field)."""
    text = bibfile.read_text(errors="ignore")
    out: dict[str, str | None] = {}
    for m in _ENTRY.finditer(text):
        key, body = m.group(1).strip(), m.group(2)
        dm = _DOI.search(body)
        out[key] = dm.group(1).strip() if dm else None
    return out


def doi_resolves(doi: str, timeout: int = 15) -> bool | None:
    """True if the DOI resolves, False if it 404s, None if the network is down."""
    url = f"https://doi.org/{doi}"
    req = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "physics-waves-refcheck"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200 <= r.status < 400
    except urllib.error.HTTPError as e:
        return e.code < 400
    except Exception:
        return None  # inconclusive (offline / DNS / timeout)


def check_file(texfile: Path, bib: dict[str, str | None], do_doi: bool) -> list[str]:
    problems: list[str] = []
    keys = cite_keys(texfile)
    for k in sorted(keys):
        if k not in bib:
            problems.append(f"  MISSING bib entry: {k}")
            continue
        doi = bib[k]
        if not doi:
            problems.append(f"  NO doi field: {k}")
            continue
        if do_doi:
            r = doi_resolves(doi)
            if r is False:
                problems.append(f"  DEAD doi: {k} -> {doi}")
            elif r is None:
                problems.append(f"  UNVERIFIED doi (network): {k} -> {doi}")
    print(f"[refcheck] {texfile.relative_to(REPO)}: {len(keys)} citation(s)")
    for p in problems:
        print(p)
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check \\cite keys against the bibliography.")
    ap.add_argument(
        "texfile", nargs="?", help="a .tex file; default: all in theory/ and manuscript/"
    )
    ap.add_argument("--no-doi", action="store_true", help="skip DOI HEAD resolution")
    args = ap.parse_args(argv)

    if not BIB.exists():
        rel = BIB.relative_to(REPO)
        print(f"[refcheck] no bibliography file yet ({rel}); nothing to check.")
        print("[refcheck] Session L4 creates references.bib. This is not a failure.")
        return 0
    bib = parse_bib(BIB)

    if args.texfile:
        targets = [Path(args.texfile)]
    else:
        targets = sorted(
            Path(p)
            for p in glob.glob(str(REPO / "theory" / "*.tex"))
            + glob.glob(str(REPO / "manuscript" / "*.tex"))
        )
    if not targets:
        print("[refcheck] no .tex files found to check.")
        return 0

    hard = 0
    for tf in targets:
        if not tf.exists():
            print(f"[refcheck] {tf}: file not found")
            hard += 1
            continue
        problems = check_file(tf, bib, do_doi=not args.no_doi)
        hard += sum(1 for p in problems if "UNVERIFIED" not in p)

    print(f"[refcheck] {'OK' if hard == 0 else f'{hard} inconsistency(ies) found'}")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
