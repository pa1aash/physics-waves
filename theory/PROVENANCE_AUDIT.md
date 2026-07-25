# Provenance audit — every external-match claim in the theory output

**Written Session L3-PATCH, 2026-07-25.**

## Why this file exists

Session L3 produced `theory/sympy_checks/check_crw_two_interface.py`, which
compared three computed constants against numbers labelled "published". Operator
review asked the obvious question: were those numbers read from a page of a
paper, or supplied from general familiarity with the classical problem? The
project's standing rule (`docs/CONVENTIONS.md`, "Third-party text") permits only
the first.

Investigating that one script surfaced a second instance of the same pattern
elsewhere. This file is the systematic sweep, so the class of gap cannot recur
silently: **every place in `theory/sympy_checks/output/*.txt` and
`theory/derivations.tex` that claims agreement with something external now has a
row here**, and each row names either a specific page or equation of a source
actually read, or says plainly that no external source is involved.

## The rule this enforces

A claim of the form "matches published", "agrees with", "cf.", "standard",
"classical" is acceptable only if it resolves to one of five categories. The
first three were defined in Session L3-PATCH; the last two were added in Session
PRE-L5, when Session L4b's findings were merged into this ledger.

| Category | What it means | What it licenses |
|----------|---------------|------------------|
| **READ** | A PDF held in `docs/literature/` was opened and the specific passage located | Page- and equation-precise claims |
| **ABSTRACT-VERIFIED** | The publisher's own abstract was read directly; the full text was **not** obtained | Only claims the abstract itself makes, in its own words. **No page or equation pointer.** |
| **TITLE-ONLY** | Neither full text nor abstract was obtained; only the title and bibliographic record | Essentially nothing beyond existence and, where the title names it, the governing equation. Must be flagged wherever used |
| **DOI-ATTRIBUTED** | Not held, cited for historical attribution only, and nothing in the derivation depends on its contents | Attribution alone |
| **INTERNAL** | No external source at all; derived and verified within the project | Whatever the internal check establishes |

**Why ABSTRACT-VERIFIED needed its own row rather than being folded into
DOI-ATTRIBUTED.** They are materially different evidentiary standards. A
DOI-attributed citation is a name in a reference list. An abstract read from the
publisher is a statement the authors wrote about their own result, and it can
legitimately support a claim about *what the paper found* — but it cannot support
a claim about *how they found it*, or any number that appears only in the body.
Session L4b's central finding rests on two such abstracts, so conflating the two
categories would have hidden exactly the distinction that matters.

**Why TITLE-ONLY is worth recording at all.** Because the alternative is silence,
and silence reads as a stronger claim than it is. Two Skiba papers are cited on
their titles alone; one of them names its governing equation in the title, which
is genuinely informative, and the other does not, which is genuinely not.

"Recalled from familiarity" is not on the list.

## The audit

### `theory/sympy_checks/output/`

| Location | Claim | Grounding | Status |
|----------|-------|-----------|--------|
| `check_crw_two_interface.txt` arm 1 | "matches HBA99 Eq. (6)" | **READ** — Heifetz, Bishop & Alpert (1999), QJRMS 125(560), **p. 2838, Eq. (6)**. Read from the held PDF this session. | OK |
| `check_crw_two_interface.txt` arm 3 | `K_c` vs 1.28 | **READ** — same paper, **p. 2838**, paragraph immediately after Eq. (6): states the critical wavenumber as `K_c = 1 + exp(−K_c) ≈ 1.28`. | OK |
| `check_crw_two_interface.txt` arm 3 | `K_m` vs 0.8 | **READ** — same paragraph: the growth rate `ΛKC_i` is maximum at `K_max ≈ 0.8`. | OK |
| `check_crw_two_interface.txt` arm 3 | peak growth vs 0.20 | **READ** — same paragraph: that maximum "is equal to about 20% of the shear Λ". | OK |
| `check_christoffel_symbols.txt` arm 2 | previously "against published 2-sphere values" | **INTERNAL** — no source was consulted. **Corrected this session**: the arm now recomputes the connection independently from the colatitude metric and transports it, quoting nothing. | **FIXED** |
| `check_christoffel_symbols.txt` arm 3 | Gaussian curvature `= 1/R²` | **INTERNAL** — computed from the Riemann tensor of the connection under test. Added this session as a second source-free confirmation. | OK |
| `check_christoffel_symbols.txt` arm 1 | "against the closed forms written in §2" | **INTERNAL** — compares the script against the document, both derived from the same metric. | OK |
| `check_rh_dispersion.txt` arms 1–3 | "expected −Ω/…", "expected −β/k²" | **INTERNAL** — the expected values are the project's own derivation; the script re-derives them from the ansatz. | OK |
| `check_spherical_laplacian_eigenvalue.txt` | eigenvalue `−n(n+1)/R²` | **INTERNAL** — the associated Legendre equation, verified symbolically and numerically. | OK |
| `check_pv_conservation.txt` | identity `h Dq/Dt = curl(M) − qC` | **INTERNAL** — proved symbolically for arbitrary fields. | OK |
| `check_hough_epsilon_limit.txt` arms 1–3 | recurrences, adjoint identity, rate ≈ 1 | **INTERNAL** — quadrature vs closed-form recurrence, both computed here; the rate is measured, not compared to a literature value. | OK |
| `check_hough_epsilon_limit.txt` arms 4–5 | H5 readout, sectoral explanation | **INTERNAL** — computed and demonstrated causally within the project. | OK |
| `check_rayleigh_kuo.txt` arms 1–3 | the necessary condition | **INTERNAL** — derived symbolically. Kuo (1949) is cited in the document for the result's origin, not used as a numerical benchmark. | OK |
| `check_rayleigh_kuo.txt` arm 4 | Galewsky jet growth rates | **INTERNAL** — solved here. The jet profile itself is READ (Galewsky et al. 2004, eq. 2). No published growth rate is compared against. | OK |

