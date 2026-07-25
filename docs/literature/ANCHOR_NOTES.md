# Anchor-paper notes

**Session L4, Steps 9–10.** Close reading of the load-bearing papers, with page,
section and equation pointers precise enough that a later reader can find the
passage without re-reading the paper.

Each subsection records three things the manuscript needs and cannot get from an
abstract: **what this project borrows or compares against**, **the exact scope of
the paper's own claim** (so this project's claim can be stated as narrower, equal
or building on it without overstatement), and **the caveats the original authors
stated themselves** — because a referee is likely to know those and will expect
them acknowledged.

`[READ]` means the PDF is held in `docs/literature/` and was opened.
`[IDENTIFIER-ONLY]` means the citation is verified against Crossref but the paper
was not read; nothing page-precise is claimed from it.

---

## 1. Williamson, Drake, Hack, Jakob & Swarztrauber (1992) `[READ]`

**Citation used:** *J. Comput. Phys.* **102**(1), 211–224.
DOI `10.1016/0021-9991(92)90060-C`.

> **IDENTITY MISMATCH — the held PDF is not the cited paper.** The file
> `williamson_1992_standard_test_set.pdf` is **ORNL/TM-11895**, an Oak Ridge
> National Laboratory technical memorandum, confirmed from its cover page (Oak
> Ridge / Martin Marietta masthead, report number, DOE distribution statement).
> Same five authors, same title, but a *different document* from the *JCP*
> article. Its pagination and equation numbering do **not** match the journal
> version, so **no page- or equation-precise pointer may be drawn from this PDF
> and attributed to the JCP paper.** This is the third citation-identity defect
> found in this project's own literature holdings, after the Haurwitz filename
> (L3-PATCH) and the Kasahara venue (this session).
>
> Disposition: the *JCP* citation stands as the published reference and its DOI
> verifies. Claims about the test suite are drawn from the sources below that
> discuss it, not from page numbers in the held report.

**What this project takes:** the test-suite framing — that a shallow-water model
on the sphere should be validated against a standard, published set of cases with
stated error norms — and specifically case 2 (steady zonal geostrophic flow) and
case 6 (the Rossby–Haurwitz wave, zonal wavenumber 4).

**Scope of their claim:** a proposed standard suite, offered as a common
reference point. Not a claim about the physics of any case.

**Caveat, stated by others rather than by them:** see Galewsky et al. below, who
document that the suite's later cases carry "unexpected subtleties which render
them less useful than originally thought."

---

## 2. Thuburn & Li (2000) `[READ]` — **the most consequential find of this campaign**

**Citation:** "Numerical simulations of Rossby–Haurwitz waves", *Tellus A*
**52**(2), **181–189**. DOI `10.3402/tellusa.v52i2.12258`.

This paper was already held by the project and had never been extracted. It
directly constrains the phase-speed campaign.

**What it establishes** (abstract, p. 181, and §1 pp. 181–182):

1. "**contrary to common belief, the zonal wavenumber 4 Rossby–Haurwitz wave is
   dynamically unstable and will eventually break down if initially perturbed.**"
2. Unlike the nondivergent case, the *shallow-water* Rossby–Haurwitz wave
   "locally generates small-scale features and so has a potential enstrophy
   cascade."
3. The prior belief it overturns, stated on p. 182: RH waves with zonal
   wavenumbers ≤ 5 were believed stable, those > 5 unstable — and Williamson et
   al. (1992) proposed the wavenumber-4 wave as a test case *because* it was
   believed stable.
4. Numerical solutions are sensitive to the hyperdiffusion coefficient, and "the
   optimal value of `k` depends on the details of the flow", with larger `k`
   needed when small scales are generated (pp. 182, citing Bates et al. 1995 and
   Bates & Li 1997).
5. Growth is exponential with an **e-folding time of 1.3 days** for the modes
   they track (p. 464 of the extracted text, §4).

**Consequences for this project — these are real and must reach the operator:**

