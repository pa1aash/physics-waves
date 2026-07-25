# Width critique — blind-spot probe

**Session L4, Step 7.** Adversarial coverage review of the literature campaign.
Inputs: `SCOPE_CONTRACT.md`, `QUERY_MATRIX.md`, `VERIFIED_POOL.csv` (669 rows),
`theory/derivations.tex`, `PROJECT_BLUEPRINT.md` §2.3 / §5 / §8 / §9 / §10.4 / §11.

The question this document asks is not "did the campaign execute its plan?" — it
did — but "what would a referee at *Theoretical and Computational Fluid
Dynamics* ask for that the plan never contemplated?" TCFD's readership is fluid
dynamicists and numerical analysts, not meteorologists. That shifts the referee
risk away from the geophysical framing (which Q1–Q11 cover competently) and
toward two things the query matrix barely touches: **the correctness of the
stability operator for the system actually being solved**, and **the
computational-fluid-dynamics verification canon**.

Every finding below carries exactly one disposition. Findings are ordered by
estimated probability that a referee raises them.

---

## Part 0 — Corpus profile, for calibration

| Slice | Count |
|---|---|
| Verified rows | 669 |
| Selected for bibliography | 406 |
| `READ` | 16 |
| `IDENTIFIER-ONLY` | 653 (390 of the 406 selected) |
| F1 (forward citations of Galewsky 2004) | 177 |
| Largest F1 venues | *J. Comput. Phys.* 44, *Mon. Wea. Rev.* 17, *QJRMS* 11, *GMD* 9 |

Keyword probes against title + author across all 669 rows:

| Probe | True hits |
|---|---|
| Ripa / Sakai / Hayashi & Young / Zeitlin / Bouchut | **0** |
| Matsuno | **0** |
| aliasing / dealiasing / two-thirds / three-halves | **0** |
| hyperdiffusion / hyperviscosity / biharmonic | **0** |
| Doppler | **0** |
| Roache / Oberkampf / GCI / Richardson extrapolation / manufactured solution | **0** |
| White–Hoskins consistent approximation / traditional approximation | **0** |
| Fjørtoft / Kraichnan / enstrophy cascade / Boer & Shepherd | **0** |
| Machenhauer / Baer / Tribbia / slow manifold / normal-mode initialisation | **0** |
| Eliassen–Palm / pseudomomentum / wave activity | **1** (Morgan 2001) |
| Andrews & McIntyre / GLM / Edmon | **0** |
| `Hough` in title | **1** (Wang, Boyd & Akmaev 2016) |
| torch-harmonics / SFNO primary paper | **0** |

Those zeros are the shape of the blind spot. They cluster in exactly two places:
the divergent-shallow-water stability literature, and the numerical-methods
provenance literature.

---

## Part 1 — Direct answers to the three tested prompts

### Prompt 1 — GCM / dynamical-core validation against the Williamson (1992) suite

**Answer: YES, a body exists and it adds useful context — but not the context
the campaign is currently drawing from it, and the campaign never swept it.**

Evidence. The 177 F1 rows are a coherent, twenty-year *discretisation-development*
literature, not a physics literature. Method-family tallies over F1 titles:
grid/mesh construction (cubed-sphere, icosahedral, C-grid, AMR, Voronoi) 40;
DG / finite-element 28; time integration (IMEX, exponential, parallel-in-time,
deferred correction) 20; conservation / mimetic / Hamiltonian 18; finite-volume
17; spectral or double-Fourier 13; data assimilation and ML 13; applications
(ocean, tsunami, moist, tropical cyclone) 19. Year histogram runs 2004→2026 with
the mass post-2019. What the set collectively represents is: *Galewsky (2004) has
become test case #7 of the de-facto dynamical-core acceptance suite.*

Two consequences, one favourable and one adverse.

Favourable, and it should be banked. Only **4 of 177** F1 titles contain any of
{stability, normal mode, growth rate, eigen, instability}, and on inspection all
four are about *numerical* stability of a discretisation, not about the linear
stability spectrum of the jet. Twenty years and 177 forward citations produced no
published normal-mode spectrum of the Galewsky base state. That is a *negative
result of a systematic search*, which is precisely what exit criterion 4 requires
for fragment **b2** — and it is stronger evidence than any single "we looked and
found nothing" assertion. It is currently sitting unrecorded in a CSV.

