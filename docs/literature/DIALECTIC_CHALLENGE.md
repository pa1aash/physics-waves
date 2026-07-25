# Dialectic challenge to the novelty claims

**Session L4, Step 11.** Permanent record, kept whether or not the gap statement
later changes.

This step is adversarial by design. For each claim fragment in
`SCOPE_CONTRACT.md` §M2 the task was to build the strongest available case that
the fragment is **not** novel, search specifically for the prior art that would
establish it, and report honestly whether the steelman succeeds. A novelty claim
that survives only because nobody looked for the counter-argument is not
something to put in front of a referee.

The governing constraint throughout is `PROJECT_BLUEPRINT.md` §2.3, in the
project's own words: **"The contribution is not new theory."** Several verdicts
below simply confirm that the blueprint was right and the first draft of the
scope contract had drifted.

## Verdict summary

| Fragment | Verdict | One-line reason |
|----------|---------|-----------------|
| **a1** Hough slowing quantification | **SIGNIFICANTLY NARROWED** | The `ε`-dependence of Hough eigenfrequencies *is* the classical Hough literature (Longuet-Higgins 1968; Kasahara 1976) |
| **a2** `ε → 0` as validation target | **SURVIVES (as practice, not as a result)** | Sound verification hygiene; no prior art needed and none claimed |
| **a3** Sectoral-mode departure + mechanism | **PARTIALLY NARROWED** | The phenomenon is almost certainly implicit in the classical eigenstructure; the causal basis-truncation demonstration was not found in the retrieved corpus, but the classical sources are unread |
| **b1** Stability EVP method | **SIGNIFICANTLY NARROWED** | Skiba & Pérez-García (2004) solve a spherical normal-mode instability problem with growth rates; Kuo (1949) is the flat-plane original |
| **b2** Galewsky-jet spectrum numbers | **SURVIVES, HEAVILY CAVEATED** | No published spectrum found in 185 forward citations plus 5 targeted searches — but the project's operator is nondivergent while the jet is shallow-water |
| **c1** Doppler correction | **FULLY NARROWED — not a contribution** | Standard practice in space–time spectral analysis of atmospheric waves |
| **c2** Two-season ENSO design | **SURVIVES (as study design, not as a result)** | A robustness control the project chose; no novelty claimed |
| **c3** Is a westward branch resolvable at 500 hPa? | **SURVIVES** | A genuine diagnostic question with a reportable answer either way; arguably the most defensible empirical fragment |
| **d** One-interface / two-interface identification | **NOT NOVEL — exposition** | Bretherton (1966) originated it; Heifetz et al. (1999) explicitly present it as pedagogy |

---

## a1 — quantifying the Hough-mode departure from Rossby–Haurwitz

**Steelman.** Laplace's tidal equations are nineteenth-century. Longuet-Higgins
(1968), *Phil. Trans. R. Soc. A* 262, 511–607 — 561 citations, and the single
longest paper in this pool — is titled "The eigenfunctions of Laplace's tidal
equations over a sphere" and tabulates the eigenstructure as a function of Lamb's
parameter. Quantifying how the divergent eigenfrequencies depart from the
nondivergent `−2Ω/[n(n+1)]` as `ε` grows is *what that paper is about*. Kasahara
(1976), obtained this session, states the three-family branch structure —
eastward gravity, westward gravity, and "westward propagating rotational waves of
the Rossby/Haurwitz type" — in its abstract.

**Search run.** Query row Q3 (6 strings), targeted row T1, gap row G2 (4
strings). Both classical references were located and verified; neither could be
obtained as a PDF (recorded in `MISSING.md` since Session 00b).

**Does the steelman succeed? YES.** The physics of a1 is classical and was
classical before this project began.

**What is left.** Only this: the mode-by-mode numbers *for the specific
configuration this project integrates*, computed with the project's own solver
and used as its validation target. That is a verification artefact, not a
physical discovery.

**Aggravating factor that must be stated.** The project cites Longuet-Higgins and
Swarztrauber & Kasahara for "the classical formulation and its eigenstructure"
(theory §6.1) **without having read either.** Claiming to quantify a departure
that an unread paper tabulated is the weakest position in this entire campaign.
Kasahara (1976), now held and read, partially repairs this — it independently
confirms the branch structure — but does not supply the numbers.

## a2 — the `ε → 0` limit as an internal validation target

