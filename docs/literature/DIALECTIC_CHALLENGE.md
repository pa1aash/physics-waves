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
| **e1** Extending the stability analysis to the divergent shallow-water system | **FULLY NARROWED — not a contribution** | Paldor, Shamir & Garfinkel (2020) publish exactly this comparison for a spherical jet; White & Staniforth (2009) already apply Ripa's criteria on the sphere to guide model testing |

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

**Session L4b sharpens this.** The verdict was recorded on the strength of titles;
it now rests on governing equations. All five papers in this programme — Skiba &
Pérez-García (2004), Skiba (2008), Skiba (2024), Constantin & Germain (2022) and
Cao, Wang & Zuo (2023) — work in the **nondivergent** barotropic vorticity
equation or the incompressible Euler equation on the sphere, established from
their abstracts (see `SKIBA_PROGRAMME_NOTES.md`). Since this project's EVP is also
nondivergent, the prior art is exactly on target.

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

**Session L4b weakens this further, and the reported precision must drop.** Paldor,
Shamir & Garfinkel (2020), *GAFD* 115(1), 15–34, compare barotropic-instability
growth rates for a zonal jet on the sphere across the nondivergent, quasi-geostrophic
and full shallow-water formulations. Per the authors' own EGU2020 abstract of that
work, shallow-water growth rates "can be smaller by more than 50%" than the
nondivergent prediction at mean depths of 5–10 km, converging only above 30 km.
**This project uses H = 10 km.** Quoting `σ` to five significant figures and
distinguishing `m = 6` from `m = 7` at 0.07% inside a >50% formulation bias is not
defensible. See `DIVERGENT_STABILITY_DECISION.md`.

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

1. **Hayashi & Young (1987)**, `10.1017/S0022112087002982` — **RESOLVED in
   Session L4b, and the report was correct.** Their abstract, obtained verbatim,
   states that "when the basic state has no potential vorticity gradients an
   unstable wave has zero wave energy": instability with no PV gradient at all is
   real in the divergent system, so Rayleigh–Kuo's necessary condition does not
   transfer. **But the setting is an equatorial β-plane**, and the mechanism is
   energetic — the free surface makes wave energy non-positive-definite, which
   requires the flow to be comparable to the gravity-wave speed. This project's
   midlatitude jet has a Froude-like ratio of 0.26 and sits 7.8× inside Ripa's
   gravity-wave condition. **The counterexample is real and does not reach this
   configuration.** H7 stands as a prohibition on modal growth for the
   nondivergent problem it is posed in. See `RIPA_HAYASHI_YOUNG_NOTES.md`.
2. **Longuet-Higgins (1968) and Swarztrauber & Kasahara (1985)** remain unobtained,
   and they are the papers most likely to contain fragment a3.
3. **Ripa (1983)** — **RESOLVED in Session L4b.** Still unobtained as full text,
   but the publisher abstract was obtained verbatim and states both conditions.
   They **reduce cleanly** to the classical Rayleigh–Kuo condition in the
   nondivergent limit: divergence does not modify the classical condition, it adds
   a second, independent gravity-wave criticality condition. White & Staniforth
   (2009), `10.1002/qj.504`, extend the criteria to the sphere and close the
   remaining question about the spherical form. See `RIPA_HAYASHI_YOUNG_NOTES.md`.
4. **Randel & Held (1991)** or equivalent still absent.

---

## e1 — extending the stability analysis to the divergent system

**Added Session L4b.** Full record below; the decision it feeds is
`docs/literature/DIVERGENT_STABILITY_DECISION.md`.

# Dialectic challenge — fragment e1 (divergent stability extension)

**Session L5, Step 11-equivalent.** Same standard as `DIALECTIC_CHALLENGE.md`
(a1–d). Adversarial by design.

**Fragment.** Extend the stability analysis from the nondivergent barotropic
vorticity equation to the full divergent shallow-water system; test whether
Ripa's condition holds / is modified / is violated for the Galewsky jet across
the project's rotation-rate sweep; cross-validate against the nonlinear runs.

---

## VERDICT: FULLY NARROWED — not a contribution

Stronger than any verdict reached in Session L4. Fragment e1 fails on three
independent grounds: the prior art is direct and recent, the answer is known in
advance and is vacuous, and the fragment's stated premise about the project's own
campaign is factually false.

---

## Attack 1 — prior art (decisive)

All found by forward-citation sweep of Ripa (1983) via OpenAlex
(`W2166185040`, 118 citing works retrieved). None was in `CANDIDATE_POOL.csv`.

**a. Staniforth & White (2008)**, *Stability of some exact solutions of the
shallow-water equations for testing numerical models in spherical geometry*,
QJRMS 134, `10.1002/qj.240`. Abstract, verbatim: sufficient stability conditions
are derived for axisymmetric spherical shallow-water solutions "as an aid to the
development and testing of global numerical models … so that any significant time
evolution occurring in a numerical model initialised with one of these exact
solutions is of numerical origin, and does not reflect an inherent physical
instability," and — the killer clause — "**planetary rotation stabilises the
solutions** (as would be so if the flow were governed by barotropic vorticity
dynamics), and **low Rossby and Froude numbers favour their stability**." That is
fragment e1's deliverable — Ripa-class conditions, on the sphere, swept over
rotation, in the numerical-model-verification context — published in 2008.