Adverse. The campaign ran a forward sweep on Galewsky (2004) but ran **no forward
sweep on Williamson et al. (1992)**, which is the actual benchmark the V-01…V-08
gate is built on. The pool holds six Williamson-adjacent rows. The literature
that sweep would surface is the part a referee will want: the documented
limitations of the suite (case 2 is a *steady* solution, so its error norms
measure balance preservation rather than transient accuracy — yet blueprint §9.4
pass criteria 1 and 2 rest entirely on case 2); the "effective resolution"
concept, which is what actually determines whether an `m = 6` growth rate is
resolved at L1; and the successor suites (DCMIP, Lauritzen transport suite —
the latter is already held) that exist *because* the 1992 suite was found
insufficient. Blueprint §9.4 criterion 2 asks that error magnitudes be
"consistent in order of magnitude with published values for spectral methods";
the campaign holds Jakob-Chien et al. (1995) for that, but no modern
recalibration of what a spectral method should achieve at T170-equivalent.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `OpenAlex: cited_by:W<Williamson1992> filtered to venue in {J. Comput. Phys., Mon. Wea. Rev., QJRMS, GMD}, sorted by citation count, top 60`
- `shallow water test set limitations deficiencies proposed additional test cases`
- `effective resolution dynamical core numerical diffusion kinetic energy spectrum`
- `DCMIP dynamical core model intercomparison project test case suite`
- `steady state geostrophic flow test case error norm balance preservation critique`

Also: record the F1 null result explicitly as the search-of-record for fragment
b2 in `DIALECTIC_CHALLENGE.md` — "177 forward citations screened, zero linear
stability spectra" — with the verdict *survives*.

---

### Prompt 2 — Does the ML weather-modelling literature need acknowledgement?

**Answer: NO for a survey — X4's "acknowledgement only" is the right call and
silence on the ML *field* would not look like an omission at TCFD. But YES for
one specific citation, and its absence is not an ML question at all.**

Evidence. Blueprint §7.5 designates as the optional cross-check "a public
spherical shallow-water dataset generated by an independent spectral solver on
an equiangular latitude-longitude grid with Earth-matched parameters […]
available through the torch-harmonics package." That dataset is generated by the
`torch_harmonics` shallow-water solver, whose primary reference is Bonev et al.,
*Spherical Fourier Neural Operators: Learning Stable Dynamics on the Sphere*
(ICML 2023, arXiv:2306.03838). The pool contains **zero** rows for it. The
nearest thing held is Mahesh et al. (2025), *Huge ensembles Part 1*, which
*uses* SFNO but is not the solver's source.

This is a data-provenance failure, not a literature-coverage failure, and it is
the exact failure mode the scope contract's paper-trail rule was written to
catch: an external artefact used in the project with no retrieval row behind it.
It sits under blueprint §7.4 ("constants and parameter provenance"), not under
X4. A referee who checks where Tier-4 numbers came from will find an
unattributed dataset; that is a data-availability-statement problem and journals
now check it mechanically.

The Q12 slice itself (23 rows) is adequate for X4's one-sentence
acknowledgement and is in fact over-collected — 15 of 23 are deselected and
several are irrelevant (agriculture ML, solar irradiance forecasting, phased-array
radar, IoT-adjacent reviews). Nothing further is needed there.

**Disposition: ADDRESSED IN STEP 8** — but as a provenance retrieval, not an ML
sweep.
Suggested queries:
- `Bonev spherical Fourier neural operators learning stable dynamics sphere ICML 2023`
- `torch-harmonics differentiable spherical harmonic transforms PyTorch software citation`
- verify against arXiv `2306.03838` and record the shallow-water dataset
  generation parameters (grid, `dealiasing`, `H`, `Ω`) alongside the DOI, since
  §7.5 compares against them.

*(The separate question of surveying ML weather models is disposed of in Part 3.)*

---

### Prompt 3 — Is there a post-2010 treatment of Rayleigh–Kuo on the sphere?

**Answer: YES. Two independent post-2010 bodies exist, and neither is in the
pool. The stronger of the two also partially undermines theory §8's claim that
"the argument's structure is unchanged."**

Evidence.

1. **Skiba (2017), *Mathematical Problems of the Dynamics of Incompressible
   Fluid on a Rotating Sphere*, Springer, DOI `10.1007/978-3-319-65412-6`**
   (surfaced via OpenAlex this session; not yet verified per the campaign's
   Step-4 standard). This is the modern monograph treatment of exactly the
   problem theory §8 and §9 pose: necessary conditions, the spectral problem,
   and Liapunov stability for the barotropic vorticity equation *on the sphere*.
   The pool already holds **four** Skiba journal papers (Q5: 2000, 2003, 2004,
   2018) — and **three of the four are `selected_for_bib = no`**, including
   *On Liapunov and Exponential Stability of Rossby–Haurwitz Waves in Invariant
   Sets of Perturbations* (2018, `10.1007/s00021-017-0359-9`). The campaign
   found the right author and then deselected him. Skiba's invariant-sets result
   is the correct literature basis for the §9 caveat about what a normal-mode
   spectrum can and cannot establish, and for the H7 prohibition's status.