- The phase-speed campaign (P-01 … P-18) initialises single Rossby–Haurwitz
  modes and measures phase speed over an integration window. If the initialised
  wave is itself dynamically unstable with an e-folding time of order a day, the
  **measurement window is not a free choice**: phase speed must be extracted
  before breakdown contaminates it, and the window must be reported.
- The blueprint sweeps degree `n = 2…8`. On Thuburn & Li's account the higher
  degrees are the ones expected to break down soonest.
- Blueprint run **P-18** (hyperdiffusion sensitivity) is not a formality. Thuburn
  & Li show the answer depends on the dissipation coefficient in exactly the
  regime this project works in.
- H1–H4 are framed as statements about clean propagating modes. They remain
  testable, but the test is now explicitly "phase speed of the mode *while it
  survives*", not "phase speed of a steady solution".

**Scope of their claim:** four numerical models, shallow-water and nondivergent
barotropic, on the sphere. They do not solve a linear eigenvalue problem for the
RH wave; the instability is diagnosed from nonlinear integrations.

---

## 3. Galewsky, Scott & Polvani (2004) `[READ]`

**Citation:** *Tellus A* **56**(5), 429–440. DOI `10.3402/tellusa.v56i5.14436`.

**What this project takes:** the jet profile (their eq. 2), the gradient-wind
balance integration for the height field (eq. 3), and the localised height
perturbation (eq. 4), with the parameter values `u_max = 80 m/s`, `φ₀ = π/7`,
`φ₁ = π/2 − φ₀`, `ĥ = 120 m`, `φ₂ = π/4`, `α = 1/3`, `β = 1/15`. Verified
parameter-for-parameter against the shipped Dedalus example in Session L1
(`tests/phase0_gate/galewsky_comparison.md`).

**Their stated motivation, p. 429–430 — worth quoting in Related Work:** the
Williamson suite's "widespread use has revealed a number of serious problems
that severely limit their practical utility." Cases 1–4 are "completely
idealized and thus largely unrepresentative"; cases 5–7 show "unexpected
subtleties which render them less useful than originally thought."

**Caveats they state themselves:**

- Their reference solution is a **T341 spectral computation**, not an analytic
  solution; l₂ errors at T42/T85/T170 are measured against it (§3).
- The small-scale features in the evolved solution "are highly dependent on the
  diffusive nature of the scheme used to compute the solution, and are thus very
  difficult to reproduce."
- They integrate the *unperturbed* balanced jet for 120 h as a balance check, and
  report all fields remaining identical to machine precision. They note this step
  is "in some sense trivial for a spectral model because the spectral method has
  no means of generating non-zonal components from an initially zonal flow" —
  i.e. **this project's spectral solver passing that check is weak evidence**, and
  should be reported as a sanity check rather than as validation.

**Scope:** a test case with a reference solution. They make no claim about growth
rates or a most-unstable wavenumber, which is why no published spectrum of this
jet was found (see `DIALECTIC_CHALLENGE.md`, fragment b2).

---

## 4. Heifetz, Bishop & Alpert (1999) `[READ]`

**Citation:** *Q. J. R. Meteorol. Soc.* **125**(560), 2835–2853.
DOI `10.1002/qj.49712556004`.

**What this project takes — page-precise, re-verified in L3-PATCH:** their
**Eq. (6), p. 2838**, the nondimensional dispersion relation for Rayleigh's
constant-shear strip, `C = ±(1/2K)[(K−1)² − e^{−2K}]^{1/2}` with `K = 2kb`; and
the three constants stated in the paragraph **immediately following it on the
same page**: critical wavenumber `K_c = 1 + e^{−K_c} ≈ 1.28`; growth rate
`ΛKC_i` maximum at `K_max ≈ 0.8`, corresponding to a wavelength about eight
times the vorticity-strip width; and that maximum equal to "about 20% of the
shear Λ". The project's own two-interface reduction reproduces these as 1.2785,
0.7968 and 0.2012.