### `theory/derivations.tex`

| Location | Claim | Grounding | Status |
|----------|-------|-----------|--------|
| §2, after eq. (5) | previously "transporting the published colatitude forms" | **INTERNAL** — **corrected this session** to describe the independent recomputation and the curvature check. | **FIXED** |
| §2 | operators "follow from √g in the standard way" | **INTERNAL** — verified in `check_christoffel_symbols.py` arms 4–5. | OK |
| §5 | `c_ang = −2Ω/[n(n+1)]` attributed to Rossby (1939), Haurwitz (1940b) | **DOI-ATTRIBUTED / bibliographic** — Rossby's identity confirmed by reading the held scan's title page; Haurwitz (1940b) is *not held* (see `docs/literature/MISSING.md`). Neither is load-bearing: §5 derives the result and `check_rh_dispersion.py` verifies it. | OK |
| §6 | "classical formulation … due to Longuet-Higgins (1968), with the vector-harmonic treatment of Swarztrauber & Kasahara (1985)" | **DOI-ATTRIBUTED** — both unobtainable, recorded in `MISSING.md`. Cited for historical attribution only; the derivation and its validation target (`ε → 0`) are internal. | OK |
| §7 | Rhines' arrest wavenumber `k_β = (β/2U)^{1/2}` | **READ** — Rhines (1975), JFM 69, abstract and §1, held and read. | OK |
| §7 | Vallis & Maltrud's `O(√(U/β))` transition scale | **READ** — Vallis & Maltrud (1993), JPO 23, p. 1346, abstract and introduction, read visually from the held scan. | OK |
| §8 | Rayleigh–Kuo criterion attributed to Kuo (1949) | **READ** — Kuo (1949), J. Meteorol. 6(2), pp. 105–110 read visually; §5 of that paper states the necessary condition as the existence of a point where `β − U'' = 0`. | OK |
| §9 | critical-layer argument attributed to Bretherton (1966) | **READ** — Bretherton (1966), QJRMS 92, read in full this session; §5 and p. 332 carry the statement that a growing normal mode must have a critical layer. | OK |
| §10 | edge-wave / delta-function equivalence attributed to Bretherton (1966) | **READ** — same paper, p. 329 eq. (6): a discontinuity is equivalent to a delta function in PV. | OK |
| §10 | PV inversion attributed to Hoskins et al. (1985) | **READ** — held and read. | OK |
| §10 | CRW dispersion relation and constants | **READ** — Heifetz et al. (1999) p. 2838, as above. Page reference now given in the text. | OK |
| §11 | Galewsky jet, balance integration, perturbation | **READ** — Galewsky et al. (2004), eqs. (2), (3), (4), held and read. | OK |
| §11 | comparison of the published balance construction against the shipped Dedalus example | **READ** — recorded in `tests/phase0_gate/galewsky_comparison.md` (Session L1). | OK |

## Outcome

Two items were **FIXED**; both were in the same category, and neither changed any
physics.

1. **`check_christoffel_symbols.py` arm 2** claimed agreement with "published
   2-sphere values" when no publication had been consulted. The 2-sphere
   Christoffel symbols are standard material, which is exactly what makes the
   phrasing tempting and exactly why the rule exists. The arm was rewritten to
   recompute the connection independently in the colatitude chart and transport
   it — a stronger check than the original, since it now verifies the convention
   handling instead of restating it — and a new arm confirms the implied
   Gaussian curvature is `1/R²`.

2. **§2 of `derivations.tex`** carried the same phrasing and was corrected to
   match.

The three CRW constants that prompted the audit turned out to be **properly
grounded all along**: they are on p. 2838 of Heifetz, Bishop & Alpert (1999),
which is the PDF the project holds and which Session L3 read. What was wrong was
narrower — the *file* was named `heifetz_2004_…`, so a reader of the review
document could not tell which paper had actually been consulted. The filename is
corrected and the page reference is now explicit in the script, the output, the
document and the bibliography.

