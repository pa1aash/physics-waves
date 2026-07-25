# Positioning and gap statement

**Session L4, Step 12.** Final form, hardened against every challenge in
`docs/literature/DIALECTIC_CHALLENGE.md` that succeeded or partially succeeded.

Written to become, with light editing, the closing paragraphs of the manuscript's
Introduction. Its purpose is to fix what this paper is allowed to claim.

---

## The one-sentence version

**This paper does not contribute new theory. It contributes a controlled,
separately-verified numerical isolation of the beta effect across the whole range
from linear wave propagation to nonlinear shear instability, in one model and one
framework, with quantified numerical uncertainty and an explicit closure against
reanalysis.**

That sentence is `PROJECT_BLUEPRINT.md` §2.3, not a retreat from a stronger claim.
An earlier draft of this campaign's scope contract proposed three "contributions"
in language that overclaimed against the project's own authoritative document. The
dialectic challenge dismantled most of that language, and the blueprint turned out
to have been right from the start.

## What is genuinely new

Stated narrowly, because narrow claims survive referees.

**1. A single mechanism carried across two regimes, in one consistent model.**
The literature treats Rossby-wave dispersion and barotropic shear instability in
largely separate bodies of work — the wave line running Rossby (1939), Haurwitz
(1940b), Longuet-Higgins (1968), Kasahara (1976); the instability line running
Rayleigh, Kuo (1949), Bretherton (1966), Skiba and co-workers. What this paper
does is carry *one* solver, *one* set of conventions, and *one* uncertainty
budget across both regimes, so that the numbers in the wave sections and the
numbers in the instability sections are commensurable. That is a contribution of
*integration*, not of discovery, and it is the honest reading of blueprint §2.3.

**2. Rotation rate as a genuine free parameter.** The campaign sweeps `Ω` over a
sixteen-fold range (`0.25 Ω₀` to `4 Ω₀`, runs P-08 to P-12), which turns a fixed
physical constant into an independent variable and lets the predicted scalings —
`c_ang ∝ Ω` for the wave, `L_R ∝ Ω^{−1/2}` for the Rhines scale, and the
stabilising effect of increasing `Ω` on a fixed jet — be tested rather than
assumed. Most studies of these phenomena hold `Ω` at its terrestrial value.

**3. Verification reported separately from validation.** Convergence against
analytic solutions, discretisation-error bars from a resolution ladder,
hyperdiffusion-sensitivity brackets and timestep sensitivity are reported as
their own activity, distinct from comparison against observation. This is
ordinary good practice that is nonetheless often skipped, and the paper's value
rests substantially on having done it.

**4. One narrow empirical question with a reportable answer either way.**
Whether a westward-propagating barotropic branch is separable at all in a
space–time spectral decomposition of reanalysis geopotential height at the levels
examined — and if so at which level, with the ERA5-versus-NCEP spread carried as
observational uncertainty. This survived the dialectic challenge intact precisely
because it is small and falsifiable. If the answer is no, that is a finding about
which level is appropriate for the comparison, not a failure.

## What builds incrementally on established methods

Named explicitly, so no reader has to work out which is which.

| Element | Established by | What this paper adds |
|---------|----------------|----------------------|
| Divergent (Hough) eigenfrequencies and their dependence on Lamb's parameter | Longuet-Higgins (1968); Kasahara (1976) | The mode-by-mode numbers for this configuration, computed with the project's own solver and used as its validation target |
| The `ε → 0` limit as a check on a divergent eigenvalue solver | Standard verification practice | Nothing. It is used because it is correct, not because it is new |
| Linear stability eigenvalue problem for a zonal jet | Kuo (1949) on the plane; Skiba & Pérez-García (2004) and Skiba (2008, 2024) on the sphere — all nondivergent, as this project's is | Application to the Galewsky (2004) jet, with an explicit resolution-doubling filter and plateau reporting |
| Comparison of nondivergent, quasi-geostrophic and shallow-water growth rates for a spherical jet | Paldor, Shamir & Garfinkel (2020) | Nothing. This project does not attempt the comparison; it cites theirs for the size of its own formulation bias |
| Gradient-wind balanced initial condition for a prescribed jet | Galewsky, Scott & Polvani (2004) | Nothing; the construction is taken as published |
| Doppler correction of observed phase speed before comparison with an intrinsic prediction | Standard in space–time spectral analysis of atmospheric waves | Nothing. Omitting it would be an error; performing it is not a contribution |
| The counter-propagating Rossby-wave picture of shear instability | Bretherton (1966); Hoskins, McIntyre & Robertson (1985); Heifetz, Bishop & Alpert (1999) | Exposition only. Heifetz et al. themselves present it as "a useful pedagogical framework" |

## What is explicitly not claimed as novel

There is no shame in this list, and overclaiming would be a worse outcome than
stating it plainly.

- **Not new physics.** No new equation, mechanism, instability or wave type.
- **Not a new numerical method.** The solver is Dedalus (Burns et al. 2020) on the
  spherical basis of Vasil et al. (2019), used as documented.
- **Not the first spherical barotropic-instability eigenvalue calculation.** Skiba
  and co-workers have a sustained programme on exactly this.
- **Not the first quantification of divergent Rossby-mode dispersion.** That is the
  classical Hough literature.
- **Not a new observational diagnostic.** The Hayashi-style decomposition and the
  Doppler correction are both standard.