Also taken: the phase-locking criterion (§2b, pp. 2839–2842) — growth when the
northern wave lies less than half a wavelength west of the southern one — and the
edge-wave inversion `ψ' = e^{−k|y−b|}e^{ikx}` (their eq. 8, p. 2839).

**Scope of their claim:** a *pedagogical* reframing. They say so explicitly
(p. 2839): the normal-mode explanation "the waves must grow because a complex
phase speed is required" is one "the authors find rather unsatisfying", and the
CRW description is offered because "it provides a useful pedagogical framework".
**This project's §10 must be framed the same way** — as exposition of an
established mechanism, not as new theory.

**Caveat they state:** the model is Rayleigh's — a constant-shear strip on an
`f`-plane with piecewise-constant vorticity, no `β`, no sphere, no free surface.

---

## 5. Bretherton (1966) `[READ, in full]`

**Citation:** *Q. J. R. Meteorol. Soc.* **92**(393), 325–334.
DOI `10.1002/qj.49709239302`.

**What this project takes:**

- **p. 329, eq. (6):** a discontinuity in the background field is mathematically
  equivalent to a delta function in potential vorticity. This is what makes the
  §10 edge-wave idealisation exact for piecewise-constant `Q` rather than a
  cartoon.
- **p. 331, eq. (13):** `∫∫ ρ (dQ/dy) (d/dt)(½ η̄²) dy dz = 0`, the integrated
  eddy potential-vorticity flux constraint, and the statement immediately after
  it that there can be no growing normal mode "unless the basic potential
  vorticity gradient `dQ/dy` assumes both positive and negative values within
  the fluid" — with the attribution he gives: proved for a special case by
  Charney & Stern (1962), extended by Pedlosky (1964).
- **p. 332:** the paper's main result — a growing or slowly growing mode is
  associated with a down-gradient PV flux near the critical layer, so "there can
  be no stable, infinitesimal, disturbance to a flow `U(y,z)` in a normal mode
  which has a critical level lying within the flow".

**Scope:** quasi-geostrophic, Boussinesq or compressible, `β`-plane. Not
shallow-water, not spherical.

---

## 6. Kuo (1949) `[READ]`

**Citation:** *J. Meteorol.* **6**(2), 105–122.
DOI `10.1175/1520-0469(1949)006<0105:DIOTDN>2.0.CO;2`.

**What this project takes:** his eq. (1), the perturbation vorticity equation
`(∂/∂t + U ∂/∂x)∇²ψ + (β − U'')∂ψ/∂x = 0`, and his eq. (2), the normal-mode
form `(U − c)(Ψ'' − α²Ψ) + (β − U'')Ψ = 0` (p. 106). The necessary condition
appears in his §5 (p. 110 in the held scan): the existence of a critical point
where the absolute-vorticity gradient `dZ/dy ≡ β − U''` vanishes.

**Caveat he states himself, p. 106 — and this project should quote it:** "The
dynamic stability or instability can only give some indication of the possibility
for the development of some disturbances, while the actual mechanism of the
disturbance itself must be studied from other considerations."

**Scope:** two-dimensional, nondivergent, barotropic, flat plane.

---

## 7. Rhines (1975) `[READ]`

**Citation:** *J. Fluid Mech.* **69**(3), 417–443.
DOI `10.1017/S0022112075001504`.

**What this project takes:** the arrest wavenumber from the abstract, p. 417:
"the turbulent migration of the dominant scale nearly ceases at a wavenumber
`k_β = (β/2U)^{1/2}`", independent of initial conditions other than `U` (the rms
particle speed) and `β`. Note the factor of 2 — `L_R = (2U/β)^{1/2}`, √2 larger
than a bare `√(U/β)`. Also: "the cascade generates, by itself, zonal flow", and
the quoted atmospheric value `k_β^{-1} ≈ 1000 km`.

**Caveat he states:** the end state of alternating zonal jets is reached in the
*homogeneous* case; "when the energy is intermittent in space … the cascade is
halted simply by the spreading of energy about space, and then the end state of
a zonal flow is probably not achieved" (abstract).

