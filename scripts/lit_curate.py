"""Session L4 Step 4b: curate the verified corpus down to a bibliography.

`VERIFIED_POOL.csv` is a 669-entry *corpus*: everything a query surfaced whose
DOI resolves and whose title matches. That is the honest retrieval record, and it
stays. It is not a bibliography.

Selecting by citation count alone does not work, and it is worth saying why
because the failure is instructive: OpenAlex relevance-matches on words, so
ranking its hits by citations surfaces the most-cited paper that happened to
share vocabulary, not the most relevant one. The first attempt at this promoted
"The Yamabe problem", "4D flow MRI" and "Machine Learning in Agriculture" into a
geophysical fluid dynamics bibliography.

Selection here is therefore topical and explicit:

  ANCHOR   the project holds the PDF, or the theory cites it directly -> always in
  DOMAIN   title carries a strong domain term AND the venue is a plausible
           GFD / atmospheric / fluids / numerical-methods outlet
  EXCLUDE  title carries an off-domain term (medicine, ecology, finance, ...)

Every selected row records WHY it was selected, so the choice is auditable rather
than a matter of taste.

Run: python scripts/lit_curate.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POOL = REPO / "docs" / "literature" / "VERIFIED_POOL.csv"

# --- strong domain vocabulary -------------------------------------------------
# A title must hit at least one of these to be considered on-topic.
DOMAIN = [
    r"rossby",
    r"haurwitz",
    r"barotropic",
    r"baroclinic",
    r"shallow[- ]water",
    r"vortic",
    r"potential vorticity",
    r"\bjet\b",
    r"\bjets\b",
    r"zonal",
    r"beta[- ]plane",
    r"beta effect",
    r"spherical harmonic",
    r"\bsphere\b",
    r"spherical geometry",
    r"hough",
    r"tidal equation",
    r"laplace tidal",
    r"geostrophic",
    r"quasi[- ]geostrophic",
    r"instabilit",
    r"stabilit",
    r"reanalysis",
    r"era5",
    r"ncep",
    r"teleconnection",
    r"planetary wave",
    r"gravity wave",
    r"normal mode",
    r"eigen",
    r"critical layer",
    r"turbulence",
    r"dynamical core",
    r"spectral method",
    r"spectral transform",
    r"semi[- ]lagrangian",
    r"finite[- ]volume",
    r"discontinuous galerkin",
    r"icosahedral",
    r"cubed[- ]sphere",
    r"atmospher",
    r"ocean",
    r"coriolis",
    r"deformation radius",
    r"burger number",
    r"stratospher",
    r"tropospher",
    r"phase speed",
    r"dispersion relation",
    r"wavenumber",
    r"hurricane",
    r"cyclone",
    r"zonostrophic",
    r"rhines",
    r"annular mode",
    r"storm track",
    r"dedalus",
    r"weather forecast",
    r"climate model",
    r"general circulation",
]

# --- venues that publish this field ------------------------------------------
VENUE_OK = [
    r"journal of the atmospheric sciences",
    r"monthly weather review",
    r"quarterly journal of the royal meteorological society",
    r"journal of fluid mechanics",
    r"tellus",
    r"journal of computational physics",
    r"journal of physical oceanography",
    r"geophysical.*fluid dynamics",
    r"journal of advances in modeling earth systems",
    r"geoscientific model development",
    r"ocean modelling",
    r"physical review fluids",
    r"physics of fluids",
    r"journal of climate",
    r"climate dynamics",
    r"physical review research",
    r"bulletin of the american meteorological society",
    r"journal of geophysical research",
    r"geophysical research letters",
    r"philosophical transactions",
    r"proceedings of the royal society",
    r"siam journal",
    r"annual review of fluid",
    r"nature",
    r"science",
    r"atmospheric chemistry and physics",
    r"icarus",
    r"journal of the meteorological society of japan",
    r"journal of meteorology",
    r"dynamics of atmospheres and oceans",
    r"computers.*fluids",
    r"international journal for numerical methods in fluids",
    r"j\. atmos",
    r"weather and climate dynamics",
    r"journal of marine research",
    r"communications in computational physics",
    r"astrophysical journal",
    # Applied-mathematics outlets that publish spherical-flow stability work. Added
    # after the first pass silently dropped Skiba & Perez-Garcia (2004) and
    # Constantin & Germain (2022) -- the two strongest prior-art hits for the
    # project's own stability claim -- purely because their venues were absent.
    r"numerical methods for partial differential equations",
    r"archive for rational mechanics and analysis",
    r"journal of mathematical fluid mechanics",
    r"nonlinearity",
    r"dynamics of partial differential equations",
    r"journal of nonlinear science",
    r"studies in applied mathematics",
    r"geophysical and astrophysical fluid dynamics",
    r"journal of mathematical sciences",
    r"nonlinear processes in geophysics",
    r"quarterly of applied mathematics",
    r"theoretical and computational fluid dynamics",
]

# --- hard off-domain exclusions ----------------------------------------------
OFF_DOMAIN = [
    r"\bmri\b",
    r"endothelium",
    r"ion channel",
    r"receptor",
    r"cancer",
    r"cardiac",
    r"agricultur",
    r"evapotranspiration",
    r"macroalgal",
    r"estuar",
    r"soil",
    r"anomaly detection",
    r"deep learning: concepts",
    r"time-series forecasting",
    r"solar irradiance",
    r"yamabe",
    r"black hole",
    r"analogue gravity",
    r"x-ray binaries",
    r"supernova",
    r"nanotube",
    r"glasses and jamming",
    r"seismic",
    r"q-ball",
    r"digital twin",
    r"swat",
    r"stellar astrophysics",
    r"rayleigh-b[eé]nard",
    r"cavitation",
    r"shear banding",
    r"complex fluids",
    r"body tides",
    r"inverted barometer",
    r"tide models",
    r"general relativity and experiment",
    r"tachocline",
]


def hits(patterns: list[str], text: str) -> list[str]:
    return [p for p in patterns if re.search(p, text, re.I)]


def main() -> int:
    rows = list(csv.DictReader(POOL.open(newline="", encoding="utf-8")))
    fields = list(rows[0].keys())
    if "selected_for_bib" not in fields:
        fields += ["selected_for_bib", "selection_reason"]

    n_anchor = n_domain = 0
    for r in rows:
        title = r["title"]
        venue = r["venue"]
        blob = f"{title} {venue}"

        if r["read_status"] == "READ" or r["query_id"] == "A1":
            r["selected_for_bib"] = "yes"
            r["selection_reason"] = "ANCHOR: PDF held or cited directly by the theory"
            n_anchor += 1
            continue

        # Rows from a TARGETED query -- the Step 1 critique's named deliverables
        # (T*) and the Step 5/7 gap-fills (G*) -- are forced in. They were
        # retrieved BY NAME for a stated reason, so the venue whitelist must not
        # veto them. It nearly did: Skiba & Perez-Garcia (2004), the single most
        # important prior-art hit for fragment b1, appeared in "Numerical Methods
        # for Partial Differential Equations", and Constantin & Germain (2022) in
        # "Archive for Rational Mechanics and Analysis" -- neither on the list.
        # A whitelist that silently drops the papers that narrow your own novelty
        # claim is worse than no whitelist.
        if r["query_id"].startswith(("T", "G")):
            r["selected_for_bib"] = "yes"
            r["selection_reason"] = f"TARGETED retrieval ({r['query_id']}): {r['area'][:60]}"
            n_anchor += 1
            continue

        off = hits(OFF_DOMAIN, blob)
        if off:
            r["selected_for_bib"] = "no"
            r["selection_reason"] = f"off-domain term: {off[0]}"
            continue

        dom = hits(DOMAIN, title)
        ven = hits(VENUE_OK, venue)
        if dom and ven:
            r["selected_for_bib"] = "yes"
            r["selection_reason"] = f"DOMAIN: title '{dom[0]}' in venue '{ven[0]}'"
            n_domain += 1
        elif dom and not ven:
            r["selected_for_bib"] = "no"
            r["selection_reason"] = f"on-topic title but venue outside the field: {venue[:40]}"
        else:
            r["selected_for_bib"] = "no"
            r["selection_reason"] = "no strong domain term in title"

    with POOL.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    sel = [r for r in rows if r["selected_for_bib"] == "yes"]
    print(f"corpus            {len(rows)}")
    print(f"selected for bib  {len(sel)}   (anchor {n_anchor}, domain {n_domain})")
    for t in ("core", "supporting", "tangential"):
        print(f"  {t:12s} {sum(1 for r in sel if r['relevance_tier'] == t)}")
    print(f"  READ         {sum(1 for r in sel if r['read_status'] == 'READ')}")
    return 0 if len(sel) >= 60 else 1


if __name__ == "__main__":
    sys.exit(main())
