# Corpus adequacy audit

**Session L4/L5, Step 5.** Cross-checks `docs/literature/VERIFIED_POOL.csv`
(669 rows) against every theory section, hypothesis, and M2 fragment. Table 1
is built directly from the `\citet{}`/`\citep{}` macros actually present in
`theory/derivations.tex` (verified by `grep`, not by section topic), not from
the "area" labels in the CSV, which are search-query buckets and drift from
their nominal topic in several cases (noted in §6 below). Table 2 cross-checks
against `PROJECT_BLUEPRINT.md` §13.1 and the hypothesis-to-equation summary
table in `theory/derivations.tex` §12. Table 3 cross-checks against the M2
fragment table in `docs/literature/SCOPE_CONTRACT.md`.

---

## 1. Theory sections §1–§12

`derivations.tex` contains exactly nine `\citet`/`\citep` calls, in five of
its twelve sections. The other seven sections cite nothing external by design
— they are self-contained derivations, each backed by a script in
`theory/sympy_checks/`. That split is reported explicitly per row; "GAP" is
reserved for cases where neither a citation nor a working internal artefact
exists.

| § | Section | Cites (in-text) | Pool coverage | DOI(s) | Internal artefact |
|---|---------|------------------|----------------|--------|--------------------|
| §1 | Physical setting and governing principle | none | n/a — no claim needs external grounding here | — | `theory/sympy_checks/check_pv_conservation.py` |
| §2 | The rotating sphere as a curved manifold | none | n/a | — | `check_christoffel_symbols.py`, `check_spherical_laplacian_eigenvalue.py` |
| §3 | Shallow-water equations and PV on the sphere | none | n/a | — | `check_pv_conservation.py` |
| §4 | Nondimensionalisation | none | n/a | — | `check_hough_epsilon_limit.py` (shared with §6; verifies the ε-scaling this section defines) |
| §5 | Linearisation I: waves on a state of rest | `\citep{rossby1939,haurwitz1940b}` | **NOT in VERIFIED_POOL.csv** — both are pre-DOI (1939/1940 *J. Marine Research*) and structurally invisible to a DOI-keyed pool | — (see confirmation §5 below) | `check_rh_dispersion.py` |
| §6 | Linearisation II: Hough modes | `\citet{longuethiggins1968}`, `\citet{swarztrauber1985}` | Present, core tier, IDENTIFIER-ONLY (never claimed as read; text says derivation "does not depend on either") | `10.1098/rsta.1968.0003`; `10.1137/0906033` | `check_hough_epsilon_limit.py` |
| §7 | The Rhines scale | `\citet{rhines1975}`, `\citet{vallis1993}` | Present, core tier, **READ** | `10.1017/s0022112075001504`; `10.1175/1520-0485(1993)023<1346:gomfaj>2.0.co;2` | — (empirical/scaling section, no dedicated script) |
| §8 | Rayleigh–Kuo criterion | `\citep{kuo1949}` | Present, core tier, **READ** | `10.1175/1520-0469(1949)006<0105:diotdn>2.0.co;2` | `check_rayleigh_kuo.py` |
| §9 | Linear stability EVP | `\citet{kuo1949}`, `\citet{bretherton1966}` | Both present, core tier, **READ** | as above; `10.1002/qj.49709239302` | `check_rayleigh_kuo.py` |
| §10 | Instability as counter-propagating Rossby waves | `\citet{bretherton1966}`, `\citet{hoskins1985}`, `\citet{heifetz1999}` | All present, core tier, **READ** | `10.1002/qj.49709239302`; `10.1002/qj.49711147002`; `10.1002/qj.49712556004` | `check_crw_two_interface.py` |
| §11 | Galewsky jet and balanced IC | `\citet{galewsky2004}` | Present, core tier, **READ** | `10.3402/tellusa.v56i5.14436` | `src/solver/initial_conditions/galewsky.py`, `tests/phase0_gate/galewsky_comparison.md` |
| §12 | Summary: hypotheses to equations | none (consolidating table) | n/a — every equation number in this table's "Equation" column resolves to a citation or artefact already listed in the row above for the section that derives it | — | The table itself, cross-referenced against `PROJECT_BLUEPRINT.md` §13.1 |

