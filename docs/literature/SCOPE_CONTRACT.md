# Literature campaign — scope contract

**Session L4, Step 1. Revised after instruction-critic review.**
Critique record: `docs/literature/STEP1_CRITIQUE.json` (15 findings, 12 high).

A literature campaign without a stated boundary sprawls until it is abandoned
rather than finished. This document fixes what the campaign must establish and
what it must not chase, and it is what Step 16 checks the finished bibliography
against.

## The frame

Everything below is tied to the theoretical spine in `theory/derivations.tex`:
material conservation of potential vorticity on a rotating, curved surface,

    Dq/Dt = 0 ,    q = (ζ + f) / h

and its two regimes — wave propagation at one potential-vorticity interface,
shear instability at two.

## The governing constraint, stated before anything else

`PROJECT_BLUEPRINT.md` §2.3 says, in the project's own authoritative words:

> **The contribution is not new theory.** It is a controlled, systematically
> verified numerical isolation of the beta-effect as a single independent
> variable […] with quantified numerical uncertainty and an explicit link to
> observed atmospheric scales.

The first draft of this contract proposed three "contributions" in language that
overclaimed relative to that sentence. **The blueprint governs.** What follows is
rewritten so that every claim is either (i) a verification/methodology claim, (ii)
a quantification claim about a specific configuration, or (iii) an expository
claim — and never a claim to new physics. Blueprint §2.3's own three
distinguishing features (verification separated from validation; Ω as a genuine
free parameter; closure against reanalysis) are the frame.

## MUST establish

### M1. Grounding for the spine

That material PV conservation is the common source of both Rossby-wave dispersion
and barotropic instability: the line from Rossby (1939) and Haurwitz (1940b)
through Kuo (1949) to the PV-thinking synthesis of Hoskins, McIntyre & Robertson
(1985) and the counter-propagating-wave picture of Bretherton (1966) and
Heifetz, Bishop & Alpert (1999).

**This is background to be grounded, not a contribution.** The
one-interface/two-interface identification the manuscript is organised around is
an *expository* framing of established results — see M2(d).

### M2. The claims, split into separately challengeable fragments

The first draft bundled several distinct claims into three items. Step 11 must
challenge each fragment separately, because they have very different novelty
profiles.

| ID | Fragment | Kind of claim |
|----|----------|---------------|
| **a1** | Mode-by-mode quantification of Hough-mode slowing relative to `−2Ω/[n(n+1)]` at Earth's `ε ≈ 8.80`, for the specific configuration this project solves | Quantification |
| **a2** | Use of the closed-form `ε → 0` limit as the solver's validation target | Verification practice |
| **a3** | The sectoral (`n = m`) family departs systematically from the trend, with a causal demonstration that its single degree-ladder coupling partner is the reason | Quantification + mechanism |
| **b1** | Modal growth rates `σ(m)` and eigenmode structure for each zonal base state, converting Rayleigh–Kuo's prohibition into a prediction | Methodology application |
| **b2** | Specific numbers for the Galewsky (2004) jet: resolved band `m = 1–8`, peak on an `m = 6–7` plateau, `σ ≈ 2.07×10⁻⁵ s⁻¹` | Quantification |
| **c1** | Doppler correction of observed ground-relative phase speed before comparison with an intrinsic theoretical prediction | Hygiene |
| **c2** | Two-season (ENSO-neutral / strong El Niño) design as a robustness control on `ū` | Study design |
| **c3** | Whether a westward barotropic branch is resolvable at all in a Hayashi decomposition at 500 hPa, and at which level, with ERA5-vs-NCEP spread as observational uncertainty | Diagnostic finding |
| **d** | The expository identification: wave propagation and shear instability as one mechanism at one vs two PV interfaces | Exposition |

**a3 was absent from the first draft entirely.** It is the most distinctive
single result in the theory (§6.4) and was about to go unchallenged and
un-searched for prior art. It is now a named fragment.

**b1 is deliberately *not* called a "sufficient stability test".** A normal-mode
EVP cannot establish stability: the linearised barotropic shear operator is
non-normal, so a spectrum with no growing eigenvalue permits large finite-time
transient growth. The theory document said "genuine sufficient computational
test"; **that was wrong and has been corrected** in this session, with an
explicit caveat paragraph added to §9. Recorded here because it changes what
H7 can be read as testing: H7 is a prohibition on *modal* growth.

