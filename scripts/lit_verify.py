"""Session L4 Step 4: source triage, credibility scoring and DOI verification.

Reads `docs/literature/CANDIDATE_POOL.csv` and writes the scored, *verified*
subset to `docs/literature/VERIFIED_POOL.csv`.

Verification is deliberately stricter than "the DOI resolves". A DOI that
resolves proves an identifier exists, not that it points at the paper we think
it does. This project has already shipped one file that turned out to be the
wrong Haurwitz paper, caught only in L3-PATCH, so the standard here is:

    resolve the DOI against the Crossref work record
    AND require the returned title to match the recorded title

Anything failing either test is dropped from the pool entirely rather than kept
with a caveat. Per the scope contract: an unverifiable reference is not a weaker
citation, it is not a citation.

Run: python scripts/lit_verify.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "docs" / "literature" / "CANDIDATE_POOL.csv"
OUT = REPO / "docs" / "literature" / "VERIFIED_POOL.csv"
MAILTO = "research@example.com"

# Title-similarity floor for a DOI to count as verified. 0.85 tolerates
# punctuation, ligature and case differences between OpenAlex and Crossref
# renderings of the same title, but not a different paper.
TITLE_MATCH_FLOOR = 0.85

# --- relevance tiers ----------------------------------------------------------
# Assigned from the query row that surfaced a paper, then upgraded for the named
# anchor DOIs. Tier drives what a citation may be used for downstream, so it is
# recorded rather than inferred later.
CORE_QUERIES = {"Q2", "Q3", "Q4", "Q5", "Q6", "Q9", "T1"}
SUPPORTING_QUERIES = {"Q1", "Q7", "Q8", "Q10", "F1"}
TANGENTIAL_QUERIES = {"Q11", "Q12", "T3"}

# Papers the project holds as PDFs, or that the theory cites directly. These are
# forced to core tier regardless of which query surfaced them.
ANCHOR_DOIS = {
    "10.3402/tellusa.v56i5.14436",  # Galewsky 2004
    "10.1016/j.jcp.2005.04.022",  # Lauter 2005
    "10.1016/0021-9991(92)90060-c",  # Williamson 1992
    "10.1002/qj.49711147002",  # Hoskins 1985
    "10.1002/qj.49712556004",  # Heifetz 1999
    "10.1002/qj.49709239302",  # Bretherton 1966
    "10.1017/s0022112075001504",  # Rhines 1975
    "10.1103/physrevresearch.2.023068",  # Burns 2020
    "10.1016/j.jcpx.2019.100013",  # Vasil 2019
    "10.1098/rsta.1968.0003",  # Longuet-Higgins 1968
    "10.1137/0906033",  # Swarztrauber & Kasahara 1985
    "10.1175/1520-0493(1976)104<0669:nmouwi>2.0.co;2",  # Kasahara 1976
    "10.1175/1520-0469(1949)006<0105:diotdn>2.0.co;2",  # Kuo 1949
    "10.1175/1520-0485(1993)023<1346:gomfaj>2.0.co;2",  # Vallis & Maltrud 1993
    "10.1002/qj.3803",  # Hersbach 2020 (ERA5)
    "10.1175/1520-0477(1996)077<0437:tnyrp>2.0.co;2",  # Kalnay 1996
    "10.1006/jcph.1995.1125",  # Jakob-Chien 1995
    "10.3402/tellusa.v52i2.12258",  # Thuburn & Li 2000
}

# PDFs actually present in docs/literature/, keyed by DOI -> filename. "READ"
# status in the output means the project holds the paper; anything else is
# IDENTIFIER-ONLY, a distinction the scope contract requires be recorded.
HELD: dict[str, str] = {
    "10.3402/tellusa.v56i5.14436": "galewsky_2004_initial_value_problem.pdf",
    "10.1016/j.jcp.2005.04.022": "lauter_2005_unsteady_analytical_solutions.pdf",
    "10.1016/0021-9991(92)90060-c": "williamson_1992_standard_test_set.pdf",
    "10.1002/qj.49711147002": "hoskins_1985_isentropic_potential_vorticity.pdf",
    "10.1002/qj.49712556004": "heifetz_1999_counter_propagating_rossby_waves.pdf",
    "10.1002/qj.49709239302": "bretherton_1966_critical_layer_instability.pdf",
    "10.1017/s0022112075001504": "rhines_1975_waves_and_turbulence_beta_plane.pdf",
    "10.1103/physrevresearch.2.023068": "burns_2020_dedalus.pdf",
    "10.1016/j.jcpx.2019.100013": "vasil_2019_tensor_calculus_spheres.pdf",
    "10.1175/1520-0493(1976)104<0669:nmouwi>2.0.co;2": (
        "kasahara_1976_normal_modes_ultralong_waves.pdf"
    ),
    "10.1175/1520-0469(1949)006<0105:diotdn>2.0.co;2": "kuo_1949_dynamic_instability.pdf",
    "10.1175/1520-0485(1993)023<1346:gomfaj>2.0.co;2": (
        "vallis_1993_generation_of_mean_flows_and_jets.pdf"
    ),
    "10.1002/qj.3803": "hersbach_2020_era5_global_reanalysis.pdf",
    "10.1175/1520-0477(1996)077<0437:tnyrp>2.0.co;2": "kalnay_1996_ncep_ncar_reanalysis.pdf",
    "10.1006/jcph.1995.1125": "jakobchien_1995_spectral_transform_solutions.pdf",
    "10.3402/tellusa.v52i2.12258": "thuburn_2000_numerical_simulations_rossby_haurwitz.pdf",
}

TYPE_MAP = {
    "article": "peer-reviewed journal",
    "preprint": "preprint",
    "book": "textbook",
    "book-chapter": "book chapter",
    "report": "technical report",
    "dissertation": "thesis",
    "proceedings-article": "conference proceedings",
}


def normalise(s: str) -> str:
    s = s.lower()
    s = re.sub(r"&(amp|lt|gt|#\d+);", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def crossref(doi: str) -> dict | None:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    req = urllib.request.Request(url, headers={"User-Agent": f"physics-waves-L4 ({MAILTO})"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)["message"]
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(3 * (attempt + 1))
                continue
            return None
        except Exception:
            time.sleep(2)
    return None


def verify(row: dict) -> dict | None:
    m = crossref(row["doi"])
    if m is None:
        return None
    titles = m.get("title") or []
    if not titles:
        return None
    sim = max(SequenceMatcher(None, normalise(row["title"]), normalise(t)).ratio() for t in titles)
    if sim < TITLE_MATCH_FLOOR:
        return None

    doi = row["doi"]
    qid = row["query_id"]
    tier = (
        "core"
        if (doi in ANCHOR_DOIS or qid in CORE_QUERIES)
        else "supporting" if qid in SUPPORTING_QUERIES else "tangential"
    )
    ctype = m.get("type", row.get("type", ""))
    return {
        **row,
        "crossref_title": titles[0].replace("\n", " ").strip(),
        "title_similarity": f"{sim:.3f}",
        "source_type": TYPE_MAP.get(ctype, ctype or "unknown"),
        "relevance_tier": tier,
        "verified": "yes",
        "read_status": "READ" if doi in HELD else "IDENTIFIER-ONLY",
        "local_pdf": HELD.get(doi, ""),
        "verified_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main() -> int:
    rows = list(csv.DictReader(SRC.open(newline="", encoding="utf-8")))
    print(f"candidates: {len(rows)}")

    kept: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, res in enumerate(ex.map(verify, rows), start=1):
            if res:
                kept.append(res)
            if i % 100 == 0:
                print(f"  verified {i}/{len(rows)} … kept {len(kept)}")

    dropped = len(rows) - len(kept)
    print(f"\nverified: {len(kept)}   dropped (unresolvable or title mismatch): {dropped}")

    order = {"core": 0, "supporting": 1, "tangential": 2}
    kept.sort(key=lambda r: (order[r["relevance_tier"]], -int(r["cited_by"] or 0)))

    fields = [
        "doi",
        "title",
        "crossref_title",
        "title_similarity",
        "authors",
        "year",
        "venue",
        "source_type",
        "relevance_tier",
        "verified",
        "read_status",
        "local_pdf",
        "cited_by",
        "oa_url",
        "query_id",
        "area",
        "query_string",
        "retrieved_utc",
        "verified_utc",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(kept)

    for t in ("core", "supporting", "tangential"):
        n = sum(1 for r in kept if r["relevance_tier"] == t)
        print(f"  {t:12s} {n}")
    print(f"  READ (PDF held) {sum(1 for r in kept if r['read_status'] == 'READ')}")
    print(f"\n-> {OUT.relative_to(REPO)}")
    return 0 if len(kept) >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())