**Reading the "GAP" question directly: zero of the twelve sections are an
uncovered GAP.** Seven have no external claim to cover (internal derivation +
script); five have external claims, and four of those five resolve cleanly
against the pool. §5 is the one exception, and it is a **structural** gap, not
a missed search: `VERIFIED_POOL.csv`'s verification protocol (Exit criterion
1 in `SCOPE_CONTRACT.md`) requires a DOI that resolves against Crossref, and
Rossby (1939) and Haurwitz (1940b) predate DOIs entirely. They are tracked
instead in `docs/literature/MISSING.md` (Rossby 1939 is held as a local PDF;
Haurwitz 1940b is not — see confirmation §5). This is worth recording
explicitly in `CLAIM_MAP.md` rather than leaving §5 looking like an
unexplained hole in the DOI-keyed pool.

---

## 2. Hypotheses H1–H10

None of H1–H10 are "purely internal" in the sense of needing zero literature
— H5, H6, H7 and H10 each rest partly on an external result — but every one
maps to a specific internal artefact, and the mapping is named rather than
asserted, per the scope contract's ban on a bare "needs none."

| H | Prediction | External citation | DOI | Internal artefact / run ID |
|---|------------|--------------------|-----|------------------------------|
| H1 | All modes propagate westward | `rossby1939`, `haurwitz1940b` (not in pool, §5 above) | — | `check_rh_dispersion.py`; falsified by any eastward mode in `configs/phase_speed/P-01`…`P-18` |
| H2 | `c_ang ∝ 1/[n(n+1)]` at fixed Ω | same | — | `check_rh_dispersion.py`; `configs/phase_speed/P-01`…`P-07` |
| H3 | `c_ang ∝ Ω` at fixed n | same | — | `check_rh_dispersion.py`; `configs/phase_speed/P-08`…`P-12` |
| H4 | Measured speeds agree with `−2Ω/[n(n+1)]` | same | — | `fit_phase_speed.py` output vs. `check_rh_dispersion.py` target |
| H5 | Departure from nondivergent prediction grows with Bu | `longuethiggins1968`, `swarztrauber1985` (background only — text states the derivation does not depend on them) | `10.1098/rsta.1968.0003`; `10.1137/0906033` | `check_hough_epsilon_limit.py` |
| H6 | Benchmark error decays spectrally | `williamson1992` (Table 1, §11); `jakobchien1995` | `10.1016/0021-9991(92)90060-c`; `10.1006/jcph.1995.1125` | `configs/verification/V-01`…`V-08`; `compute_error_norms.py` |
| H7 | Jets failing Rayleigh–Kuo remain stable | `kuo1949` | `10.1175/1520-0469(1949)006<0105:diotdn>2.0.co;2` | `check_rayleigh_kuo.py`; `configs/instability/I-01`…`I-12` |
| H8 | Growth rate rises with supercriticality | none needed — internal EVP result | — | `check_rayleigh_kuo.py`; `configs/instability/I-01`…`I-05`; `fit_growth_rate.py` |
| H9 | Increasing Ω stabilises a fixed jet shape | none needed — internal EVP result | — | `configs/instability/I-06`…`I-09` |
| H10 | Model wavenumber ~ observed wavenumber | `hersbach2020` (ERA5), `kalnay1996` (NCEP/NCAR); Hayashi decomposition methodology | `10.1002/qj.3803`; `10.1175/1520-0477(1996)077<0437:tnyrp>2.0.co;2` | `check_crw_two_interface.py` (for the `m*` scaling, eq. `\eqref{eq:mstar}`); `configs/instability/I-10`; `process_reanalysis.py` |

All ten rows resolve to *something specific*, per the exit-criteria escape-hatch
ban. H1–H4 inherit §5's structural pre-DOI gap; that is the only unresolved
item in this table.

---

## 3. M2 fragments — possible prior art

Per instruction, this section is deliberately generous: candidates below are
named as the *strongest thing found in the pool*, not filtered for how
damaging they'd be to novelty. Step 11's dialectic challenge should treat
every non-empty cell as a real prior-art candidate to defeat or narrow
against, not a false positive to wave away.