**c1–c3 are capped by blueprint §10.4**, which limits the observational
comparison to "order of magnitude and dominant wavenumber […] explicitly one of
scales, not of trajectories." No fragment may claim more than that.

### M3. A novelty statement consistent with §2.3

Narrow enough to survive a referee who knows this literature, and consistent with
the blueprint's own "not new theory". Step 11 must *try to defeat* every fragment
in M2 before any of them enters the gap statement.

## MUST NOT chase

| # | Out of scope | What *is* in scope, and why the boundary sits there |
|---|--------------|------------------------------------------------------|
| X1 | Baroclinic instability theory (Eady, Charney, Green model detail) | **Two things are in scope.** (i) Enough to state why the project stays barotropic. (ii) **Observed eddy phase-speed and wavenumber–frequency phenomenology at 500 hPa** — because `docs/CONVENTIONS.md` requires a Hayashi decomposition whose stated purpose is separating eastward baroclinic disturbances from any westward barotropic signal, and blueprint §10.4 attributes residual disagreement to baroclinicity. Both need sourcing. *The first draft excluded exactly the literature needed to defend its own observational method.* |
| X2 | NWP and operational forecasting | **Reanalysis production and documentation is in scope** (ERA5, NCEP/NCAR): the project runs on both. Forecast skill, data assimilation methodology and operational verification are not. |
| X3 | Turbulence-closure modelling | **The Rhines scale and the jet-spacing question are in scope.** Theory §7.3 claims the Ω sweep spans "the difference between a terrestrial banding pattern and a Jovian one". Rhines (1975) and Vallis & Maltrud (1993) alone do not support that, and the Rhines scale's status as a jet-spacing predictor is contested in the zonostrophic-turbulence literature a TCFD referee will know. Either the claim is sourced or it is struck. Closure schemes, LES and spectral-transfer theory remain out. |
| X4 | Machine-learning weather models | A brief acknowledgement only, where the optional `torch-harmonics` cross-check touches it. Not a survey. |

## Exit criteria

Rewritten to be checkable. The first draft's criteria 3 and 4 were unfalsifiable.

1. **≥ 60 verified references** in `VERIFIED_POOL.csv`. "Verified" means the DOI
   was resolved *during this session* **and** the returned metadata title matched
   the recorded title. Identifier-resolves-alone is insufficient: this project has
   already shipped one file that was the *wrong Haurwitz paper*, caught only in
   L3-PATCH.
2. **Zero unverifiable references.** Anything whose identifier cannot be confirmed
   is dropped, not downgraded and retained.
3. **Every hypothesis H1–H10 and theory section §1–§12** maps, in
   `CLAIM_MAP.md`, to a named citation *or* to a named internal artefact (a
   `theory/sympy_checks/` script or a run ID). The escape hatch "needs none" is
   removed: the mapping must point at something specific either way.
4. **Every fragment a1…d has a row in `DIALECTIC_CHALLENGE.md`** recording the
   strongest prior-art candidate found, the search actually run to find it, and
   one of three verdicts: *survives / partially narrowed / significantly
   narrowed*. A fragment with no recorded search does not satisfy this criterion.
5. **Every citation is marked READ or IDENTIFIER-ONLY** in the verified pool. The
   distinction matters: theory §6 currently attributes "the classical formulation
   and its eigenstructure" to two papers nobody on this project has read.

## Targeted deliverables carried forward from the critique

- **Kasahara (1976)**, *J. Atmos. Sci.* 33, 408–424 — promoted from "optional
  substitute to chase" in `MISSING.md` to a **hard retrieval target**, because it
  is the open-access source closest to fragment a1's prior art.
- **A forward-citation sweep on Galewsky et al. (2004)** looking specifically for
  a published normal-mode spectrum of that jet. If one exists, fragment b2 is a
  reproduction, not a result, and must be reported as such.
- **Randel & Held (1991)** or equivalent, for observed eddy phase-speed spectra,
  as the X1 boundary case.

## The paper trail rule

Every reference reaching `manuscript/references.bib` traces to a row in
`CANDIDATE_POOL.csv` recording the query string that surfaced it and its
retrieval timestamp. A citation with no retrieval row is dropped, however
plausible. This is the standard L3-PATCH applied after review found one constant
stated from familiarity rather than from a source; the rule exists because that
failure mode is quiet and this project has already seen it once.