2. **Zhu, Zhou & Dodin (2018), "On the Rayleigh–Kuo criterion for the tertiary
   instability of zonal flows"** (surfaced via OpenAlex, 24 citations,
   plasma-physics venue). The drift-wave/plasma community re-derived Rayleigh–Kuo
   in the Charney–Hasegawa–Mima setting after 2010 and found the criterion's
   structure *does* change once the finite deformation radius (their `ρ_s`, the
   project's `L_d`) is retained. That is a cross-disciplinary near-neighbour to
   the project's own configuration and a referee at a fluids journal — where the
   plasma and geophysical literatures are read side by side — is more likely to
   know it than a meteorology referee would be.

The stronger point, which is finding **W1** below: item 2's conclusion is not
merely additional context. Theory §8 states that on the sphere the criterion
changes "*where* the criterion is met, not *whether* the argument works." That is
true for the *nondivergent* system §8 actually linearises. It is not established
for the divergent system the project simulates.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `Skiba stability barotropic vorticity equation rotating sphere invariant sets Liapunov`
- `Skiba mathematical problems dynamics incompressible fluid rotating sphere monograph`
- `Rayleigh-Kuo criterion finite deformation radius Charney-Hasegawa-Mima tertiary instability`
- `necessary condition barotropic instability sphere modern derivation post-2010`
- and re-select the three deselected Skiba rows already in the pool.

---

## Part 2 — Blind spots not on the prompt list, ranked

### W1 — The stability operator is nondivergent; the simulated system is not

**Highest referee risk in this document.**

Theory eq. `genevp` poses the linear stability problem as
`[ū_a 𝓛_m + (1/R²cosφ)(dQ/dφ)] Ψ = c_a 𝓛_m Ψ`, where `𝓛_m` is the bare spherical
Laplacian on a streamfunction. There is no free-surface term, no `1/L_d²`. A grep
of `derivations.tex` for `divergen` returns hits in §3, §4, §5 and §6 and **none
anywhere in §8 or §9**. The nondivergent assumption is never stated in the two
sections that depend on it.

Meanwhile §6.4 of the same document establishes, at Earth's `ε ≈ 8.80`, that the
free surface slows Rossby modes by 40% (`n=2`) down to 6% (`n=8`), and §4 states
outright that "the divergent correction is not a small perturbation and should be
measurable." The Galewsky configuration has `H = 10⁴ m`, so `L_d ≈ 3×10⁶ m` at
45°N — comparable to both the jet width and the `m = 6` zonal wavelength. The
project then quotes `σ(m*) = 2.0748×10⁻⁵ s⁻¹` to five significant figures and
distinguishes `m = 6` from `m = 7` at the 0.07% level, from an operator whose
neglected physics the project's own §6.4 sizes at several percent.

The literature that governs this is absent from the pool entirely:

- **Ripa (1983)**, *General stability conditions for zonal flows in a one-layer
  model on the β-plane or the sphere*, J. Fluid Mech., DOI
  `10.1017/S0022112083000270` (128 citations). The title is the project's exact
  configuration. It gives the correct necessary conditions for the *one-layer*
  system, which are not the nondivergent Rayleigh–Kuo condition.
- **Hayashi & Young (1987)**, *Stable and unstable shear modes of rotating
  parallel flows in shallow water*, J. Fluid Mech., DOI
  `10.1017/S0022112087002982` (129 citations). Demonstrates shallow-water shear
  instabilities arising from Rossby–gravity resonance that require **no
  PV-gradient sign change**. This is a direct counterexample to H7 read as a
  prohibition, in the divergent system.
- **Sakai (1989)** and the Zeitlin-school follow-ups on ageostrophic /
  Rossby–Kelvin instability of shallow-water jets.

A JFM/TCFD referee will know Hayashi & Young. H7 is described in `SCOPE_CONTRACT`
M2 as "the strongest test in the set because it forbids rather than fits" — the
strongest claim is the one resting on the weakest-supported operator.

Note this is *fixable by scoping*, not necessarily by re-deriving: the honest
move may be to state that §8–§9 are the nondivergent limit, cite Ripa for the
one-layer conditions, cite Hayashi & Young for what the nondivergent prohibition
does not cover, and bound the resulting bias on `σ` using §6.4's own numbers.
That is a two-paragraph fix — but it cannot be written without the citations.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `Ripa general stability conditions zonal flows one-layer model beta-plane sphere`
- `stable and unstable shear modes of rotating parallel flows in shallow water Hayashi Young`
- `Rossby-Kelvin instability shallow water jet resonance ageostrophic Sakai`
- `barotropic instability finite deformation radius divergent shallow water growth rate comparison`
- `Zeitlin nonlinear dynamics rotating shallow water instabilities of jets`

---

### W2 — The CFD verification-and-validation canon is absent, and Richardson extrapolation is asserted under a claim of spectral convergence

Blueprint §2.3 names as the project's *first* distinguishing feature that
"verification and validation are treated as separate, explicitly reported
activities rather than being conflated." That is a claim about methodology, made
to a computational-fluid-dynamics journal, and the pool supports it with **zero**
references. No Roache, no Oberkampf & Roy, no ASME/AIAA standard, no method of
manufactured solutions, no grid-convergence-index literature. The V-vs-V
distinction the project treats as its own framing is a forty-year-old formalised
standard in the CFD community, and presenting it without attribution reads either
as unfamiliarity with the field or as appropriation.

Worse, there is an internal inconsistency the same literature would expose.
Blueprint §11.1 estimates discretisation error "by Richardson-type extrapolation
across the resolution ladder", and §11.6 requires every headline number to carry
an uncertainty derived from it. But blueprint §2.5 claims the method "converges
spectrally, meaning error falls faster than any fixed power of resolution."
Richardson extrapolation is defined for algebraic convergence at a fixed observed
order `p`; under exponential convergence the observed order is not constant
across the ladder and the extrapolated limit and its error bar are not
well-defined in the usual way. The project cannot simultaneously claim spectral
convergence and Richardson-extrapolated error bars without addressing the
tension. A numerical-analysis referee will spot this in the uncertainty section,
which is the section §11.6 makes load-bearing for every quoted number.

Candidate anchors surfaced this session (unverified): Celik et al. (2008),
*Procedure for Estimation and Reporting of Uncertainty Due to Discretization in
CFD Applications*, ASME J. Fluids Eng., DOI `10.1115/1.2960953` (4120 citations);
Oberkampf & Trucano, *Verification and validation benchmarks* (2007). For the
spectral-convergence side, the standard treatment of estimating error under
exponential convergence is in Boyd's *Chebyshev and Fourier Spectral Methods*.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `Roache verification and validation computational science quantification of uncertainty CFD`
- `Oberkampf Trucano verification validation predictive capability computational fluid dynamics`
- `ASME procedure estimation reporting uncertainty due to discretization CFD grid convergence index`
- `method of manufactured solutions code verification`
- `error estimation spectral methods exponential convergence Richardson extrapolation validity`

---

### W3 — The two discretisation choices that most affect the measured growth rates have no source

Blueprint §5.2 specifies, verbatim: "**Dealiasing.** Three-halves rule, to
eliminate aliasing error from quadratic nonlinear terms" and "**Dissipation.**
Hyperdiffusion of the form `ν∇⁴` or higher". The pool contains **zero** rows on
aliasing or dealiasing and **zero** on hyperdiffusion or hyperviscosity. The only
Orszag paper held is *Fourier Series on Spheres* (1974), and it is
`selected_for_bib = no`.

This matters more than a normal citation gap for three reasons. First, TCFD is a
computational journal and these are the two lines of §5.2 its referees will read
most carefully. Second, hyperdiffusion is not a bystander here: blueprint §10.2
already anticipates that "finite deformation radius and hyperdiffusion both act
preferentially at small scales" and §11.3 makes hyperdiffusion sensitivity a
named uncertainty source — so the modelling choice is doing real work in the
results and is defended only by a self-consistency test, not by any external
practice. Third, the theory's §9.2 spurious-mode filter (solve at `N` and `2N`,
retain eigenvalues that do not move) is a standard technique stated without
attribution; the pool does hold McFadden et al. (1990) on spurious eigenvalues in
Chebyshev-tau, which is adjacent but is not the source for the resolution-doubling
filter.

