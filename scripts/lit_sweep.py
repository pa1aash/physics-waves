"""Session L4 Step 3: broad literature retrieval sweep.

Drives the query matrix (`docs/literature/QUERY_MATRIX.md`) against OpenAlex and
writes every candidate to `docs/literature/CANDIDATE_POOL.csv` with the query
string that surfaced it and a UTC retrieval timestamp.

Why OpenAlex rather than web search: it returns a DOI alongside structured
metadata in the same call, which is what makes the scope contract's paper-trail
rule enforceable. Web search returns prose about papers; this returns the papers.

Verification is deliberately NOT done here. Step 4 re-resolves every DOI against
Crossref and requires the returned title to match. Resolution alone is not
verification -- this project has already shipped one file that turned out to be
the wrong Haurwitz paper.

Run: python scripts/lit_sweep.py
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
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "literature" / "CANDIDATE_POOL.csv"
MAILTO = "research@example.com"

# --- the query matrix, as executable rows --------------------------------------
# (row id, theory area, [query strings])
QUERIES: list[tuple[str, str, list[str]]] = [
    (
        "Q1",
        "benchmark suite",
        [
            "shallow water equations spherical geometry standard test set",
            "spectral transform shallow water test suite error norms",
            "numerical approximations shallow water sphere benchmark",
            "shallow water model intercomparison sphere",
        ],
    ),
    (
        "Q2",
        "Rossby wave dispersion",
        [
            "Rossby Haurwitz wave sphere dispersion relation",
            "barotropic vorticity equation spherical harmonics normal modes",
            "planetary waves rotating sphere phase speed",
            "nondivergent barotropic Rossby wave westward propagation",
        ],
    ),
    (
        "Q3",
        "Hough modes / Laplace tidal equations",
        [
            "Laplace tidal equations Hough functions sphere",
            "Lamb parameter shallow water sphere eigenfrequencies",
            "normal modes ultralong waves atmosphere",
            "divergent barotropic dispersion deformation radius",
            "Hough mode eigenfrequency shallow water sphere",
            "free oscillations rotating atmosphere spherical",
        ],
    ),
    (
        "Q4",
        "barotropic instability Rayleigh-Kuo",
        [
            "barotropic instability zonal jet Rayleigh Kuo criterion",
            "Charney Stern theorem potential vorticity gradient",
            "necessary condition instability barotropic shear flow",
            "barotropic instability sphere spherical geometry",
            "inflection point criterion rotating shear flow",
        ],
    ),
    (
        "Q5",
        "linear stability EVP for jets",
        [
            "linear stability eigenvalue problem barotropic jet sphere",
            "normal mode instability zonal flow spherical harmonics growth rate",
            "stability Rossby Haurwitz wave",
            "barotropic instability normal mode spectrum numerical",
            "non-normal transient growth shear flow",
        ],
    ),
    (
        "Q6",
        "counter-propagating Rossby waves",
        [
            "counter propagating Rossby waves shear instability",
            "potential vorticity thinking isentropic maps",
            "Rossby edge wave phase locking instability",
            "critical layer instability baroclinic flow",
            "Bretherton potential vorticity sheet boundary",
        ],
    ),
    (
        "Q7",
        "Rhines scale / jets / zonostrophic",
        [
            "Rhines scale beta plane turbulence arrest",
            "zonal jet formation rotating turbulence",
            "zonostrophic turbulence jet spacing",
            "beta plane turbulence anisotropy zonal flow",
            "Jovian banding zonal jets turbulence",
        ],
    ),
    (
        "Q8",
        "spectral methods / Dedalus",
        [
            "Dedalus spectral framework partial differential equations",
            "tensor calculus spherical coordinates Jacobi polynomials",
            "spherical harmonic transform numerical method sphere",
            "sphere spectral method pole problem",
        ],
    ),
    (
        "Q9",
        "Galewsky jet and forward citations",
        [
            "initial value problem testing numerical models global shallow water",
            "Galewsky barotropic instability test case",
            "barotropic instability test case shallow water models comparison",
        ],
    ),
    (
        "Q10",
        "reanalysis / observed eddy phenomenology",
        [
            "ERA5 global reanalysis",
            "NCEP NCAR reanalysis project",
            "space time spectral analysis atmospheric waves Hayashi",
            "observed phase speed spectra extratropical eddies",
            "wavenumber frequency spectrum geopotential height",
            "stationary and transient eddy phase speed troposphere",
        ],
    ),
    (
        "Q11",
        "barotropic/baroclinic scope boundary",
        [
            "barotropic model limitations atmospheric dynamics",
            "baroclinic instability energy source extratropical cyclone",
            "equivalent barotropic level atmosphere",
        ],
    ),
    (
        "Q12",
        "ML weather models (acknowledgement)",
        [
            "spherical harmonic neural operator weather",
            "machine learning global weather forecasting model",
        ],
    ),
    # Targeted deliverables promoted by the Step 1 critique.
    (
        "T1",
        "TARGET Kasahara 1976",
        [
            "Kasahara normal modes of ultralong waves in the atmosphere",
        ],
    ),
    (
        "T3",
        "TARGET observed eddy phase speeds",
        [
            "Randel Held phase speed spectra baroclinic eddies",
        ],
    ),
]

PER_QUERY = 12


def openalex(query: str, per_page: int = PER_QUERY) -> list[dict]:
    url = (
        "https://api.openalex.org/works?search="
        + urllib.parse.quote(query)
        + f"&per-page={per_page}&mailto={MAILTO}"
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                return json.load(r).get("results", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(8 * (attempt + 1))
                continue
            return []
        except Exception:
            time.sleep(4)
    return []


def forward_citations(doi: str, limit: int = 200) -> list[dict]:
    """Every work citing a given DOI, paged.

    Must go via the OpenAlex work id: the ``cites:doi:...`` filter form returns
    HTTP 200 with an empty result set rather than an error, which is how the
    first run of this sweep silently reported zero forward citations for a paper
    with 208 of them. Resolve the id first, then filter on it.
    """
    try:
        u = f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}?mailto={MAILTO}"
        with urllib.request.urlopen(u, timeout=45) as r:
            wid = json.load(r)["id"].rsplit("/", 1)[-1]
    except Exception:
        return []
    out: list[dict] = []
    page = 1
    while len(out) < limit:
        url = (
            f"https://api.openalex.org/works?filter=cites:{wid}"
            f"&per-page=100&page={page}&mailto={MAILTO}"
        )
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                res = json.load(r).get("results", [])
        except Exception:
            break
        if not res:
            break
        out.extend(res)
        page += 1
        time.sleep(0.4)
    return out[:limit]


def norm_doi(raw: str | None) -> str:
    if not raw:
        return ""
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", raw.strip()).lower()


def row_from(w: dict, qid: str, area: str, query: str, ts: str) -> dict | None:
    doi = norm_doi(w.get("doi"))
    if not doi:
        return None
    title = (w.get("display_name") or "").replace("\n", " ").strip()
    if not title:
        return None
    authors = "; ".join(a["author"]["display_name"] for a in (w.get("authorships") or [])[:4])
    src = (w.get("primary_location") or {}).get("source") or {}
    return {
        "doi": doi,
        "title": title,
        "authors": authors,
        "year": w.get("publication_year") or "",
        "venue": (src.get("display_name") or "").strip(),
        "type": w.get("type") or "",
        "cited_by": w.get("cited_by_count") or 0,
        "oa_url": ((w.get("open_access") or {}).get("oa_url") or ""),
        "query_id": qid,
        "area": area,
        "query_string": query,
        "retrieved_utc": ts,
    }


def main() -> int:
    pool: dict[str, dict] = {}
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    for qid, area, queries in QUERIES:
        for q in queries:
            results = openalex(q)
            added = 0
            for w in results:
                row = row_from(w, qid, area, q, ts)
                if row and row["doi"] not in pool:
                    pool[row["doi"]] = row
                    added += 1
            print(f"  {qid:4s} {added:3d} new / {len(results):3d} hits  <- {q}")
            time.sleep(0.4)

    # Forward-citation sweep on Galewsky et al. (2004): does a published
    # normal-mode spectrum of that jet exist? Fragment b2 depends on the answer.
    gal = "10.3402/tellusa.v56i5.14436"
    cites = forward_citations(gal, limit=250)
    added = 0
    for w in cites:
        row = row_from(w, "F1", "forward-cite: Galewsky 2004", f"cites:{gal}", ts)
        if row and row["doi"] not in pool:
            pool[row["doi"]] = row
            added += 1
    print(f"  F1   {added:3d} new / {len(cites):3d} hits  <- forward citations of Galewsky 2004")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "doi",
        "title",
        "authors",
        "year",
        "venue",
        "type",
        "cited_by",
        "oa_url",
        "query_id",
        "area",
        "query_string",
        "retrieved_utc",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        wtr = csv.DictWriter(fh, fieldnames=fields)
        wtr.writeheader()
        for row in sorted(pool.values(), key=lambda r: (r["query_id"], -int(r["cited_by"]))):
            wtr.writerow(row)

    print(f"\ncandidate pool: {len(pool)} unique DOIs -> {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
