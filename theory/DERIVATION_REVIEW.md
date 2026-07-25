# Derivation review — operator sign-off required

**Session L3. Written 2026-07-25. Status: AWAITING SIGN-OFF.**

This document is self-contained. It can be read on its own, without
`theory/derivations.tex` open alongside it, and it is the thing to read before
deciding whether the theory is fit to be consumed as ground truth by
Session L5.

Contents, in the order the sign-off gate specifies:

1. [The spine, in plain language](#1-the-spine-in-plain-language)
2. [Verdict of every verification check](#2-verdict-of-every-verification-check)
3. [Modelling choices and assumptions requiring approval](#3-modelling-choices-and-assumptions-requiring-conscious-approval)
4. [Citations attributed by DOI rather than direct reading](#4-citations-attributed-by-doi-rather-than-direct-reading)
5. [Closing statement](#5-closing-statement)

---

## 1. The spine, in plain language

### The one statement everything comes from

A column of fluid on a rotating planet carries a label it cannot change:

```
    Dq/Dt = 0 ,        q = (ζ + f) / h
```

Here `ζ` is the column's own spin (relative vorticity), `f = 2Ω sin φ` is the
spin it has merely by sitting on a rotating planet (planetary vorticity), and
`h` is its depth. The quantity `q` is called potential vorticity because it is
the spin the column *would* have if it were squeezed to unit depth — the spin it
holds in potential, partly as rotation and partly as stretching.

Why is it conserved? Two older statements, divided into each other. Kelvin's
circulation theorem says the absolute circulation around a material loop is
constant, so `(ζ + f) × area` is fixed. Mass conservation says `h × area` is
fixed. Divide, the unknown area cancels, and `(ζ + f)/h` is fixed. That is the
whole derivation, and it is done before any coordinates appear, because the
physics should be understood before the bookkeeping.

Three consequences carry the rest of the document:

- **Displacement costs vorticity.** Push a column poleward and `f` rises. If the
  surface is stiff so `h` cannot change, `ζ` must fall by exactly as much.
- **That cost is what makes a wave.** The vorticity a chain of displaced columns
  acquires induces a flow that is a quarter wavelength out of phase with the
  displacement — and a quarter-phase forcing translates a pattern rather than
  growing it. The pattern moves west. Always.
- **When the background `q` stops being monotonic, the same cost makes an
  instability instead.** If `q` has an interior extremum, a displaced column no
  longer always finds more `q` ahead of it, and a disturbance can take energy
  from the flow rather than merely riding on it.

### How the twelve sections build on it

**§1 Physical setting and governing principle.** States what the shallow-water
system stands for — the barotropic (depth-independent) response of a stratified
layer, not its vertical structure — and derives `Dq/Dt = 0` from Kelvin plus
mass conservation, physically, before coordinates.

**§2 The rotating sphere as a curved manifold.** Only as much geometry as the
physics forces. The metric `ds² = R²dφ² + R²cos²φ dλ²`, its two non-zero
Christoffel symbols, and the divergence, curl and Laplacian they generate. The
payoff is that "westward" becomes a physical statement rather than a coordinate
accident, and that `∇²Y_n^m = −n(n+1)/R² Y_n^m` — the single fact that turns a
partial differential equation into an algebraic dispersion relation later.

**§3 Shallow-water equations and PV on the sphere.** The momentum and continuity
equations in vector-invariant form; the curl of the momentum equation; the
elimination of divergence between the two to give `Dq/Dt = 0` rigorously on the
sphere. Recorded in the sharper form `h Dq/Dt = curl(M) − q C`, an identity that
holds for *arbitrary* fields, so that PV conservation is visibly not an extra
assumption but a restatement of the equations of motion.

**§4 Nondimensionalisation.** Two numbers. The Rossby number `Ro = U/2ΩR` sets
how much the fluid's own vorticity matters against the planet's. Lamb's
parameter `ε = 4Ω²R²/(gH) = (R/L_d)²` appears in exactly one place — multiplying
the surface-height tendency in the continuity equation — and that placement *is*
its meaning: it measures how compliant the free surface is, hence how much of
the PV budget stretching can absorb. Earth, with `H = 10 km`, has `ε ≈ 8.80`.

**§5 Waves on a state of rest.** Take `ε → 0` so the surface is rigid. The
nondivergent barotropic vorticity equation follows, and a spherical-harmonic
mode gives the Rossby–Haurwitz angular phase speed `c_ang = −2Ω/[n(n+1)]`. The
sign is derived, not chosen: the displacement argument gives `c = −β/k² < 0` with
both `β` and `k²` positive, so westward is unconditional. A cancellation worth
noticing: the `cos φ` in `β` cancels the `1/cos φ` in the metric expression for
`v`, which is why the spherical answer depends on degree alone and carries no
residual latitude dependence.

**§6 The divergent correction: Laplace's tidal equations and Hough modes.**
Restore the free surface. Columns can now stretch, so part of the change in `f`
is paid for by stretching rather than by `ζ`, the restoring agent is diluted, and
the wave slows. The eigenvalue problem is posed in vorticity–divergence–height
variables rather than as the classical second-order tidal equation, because in
those variables it is *linear* in the frequency and regular everywhere, whereas
the classical form is nonlinear in the frequency and carries a spurious
coordinate singularity. Setting divergence and height to zero recovers §5
exactly — that is the validation target, a closed form the project derives for
itself rather than a table copied from elsewhere.

**§7 The Rhines scale.** Balancing the nonlinear term §5 discarded against the
linear restoring term gives `L_R ~ √(U/β)`. Physically it is the scale at which
the upscale turbulent cascade is arrested — and arrested *anisotropically*, since
`βv` acts only on meridional motion and a purely zonal flow feels no restoring
force at all. That is why energy piles up in zonally elongated jets. Because
`β ∝ Ω`, the blueprint's sixteen-fold `Ω` sweep moves `L_R` by a factor of four,
which reframes that sweep as a question about planetary regime rather than a
convergence exercise.

**§8 Instability of a zonal jet: Rayleigh–Kuo.** Linearise about `ū(φ)` instead
of about rest. A growing mode forces `∫ (dQ/dφ) |Ψ|²/|ū_a − c_a|² dφ = 0`, and
since the weight is strictly positive, `dQ/dy` must change sign somewhere.
Stated prominently in the text and repeated here: **this is necessary, not
sufficient.** As a prohibition it is powerful; as a prediction of instability it
says nothing.

**§9 The linear stability eigenvalue problem.** Turns §8 into a computation:
a generalised eigenvalue problem `A_m Ψ = c_a B_m Ψ` for the complex angular
phase speed at each zonal wavenumber, with growth rate `σ(m) = m Im(c_a)`. The
sphere has no boundaries, so what replaces boundary conditions is regularity at
the poles, imposed for free by expanding in spherical harmonics. The section
specifies the operator, the basis, the treatment of the critical layer (where
`ū_a = c_r`), and the resolution-doubling filter for spurious modes — enough
that Session L5's `evp_stability.py` has an unambiguous target to code against.

**§10 Instability as counter-propagating Rossby waves.** The physical heart. A
PV gradient concentrated at a single line supports an *edge wave*: §5's
mechanism restricted to one line, propagating to the left of its local gradient
at a speed `∝ 1/k`. Put two such lines with oppositely signed jumps a distance
apart, and each wave's inverted flow reaches the other. Growth requires
`Δ₁Δ₂ < 0` — the §8 sign change, reached as a phase-locking requirement rather
than as an integral identity — and requires the coupling to overcome the
differential advection. The section closes with the sentence the manuscript is
organised around: *the wave-propagation mechanism of §5 and the instability
mechanism of §8–9 are the same physics, viewed as one interface versus two.*

**§11 The Galewsky jet and its balanced initial condition.** The
gradient-wind integration that builds a balanced height field from a prescribed
zonal jet, plus the localised unbalanced perturbation that seeds growth. This is
the analytic groundwork for Session L5's `initial_conditions/galewsky.py`.

**§12 Hypotheses to equations.** A table mapping every blueprint hypothesis
H1–H10 to the numbered equation predicting it and to what would falsify it.

---

## 2. Verdict of every verification check

Seven scripts under `theory/sympy_checks/`. All seven report **VERIFIED**. Full
recorded output is in `theory/sympy_checks/output/`; the verbatim verdicts and
the substantive numbers are reproduced below.

**There are no unresolved discrepancies.** Nothing in this section is being held
back for operator adjudication on grounds of a symbolic or numerical mismatch.
The judgement calls are in §3 below instead, which is where the real risk lies.

| Script | Verdict | Substance |
|--------|---------|-----------|
| `check_spherical_laplacian_eigenvalue.py` | **VERIFIED** | Symbolic residual exactly zero for 8 pairs `(n,m)`; worst relative residual `7.03e-15` over `1 ≤ n ≤ 40`, `0 ≤ m ≤ 8` (tolerance `1e-9`) |
| `check_christoffel_symbols.py` | **VERIFIED** | All 8 components agree with the closed forms *and* with published 2-sphere values transported from colatitude; divergence formula and both momentum metric terms exact |
| `check_pv_conservation.py` | **VERIFIED** | `h Dq/Dt − curl(M) + qC = 0` exactly, symbolically, for arbitrary `u,v,h`; numeric spot-check residual `7.7e-180` |
| `check_rh_dispersion.py` | **VERIFIED** | `ω = −2Ωm/[n(n+1)]` exact for 9 pairs `(n,m)`; beta-term cancellation exact; sign derived from the displacement argument |
| `check_hough_epsilon_limit.py` | **VERIFIED** | Convergence rate `1.0000` (four figures) for every degree and order tested; see the detail below |
| `check_rayleigh_kuo.py` | **VERIFIED** | Necessary condition follows with no extra assumption; solid-body spectrum real to machine precision; Galewsky jet gives `m* = 6`, e-folding `0.56` days |
| `check_crw_two_interface.py` | **VERIFIED** | Reduces exactly to the published Rayleigh dispersion relation; `K_c = 1.2785`, `K_m = 0.7968`, peak growth `0.2012 × shear` |

### `check_hough_epsilon_limit.py` — convergence behaviour in detail

The gate item explicitly asks for the convergence *rate*, not a pass/fail at one
small `ε`. Errors are relative, against `σ₀ = −m/[n(n+1)]`:

| m | n | rel. err at ε=1e-2 | rel. err at ε=1e-6 | fitted d(log err)/d(log ε) |
|---|---|--------------------|--------------------|----------------------------|
| 1 | 2 | 9.18e-04 | 9.19e-08 | **0.9999** |
| 1 | 3 | 4.50e-04 | 4.50e-08 | **1.0000** |
| 1 | 5 | 1.73e-04 | 1.73e-08 | **1.0000** |
| 2 | 2 | 1.06e-04 | 1.06e-08 | **1.0000** |
| 2 | 3 | 3.01e-04 | 3.01e-08 | **1.0000** |
| 2 | 5 | 1.54e-04 | 1.54e-08 | **1.0000** |

First order is what the physics predicts: the fraction of the PV budget the
surface absorbs is proportional to its compliance, and the compliance is `ε`.
The rate is clean to four figures across two zonal orders and three degrees,
which is a stronger statement than the limit merely being approached.

Supporting arms: Legendre matrix elements agree with their closed-form
recurrences to `6.1e-13` and satisfy the integration-by-parts adjoint identity
`Dᵀ = −D + 2M` to `1.6e-13`; the answer moves by `4.3e-13` when the spectral
truncation is doubled from 40 to 80.

### `check_hough_epsilon_limit.py` — the H5 readout at Earth's ε

Not a pass/fail arm; a physical readout, obtained by following each Rossby
branch by continuation from `ε = 1e-6`:

| m | n | nondivergent σ | Hough σ | slowing |
|---|---|----------------|---------|---------|
| 1 | 2 | −0.166667 | −0.099366 | −40.4% |
| 1 | 3 | −0.083333 | −0.060134 | −27.8% |
| 1 | 5 | −0.033333 | −0.028895 | −13.3% |
| 1 | 8 | −0.013889 | −0.013071 | −5.9% |
| 2 | 2 | −0.333333 | −0.308288 | −7.5% |
| 2 | 3 | −0.166667 | −0.133662 | −19.8% |
| 2 | 5 | −0.066667 | −0.058738 | −11.9% |
| 2 | 8 | −0.027778 | −0.026213 | −5.6% |

Every mode is slowed, and within each `m` the fractional slowing falls as `n`
rises — large scales, closest to the deformation radius, are affected most. One
entry departs from that pattern and is flagged in §3 item (g): the `m = 2, n = 2`
sectoral mode is slowed by only 7.5%, less than `m = 2, n = 3`.

### `check_rayleigh_kuo.py` — the growth-rate spectrum

Solid-body rotation (`U₀ = 40 m/s`, no sign change in `dQ/dφ`): every eigenvalue
real to machine precision at `m = 1…6`, `max|Im c_a|/spread(Re c_a) = 0`
exactly. This is H7 as a prohibition, and it holds.

Galewsky jet (`dQ/dφ` changes sign at 32.20°, 39.79°, 49.82°, 58.16°N):

| m | growth `m·Im(c_a)` [1/s] | e-folding [days] | change on doubling N | resolved? |
|---|--------------------------|------------------|----------------------|-----------|
| 1 | 2.988e-06 | 3.873 | 2.75e-05 | yes |
| 2 | 5.710e-06 | 2.027 | 7.79e-05 | yes |
| 3 | 7.551e-06 | 1.533 | 2.91e-04 | yes |
| 4 | 1.483e-05 | 0.780 | 3.56e-08 | yes |
| 5 | 1.889e-05 | 0.613 | 2.63e-08 | yes |
| **6** | **2.075e-05** | **0.558** | 4.84e-07 | yes |
| 7 | 2.073e-05 | 0.558 | 1.47e-05 | yes |
| 8 | 1.891e-05 | 0.612 | 1.96e-04 | yes |
| 9 | 1.516e-05 | 0.763 | 1.97e-03 | **no** |
| 10–12 | — | — | 9.9e-02 … 3.5e-01 | **no** |

`m* = 6`, though `m = 7` is within 0.1% of it — see §3 item (e).

---

## 3. Modelling choices and assumptions requiring conscious approval

Session L3 raised ten judgement items here. Every one now carries an explicit
disposition — **Resolved (no issue found)**, **Resolved (fixed)**, or **Accepted
as a stated limitation**. None is left in a bare "flagged" state.

| # | Item | Disposition | Evidence |
|---|------|-------------|----------|
| (a) | The two-interface CRW model does not predict `m*` for a smooth jet: toy model gives `m* ≈ 1.8`, solved EVP gives `m* ≈ 6` | **Accepted as a stated limitation** | Detail below |
| (b) | Numerical tolerances chosen in the verification suite | **Accepted as a stated limitation** | Table below; all eight named in-script |
| (c) | Spurious-mode filter: an earlier `N=48`/`1e-4` setting reported the Galewsky jet stable | **Resolved (fixed)** | `N=240/480`, tol `1e-3`; commit `e4fd533` |
| (d) | Where the sphere was asserted to behave like the flat plane | **Resolved (no issue found)** | `check_rayleigh_kuo.py` arm 2 verifies the integration-by-parts identity symbolically; the one genuine distinction is stated below |
| (e) | `m*=6` and `m*=7` differ by 0.07%, so naming a single `m*` overstates resolution | **Resolved (fixed)** | `check_rayleigh_kuo.py` now reports the plateau; §9 and §12 of `derivations.tex` updated |
| (f) | The Rhines scale carries a factor-of-√2 convention ambiguity | **Accepted as a stated limitation** | Both conventions stated in §7; nothing depends on the constant |
| (g) | The `(m=2, n=2)` entry of the H5 table departs from the trend | **Resolved (no issue found — explained)** | Not an anomaly: *every* sectoral mode behaves this way, for a structural reason demonstrated causally. `check_hough_epsilon_limit.py` arm 5 |
| (h) | The model represents the barotropic response only, not baroclinic conversion | **Accepted as a stated limitation** | Stated in §1 and inherited by every later claim |
| (i) | §6 solves the vorticity–divergence–height form, not the classical second-order tidal equation | **Accepted as a stated limitation** | Equivalent formulation, better conditioned; validated by the `ε→0` limit |
| (j) | Branch continuation, not nearest-frequency matching, at large `ε` | **Resolved (fixed)** | Nearest matching gave a demonstrably wrong table; continuation used; commit `e4fd533` |

The four items accepted as limitations, and the three whose resolution needs
detail, are set out below.

### (a) The two-interface CRW model does not predict `m*` for a smooth jet
**Accepted as a stated limitation.**

The toy model of §10 is an *exact* reduction for piecewise-constant potential
vorticity — it reproduces the dispersion relation and the three benchmark
constants of Heifetz, Bishop & Alpert (1999) to three or four figures. But
mapping it to a spherical zonal wavenumber requires an effective interface
half-separation `b_eff` that the model does not supply for a jet whose PV
gradient reverses smoothly over a band rather than jumping at a line. The most
natural choice (`b_eff = 1001 km`, half the separation between the centres of the
two reversed-gradient bands) gives `m* ≈ 1.8` against the solved eigenvalue
problem's `m* ≈ 6`. **They disagree by a factor of about three, and this was not
tuned away.** Two physical reasons are identified: concentrating each gradient
into a delta function maximises the long-range reach of the inverted flow and so
biases the optimum toward longer waves; and the Galewsky jet has *three* gradient
regions, not two, so a two-interface reduction omits an interacting wave.

**What is being accepted:** §10 claims the mechanism, the opposite-sign
requirement, both cutoffs, and the *scaling* `m* ∝ cos φ_j / b_eff` — and claims
nothing about the absolute value of `m*`, which §9 supplies. Anywhere §10's
result is later used in the manuscript it must be stated exactly that carefully.

### (b) Numerical tolerances
**Accepted as a stated limitation.** Every tolerance is a named constant at the
top of its script.

| Constant | Value | Where | Meaning |
|----------|-------|-------|---------|
| `NUMERIC_RTOL` | 1e-9 | Laplacian | Residual normalised by the largest single term |
| `MATRIX_ATOL` | 1e-12 | Hough arm 1 | Machine-precision claim for the Legendre matrix elements |
| `TRUNCATION_RTOL` | 1e-10 | Hough arm 2 | Relative movement in σ on doubling the truncation |
| `RATE_WINDOW` | (0.90, 1.10) | Hough arm 3 | Admits only first order; excludes half and second. Observed 1.0000 |
| `SMALLEST_EPS_RTOL` | 1e-5 | Hough arm 3 | Stops a clean power law through uniformly large errors passing on rate alone |
| `STABLE_IMAG_RTOL` | 1e-8 | Rayleigh–Kuo 4a | Imaginary parts scaled by the spread of real parts. Observed exactly 0 |
| `PERSIST_RTOL` | 1e-3 | Rayleigh–Kuo 4b | Resolution-doubling filter — see (c) |
| `PUBLISHED_TOL` | 0.01/0.05/0.01 | CRW | Agreement with HBA99 p. 2838, at the precision that page states |

Only `RATE_WINDOW` and `PERSIST_RTOL` carry real judgement; the rest are
machine-precision claims that either hold or do not.

### (c) The spurious-mode filter
**Resolved (fixed), Session L3, commit `e4fd533`.**

Worth recording because the earlier choice gave a **materially wrong answer**. A
first pass used `N = 48` doubled to 96 with tolerance `1e-4` on the full complex
eigenvalue. That rejected *every* unstable mode and reported the Galewsky jet
stable — contradicting the Phase-0 gate, where roll-up was observed. The cause
was insufficient resolution, not absent physics: at `N = 48` the unstable
eigenvalue had not converged, so it failed its own persistence test. At
`N = 240/480` growth rates for `m ≤ 8` are stable to between `3.6e-08` and
`2.0e-04`, while `m ≥ 9` move by `2e-03` or more — a clean two-decade gap with
the threshold inside it.

*Standing caution:* the threshold is a choice placed inside a gap, not derived.
A later session that changes the base state must re-inspect the gap rather than
reuse the number.

### (d) Where the sphere was asserted to behave like the flat plane
**Resolved (no issue found).** The accounting is in two parts.

- **The background PV gradient is *not* the flat-plane expression.** On a plane
  `dQ/dy = β − d²ū/dy²`; on the sphere the `cos φ` factors survive and the
  curvature term is not a bare second derivative. §8 writes the spherical form
  explicitly. This changes *where* the criterion is met.
- **The structure of the argument *is* unchanged, and this was checked, not
  assumed.** `check_rayleigh_kuo.py` arm 2 verifies the integration-by-parts
  identity symbolically and confirms both quadratic terms are real and
  non-negative. Regularity at the poles kills the boundary term — the role walls
  play in the flat-channel argument.

**One genuine physical distinction remains, and it must propagate to Session
L5:** on the sphere the eigenvalue is the *angular* phase speed `c_a`, and the
critical layer is where `ū_a(φ) = c_r` — where the base flow's angular velocity
matches the mode's, not where `ū = c` in metres per second. `evp_stability.py`
must not carry over a flat-plane critical-layer criterion in linear units.

### (e) The growth-rate plateau
**Resolved (fixed), this session.** Growth rates are `2.0748e-05` at `m = 6` and
`2.0734e-05` at `m = 7` — 0.07% apart, far below any physical uncertainty in the
base state. `check_rayleigh_kuo.py` now reports the plateau explicitly ("within
1% of the peak: m = 6, 7"), and §9 and §12 of `derivations.tex` state
`m* ≈ 6`, on a plateau spanning `m = 6–7`, rather than a sharp `m* = 6`.

### (f) The Rhines-scale constant
**Accepted as a stated limitation.** §7 derives `L_R ~ √(U/β)` from a scaling
balance, which fixes the form but not the constant. Rhines' own arrest
wavenumber is `k_β = (β/2U)^{1/2}`, i.e. `L_R = (2U/β)^{1/2}`, a factor √2
larger. §7 states both. Vallis & Maltrud reach the same `O(√(U/β))` scale by a
different route and note the particular form is not crucial to their argument.

**What is being accepted:** any quantitative comparison of a measured jet spacing
against `L_R` in the discussion must state its convention. Nothing in this
document depends on the constant, and the `Ω^{-1/2}` scaling the campaign
actually tests is convention-independent.

### (g) The sectoral-mode entry in the H5 table
**Resolved (no issue found — explained), this session.** Session L3 left this as
an unexplained outlier. It is neither an outlier nor numerical.

*It is not numerical.* The value is invariant to the continuation ladder length
(30 → 1500 steps), to the matching method (eigenvalue proximity vs eigenvector
overlap), and to the spectral truncation (`N` = 30, 60, 120) — identical to eight
decimal places in every case.

*It is not an outlier.* **Every** sectoral mode `n = m` behaves this way, for
`m = 1…6` without exception; the sectoral mode is always less slowed than its
`n = m + 1` neighbour. Session L3's table simply happened to start its `m = 2`
row at the sectoral minimum and its `m = 1` row at the non-sectoral maximum.

*The cause, demonstrated causally.* The Coriolis coupling matrix is tridiagonal —
it connects degree `n` only to `n ± 1`. A sectoral mode sits at the bottom of the
degree ladder (`n ≥ m`), so it has only **one** neighbour to couple through
instead of two: half the channels by which its rotational flow can be converted
into divergence and surface displacement. The test: take a non-sectoral mode and
delete its lower neighbour from the basis, leaving its latitudinal structure
untouched. Its slowing collapses to sectoral values.

| m | n | full basis | lower partner removed | true sectoral (n=m) |
|---|---|-----------|----------------------|---------------------|
| 1 | 2 | −40.38% | −10.90% | −15.78% |
| 2 | 3 | −19.80% | −6.44% | −7.51% |
| 3 | 4 | −10.45% | −3.98% | −4.00% |

A secondary effect is also present and consistent: slowing correlates with the
*local* Burger parameter `ε⟨sin²φ⟩/n(n+1)` — the squared ratio of the mode's
scale to the deformation radius `√(gH)/|f|` at its characteristic latitude
(Pearson r = 0.74 over 30 modes). Sectoral modes, being equatorially confined,
sit where that local deformation radius is largest. Both effects push the same
way. Recorded in `check_hough_epsilon_limit.py` arm 5 and in §6 of the
derivation.

### (h) Model scope
**Accepted as a stated limitation.** The shallow-water system models the
**barotropic** response of a stratified layer. One vertical degree of freedom
means no baroclinic conversion. §1 says so explicitly.

**What is being accepted:** every later claim about the atmosphere inherits this
limit, including the observational comparison — which matters because the
observed 500 hPa wave field contains eastward-moving baroclinic disturbances the
system does not describe. The Doppler-correction protocol in
`docs/CONVENTIONS.md` already handles the consequence.

### (i) The form of the §6 eigenvalue problem
**Accepted as a stated limitation.** §6 deliberately does not solve the classical
second-order Laplace tidal equation for `N(μ)`: that form is nonlinear in the
frequency and carries a coordinate singularity wherever `μ² = σ²`. §6 poses the
system in vorticity–divergence–height variables, where it is linear in the
frequency and regular everywhere.

**What is being accepted:** this is a better-conditioned formulation of the same
problem, not a different problem, and the `ε → 0` check validates the one
actually used — but the project's intermediate quantities will not look like
those of Longuet-Higgins or Swarztrauber & Kasahara.

### (j) Branch continuation at large ε
**Resolved (fixed), Session L3, commit `e4fd533`.** Nearest-frequency matching at
the target `ε` **produced a wrong answer**: it assigned one eigenvalue to both
`n = 2` and `n = 3` at `m = 1`, and reported `n = 3` as 19% *faster* than
nondivergent. By Earth's `ε` the Rossby frequencies of neighbouring degrees are
too close for bare nearest matching to be a valid labelling. Continuation from
`ε = 1e-6` is used instead. Independently re-confirmed this session against
eigenvector-overlap tracking, which agrees to eight decimal places.

*Standing caution:* Session L5 must use continuation, not nearest matching, when
labelling Hough modes by degree at finite `ε`.

## 4. Citations attributed by DOI rather than direct reading

Eleven works are cited in `theory/derivations.tex`. The grounding of each:

### Read directly from the PDF in `docs/literature/`

| Citation | How read | Used for |
|----------|----------|----------|
| Bretherton (1966) | Image scan, pages 1–6 read visually | §9 critical layer; §10 the delta-function equivalence that makes the edge-wave idealisation exact |
| Galewsky, Scott & Polvani (2004) | Text layer | §11 jet profile, balance integration, perturbation |
| Heifetz, Bishop & Alpert (1999) | Text layer | §10 the CRW phase-locking picture and the Rayleigh-model dispersion relation |
| Hoskins, McIntyre & Robertson (1985) | Text layer | §10 PV inversion |
| Kuo (1949) | Image scan, pages 1–6 read visually | §8 the necessary condition |
| Rhines (1975) | Text layer | §7 the arrest wavenumber `k_β = (β/2U)^{1/2}` |
| Rossby (1939) | Image scan, page 1 read visually (identity confirmed) | §5 attribution |
| Vallis & Maltrud (1993) | Image scan, page 1 read visually (abstract and introduction) | §7 the `O(√(U/β))` transition scale |

### Attributed by DOI, not read

| Citation | DOI | Why, and what depends on it |
|----------|-----|------------------------------|
| Longuet-Higgins (1968) | `10.1098/rsta.1968.0003` | **Could not be obtained** — recorded in `docs/literature/MISSING.md`. Cited in §6 for the classical formulation only. Nothing in the derivation depends on it: the validation target is the internal `ε → 0` limit, not a published table. |
| Swarztrauber & Kasahara (1985) | `10.1137/0906033` | **Could not be obtained** — same record. Cited in §6 for the vector-harmonic treatment only. Same independence. |
| Haurwitz (1940b) | none (pre-DOI) | **Not present in `docs/literature/`.** See the warning below. |

### Two preflight findings about the literature directory that must be recorded

**1. The file named `haurwitz_1940_motion_of_atmospheric_disturbances.pdf` is not
the paper the project's index says it is.** It is Haurwitz (1940),
*The motion of atmospheric disturbances*, J. Mar. Res. **3**(1), 35–50 — the
**beta-plane, finite-lateral-extent** extension of Rossby (1939). Its own text
says the spherical case "will be given in a later paper." The paper that
actually contains the spherical Rossby–Haurwitz result is Haurwitz (1940),
*The motion of atmospheric disturbances on the spherical earth*, J. Mar. Res.
**3**(3), 254–267, and **that paper is not in `docs/literature/`.** §5 cites it
for attribution of `c_ang = −2Ω/[n(n+1)]`. The derivation does not depend on
having read it — §5 derives the result from first principles and
`check_rh_dispersion.py` verifies it symbolically — but the attribution is
bibliographic rather than checked against the primary source.

**2. The file named `heifetz_2004_counter_propagating_rossby_waves.pdf` is
Heifetz, Bishop & Alpert (1999)**, QJRMS **125**(560), 2835–2853, not the 2004
Heifetz–Methven–Hoskins–Bishop paper the session brief names. The 1999 paper is
the one actually read and the one cited; §10's toy model is validated against
its published dispersion relation and numbers. Heifetz et al. (2004) is *not*
cited, since it was neither read nor needed.

*Operator decision required:* both filenames should be corrected in
`docs/literature/README.md`, and Haurwitz (1940b) added to the fetch list. That
is a documentation fix outside this session's scope; flagged rather than done.

### Textbooks named in the session brief that are absent

`pedlosky_1987_gfd.pdf` and `vallis_2017_aofd.pdf` are listed in
`docs/literature/README.md` but are not present in the directory. **No claim in
`theory/derivations.tex` is attributed to either.** Where a standard textbook
result was needed — the 2-sphere Christoffel symbols — it was verified
computationally against the published colatitude forms instead of cited
(`check_christoffel_symbols.py`, arm 2).

### DOI resolution

All nine DOIs in the bibliography were confirmed **registered** against the
Crossref REST API. Six additionally resolve on a live `HEAD` request. Two —
the AMS legacy identifiers for Kuo (1949) and Vallis & Maltrud (1993) — return
HTTP 403 to an unauthenticated `HEAD`, which is publisher access control, not a
missing record. `scripts/refcheck.py` treats any status ≥ 400 as a failure and
will flag these two when Session L4 creates `manuscript/references.bib`; that is
a false negative in the checker. Recorded in `theory/README.md`.

`make refcheck` was run and correctly reports "no bibliography file yet;
nothing to check" — `manuscript/references.bib` arrives in Session L4. The
equivalent check was therefore done by hand: all 11 `\cite` keys resolve to a
`\bibitem`, no `\bibitem` is uncited, and the DOI verification above was
performed independently.

---

## 5. Closing statement

```
THIS DOCUMENT REQUIRES OPERATOR SIGN-OFF BEFORE SESSION L5 MAY BEGIN.
SESSION L5 CONSUMES theory/derivations.tex AS GROUND TRUTH FOR THE SOLVER'S
GOVERNING EQUATIONS AND INITIAL CONDITIONS. NO FURTHER AUTOMATED SESSION IN
THIS PROJECT MAY PROCEED UNTIL THIS REVIEW HAS BEEN READ AND EXPLICITLY
APPROVED BY THE OPERATOR.
```
