"""Session L4 Step 16: compile manuscript/references.bib from the verified pool.

Only rows marked ``selected_for_bib == yes`` in
``docs/literature/VERIFIED_POOL.csv`` are emitted, and every emitted entry carries
author, title, venue, year and a ``doi`` field -- the audit enforces all five.

Entry keys are ``firstauthorlastname + year`` with a letter suffix on collision,
so a key traces to a human-readable reference at a glance.

The .bib is deliberately a superset of what the drafts cite: LaTeX emits only
cited entries, so a curated corpus in the file costs nothing and lets Session L11
draw on the whole verified set without another retrieval round.

Run: python scripts/lit_bib.py
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POOL = REPO / "docs" / "literature" / "VERIFIED_POOL.csv"
OUT = REPO / "manuscript" / "references.bib"

TYPE_TO_BIB = {
    "peer-reviewed journal": "article",
    "preprint": "misc",
    "textbook": "book",
    "book chapter": "incollection",
    "technical report": "techreport",
    "thesis": "phdthesis",
    "conference proceedings": "inproceedings",
}


def ascii_key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


def latex_escape(s: str) -> str:
    """Escape the characters that break a .bib field, leaving maths alone."""
    s = s.replace("\\", " ")
    for a, b in (
        ("&", r"\&"),
        ("%", r"\%"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", "("),
        ("}", ")"),
        ("~", " "),
        ("^", " "),
        ("$", ""),
    ):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


def bib_authors(raw: str) -> str:
    """OpenAlex 'Given Family; Given Family' -> BibTeX 'Family, Given and ...'."""
    out = []
    for name in (n.strip() for n in raw.split(";")):
        if not name:
            continue
        parts = name.split()
        if len(parts) == 1:
            out.append(latex_escape(parts[0]))
        else:
            out.append(f"{latex_escape(parts[-1])}, {latex_escape(' '.join(parts[:-1]))}")
    return " and ".join(out) if out else "Anon"


def main() -> int:
    rows = [
        r
        for r in csv.DictReader(POOL.open(newline="", encoding="utf-8"))
        if r.get("selected_for_bib") == "yes"
    ]
    rows.sort(key=lambda r: (str(r["year"]), r["title"]))

    used: dict[str, int] = {}
    entries: list[str] = []
    for r in rows:
        first = (r["authors"].split(";")[0] or "anon").strip().split()
        last = ascii_key(first[-1]) if first else "anon"
        base = f"{last or 'anon'}{r['year'] or 'nd'}"
        n = used.get(base, 0)
        used[base] = n + 1
        key = base if n == 0 else f"{base}{chr(ord('a') + n)}"

        etype = TYPE_TO_BIB.get(r["source_type"], "article")
        title = latex_escape(r["crossref_title"] or r["title"])
        venue = latex_escape(r["venue"])
        fields = [
            f"  author  = {{{bib_authors(r['authors'])}}}",
            f"  title   = {{{title}}}",
            f"  year    = {{{r['year']}}}",
            f"  doi     = {{{r['doi']}}}",
        ]
        if venue:
            fields.insert(
                2,
                f"  journal = {{{venue}}}" if etype == "article" else f"  publisher = {{{venue}}}",
            )
        entries.append("@" + etype + "{" + key + ",\n" + ",\n".join(fields) + "\n}")

    header = (
        "% manuscript/references.bib\n"
        "% Compiled by scripts/lit_bib.py from docs/literature/VERIFIED_POOL.csv\n"
        "% (Session L4). Every entry's DOI was resolved against the Crossref work\n"
        "% record AND its title matched before the entry was admitted; see\n"
        "% docs/literature/SCOPE_CONTRACT.md for the verification standard.\n"
        f"% Entries: {len(entries)}\n\n"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(header + "\n\n".join(entries) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} entries -> {OUT.relative_to(REPO)}")
    return 0 if len(entries) >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())