**Steelman.** Checking a numerical eigenvalue solver against an analytically known
limit is ordinary practice, not a contribution. And the Step 1 instruction-critic
noted a real weakness: setting `δ = η̃ = 0` leaves a *diagonal* system that
exercises only one matrix entry, so the limit alone cannot detect an error in the
coupling matrix `B = M − DΛ⁻¹`, which is the operator that produces the departure
being measured.

**Does the steelman succeed? PARTLY — and the weakness is answerable.** The
coupling matrix is independently constrained: `check_hough_epsilon_limit.py` arm 1
verifies `M` and `D` against closed-form recurrences to `6×10⁻¹³` and checks the
integration-by-parts adjoint identity `Dᵀ = −D + 2M`. So `B` is verified by a
different route than the limit. What remains true is that the *fitted convergence
rate* is measured over `ε ∈ [10⁻⁶, 10⁻²]` while the headline numbers are quoted at
`ε ≈ 8.80` — three decades outside the fitted window. That must be said plainly.

**Verdict:** survives as sound verification practice. **No novelty is claimed for
it**, and the drafts must not imply any.

## a3 — the sectoral (`n = m`) family departs from the trend

**Steelman.** Longuet-Higgins classified the Hough eigenstructure exhaustively,
including the sectoral cases. Anyone who has computed a Hough spectrum has seen
the `n = m` modes behave differently. Presenting this as a finding risks
rediscovering something the classical literature contains.

**Search run.** Gap row G2, specifically for mode-family structure and equivalent-
depth dependence. **No paper in the 758-reference corpus states the sectoral
departure or the degree-ladder coupling explanation.** But the search cannot
settle it: the paper most likely to contain it is the one that could not be
obtained.

**Verdict: PARTIALLY NARROWED.** The observation is presented as an observation
with a mechanism — the sectoral mode sits at the bottom of the degree ladder and
so has one Coriolis coupling partner instead of two, demonstrated causally by
deleting the lower partner from the basis and watching the slowing collapse to
sectoral values. **It is not claimed as new.** The honest framing: "the sectoral
family behaves distinctly, for the following structural reason; we have not
located a prior statement of this mechanism, but the classical eigenstructure
literature was not available to us in full."

## b1 — the stability eigenvalue problem as a method

**Steelman.** Solving a linear stability eigenvalue problem for a zonal jet is a
1940s calculation. Kuo (1949) — held and read — poses exactly this problem, his
eq. (2), and solves it. On the *sphere*, Skiba has a sustained programme:

- Skiba & Pérez-García (2004), "On the structure and growth rate of unstable
  modes to the Rossby–Haurwitz wave", `10.1002/num.20042`
- Skiba (2008), "Nonlinear and linear instability of the Rossby–Haurwitz wave",
  `10.1007/s10958-008-0091-3`
- Skiba (2024), "Stability of a class of solutions of the barotropic vorticity
  equation on a sphere", `10.4310/dpde.2024.v21.n3.a1`

plus Constantin & Germain (2022), `10.1007/s00205-022-01791-3`, on rigorous
stability of stratospheric planetary flows, and Cao & Wang (2023) on degree-2
Rossby–Haurwitz stability.

**Search run.** Query row Q5 (5 strings), gap row G1 (5 strings) after the
corpus-adequacy audit named Skiba.

**Does the steelman succeed? YES, decisively.** There is nothing methodologically
new in solving this eigenvalue problem, on the plane or on the sphere.

**What is left.** Applying a standard method to a specific configuration, with the
resolution-doubling filter and the plateau reporting stated explicitly. That is
careful work, not a methodological contribution, and the paper should say so —
blueprint §2.3 already does.

## b2 — the specific Galewsky-jet numbers

**Steelman.** Galewsky et al. (2004) is heavily used; someone must have computed
its linear spectrum.

**Search run — the most thorough in this campaign.** A forward-citation sweep
retrieved **all 208 works citing Galewsky (2004)**, of which 185 entered the pool.
Their collective character: a discretisation-development corpus (finite volume,
discontinuous Galerkin, icosahedral and cubed-sphere grids, RBF methods,
semi-Lagrangian schemes) using the jet as an acceptance test. Only 4 of 185 titles
mention stability, eigenvalues or growth rates, and none is a linear spectrum of
the jet. Five further targeted searches for a Galewsky-jet stability analysis
returned nothing.

**Does the steelman succeed? NO — but the fragment is compromised for a different
reason.** The negative search result is real and worth reporting. However:

> **The project's stability operator is nondivergent; the jet it is applied to is
> divergent shallow water.** Verified by inspection: `grep divergen
> theory/derivations.tex` returns hits in §3–§6 and **none in §8 or §9**. The
> deformation radius is `L_d ≈ 3×10⁶ m`, comparable to the jet's own width, and the
> project's own §6 sizes the free-surface effect on wave frequencies at 6–40%.
> Quoting `σ = 2.0748×10⁻⁵ s⁻¹` and distinguishing `m = 6` from `m = 7` at 0.07%
> from a nondivergent calculation is therefore not defensible as a statement about
> the shallow-water jet.

Ripa (1983), "General stability conditions for zonal flows in a one-layer model on
the beta-plane **or the sphere**", `10.1017/S0022112083000270`, is where the
divergent stability conditions live. It was absent from the entire corpus until the
Step 7 width critique surfaced it. It is verified but **not obtained**.

**Verdict:** survives as a negative-search result — no prior published spectrum
found — but must be reported as the spectrum of the *nondivergent* problem, with
the divergent mismatch stated as a limitation, not discovered by a referee.

## c1 — Doppler-correcting the observed phase speed

**Steelman.** `c_ground = ū + c_intrinsic` is textbook kinematics. Separating
eastward and westward branches by space–time (Hayashi) spectral analysis has been
routine since the 1970s.

**Does the steelman succeed? YES, completely.** This is hygiene. Doing it is
necessary; claiming credit for it is not available.

**Consequence.** The drafts must present the Doppler correction as *the correct
procedure*, whose omission would be an error — not as a contribution. The project's
own `docs/CONVENTIONS.md` already frames it that way; the scope contract's first
draft did not.

## c2 — the two-season ENSO-contrast design

**Steelman.** Choosing two contrasting seasons is a study-design decision. Anyone
comparing a model to reanalysis could make it.

**Verdict: survives as a design choice with no novelty claimed.** Its value is
internal: if the corrected intrinsic phase speed agrees in both an ENSO-neutral
and a strongly perturbed winter *despite `ū` differing between them*, the agreement
is attributable to the mechanism rather than to one winter's jet. That is a good
control. It is not a result until the numbers exist.

## c3 — whether a westward barotropic branch is resolvable at 500 hPa

**Steelman.** Observed wavenumber–frequency spectra of the extratropical
troposphere have been computed many times.

**Does the steelman succeed? NO.** The fragment is not "compute a spectrum"; it is
the narrower, decision-relevant question of whether a westward-propagating
barotropic branch is *separable at all* at the levels this project examines, and
if so at which level, with the ERA5-versus-NCEP spread reported as observational
uncertainty. `docs/CONVENTIONS.md` already anticipates that the answer may be no,
and requires that outcome be stated as a finding rather than worked around.

**Verdict: survives.** This is arguably the most defensible empirical fragment in
the set, precisely because it is small and falsifiable.

**Gap:** Randel & Held (1991) or an equivalent anchor for observed eddy
phase-speed spectra remains **absent** from the corpus after two search rounds.
Recorded as an outstanding item.

## d — the one-interface / two-interface identification

**Steelman.** Bretherton (1966) is the origin: wave development in flows with two
distinct PV gradients is the interaction of two Rossby waves propagating on them.
Hoskins, McIntyre & Robertson (1985) named the counter-propagating framing.
Heifetz, Bishop & Alpert (1999) p. 2839 say explicitly that they offer the CRW
description "because it provides a useful pedagogical framework".

**Does the steelman succeed? YES, entirely.** Nothing about the identification is
new.

**Verdict: exposition.** The manuscript may organise itself around the sentence —
that is a legitimate expository choice, and it is what makes the paper coherent —
but it must attribute the mechanism to Bretherton and the framing to Hoskins et
al. and Heifetz et al., and claim only the exposition.

---

## Open questions this campaign could not close

1. **Hayashi & Young (1987)**, `10.1017/S0022112087002982`. The width critic
   reported that this paper exhibits shallow-water shear instabilities with no
   PV-gradient sign change. **Not verified** — the paper was not obtained. If true
   it bounds H7, which the blueprint calls its strongest test *because* it is a
   prohibition: the prohibition would hold for the nondivergent system and not
   necessarily for the divergent one the project integrates. **This should be
   settled before H7 is reported as a passed or failed test.**
2. **Longuet-Higgins (1968) and Swarztrauber & Kasahara (1985)** remain unobtained,
   and they are the papers most likely to contain fragment a3.
3. **Ripa (1983)** unobtained; it is the correct reference for the divergent
   stability conditions.
4. **Randel & Held (1991)** or equivalent still absent.