Anchor surfaced this session (unverified): Orszag (1971), *On the Elimination of
Aliasing in Finite-Difference Schemes by Filtering High-Wavenumber Components*,
J. Atmos. Sci., DOI `10.1175/1520-0469(1971)028<1074:OTEOAI>2.0.CO;2`
(351 citations).

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `Orszag elimination of aliasing filtering high wavenumber components two-thirds rule`
- `dealiasing spherical harmonic transform quadratic nonlinearity spectral atmospheric model`
- `hyperdiffusion hyperviscosity coefficient choice spectral global model scale selectivity`
- `spectral transform method shallow water sphere Bourke Machenhauer triangular truncation`
- `spurious eigenvalues generalized eigenvalue problem resolution doubling filter hydrodynamic stability`

---

### W4 — Wave activity, pseudomomentum and the Eliassen–Palm framework are missing

Probes return **one** hit (Morgan 2001) for wave activity and **zero** for
Eliassen–Palm, pseudomomentum, non-acceleration, Andrews & McIntyre, or
generalised Lagrangian mean. This is the single largest *conceptual* hole,
because three separate parts of the project are pseudomomentum arguments written
without the word:

- Theory §5.3's "why westward, and why that is not a convention" — the sign of
  the Rossby phase speed is the sign of the pseudomomentum, and the standard
  modern statement of the argument is in the wave-activity framework.
