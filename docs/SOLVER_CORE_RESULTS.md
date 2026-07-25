# Solver core — what it was checked against, and what it said

**Session L5, 2026-07-25.** This records the numbers, not the code. It exists
because the solver's credibility rests on a small number of comparisons against
things computed independently of it, and those comparisons should be readable in
one place rather than reconstructed from run directories.

Everything below was produced by `src/solver/`. Nothing here is a campaign result:
the verification gate of blueprint §9.4 has *not* been claimed, and the three
simulation runs are proof runs at a single resolution each.

---

## 1. The blocking check: Williamson case 2 stays steady

Case 2 is an exact steady solution of the full nonlinear shallow-water equations,
so the correct time derivative is identically zero and every observed tendency is
error. Integrated for one hour with the dissipation switched off:

| Resolution | max &#124;Δh&#124; / range(h) | max &#124;Δu&#124; / max&#124;u&#124; |
|------------|------------------------------|-------------------------------------|
| L0 (64×32) | 3.2 × 10⁻¹⁵ | 2.3 × 10⁻¹⁴ |
| L1 (256×128) | 5.9 × 10⁻¹⁴ | 3.4 × 10⁻¹³ |

on a height field whose own range is 1890 m. This is round-off. It exercises the
Coriolis sign, both metric terms, the pressure gradient, the mass flux and the
balance between the wind and height fields simultaneously — get any one of them
wrong and this number is not small. `tests/test_solver_core.py::
test_williamson_case2_is_steady` enforces it at 10⁻¹¹.

## 2. Proof run V-02 — conservation and error norms

Five days at L0 with the campaign's hyperdiffusion (`ν₄ = 3.964 × 10¹⁵ m⁴ s⁻¹`).

| Quantity | Relative drift over 5 days | Blueprint §9.3 criterion | Verdict |
|----------|---------------------------|--------------------------|---------|
| Mass | −1.5 × 10⁻¹⁶ | below 10⁻¹⁰ | **met** |
| Energy | −4.3 × 10⁻⁵ | small, decreasing with resolution | decaying, consistent with ν₄ |
| Potential enstrophy | −1.8 × 10⁻⁵ | monotonic decay acceptable, growth is not | **decaying** |

Error against the analytic solution at day 4: `l₂(h) = 2.3 × 10⁻⁵`,
`l∞(h) = 2.8 × 10⁻⁵`, i.e. a maximum departure of 3.5 cm on a 1890 m field. Note
that with ν ≠ 0 case 2 is no longer *exactly* steady — the hyperdiffusion damps
it — so this norm bounds discretisation error plus the dissipation the campaign
deliberately runs with, and is not the ν = 0 number in §1.

## 3. Proof run P-17 — the divergent correction, measured twice

**This is the strongest cross-check in the session**, because the two numbers come
from genuinely different mathematics: a nonlinear time integration of the
divergent shallow-water equations, and a linear eigenvalue problem for Laplace's
tidal equations.

P-17 initialises a single spherical-harmonic Rossby–Haurwitz mode at degree
`n = 4`, order `m = 2`, peak wind 1 m s⁻¹, and runs 20 days at L0. Fitting the
phase of the `m = 2` Fourier component of the height field at 45° N:

```
measured angular phase speed      c_ang = -6.1457e-06 rad/s      (westward)
nondivergent prediction, eq. (rhdisp)   = -7.2920e-06 rad/s
                                  ratio = 0.8428  ->  15.72% slower
```

The divergent Hough eigenvalue problem, solved independently at Earth's Lamb
parameter ε = 8.8044 by `src/solver/evp_hough.py`, gives for the same `(m, n)`:

```
sigma_nondivergent = -0.100000      sigma_Hough = -0.084233      -15.77%
```

**−15.72% measured against −15.77% predicted**, a discrepancy of 0.05 percentage
points. The free surface slows the wave, by the amount the eigenvalue problem says
it should. Hypothesis H5 is a curve here rather than an assertion.

The mode's amplitude fell by 6.2% over the twenty days, so the measurement is a
phase drift of a decaying but otherwise clean single mode.

## 4. Proof run I-00 — the Galewsky instability, and the bias that comes with it

Fifteen days at L1, the anchor barotropic-instability benchmark. Eddy enstrophy
grows exponentially from day 1, saturates around day 6–7 and decays thereafter as
the jet rolls up — the behaviour Galewsky, Scott & Polvani (2004) describe.

Decomposing the eddy enstrophy by zonal wavenumber and fitting `exp(2σt)` over
days 2.25–5.25:

| Zonal wavenumber m | Growth rate σ (s⁻¹) | e-folding (days) | Share of eddy enstrophy at day 5 |
|---|---|---|---|
| 5 | 1.24 × 10⁻⁵ | 0.93 | 0.221 |
| **6** | **1.41 × 10⁻⁵** | **0.82** | **0.282** |
| 7 | 1.26 × 10⁻⁵ | 0.92 | 0.041 |

**The dominant wavenumber is m = 6**, which is what
`theory/derivations.tex` §9 predicts from the nondivergent eigenvalue problem
(`m* ≈ 6`). The prediction was made before this run existed.