| Fragment | Claim | Strongest prior-art candidate(s) in pool | Verdict for Step 11 |
|----------|-------|--------------------------------------------|----------------------|
| **a1** | Mode-by-mode Hough-mode slowing at Earth's `ε ≈ 8.80` | Žagar, Kasahara, Terasaki & Tribbia (2015), *Normal-mode function representation of global 3-D data sets* (`10.5194/gmd-8-1169-2015`, supporting tier); Wang, Boyd & Akmaev (2016), *On computation of Hough functions* (`10.5194/gmd-9-1477-2016`, core tier); Tanaka (1985), *Global Energetics Analysis by Expansion into Three-Dimensional Normal Mode Functions* (`10.2151/jmsj1965.63.2_180`); Shigehisa (1983), *Normal Modes of the Shallow Water Equations for Zonal Wavenumber Zero* (`10.2151/jmsj1965.61.4_479`) | These are operational/diagnostic uses of Hough decomposition at real ε, not a systematic mode-by-mode slowing quantification vs. `−2Ω/[n(n+1)]` — but they are close enough on method that a referee could ask why this project's numbers differ from theirs. Search harder before calling a1 clean (see §6, gap G1). |
| **a2** | ε→0 limit as validation target | None needed as *prior art* — this is a verification-practice choice, grounded by the same eigenstructure sources already in Table 1 (§6) | Survives as stated; not a novelty claim to begin with. |
| **a3** | Sectoral (`n=m`) family departs systematically, causal mechanism = single coupling neighbour | **No candidate found.** A direct title search for "sectoral" against the full 669-row pool returns zero rows. | This is the fragment flagged in `SCOPE_CONTRACT.md` as "the most distinctive single result" and it currently has **zero recorded search** for prior art in `CANDIDATE_POOL.csv` beyond the general Q3 Hough queries. Treat as unsearched, not as clean — see gap G2. |
| **b1** | Modal `σ(m)` from an EVP, converting Rayleigh–Kuo into a prediction | **Skiba (2000)**, *On the normal mode instability of harmonic waves on a sphere* (`10.1080/03091920008203713`, core); Skiba (2003), *Instability of the Rossby–Haurwitz wave in the invariant sets of perturbations* (`10.1016/j.jmaa.2003.10.039`, core); Skiba & Pérez-García (2004), *On the structure and growth rate of unstable modes to the Rossby–Haurwitz wave* (`10.1002/num.20042`, core); Skiba (2018) (`10.1007/s00021-017-0359-9`, core); Hoskins (1973), *Stability of the Rossby-Haurwitz wave* (`10.1002/qj.49709942213` — also resolves under a second legacy DOI `10.1256/smsqj.42212`, same title/year/author; a pool duplicate worth de-duplicating before citation, see §6) | This is the single strongest prior-art hit in the whole pool for this project. Skiba's series is exactly "spherical normal-mode barotropic-instability EVP with growth rates" — for Rossby–Haurwitz base states rather than a Galewsky-type jet, but the methodological overlap with b1 is direct. Step 11 must engage this, not the weaker candidates. |
| **b2** | Specific numbers for the Galewsky jet (`m=1–8`, peak `m=6–7`, `σ≈2.07×10⁻⁵ s⁻¹`) | Shin, Sommer, Reich & Névir (2010), *Evaluation of three spatial discretization schemes with the Galewsky et al. test* (`10.1002/asl.279`, core) — but this evaluates nonlinear discretization error, not a linear normal-mode spectrum | **No published linear normal-mode spectrum of the Galewsky (2004) jet was found in the pool.** This matches `SCOPE_CONTRACT.md`'s named targeted deliverable ("forward-citation sweep... If one exists, fragment b2 is a reproduction"), and the sweep (177 rows in `forward-cite: Galewsky 2004`) did not surface one. Report as searched-and-not-found, not as untested — see gap G3 for one more pass before that verdict is final. |
| **c1** | Doppler correction before intrinsic-speed comparison | None found; Hayashi (1971, 1982) papers (`10.2151/jmsj1965.49.2_125`; `10.2151/jmsj1965.60.1_156`, both supporting) supply the progressive/retrogressive decomposition machinery this hygiene step depends on, but no paper in the pool addresses ground-relative-to-intrinsic conversion directly | Low risk (this is described in the scope contract as "hygiene," not a claim), but the citation for the *practice itself* is currently just the Hayashi papers by inference. Acceptable but worth one direct search (gap G4). |
| **c2** | Two-season (ENSO-neutral / El Niño) robustness design | None found. `Galanti & Tziperman (2000)` on ENSO phase locking (`10.1175/1520-0469(2000)057<2936:espltt>2.0.co;2`) and `Yeh et al. (2018)` on ENSO teleconnections (`10.1002/2017rg000568`, tangential) are the closest ENSO-related hits, and neither is about study-design robustness for a jet-extraction comparison | Genuine gap. No search in `QUERY_MATRIX.md` was ever aimed at this fragment specifically — see gap G5. |
| **c3** | Resolvability of a westward barotropic branch at 500 hPa, ERA5-vs-NCEP spread | Hayashi (1971, 1982), space–time spectral method; **Sun & Li (2012)**, *Space–Time Spectral Analysis of the Southern Hemisphere Daily 500-hPa Geopotential Height* (`10.1175/mwr-d-12-00019.1`, supporting) | Reasonable coverage — Sun & Li is a direct methodological precedent at the right level and hemisphere-adjacent. Not flagged as a gap. |
| **d** | Wave/instability as one PV interface vs. two (exposition) | `bretherton1966`, `hoskins1985`, `heifetz1999` — the same three sources already grounding §10 in Table 1 | This is explicitly exposition of established results (scope contract, M2 row d), not a novelty claim, so the same three sources that ground the mechanics also ground the framing. No separate prior-art search is warranted. |