- Theory §10's counter-propagating-Rossby-wave picture, which the scope contract
  makes fragment **d**, the expository identification the manuscript is
  *organised around*. CRW phase-locking is a pseudomomentum-exchange argument;
  Heifetz–Bishop–Alpert (held) presents it that way.
- The §9 caveat on modal vs. non-modal stability. The pool holds McIntyre &
  Shepherd (1987) — the finite-amplitude wave-activity conservation theorem — and
  it is selected, but it is the *only* member of its family present, so it cannot
  be used without introducing the framework from nowhere.

The missing anchors are Andrews & McIntyre (1976, 1978), Edmon, Hoskins &
McIntyre (1980), Held (1985) on pseudomomentum and mode orthogonality, Shepherd
(1990) on symmetries and conservation laws in wave–mean-flow theory, and the
modern finite-amplitude local wave activity line (Nakamura & Zhu; Huang &
Nakamura), which is what present-day midlatitude-dynamics referees use.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `Eliassen-Palm flux wave activity conservation quasi-geostrophic non-acceleration theorem`
- `Andrews McIntyre generalized Eliassen-Palm theorem wave activity pseudomomentum`
- `pseudomomentum Rossby wave propagation direction sign shear instability orthogonality`
- `Shepherd symmetries conservation laws Hamiltonian structure geophysical fluid dynamics`
- `finite-amplitude local wave activity Rossby wave breaking barotropic diagnostic`

---

### W5 — The Doppler correction, which is a named claim fragment, has no methodological source

`SCOPE_CONTRACT` M2 lists **c1** as a separately challengeable fragment: "Doppler
correction of observed ground-relative phase speed before comparison with an
intrinsic theoretical prediction", classified as *hygiene*. The pool contains
**zero** rows matching `Doppler`. Q10's query strings cover Hayashi
decomposition and observed phase-speed spectra — both well served, with Hayashi
(1971, 1982) held — but nothing on the Doppler-shifting step itself, on the
choice of the advecting `ū`, or on the depth over which `ū` should be averaged.

The same hole extends to blueprint run P-16, which measures "`A(φ)`, turning
latitude". Turning latitudes are a ray-tracing concept and the pool's only
support is Karoly & Hoskins (1982), held `IDENTIFIER-ONLY`. Hoskins & Karoly
(1981) and Karoly (1983) — the papers that actually define the stationary
wavenumber, the turning latitude and the Doppler-shifted intrinsic frequency in a
sheared basic state — are absent. Fragment c1 currently rests on nothing a
referee can check, and exit criterion 4 requires a recorded search behind every
fragment.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `Hoskins Karoly steady linear response spherical atmosphere thermal orographic forcing`
- `Doppler shift intrinsic phase speed Rossby wave background flow observed ground-relative`
- `stationary wavenumber turning latitude Rossby wave ray tracing barotropic sphere`
- `zonal mean wind averaging depth equivalent barotropic level advecting flow eddies`

---

### W6 — Energy and enstrophy conservation as a *constraint*, not as a closure

Blueprint §9.3 makes potential enstrophy "the strictest diagnostic […] the
early-warning signal", and V-08 is a dedicated conservation-audit run. §9.4 pass
criterion 4 is "potential enstrophy does not grow." The pool supports this with
**zero** rows on the two-dimensional dual-cascade constraint — no Fjørtoft, no
Charney (1971), no Boer & Shepherd. The two enstrophy hits in the pool (F1, 2017
and 2024) are about constructing conserving discretisations, not about what the
conservation constraint *implies* for an admissible solution.

Why a referee raises it: the criterion "monotonic slow decay acceptable, growth
is not" is stated as an assertion. Fjørtoft's dual-cascade argument is what makes
it a *theorem-backed* criterion in two-dimensional flow, and it is also what
tells you the expected *rate* of decay — without which "slow" is unfalsifiable.
Separately, theory §7.3's claim that the Ω sweep spans "the difference between a
terrestrial banding pattern and a Jovian one" is a statement about where the
inverse cascade halts, and X3's in-scope boundary explicitly requires that claim
to be sourced or struck.