The *rate* is a different matter, and the difference is the point. §9 gives
σ(m*) = 2.07 × 10⁻⁵ s⁻¹; the divergent nonlinear run gives 1.41 × 10⁻⁵ s⁻¹ for
m = 6. **The nondivergent calculation is 48% higher.** That is the direction and
roughly the magnitude of the formulation bias Paldor, Shamir & Garfinkel (2020)
report — nondivergent overestimates, one-signed — and it is the reason
`docs/literature/DIVERGENT_STABILITY_DECISION.md` requires that qualification to
travel with every modal growth rate this project publishes.

**Read that comparison carefully.** It is *not* modal-against-modal. The measured
number is a nonlinear growth rate from one particular perturbation, at one
resolution, with hyperdiffusion acting; the predicted number is a clean modal rate
of a nondivergent operator. The agreement in `m*` is a genuine test. The 48% is
consistent with the published bias, not a measurement of it, and no session should
quote it as one.

## 5. Extension B — the Hough sweep reproduces the derivation's table

`src/solver/evp_hough.py` is a production reimplementation of the operator
`theory/sympy_checks/check_hough_epsilon_limit.py` verifies. At Earth's ε, on the
rows the two share:

| m | n | derivation §6 | `evp_hough` | |
|---|---|---|---|---|
| 1 | 2 | −40.38% | −40.38% | |
| 1 | 3 | −27.84% | −27.84% | |
| 1 | 5 | −13.32% | −13.32% | |
| 2 | 2 | −7.51% | −7.51% | ← sectoral |
| 2 | 3 | −19.80% | −19.80% | |
| 2 | 5 | −11.89% | −11.89% | |
| 2 | 8 | −5.63% | −5.63% | |

and as ε → 10⁻⁶ every tracked branch returns to `−m/[n(n+1)]` to better than
10⁻⁵ relative. The sectoral rows (n = m) are slowed far less than their
neighbours at every m — 2.34% at (4,4) against 6.10% at (4,6) — which is §6.5's
result, and is a consequence of a sectoral mode having one Coriolis coupling
partner instead of two rather than of anything about the solver.

## 6. Extension C — the stability sweep, and where "necessary" stops

`src/solver/evp_stability.py` reproduces `theory/derivations.tex` eq.
(galewskygrowth) exactly: **m\* = 6, σ = 2.0748 × 10⁻⁵ s⁻¹, e-folding 0.56 days**
on the Galewsky jet at truncation 240/480. That is a different piece of code from
`check_rayleigh_kuo.py` landing on the same numbers.

Run across the shear ladder, it also locates something the Rayleigh–Kuo criterion
cannot:

| Run | S | u_max (m/s) | Rayleigh–Kuo sign change | Resolved growing mode | Ripa certifies stable |
|-----|---|-------------|--------------------------|-----------------------|------------------------|
| I-01 | 0.05 | 4 | no | none | **yes** |
| I-02 | 0.10 | 8 | yes | **none** | no (silent) |
| I-03 | 0.25 | 20 | yes | m\* = 7, σ = 3.52 × 10⁻⁶ s⁻¹ | no (silent) |
| I-04 | 0.50 | 40 | yes | m\* = 7, σ = 9.45 × 10⁻⁶ s⁻¹ | no (silent) |
| I-05 / I-00 | 1.00 | 80 | yes | m\* = 6, σ = 2.07 × 10⁻⁵ s⁻¹ | no (silent) |

The necessary condition is first met at **S = 0.0728** (closed form, from
`jet_family.critical_shear_parameter`) — but no normal mode grows there. Between
S = 0.10 and S = 0.25 the criterion has been satisfied for some time and the flow
still has no growing mode. **That gap is exactly what "necessary but not
sufficient" means, located rather than merely stated**, and it is the reason the
ladder does not stop at the threshold.

The Ripa column is the other half of the logic. At S = 0.05 the potential-vorticity
gradient is single-signed, a constant `c₀` above the jet's peak speed satisfies
condition (i), and the gravity-wave criticality condition (ii) holds with a margin
of 78×, so the flow is *certified stable* by a genuinely sufficient condition. For
every rung above it, condition (i) fails and Ripa's theorem says **nothing at
all** — which is not the same as saying the flow is unstable, even where it is.

## 7. Known limitations of this session's results

- **Three proof runs, one resolution each.** No convergence study, no error
  norms across the ladder, no verification gate claimed.
- **V-01 has never been run.** The advection-only problem is implemented
  (`build_problem(..., advection=True)`) but no case-1 integration was performed.
- **I-10 cannot run.** It needs the smoothed reanalysis profile that
  `src/analysis/process_reanalysis.py` produces in Session L6; the initial
  condition refuses to invent one, and refuses an unsmoothed profile outright,
  because a second derivative of raw reanalysis is noise.
- **The Läuter case is implemented but unrun.** Its signs are validated against
  the α = 0 reduction to Williamson case 2, not against a time integration.
- **The `physical.H` correction to four verification configs changes their
  meaning**, from a 10 km ocean to the depth each case actually specifies. The
  equations were exact either way; the split between implicit and explicit terms
  was not.
- **P-18 is now one point of a two-point hyperdiffusion sensitivity**, at ten
  times the standard coefficient, paired against P-03. A single config could not
  measure a sensitivity, and leaving it identical to P-03 would have been a run
  that did nothing. The wider bracket belongs to Session L7's sweep generator.
- **The mean-depth warning is not wired to a failure.** A config whose `H` does
  not describe its case still runs; the harness says so on stderr and in the
  provenance record. That is deliberate — the run is well posed — but it means a
  reader has to look at `warnings` rather than at the exit code.