**Scope:** `β`-plane, two-dimensional, homogeneous. Not spherical, not
shallow-water. The scale is an *arrest* scale for the cascade, and Rhines does
not claim it predicts jet *spacing* — a distinction §7 of the theory must respect.

---

## 8. Kasahara (1976) `[READ]` — obtained this session

**Citation:** *Mon. Wea. Rev.* **104**(6), 669–690.
DOI `10.1175/1520-0493(1976)104<0669:NMOUWI>2.0.CO;2`.
**Not** *J. Atmos. Sci.* 33, 408–424, as `MISSING.md` previously recorded; see the
correction there.

**What this project takes:** the branch structure of the normal modes, from the
abstract (p. 669): the horizontal parts are "Hough harmonics `Θ_l^s exp(isλ)`",
with three components (zonal velocity, meridional velocity, geopotential height),
and "**three modes with distinct frequencies: eastward and westward propagating
gravity waves, and westward propagating rotational waves of the Rossby/Haurwitz
type.**" That is exactly the branch structure the project's own eigenvalue solver
reproduces, so this is a genuine external cross-check on the *qualitative*
structure — not on the mode-by-mode numbers at Earth's `ε`, which remain
internally derived.

**Scope:** linearised primitive equations, basic state at rest with temperature a
function of height only (§2, p. 670). A review and tool paper — his stated aim
(p. 670) is "the construction of tools for the investigation of ultralong waves
and the presentation of preliminary results of their application to a spectral
analysis of global data."

---

## 9. Ripa (1983) `[IDENTIFIER-ONLY]` — and why it matters most

**Citation:** "General stability conditions for zonal flows in a one-layer model
on the beta-plane or the sphere", *J. Fluid Mech.* **126**, 463–489.
DOI `10.1017/S0022112083000270`.

Surfaced by the Step 7 width critique, verified against Crossref, **not obtained
as a PDF**. Nothing page-precise is claimed from it.

**Why it is the single most important reference this campaign added:** its title
names precisely the system this project actually integrates — a one-layer
(divergent, free-surface) model on the sphere — whereas the project's own
stability analysis (§8–§9 of the theory) is **nondivergent**. Confirmed by
inspection: `grep divergen theory/derivations.tex` returns hits in §3–§6 and
**none in §8 or §9**. The general stability conditions for the divergent system
are not the same as Rayleigh–Kuo, and Ripa is where they live.

Consequence, carried into `DIALECTIC_CHALLENGE.md` and `GAP_STATEMENT.md`: the
project's growth rates are for the nondivergent problem, while its nonlinear runs
are shallow-water with `L_d ≈ 3×10⁶ m` — comparable to the jet width. The paper
must state that mismatch rather than let a referee find it.

## 10. Hayashi & Young (1987) `[IDENTIFIER-ONLY]`

**Citation:** "Stable and unstable shear modes of rotating parallel flows in
shallow water", *J. Fluid Mech.* **184**, 477–504.
DOI `10.1017/S0022112087002982`.

Also surfaced by the width critique and verified. Relevant because it treats
shear instability in the *shallow-water* system specifically. The width critic
reported that it exhibits instabilities without a potential-vorticity-gradient
sign change; **that specific claim was not verified against the paper's text and
is therefore not asserted here.** It is recorded as an open question in
`DIALECTIC_CHALLENGE.md` because, if true, it bounds H7 — which the blueprint
calls its strongest test precisely because it is a prohibition.

## 11. Skiba & Pérez-García (2004) `[IDENTIFIER-ONLY]`

**Citation:** "On the structure and growth rate of unstable modes to the
Rossby–Haurwitz wave", *Numer. Methods Partial Differ. Equ.* **20**,
DOI `10.1002/num.20042`.

Direct methodological prior art for fragment b1: a normal-mode instability
calculation, with growth rates, for a Rossby–Haurwitz basic state on the sphere.
Part of a sustained programme (Skiba 2008, `10.1007/s10958-008-0091-3`; Skiba
2024, `10.4310/dpde.2024.v21.n3.a1`). Not obtained as PDF; no page-precise claim
made. See `DIALECTIC_CHALLENGE.md` fragment b1.