This finding is scoped narrowly to the **conservation constraint** on the
verification gate. Inertial-range and closure theory is disposed of separately in
Part 3.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `Fjortoft changes in spectral distribution kinetic energy two-dimensional nondivergent flow`
- `enstrophy conservation constraint spectral truncation barotropic sphere Boer Shepherd`
- `Charney geostrophic turbulence energy enstrophy conservation`
- `potential enstrophy dissipation rate hyperdiffusion diagnostic shallow water sphere acceptable drift`

---

### W7 — Balance, initialisation shock and spontaneous imbalance in the growth-rate fit window

Theory §11.2 constructs a balanced height field for the Galewsky jet by solving
the divergence of the balance relation. Blueprint §11.4 then measures growth
rates by "linear fits to log-energy over a selected window" and reports window
sensitivity as an uncertainty. What sets the *earliest admissible* window edge is
how long the initialisation transient — the gravity-wave burst from an
imperfectly balanced state — contaminates the energy record. The pool has no
literature on this: **zero** rows for normal-mode initialisation, nonlinear
balance, slow manifold, or initialisation shock. Three near-neighbours are held
(Žagar et al. 2009, 2015; Vanneste 2008 on exponentially small inertia–gravity
generation) but none is about initialising a shallow-water model.

This connects to §6 as well. Hough modes *are* the basis of nonlinear normal-mode
initialisation; the campaign built a 59-row Q3 slice around Laplace's tidal
equations and never touched the literature that made Hough functions
operationally important. Kasahara (1976) was chased as a targeted deliverable and
retrieved, but as an isolated item rather than as an entry point to that line.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `nonlinear normal mode initialization Machenhauer Baer Tribbia shallow water`
- `initialization shock gravity wave transient balanced initial condition numerical model`
- `slow manifold balance dynamics rotating shallow water spontaneous emission review`
- `Hough mode expansion initialization atmospheric model normal mode functions`

---

### W8 — The equatorial waveguide, which theory §6.4 invokes and then leaves unsupported

The scope contract calls fragment **a3** — the sectoral-mode anomaly — "the most
distinctive single result in the theory". Theory §6.4 gives it two causes. The
first (single degree-ladder coupling partner) is demonstrated causally by basis
truncation and needs no literature. The **second** is: the local deformation
radius `√(gH)/|f|` grows toward the equator, so the relevant parameter is
`ε⟨sin²φ⟩/n(n+1)`, and sectoral modes, whose `P_m^m ∝ cos^m φ` is "equatorially
confined", sit where it is largest.

That is an equatorial-trapping argument. The pool contains **zero** rows for
Matsuno (1966), `10.2151/jmsj1965.44.1_25` (2749 citations), which is the
canonical source for equatorial trapping of the shallow-water modes, and the
`ε`-dependence of Hough-function meridional structure — including the transition
to equatorial confinement as `ε` grows — is exactly the content of
Longuet-Higgins (1968), which *is* held (A1) but is `IDENTIFIER-ONLY`, i.e.
nobody on the project has read the paper their own mechanism depends on. That is
the failure mode exit criterion 5 was written to expose, applied to the project's
most distinctive claim.

The project works in midlatitudes, so the equatorial waveguide is peripheral to
the *simulations*. It is not peripheral to a3.

**Disposition: ADDRESSED IN STEP 8** — bounded to two or three references, not a
sweep.
Suggested queries:
- `Matsuno quasi-geostrophic motions in the equatorial area equatorially trapped waves`
- `Longuet-Higgins eigenfunctions Laplace tidal equations Lamb parameter equatorial trapping meridional structure`
- `Hough function meridional structure dependence on Lamb parameter sectoral modes`

---

### W9 — Non-normality references are already in the pool and were deselected

The scope contract records that the theory's "genuine sufficient computational
test" language was *wrong and has been corrected*, and that the correction turns
on the linearised barotropic shear operator being non-normal. Theory §9 now
carries a caveat paragraph making exactly that argument. It cites nothing.

Meanwhile Q5 retrieved Farrell & Ioannou (1994), Waleffe (1995), Pujals et al.
(2009) and Maretzke et al. (2014) — and **all four are
`selected_for_bib = no`**. The campaign found the literature required to defend
its own most important correction and then dropped it in the selection pass. The
canonical anchors (Farrell & Ioannou's generalised stability theory papers;
Trefethen et al. 1993; Schmid 2007) are also absent.

Cheapest finding in this document to close: three of the required rows are
already verified and merely need re-selecting.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `Farrell Ioannou generalized stability theory autonomous operators non-normal`
- `Trefethen hydrodynamic stability without eigenvalues pseudospectra`
- `transient non-modal growth barotropic shear flow beta plane optimal perturbation`
- plus: flip `selected_for_bib` on the four deselected Q5 non-normality rows.