- **Not the counter-propagating-wave picture.** Bretherton's, and named by Hoskins
  et al.
- **Not a claim about baroclinic dynamics.** The model has one degree of freedom in
  the vertical and cannot represent baroclinic conversion.

## Limitations the paper must state itself

Every item here was found by this campaign's own adversarial steps. Each is
stated because a referee who finds it unstated has a stronger objection than a
referee who finds it acknowledged.

**L1. The stability analysis is nondivergent; the jet it describes is not — and
the resulting bias has been measured, by others.** The eigenvalue problem is posed
for the nondivergent barotropic potential-vorticity equation, while the nonlinear
runs integrate the divergent shallow-water system with `L_d ≈ 3×10⁶ m`, comparable
to the jet's own width.

This is not merely a scoping choice. Paldor, Shamir & Garfinkel (2020), *Geophys.
Astrophys. Fluid Dyn.* **115**(1), 15–34, compare barotropic-instability growth
rates for a zonal jet on the sphere across the nondivergent, quasi-geostrophic and
full shallow-water formulations. Per the authors' own EGU2020 abstract of that
work, shallow-water growth rates "can be smaller by more than 50%" than the
nondivergent prediction at mean depths of 5–10 km, with the formulations
converging only above 30 km, and layer depth controlling growth in a way
"completely lost in the ND equation". **This project uses `H = 10 km`, inside the
band where the discrepancy is largest.**

Two consequences the paper must carry. Growth rates are reported as *nondivergent
modal* growth rates, with the formulation bias named and cited. And the reported
precision drops accordingly: quoting `σ` to five significant figures, or
distinguishing `m = 6` from `m = 7` at 0.07%, is not defensible inside a >50%
formulation bias — the resolved band and the plateau are what the calculation
supports.

For the *stability boundary* rather than the growth rate, Ripa (1983) gives
sufficient conditions for the one-layer system on the β-plane or the sphere, and
White & Staniforth (2009), *QJRMS*, `10.1002/qj.504`, extend them to the sphere
with orography expressly to guide numerical model testing. Ripa's conditions
reduce cleanly to Rayleigh–Kuo in the nondivergent limit; divergence adds a second
gravity-wave criticality condition, which for this jet is satisfied with a 7.8×
margin at every rotation rate the project runs. The full analysis is in
`docs/literature/DIVERGENT_STABILITY_DECISION.md`.

**L2. A normal-mode spectrum is not a stability proof.** The linearised operator
is non-normal, so an all-real spectrum establishes asymptotic stability to
infinitesimal normal-mode disturbances and nothing more. Finite-time transient
growth is not excluded and is not claimed to be. H7 is a prohibition on *modal*
growth.

**L3. The initialised Rossby–Haurwitz waves may not be stable.** Thuburn & Li
(2000) show the zonal-wavenumber-4 shallow-water Rossby–Haurwitz wave is
dynamically unstable and breaks down if perturbed, with an e-folding time of order
1.3 days, and that the shallow-water case develops a potential-enstrophy cascade
absent from the nondivergent case. Phase speeds are therefore measured over a
stated window before breakdown, and that window is reported. This also means
Williamson et al.'s (1992) choice of the wavenumber-4 wave as a test case rests
on a stability belief that has since been overturned.

**L4. The `ε → 0` convergence rate is fitted outside the range where the
headline numbers are quoted.** The rate is measured over `ε ∈ [10⁻⁶, 10⁻²]`; the
reported slowings are at `ε ≈ 8.80`.

**L5. Several sources are cited without the full text having been read, and the
count is stated exactly.** Longuet-Higgins (1968) and Swarztrauber & Kasahara
(1985) are cited for the classical divergent-wave formulation on the strength of
their bibliographic records alone; both remain unobtainable after repeated
attempts, and Unpaywall confirms no open-access copy exists anywhere. Kasahara
(1976), obtained during this campaign and read, independently confirms the branch
structure but not the numbers.

For the divergent *stability* references the position improved in Session L4b
without reaching full text: Ripa (1983) and Hayashi & Young (1987) are
**ABSTRACT-VERIFIED** — the publisher's verbatim abstract was obtained for each,
and both state their central result explicitly enough to be used, but no page or
equation pointer is available and none is given. Paldor, Shamir & Garfinkel (2020)
is likewise cited from its authors' own conference abstract of the same work
rather than from the journal text, which is bronze open-access but blocked to
scripted retrieval; **obtaining that one paper is the highest-value literature
action remaining, and its >50% figure should be checked against the published text
before it is quoted in the manuscript.** All of this is stated rather than
concealed.

**L6. The Rhines scale is an arrest scale, not a jet-spacing law.** Rhines (1975)
presents `k_β = (β/2U)^{1/2}` as where the upscale cascade nearly ceases, and
separately notes the zonal-jet end state may not be reached when energy is
spatially intermittent. Any discussion of planetary banding must respect that
distinction, and must state which convention of the factor `√2` it uses.

**L7. The sectoral-mode result is not claimed as new.** The `n = m` family departs
systematically from the trend, and a structural mechanism is demonstrated for it,
but no prior-art search could be completed against the classical eigenstructure
literature because the relevant papers were unobtainable.

## Cross-reference

The evidence and the searches behind every verdict above are in
`docs/literature/DIALECTIC_CHALLENGE.md`. That document is the record; this one is
the conclusion.