---

## 4. Confirmations

**(i) Longuet-Higgins (1968) and Swarztrauber & Kasahara (1985).**
Both are present in `VERIFIED_POOL.csv`:

- `10.1098/rsta.1968.0003` — *The eigenfunctions of Laplace's tidal equations
  over a sphere*, relevance_tier `core`, `verified = yes`, `read_status =
  IDENTIFIER-ONLY`, `local_pdf` empty (no PDF held), `selected_for_bib = yes`.
- `10.1137/0906033` — *The vector harmonic analysis of Laplace's tidal
  equations*, relevance_tier `core`, `verified = yes`, `read_status =
  IDENTIFIER-ONLY`, `local_pdf` empty, `selected_for_bib = yes`.

This matches the project's own account in `docs/literature/MISSING.md`: both
were sought and could not be obtained as full text, and both are cited for
historical attribution only, consistent with `theory/derivations.tex` line
627–630, which states the divergent-correction derivation "does not depend on
either." **By design**, not by omission.

**(ii) Kasahara (1976).** Present, `doi =
10.1175/1520-0493(1976)104<0669:nmouwi>2.0.co;2`, relevance_tier `core`,
`read_status = READ`, `local_pdf = kasahara_1976_normal_modes_ultralong_waves.pdf`,
`selected_for_bib = yes`, `selection_reason = "ANCHOR: PDF held or cited
directly by the theory"`.

**One discrepancy worth flagging.** That `selection_reason` string is not
accurate as written: `grep -n "\citet{\|\citep{"` against the full text of
`theory/derivations.tex` finds **no citation of Kasahara anywhere in the
document** — the bibliography's `\bibitem` list at the end of the file does
not even include a `kasahara1976` entry (it lists Bretherton, Galewsky,
Haurwitz, Heifetz, Hoskins, Kuo, Longuet-Higgins, Rhines, Rossby,
Swarztrauber & Kasahara, and Vallis & Maltrud — eleven entries, not the
twelve implied by "cited directly by the theory"). `MISSING.md` correctly
describes Kasahara (1976) as a paper that has been **read** and used as a
qualitative cross-check on branch structure, but that account is currently
narrative only — it is not wired into the LaTeX as a `\citet{kasahara1976}`
call anywhere near §6's Hough-mode discussion. This should be corrected
either by adding the citation where §6 discusses the three-family branch
structure (eastward/westward gravity waves, westward Rossby–Haurwitz-type
waves), or by correcting the pool's `selection_reason` to stop claiming a
citation that does not exist in the document it is supposed to support.

---

## 5. Ranked coverage gaps for Step 8

Six gaps, ranked by how much they could move the Step 11 dialectic verdict or
the final claim map if left unfilled.

1. **G1 — Sharpen a1 prior art (highest priority).** The Q3 Hough query set
   never specifically searched for a *quantitative table of Hough-mode phase
   speeds vs. the nondivergent limit at a specific ε* — it searched for the
   general topic. Search: `"Hough mode phase speed" divergence deformation
   radius table`; `Kasahara Hough function eigenfrequency numerical table`;
   `Longuet-Higgins Hough mode eigenvalue tabulation epsilon`.