## 12. Supporting anchors `[READ]`, nothing page-precise claimed

- **Hoskins, McIntyre & Robertson (1985)**, *QJRMS* **111**(470), 877–946,
  `10.1002/qj.49711147002` — PV invertibility and "PV thinking", cited in §10 for
  the inversion step.
- **Läuter, Handorf & Dethloff (2005)**, *JCP* **210**(2), 535–553,
  `10.1016/j.jcp.2005.04.022` — the unsteady analytic solution adopted as run V-09.
- **Burns, Vasil, Oishi, Lecoanet & Brown (2020)**, *Phys. Rev. Research* **2**,
  023068, `10.1103/PhysRevResearch.2.023068` — the solver framework.
- **Vasil et al. (2019)**, *JCP X* **3**, 100013, `10.1016/j.jcpx.2019.100013` —
  the spherical basis the solver uses.
- **Vallis & Maltrud (1993)**, *JPO* **23**(7), 1346–1362,
  `10.1175/1520-0485(1993)023<1346:GOMFAJ>2.0.CO;2` — the `O(√(U/β))` transition
  scale reached by weakly nonlinear Rossby-wave interaction; their abstract notes
  "this particular form is not crucial to the argument", which is the basis for
  §7's factor-of-√2 caveat.
- **Jakob-Chien, Hack & Williamson (1995)**, *JCP* **119**(1), 164–187,
  `10.1006/jcph.1995.1125` — the pseudospectral reference solutions to the
  Williamson suite. Held PDF is an image scan with no text layer; not read.
- **Hersbach et al. (2020)**, *QJRMS* **146**(730), 1999–2049, `10.1002/qj.3803`
  and **Kalnay et al. (1996)**, *BAMS* **77**(3), 437–471,
  `10.1175/1520-0477(1996)077<0437:TNYRP>2.0.CO;2` — the two reanalyses.

---

## Changelog — Step 10 depth-critique corrections

Every correction made after re-checking an extraction against the PDF text,
however small, per the Step 10 requirement.

| # | Correction | Driver |
|---|-----------|--------|
| C1 | **Williamson (1992): held PDF identified as ORNL/TM-11895, not the *JCP* article.** All page-precise pointers to this paper removed; only the framing claim retained. | Cover page read; OCR quality of the extracted text prompted the check |
| C2 | **Thuburn & Li (2000): pagination corrected** to *Tellus A* 52(2), **181–189**. The project's own `docs/literature/README.md` recorded only "52(2)" with no pages. | Journal header on p. 181 of the held PDF |
| C3 | **Kasahara (1976): venue corrected** from *J. Atmos. Sci.* 33(3), 408–424 to *Mon. Wea. Rev.* 104(6), 669–690. The wrong venue had been in `MISSING.md` since Session 00b, unchecked because the paper had never been obtained. | Crossref work record + journal masthead on p. 669 |
| C4 | **Hayashi & Young (1987): the width critic's specific claim** — that the paper shows instability without a PV-gradient sign change — **was not verified and is not asserted.** Recorded as an open question instead. | Paper not obtained; standing rule forbids claims not checked against the source |
| C5 | **Rhines (1975): the arrest scale is not claimed as a jet-spacing predictor.** Rhines' abstract presents `k_β` as where the cascade "nearly ceases", and separately notes the zonal-jet end state may not be achieved for spatially intermittent energy. §7's Jovian-banding sentence rests on more than Rhines supports. | Abstract, p. 417 |
| C6 | **Heifetz et al. (1999) reframed as pedagogical.** Their p. 2839 states the CRW view is offered as a "useful pedagogical framework", so §10 is exposition, not new theory. | p. 2839 read |
| C7 | **Galewsky et al. (2004): the 120 h balance check downgraded** from validation to sanity check, because the authors themselves note it is "in some sense trivial for a spectral model". | §3 of the paper |
