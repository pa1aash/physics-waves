# References not held, and their mitigation

Sources fall into two categories, and the distinction matters: some are
genuinely unobtainable to this project, and one is simply blocked to automated
retrieval and needs a single human click.

## Blocked to scripts, obtainable by the operator

| Suggested filename | Full citation | Where |
|--------------------|---------------|-------|
| `haurwitz_1940b_spherical_rossby_haurwitz_waves.pdf` | Haurwitz, B. (1940b). The motion of atmospheric disturbances on the spherical Earth. *Journal of Marine Research*, 3(3), 254–267. | [EliScholar record](https://elischolar.library.yale.edu/journal_of_marine_research/575/) |

**Status.** Free, open access, and a stable URL — but the bepress platform
hosting it answers scripted requests with HTTP 403, so Session L3-PATCH could not
download it (three retrieval routes tried: `curl` with browser headers and a
cookie jar, the project's `hyperresearch fetch`, and a direct `HEAD`). It needs
an operator to open the link and save the PDF. **One click, not a research task.**

**Why the project is not blocked.** This is the paper containing the spherical
Rossby–Haurwitz result `c_ang = −2Ω/[n(n+1)]`, but nothing depends on reading it:
§5 of `theory/derivations.tex` derives that result from first principles and
`theory/sympy_checks/check_rh_dispersion.py` verifies it symbolically for nine
`(n, m)` pairs. The citation is bibliographic attribution, not evidence.

**Citation grounding already achieved.** Volume, issue and year (3(3), 1940) are
confirmed live from the publisher's own landing page. The page range 254–267 is
confirmed from the reference list of Thuburn & Li (2000), a PDF this project
holds and has read — not from recollection.

*Note.* The file previously named
`haurwitz_1940_motion_of_atmospheric_disturbances.pdf` is **not** this paper. It
is Haurwitz (1940a), *J. Mar. Res.* 3(1), 35–50, the beta-plane extension of
Rossby (1939), whose own text defers the spherical case to a later paper. It was
renamed `haurwitz_1940a_beta_plane_extension.pdf` in Session L3-PATCH.

## Genuinely unobtainable

Two sources associated with **extension B** (the divergent shallow-water
eigenmodes — Hough functions / Laplace's tidal equations) could not be obtained
as full text. They are recorded here with full citations and DOIs, together with
the reason the project is not blocked by their absence and the accessible
substitutes to chase.

## The two sources

| Filename (if obtained) | Full citation | DOI |
|------------------------|---------------|-----|
| `longuethiggins_1968_laplace_tidal_eigenfunctions.pdf` | Longuet-Higgins, M. S. (1968). The eigenfunctions of Laplace's tidal equations over a sphere. *Philosophical Transactions of the Royal Society A*, 262(1132), 511–607. | [10.1098/rsta.1968.0003](https://doi.org/10.1098/rsta.1968.0003) |
| `swarztrauber_1985_vector_harmonic_analysis.pdf` | Swarztrauber, P. N., & Kasahara, A. (1985). The vector harmonic analysis of Laplace's tidal equations. *SIAM Journal on Scientific and Statistical Computing*, 6(2), 464–491. | [10.1137/0906033](https://doi.org/10.1137/0906033) |

Both are cited from their DOIs for historical attribution. They are the classical
references for the eigenstructure of the divergent tidal equations on a sphere.

## Why the project is not blocked

Neither source is required to *execute* extension B. The Hough-mode
eigenfrequencies are **not read from a published table**; the Laplace tidal
equation eigenvalue problem is derived from first principles in Session L3 and
solved numerically in Dedalus. The validation target is therefore internal, and
it is stronger than an external table would be — a table gives a handful of
tabulated numbers, whereas the solved eigenvalue problem gives the full
dispersion curve and eigenmode structure, at the project's own resolution and
parameters, checkable against a closed-form limit (below).

The physical validation argument (the `ε → 0` limit) is recorded in
`docs/CONVENTIONS.md` under "Authorised extensions to the blueprint": in the
nondivergent limit the divergent eigenfrequencies must reduce exactly to the
Rossby–Haurwitz angular speed `c_ang → −2Ω/[n(n+1)]`, which is hypotheses H1 and
H2 of the blueprint, so the solver is validated against a limit the project
derives independently rather than against a copied table.

## Accessible substitutes to obtain

Two open-access substitutes cover the same physics and should be obtained if
possible (flagged for the **Session L4 corpus-adequacy audit** to chase
open-access equivalents):

| Filename | Citation | Status |
|----------|----------|--------|
| `kasahara_1976_normal_modes_ultralong_waves.pdf` | Kasahara, A. (1976). Normal modes of ultralong waves in the atmosphere. ***Monthly Weather Review*, 104(6), 669–690.** DOI [10.1175/1520-0493(1976)104<0669:NMOUWI>2.0.CO;2](https://doi.org/10.1175/1520-0493(1976)104%3C0669:NMOUWI%3E2.0.CO;2) | **OBTAINED** in Session L4 and held. |
| `paldor_2015_shallow_water_waves.pdf` | Paldor, N. (2015). *Shallow Water Waves on the Rotating Earth.* SpringerBriefs in Earth System Sciences. | Not obtained; monograph, not open access. Not required — see below. |

> **Citation correction (Session L4).** This table previously recorded Kasahara
> (1976) as *Journal of the Atmospheric Sciences* **33**(3), 408–424. **That was
> wrong.** The paper is *Monthly Weather Review* **104**(6), 669–690, confirmed
> against the Crossref work record and against the journal masthead on page 669
> of the retrieved PDF. The erroneous venue entered the project in Session 00b
> and had never been checked, because the paper had never been obtained. It is
> the second wrong-citation record this project has found in its own literature
> index, after the Haurwitz filename corrected in L3-PATCH.

**Kasahara (1976) is now held and read**, and it does more than stand in for the
historical attribution. Its abstract states the structure this project's §6
derives independently: the horizontal parts of the normal modes are Hough
harmonics, and they fall into three families of distinct frequency — eastward and
westward gravity waves, and *westward-propagating rotational waves of the
Rossby–Haurwitz type*. That is the branch structure the project's own eigenvalue
solver reproduces, so the paper is now a genuine external cross-check on the
qualitative branch structure, not merely a citation. It does not supply the
mode-by-mode numbers at Earth's `ε`, which remain internally derived.

Paldor (2015) was not obtained and is not required: with Kasahara held, nothing
depends on it.

## Session L4b — targeted acquisition attempt, and a status this file did not previously have

Session L4b attempted acquisition of four closed-access papers central to the
divergent-stability question. **None was obtained as full text.** All four were
confirmed by Unpaywall to have `is_oa: false`, `oa_status: closed`, and **zero**
open-access locations anywhere — Unpaywall aggregates institutional repositories,
preprint servers and author-hosted copies, so this is close to authoritative. No
author-hosted copy was found for Hayashi & Young either.

| Paper | DOI | Full text | Abstract |
|-------|-----|-----------|----------|
| Ripa (1983), *J. Fluid Mech.* **126**, 463–489 | `10.1017/S0022112083000270` | **not obtained** | **obtained verbatim** from the publisher |
| Hayashi & Young (1987), *J. Fluid Mech.* **184**, 477–504 | `10.1017/S0022112087002982` | **not obtained** | **obtained verbatim** from the publisher |
| Longuet-Higgins (1968) | `10.1098/rsta.1968.0003` | not obtained | not obtained |
| Swarztrauber & Kasahara (1985) | `10.1137/0906033` | not obtained | not obtained |

### A third status: ABSTRACT-VERIFIED

This project has until now used two statuses — READ (PDF held and opened) and
IDENTIFIER-ONLY (DOI verified, nothing else). Session L4b needs a third, because
for Ripa (1983) and Hayashi & Young (1987) the **publisher's own verbatim
abstract** was obtained and it states the papers' central results explicitly
enough to answer the question the session was convened for.

**ABSTRACT-VERIFIED** means: the abstract was read from the publisher's page, and
any claim drawn from it is a claim the abstract itself makes. It does **not**
license page-precise or equation-precise pointers, which remain unavailable for
both papers. Every use of these two references in
`DIVERGENT_STABILITY_DECISION.md` is marked accordingly.

That distinction matters here more than usual: the decision memo's central
finding rests on Ripa's two stability conditions, and those conditions are stated
in his abstract in words rather than in symbols. The reconstruction of them into
the project's own notation is therefore **the project's reading of an abstract**,
not a transcription of a displayed equation, and is flagged as such wherever it
appears.