2. **G2 — Search for a3's prior art at all.** Zero searches have been run
   against the sectoral (`n=m`) departure specifically; the only hits so far
   are incidental. Search: `sectoral Hough mode rotation coupling`; `zonal
   wavenumber equals degree spherical harmonic tridiagonal coupling rotation`;
   `equatorially trapped Hough mode divergent correction`.
3. **G3 — One more forward-citation pass on Galewsky (2004) for a linear
   stability study, not just discretization/nonlinear studies.** Search:
   `Galewsky jet linear stability eigenvalue`; `Galewsky test case normal mode
   growth rate`; `barotropic instability spherical jet shallow water normal
   mode spectrum`.
4. **G4 — Doppler-shift hygiene citation (c1).** Search: `Doppler shift
   ground-relative intrinsic phase speed Rossby wave`; `zonal-mean advection
   correction eddy phase speed reanalysis`.
5. **G5 — Two-season robustness design (c2).** Search: `ENSO neutral versus El
   Nino composite zonal wind jet profile`; `seasonal robustness barotropic jet
   profile extraction reanalysis`.
6. **G6 — §5's structural pre-DOI gap.** Not a search gap in the usual sense
   (Rossby 1939 and Haurwitz 1940b cannot acquire a DOI retroactively), but
   `CLAIM_MAP.md` should record explicitly, next to H1–H4, that their
   grounding sits outside `VERIFIED_POOL.csv`'s DOI-keyed verification
   protocol and is tracked instead in `MISSING.md` — otherwise a reader of
   `CLAIM_MAP.md` alone will see H1–H4 as uncited.

---

## 6. Data-quality notes (not gaps, but relevant to how the tables above were read)

- **Query-drift contamination.** Several CSV "area" buckets contain
  substantial off-topic material at `core` relevance_tier — e.g. the "Hough
  modes / Laplace tidal equations" area (Q3) includes *Analogue Gravity*,
  *4D flow MRI*, black-hole accretion disk theory, coronary revascularization,
  and carbon-nanotube visualization papers tagged `core`; the "linear
  stability EVP for jets" area (Q5) includes TRP ion-channel biology and
  liquid-crystalline-polymer rheology, also tagged `core`. This is why Table 1
  and Table 3 above were built from `derivations.tex`'s actual `\citet{}`
  calls and from title/author keyword search, not from the `area` column or
  `relevance_tier == core` filters alone — those filters are not reliable
  on their own for this pool.
- **Duplicate DOI entries.** Hoskins (1973), *Stability of the Rossby-Haurwitz
  wave*, appears twice under two different DOI prefixes
  (`10.1002/qj.49709942213` and `10.1256/smsqj.42212`), evidently from a
  legacy Royal Meteorological Society DOI migration. Both resolve to the same
  title/author/year. Worth de-duplicating before either enters
  `manuscript/references.bib`.
- **NCAR technical notes are held but not DOI-verified.** `hack_1992_ncar_tn343.pdf`
  and `jakob_1993_ncar_tn388.pdf` are present on disk (per `docs/literature/README.md`)
  but neither appears in `VERIFIED_POOL.csv` by DOI — NCAR technical notes
  predate or lack a resolvable Crossref DOI in the same way Rossby (1939) and
  Haurwitz (1940b) do. This is the same structural gap as G6, one tier down
  in importance since §11/H6 do not depend on them for anything the held
  `williamson1992` and `jakobchien1995` DOIs don't already cover.
- **Blueprint's own textbook references are absent from the pool.**
  `PROJECT_BLUEPRINT.md` §18 cites Pedlosky (1987), Vallis (2017) and Zeitlin
  (2018) as general GFD references. None of the three appear in
  `VERIFIED_POOL.csv` (a `Pedlosky` hit exists but is a 1981 JAS article, not
  the 1987 textbook). This is expected — the query matrix targets
  DOI-resolvable journal articles, and monographs are a poor fit for that
  protocol — but it means these three should not be assumed "in the verified
  pool" if cited in the manuscript; they need their own verification pass if
  actually quoted rather than used for general background.