## For later sessions

Any new check that compares a computed number against an external value must add
a row here naming the page or equation. Audit check 31 enforces that every
external-match claim in `theory/sympy_checks/output/*.txt` has a corresponding
row in this table.

---

## Session L4b and PRE-L5 additions — the divergent-stability literature

Merged here in Session PRE-L5 so that **one file answers "how do we know this
citation says what we say it says"** for the whole project. These rows previously
lived in `docs/literature/RIPA_HAYASHI_YOUNG_NOTES.md` and
`SKIBA_PROGRAMME_NOTES.md` with their own ad hoc labels; those documents remain as
the detailed working notes, but this table is the ledger.

| Citation | DOI | Category | What is claimed from it | Basis |
|----------|-----|----------|-------------------------|-------|
| **Ripa (1983)**, *JFM* 126, 463–489 | `10.1017/S0022112083000270` | **ABSTRACT-VERIFIED** | The two sufficient stability conditions for a one-layer zonal flow, and that they reduce to the classical criterion in the nondivergent limit | Publisher abstract, obtained verbatim. It states both conditions **in words**; their translation into inequalities in `check_ripa_divergent_condition.py` is the project's reading, flagged there |
| **Hayashi & Young (1987)**, *JFM* 184, 477–504 | `10.1017/S0022112087002982` | **ABSTRACT-VERIFIED** | That shallow-water shear instability occurs with no potential-vorticity gradient at all, on an **equatorial** β-plane, by a negative-energy mechanism | Publisher abstract, obtained verbatim |
| **Paldor, Shamir & Garfinkel (2020)**, *GAFD* 115(1), 15–34 | `10.1080/03091929.2020.1724996` | **ABSTRACT-VERIFIED** | That nondivergent growth rates exceed shallow-water ones, by >50% at depths of 5–10 km, converging above 30 km; jets studied are polar and equatorial | **Published** abstract, obtained in Session PRE-L5 via OpenAlex. Upgrades L4b, which relied on the authors' EGU2020 conference abstract. Journal PDF remains unobtainable (bronze OA, blocked to scripted retrieval) |
| **White & Staniforth (2009)**, *QJRMS* 135(640), 961–971 | `10.1002/qj.504` | **ABSTRACT-VERIFIED** | That Ripa's criteria extend to the sphere with orography, in the stated context of testing discretised numerical models | Publisher abstract, obtained verbatim |
| **Staniforth & White (2008)**, *QJRMS* | `10.1002/qj.240` | **ABSTRACT-VERIFIED** | That Ripa-class conditions are used to choose test-case parameters so that evolution in a model is of numerical origin | Publisher abstract |
| **Skiba & Pérez-García (2004)** | `10.1002/num.20042` | **ABSTRACT-VERIFIED** | That the paper works in the **nondivergent** barotropic vorticity equation, and supplies a necessary condition for exponential instability plus a maximum-growth-rate estimate | Publisher abstract, which names the governing equation |
| **Skiba (2008)** | `10.1007/s10958-008-0091-3` | **TITLE-ONLY** | **Nothing.** Listed for completeness of the programme; no claim rests on it | No abstract available in Crossref or OpenAlex |
| **Skiba (2024)** | `10.4310/dpde.2024.v21.n3.a1` | **TITLE-ONLY** | That it treats the barotropic vorticity equation on a sphere — from the title, which names the equation | Title only; flagged as such |
| **Constantin & Germain (2022)**, *ARMA* 245, 587–644 | `10.1007/s00205-022-01791-3` | **ABSTRACT-VERIFIED** | That it works in **Euler's equation** on a rotating sphere, i.e. nondivergent, and proves an Arnold-type stability criterion | Publisher abstract |
| **Cao, Wang & Zuo (2023)** | `10.48550/arXiv.2305.03279` | **ABSTRACT-VERIFIED** | That it works in the **incompressible Euler equation** on a 2-D rotating sphere, i.e. nondivergent | arXiv abstract (open access) |

### The one conclusion these rows jointly support

That the Skiba/Constantin–Germain/Cao–Wang programme is uniformly **nondivergent**
— which is what narrows fragment b1 and what shows that the *divergent* territory
is occupied by Ripa, White & Staniforth and Paldor et al. instead. Every row above
that carries weight in that conclusion is ABSTRACT-VERIFIED at worst, and the two
TITLE-ONLY rows are not load-bearing for it.

### Citations added to `theory/derivations.tex` in Session PRE-L5

Four, all ABSTRACT-VERIFIED, each carrying its status in its own bibliography
entry so a reader of the theory document sees it without opening this file:
`ripa1983`, `hayashi1987`, `paldor2020`, `white2009`.