---

### W10 — Model-consistency: which approximations the spherical shallow-water system embeds

The pool has **zero** rows for the consistent-approximation literature (White,
Hoskins, Roulstone & Staniforth 2005, and the traditional / shallow-atmosphere /
spherical-geopotential approximation family). Bénard (2014), *An assessment of
global forecast errors due to the spherical geopotential approximation in the
shallow-water case*, is in the pool via F1 — the single most on-point title in
the entire 177 — and is `selected_for_bib = no`.

Why a referee raises it: theory §2 sets up the sphere as a curved manifold with
an explicit metric and Christoffel symbols, which invites the question of what
was approximated away. A fluid-dynamics referee will ask whether the model is a
*consistent* approximation — whether the neglected Coriolis components, the
geopotential shape and the shallow-atmosphere assumption are mutually consistent
and conserve the right quantities. This is one citation plus one sentence in §3.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `White Hoskins Roulstone Staniforth consistent approximate models global atmosphere quasi-hydrostatic`
- `traditional approximation shallow atmosphere neglected Coriolis terms conservation consistency`
- plus: re-select Bénard (2014) `spherical geopotential approximation shallow-water` from F1.

---

### W11 — The critical-layer regularisation is named but its methods are unsourced

Theory §9.2 states that for a neutral mode "the resolution requires either the
viscous indentation of Kuo (1949) or an explicit contour deformation." Kuo is
cited; contour deformation is not. The pool holds exactly **one** critical-layer
paper, Bretherton (1966). The standard sources for the contour-deformation
treatment of the Rayleigh problem and for the numerical realisation of an
indented contour in a spectral eigenvalue solver are absent.

Lower priority than W1–W3 because §9.2's actual computation reports only growing
modes, where the operator is regular — but the paragraph makes a claim about
neutral modes that it does not support, and the solid-body-rotation control run
in §9.3 is precisely a neutral-spectrum calculation.

**Disposition: ADDRESSED IN STEP 8.**
Suggested queries:
- `critical layer contour deformation Rayleigh equation neutral mode logarithmic branch point numerical`
- `singular neutral modes inviscid shear flow spectral eigenvalue solver regularization`

---

### W12 — Q3's retrieved slice is heavily contaminated, so §6's apparent depth is overstated

Not a referee-visible finding, but it determines whether the gaps above are real.
The Q3 slice (59 rows, all tagged `relevance_tier = core`) contains, among
others: *Optical visualization of individual ultralong carbon nanotubes*,
*Millisecond Oscillations in X-Ray Binaries*, *Non-spherical core collapse
supernovae*, *Ultrafast rogue wave patterns in fiber lasers*, *Dynamics of an
initially spherical bubble rising in quiescent liquid*, *Initial Data for
Numerical Relativity*, *Stochastic Gravitational-Wave Backgrounds*, and
*Fundamentals, progress and perspectives on high-frequency phononic crystals*.
These are OpenAlex full-text-search collisions on "normal modes", "ultralong
waves" and "sphere". Roughly 40% of the slice is off-topic, and only **one** row
in 59 has `Hough` in its title.