**b. White & Staniforth (2009)**, *Stability criteria for shallow-water flow above
zonally symmetric orography on the sphere*, QJRMS 135, `10.1002/qj.504`.
Verbatim: "the sufficient stability criteria given by P. Ripa in 1983 for zonal
shallow-water flow on the sphere may be extended to include zonally symmetric
orography … The context of the study is the use of stable flows to test the
formulation of discretized numerical models; **illustrative examples of how to
apply the criteria in this context are presented**." This is the *applied,
worked, numerical* version of Ripa on the sphere. It also closes the open
question at `RIPA_HAYASHI_YOUNG_NOTES.md` §3 (spherical vs β-plane form) — which
means it is a citation the project needs regardless.

**c. Poulin & Flierl (2003)**, *The Nonlinear Evolution of Barotropically Unstable
Jets*, JPO 33, `10.1175/1520-0485(2003)033<2173:TNEOBU>2.0.CO;2`. Verbatim: "the
linear stability problem is solved for a wide range of Rossby and Froude numbers
to elucidate the functional dependency of growth rate on these two nondimensional
parameters. Then the nonlinear evolution of the instability is investigated
through the use of numerical experiments." **Divergent shallow-water jet EVP,
swept over a rotation-equivalent parameter, cross-validated against nonlinear
runs.** That is the fragment's *entire* methodological content, minus the sphere.

**d. Shepherd (2003)**, *Ripa's Theorem and its Relatives*, ch. 1 of *Nonlinear
Processes in Geophysical Fluid Dynamics*, `10.1007/978-94-010-0074-1_1`. A review
chapter exists. Reviewed material is not a contribution.

**e. Clark & Herron (2012)**, GAFD, `10.1080/03091929.2012.671817` — *Improved
bounds on linear instability of barotropic zonal flow within the shallow water
equations*: a semi-ellipse bound "based on the wave-number, Froude number, and
depth". The "is it modified?" question already has a published sharpened answer.

**f. Dowling (1993, 2014, 2020)** — Arnol'd/Kelvin–Arnol'd second-branch
criteria evaluated numerically against *observed* planetary jets; *Jupiter-style
Jet Stability* (PSJ 2020, `10.3847/psj/ab789d`) states outright that branch KA-I
"includes as special cases the textbook shear stability theorems of Rayleigh,
Kuo, Charney–Stern, and Fjørtoft" and that the second branch is a Mach-number-like
criticality condition. The project's §7.8× margin is a KA-II margin computation.

**g. SWMHD, as the L4 width critique suspected.** Mak, Griffiths & Hughes (2016),
JFM 788, `10.1017/jfm.2015.718`: "Various classical instability results, such as
Høiland's growth-rate bound and Howard's semi-circle theorem, **are extended to
this shallow-water system** for quite general flow and field profiles," then
solved numerically for the Bickley jet across Froude number. Yes — that community
has already done the equivalent extension, and did it more generally.

## Attack 2 — there is nothing to find, and it is worse than a null result

The margin test (`check_ripa_divergent_condition.txt`) shows condition (ii) holds
at 7.83×, identically at every Ω in P-08…P-12, because (ii) contains no rotation
rate. But the fatal point is condition **(i)**, and the project has already
computed it: `check_rayleigh_kuo.txt` arm 4(b) finds `dQ/dφ` **changes sign at
four latitudes** (+32.19°, +39.79°, +49.82°, +58.16°) for the Galewsky jet.

Ripa's conditions are *sufficient for stability, jointly*. Condition (i) fails.
Therefore **Ripa's theorem returns no verdict for this jet at any rotation rate**
— it is not "satisfied", "modified" or "violated"; it is silent. The fragment
asks a question whose answer is "the theorem does not apply here", derivable in
five lines from two files the project already has.

## Attack 3 — the premise is factually wrong about this campaign

`configs/RUN_REGISTRY.md`: P-08…P-12 are **`single_harmonic` phase-speed runs**
(degree n = 4 Rossby–Haurwitz), containing no jet at all. There is **no
Galewsky-jet rotation sweep**: I-00 is a single anchor run at Ω₀, and the
rotation sweep I-06…I-09 uses the *idealised* jet. And all **42 of 42 runs are
"not started"** — there are no "nonlinear initial-value runs already in the
campaign" to cross-validate against. The existing check also inherits this: it
evaluates a jet-derived margin "across P-08 to P-12", runs that contain no jet.

## Attack 4 — scope creep

Blueprint §2.3: "The contribution is not new theory." `GAP_STATEMENT.md` records
L1 as a *limitation to state*, and the width critique already prescribed the fix:
"state that §8–§9 are the nondivergent limit, cite Ripa … bound the resulting
bias on σ using §6.4's own numbers. **That is a two-paragraph fix.**" e1 converts
a two-paragraph citation fix into a research programme in energy–Casimir
stability theory. Meanwhile nothing has been run.

---

## The steelman, honestly

There is one, and it is **not** an argument for e1 as written.

A large margin on a *sufficient stability condition* says nothing about the
*magnitude* of a growth rate. The project's exposed number is
`σ = 2.0748×10⁻⁵ s⁻¹` quoted to five figures with `m = 6` vs `m = 7` separated at
0.07%, from a nondivergent operator, for a jet with `L_d ≈ 3×10⁶ m`. Poulin &
Flierl (2003) demonstrate that σ depends functionally on Froude number; Mak et al.
(2016) find weak shear instabilities surviving to arbitrarily large Froude number.
So "condition (ii) holds at 7.83×" does **not** license "the divergent correction
to σ is negligible", and §6.4's own 6–40% frequency corrections point the other
way.

The defensible move is therefore the *divergent EVP for σ(m)* — a bias estimate on
the headline number, framed as verification, claimed as nothing — not a test of
Ripa's conditions, which is answered and occupied. Even that should be ranked
against simply reporting L1 honestly and running the 42 pending runs.