So the campaign's largest theory-area slice is, after screening, thin exactly
where fragments a1–a3 need it to be thick. The same collision pattern degrades Q1
(hydrology, ice-sheet, geoengineering and aerosol "model intercomparison
projects") and Q9 (macroalgal blooms, evapotranspiration, digital twins).

**Disposition: ADDRESSED IN STEP 8.**
Suggested action and queries:
- re-run Q3 with phrase-constrained title search rather than full-text relevance:
  `title.search:"Hough function"`, `title.search:"Laplace tidal equation"`,
  `title.search:"Lamb parameter"`, `title.search:"normal modes" AND atmosphere`
- `Kasahara normal mode expansion atmospheric dynamics equivalent depth Hough vector functions`
- and downgrade the mis-tagged `core` rows to `tangential` or drop them, so the
  Step-16 bibliography check measures real coverage rather than row count.

---

## Part 3 — Explicitly out of scope, disposed of

These were considered and are being ruled out deliberately, so that the record
shows they were examined rather than missed.

**Baroclinic instability model detail (Eady, Charney, Green growth-rate
structure; baroclinic life-cycle taxonomy).** The pool's Q11 slice (20 rows) and
the CRW Part III/IV papers in Q6 already carry the boundary case X1 permits —
enough to say why the project stays barotropic, plus the observed 500 hPa eddy
phase-speed phenomenology the Hayashi decomposition needs. Nothing further.
**Disposition: EXPLICITLY OUT OF SCOPE per SCOPE_CONTRACT X1, no action** —
the project makes no baroclinic claim; §10.4 attributes residual disagreement to
baroclinicity qualitatively only, and that attribution is already sourced.

**Data assimilation, 4D-Var, POD-4DVar, particle filters, operational forecast
verification.** Thirteen F1 rows fall in this family (POD-4D-Var, independent set
perturbation method, equal-weights particle filter, GRAPES dycore verification,
stratospheric wind extraction from 4D-Var). They arrived as forward citations,
not as targets.
**Disposition: EXPLICITLY OUT OF SCOPE per SCOPE_CONTRACT X2, no action** — X2
puts reanalysis *production* in scope and assimilation *methodology* out; ERA5
and NCEP/NCAR are already held and READ, which is the whole of what §7.3 needs.

**Inertial-range and spectral-transfer theory (Kraichnan's `k⁻³` range, closure
schemes, LES, zonostrophic spectral budgets).** Distinct from W6, which is about
the conservation constraint on the verification gate. The transfer-theory half is
what X3 names.
**Disposition: EXPLICITLY OUT OF SCOPE per SCOPE_CONTRACT X3, no action** — the
project runs no forced-dissipative turbulence experiment; the Ω sweep is a
free-decay and single-mode campaign, and the Rhines/jet-spacing claim is sourced
through the Q7 slice (30 rows, incl. Dritschel & McIntyre 2008, Galperin et al.
2004, Scott & Polvani 2007) which X3 explicitly admits.

**A survey of machine-learning weather models.** Q12's 23 rows exceed what is
needed; GraphCast, Pangu, FuXi, GenCast and WeatherBench are held and five are
selected.
**Disposition: EXPLICITLY OUT OF SCOPE per SCOPE_CONTRACT X4, no action** — the
acknowledgement X4 permits is one sentence, and the *only* genuinely missing item
(the torch-harmonics/SFNO primary reference) is a §7.4 data-provenance obligation
disposed of under Prompt 2 above, not an ML-literature obligation.

---

## Summary table

| # | Finding | Disposition |
|---|---------|-------------|
| W1 | Nondivergent stability operator applied to a divergent shallow-water jet (Ripa 1983; Hayashi & Young 1987; Sakai 1989) | ADDRESSED IN STEP 8 |
| W2 | CFD V&V canon absent; Richardson extrapolation vs. claimed spectral convergence | ADDRESSED IN STEP 8 |
| W3 | Dealiasing rule and hyperdiffusion operator stated without a source | ADDRESSED IN STEP 8 |
| P3 | Post-2010 Rayleigh–Kuo on the sphere exists (Skiba 2017; plasma revisit); 3 Skiba rows deselected | ADDRESSED IN STEP 8 |
| W4 | Wave activity / pseudomomentum / Eliassen–Palm framework missing | ADDRESSED IN STEP 8 |
| P1 | No Williamson-1992 forward sweep; F1 null result on b2 unrecorded | ADDRESSED IN STEP 8 |
| W5 | Fragment c1's Doppler correction and P-16's turning latitude unsourced | ADDRESSED IN STEP 8 |
| W6 | Energy–enstrophy conservation constraint behind the §9.3 gate | ADDRESSED IN STEP 8 |
| W7 | Balance / initialisation shock / slow manifold and the growth-rate fit window | ADDRESSED IN STEP 8 |
| W8 | Equatorial trapping (Matsuno 1966; Longuet-Higgins unread) behind fragment a3 | ADDRESSED IN STEP 8 |
| W9 | Non-normality rows already in pool, all deselected | ADDRESSED IN STEP 8 |
| W10 | Model-consistency approximations; Bénard 2014 held but deselected | ADDRESSED IN STEP 8 |
| W11 | Critical-layer contour deformation unsourced | ADDRESSED IN STEP 8 |
| W12 | Q3/Q1/Q9 slices contaminated; §6's apparent depth overstated | ADDRESSED IN STEP 8 |
| P2 | torch-harmonics / SFNO primary citation missing (provenance, not ML) | ADDRESSED IN STEP 8 |
| — | Baroclinic instability model detail | OUT OF SCOPE per X1, no action |
| — | Data assimilation / operational forecast verification | OUT OF SCOPE per X2, no action |
| — | Inertial-range and closure theory | OUT OF SCOPE per X3, no action |
| — | ML weather-model survey | OUT OF SCOPE per X4, no action |

**All identifiers surfaced in this document were found via OpenAlex or Semantic
Scholar during this session and are recorded as candidates only. None has been
verified to the campaign's Step-4 standard (Crossref title match); Step 8 must
verify before any enters `manuscript/references.bib`, per the paper-trail rule.**
