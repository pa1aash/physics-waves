# Run registry

Master index of every run ID. Run IDs are immutable once a run has
executed. Status advances from `not started` as each run completes. Row
counts in the phase-speed and instability campaigns are provisional until the
first L0 exploratory runs (blueprint section 8 revision notes).

**Phase-0 gate.** The toolchain-validation gate (blueprint Phase 0) was executed
on 2026-07-25 and **PASSED** — see `tests/phase0_gate/` (`GATE_RESULTS.md`). It is
a prerequisite for every run below, not a run itself, so it carries no run ID: it
validates that Dedalus correctly solves the rotating shallow-water instability on
the sphere before any project run consumes compute.

Sub-questions (blueprint section 3.2): **SQ1** dispersion-relation theory · **SQ2** verification and convergence · **SQ3** phase speed vs wavenumber and rotation · **SQ4** meridional structure and observational comparison · **SQ5** jet instability.

| Run ID | Campaign | Purpose | Initial condition | Resolution | Varies | Measured | Sub-question | Status |
|--------|----------|---------|-------------------|------------|--------|----------|--------------|--------|
| V-01 | verification | Advection accuracy — Williamson case 1 (cosine-bell advection across the poles) | williamson_1 | L0 | Resolution | l2, l-inf vs analytic | SQ2 | not started |
| V-02 | verification | Steady-state accuracy — Williamson case 2 (steady nonlinear geostrophic flow) | williamson_2 | L0 | Resolution | l2, l-inf vs analytic | SQ2 | not started |
| V-03 | verification | Topographic forcing — Williamson case 5 (zonal flow over an isolated mountain) | williamson_5 | L1 | Resolution | l2, l-inf vs L3 reference | SQ2 | not started |
| V-04 | verification | Reference generation — Williamson case 5 at L3 | williamson_5 | L3 | — | Case-5 reference fields | SQ2 | not started |
| V-05 | verification | Rossby-Haurwitz fidelity — Williamson case 6 | williamson_6 | L1 | Resolution | l2, l-inf vs L3 reference | SQ2 | not started |
| V-06 | verification | Reference generation — Williamson case 6 at L3 | williamson_6 | L3 | — | Case-6 reference fields | SQ2 | not started |
| V-07 | verification | Convergence study — Williamson case 2 across the resolution ladder | williamson_2 | L0 | Truncation | Error vs N_theta, convergence order | SQ2 | not started |
| V-08 | verification | Conservation audit — Williamson case 6 | williamson_6 | L1 | Resolution | Drift in mass, energy, potential enstrophy | SQ2 | not started |
| V-09 | verification | Unsteady analytic solution — Lauter, Handorf & Dethloff (2005) | lauter | L0 | Resolution | Error norms vs unsteady analytic solution | SQ2 | not started |
| P-01 | phase_speed | Wavenumber dependence — single Rossby-Haurwitz mode, degree n=2 | single_harmonic | L1 | degree n (=2) | c, c_ang | SQ3 | not started |
| P-02 | phase_speed | Wavenumber dependence — single Rossby-Haurwitz mode, degree n=3 | single_harmonic | L1 | degree n (=3) | c, c_ang | SQ3 | not started |
| P-03 | phase_speed | Wavenumber dependence — single Rossby-Haurwitz mode, degree n=4 | single_harmonic | L1 | degree n (=4) | c, c_ang | SQ3 | not started |
| P-04 | phase_speed | Wavenumber dependence — single Rossby-Haurwitz mode, degree n=5 | single_harmonic | L1 | degree n (=5) | c, c_ang | SQ3 | not started |
| P-05 | phase_speed | Wavenumber dependence — single Rossby-Haurwitz mode, degree n=6 | single_harmonic | L1 | degree n (=6) | c, c_ang | SQ3 | not started |
| P-06 | phase_speed | Wavenumber dependence — single Rossby-Haurwitz mode, degree n=7 | single_harmonic | L1 | degree n (=7) | c, c_ang | SQ3 | not started |
| P-07 | phase_speed | Wavenumber dependence — single Rossby-Haurwitz mode, degree n=8 | single_harmonic | L1 | degree n (=8) | c, c_ang | SQ3 | not started |
| P-08 | phase_speed | Rotation dependence — degree n=4, Omega=0.25 Omega0 | single_harmonic | L1 | Rotation rate Omega | c, c_ang | SQ3 | not started |
| P-09 | phase_speed | Rotation dependence — degree n=4, Omega=0.5 Omega0 | single_harmonic | L1 | Rotation rate Omega | c, c_ang | SQ3 | not started |
| P-10 | phase_speed | Rotation dependence — degree n=4, Omega=1.0 Omega0 | single_harmonic | L1 | Rotation rate Omega | c, c_ang | SQ3 | not started |
| P-11 | phase_speed | Rotation dependence — degree n=4, Omega=2.0 Omega0 | single_harmonic | L1 | Rotation rate Omega | c, c_ang | SQ3 | not started |
| P-12 | phase_speed | Rotation dependence — degree n=4, Omega=4.0 Omega0 | single_harmonic | L1 | Rotation rate Omega | c, c_ang | SQ3 | not started |
| P-13 | phase_speed | Linearity check — degree n=4, initial-amplitude step 1 of 3 | single_harmonic | L1 | Initial amplitude A0 | c, departure from linear | SQ3 | not started |
| P-14 | phase_speed | Linearity check — degree n=4, initial-amplitude step 2 of 3 | single_harmonic | L1 | Initial amplitude A0 | c, departure from linear | SQ3 | not started |
| P-15 | phase_speed | Linearity check — degree n=4, initial-amplitude step 3 of 3 | single_harmonic | L1 | Initial amplitude A0 | c, departure from linear | SQ3 | not started |
| P-16 | phase_speed | Meridional structure — degree n=4 | single_harmonic | L2 | — | A(phi), turning latitude | SQ4 | not started |
| P-17 | phase_speed | Resolution robustness — degree n=4 | single_harmonic | L0 | Resolution | c convergence | SQ3 | not started |
| P-18 | phase_speed | Hyperdiffusion sensitivity — degree n=4 | single_harmonic | L1 | Hyperdiffusion nu | c sensitivity | SQ3 | not started |
| I-00 | instability | Galewsky, Scott & Polvani (2004) barotropic-instability anchor | galewsky | L1 | — | sigma, m*, onset (anchor case) | SQ5 | not started |
| I-01 | instability | Shear threshold — idealised zonal jet, shear step 1 of 5 | jet | L1 | Shear parameter S | sigma, m*, Rayleigh-Kuo diagnostic | SQ5 | not started |
| I-02 | instability | Shear threshold — idealised zonal jet, shear step 2 of 5 | jet | L1 | Shear parameter S | sigma, m*, Rayleigh-Kuo diagnostic | SQ5 | not started |
| I-03 | instability | Shear threshold — idealised zonal jet, shear step 3 of 5 | jet | L1 | Shear parameter S | sigma, m*, Rayleigh-Kuo diagnostic | SQ5 | not started |
| I-04 | instability | Shear threshold — idealised zonal jet, shear step 4 of 5 | jet | L1 | Shear parameter S | sigma, m*, Rayleigh-Kuo diagnostic | SQ5 | not started |
| I-05 | instability | Shear threshold — idealised zonal jet, shear step 5 of 5 | jet | L1 | Shear parameter S | sigma, m*, Rayleigh-Kuo diagnostic | SQ5 | not started |
| I-06 | instability | Rotational stabilisation — idealised jet at fixed shear, rotation step 1 of 4 | jet | L1 | Rotation rate Omega | sigma, stability boundary | SQ5 | not started |
| I-07 | instability | Rotational stabilisation — idealised jet at fixed shear, rotation step 2 of 4 | jet | L1 | Rotation rate Omega | sigma, stability boundary | SQ5 | not started |
| I-08 | instability | Rotational stabilisation — idealised jet at fixed shear, rotation step 3 of 4 | jet | L1 | Rotation rate Omega | sigma, stability boundary | SQ5 | not started |
| I-09 | instability | Rotational stabilisation — idealised jet at fixed shear, rotation step 4 of 4 | jet | L1 | Rotation rate Omega | sigma, stability boundary | SQ5 | not started |
| I-10 | instability | Observationally seeded — reanalysis-derived zonal-mean jet u-bar(phi) | jet | L1 | — | sigma, m* vs observed wavenumber | SQ5 / SQ4 | not started |
| I-11 | instability | Resolution robustness — supercritical idealised jet | jet | L1 | Resolution | sigma convergence | SQ5 | not started |
| I-12 | instability | Perturbation-seed robustness — supercritical idealised jet | jet | L1 | Random seed | sigma spread across seeds | SQ5 | not started |
| EVP-hough | evp | Hough-mode eigenfrequencies of the divergent shallow-water system, swept over Lamb's parameter and azimuthal order (authorised extension B) | — | L1 | Lamb's parameter, azimuthal order | Hough eigenfrequencies | SQ1 / SQ3 | not started |
| EVP-jet-stability | evp | Linear stability eigenvalues about each zonal base state u-bar(phi) (authorised extension C) | jet | L1 | Base state, azimuthal order | Growth rates sigma(m), eigenmodes | SQ5 | not started |

## Observational datasets (D1–D4)

External reanalysis inputs used for the validation diagnostics of blueprint
§7.3, acquired and provenance-tracked under `data/external/`. Two contrasting DJF
seasons are used — **2013/14** (ENSO-neutral) and **2015/16** (strong El Niño) —
across **two independent reanalyses** (ERA5 and NCEP/NCAR R1), so every
observational diagnostic is computed twice and any spread is reported as
observational uncertainty (see `docs/CONVENTIONS.md`, "Two contrasting DJF
seasons").

| Dataset | Description | Status | Seasons covered | §7.3 diagnostic supported | Sub-question |
|---------|-------------|--------|-----------------|---------------------------|--------------|
| D1 | ERA5 monthly-mean climatology (u, v, z at 250/300/500 hPa; DJF 1991–2020) | acquired | 30-yr DJF climatology | Zonal-mean jet `ū(φ)`, curvature `d²ū/dy²`, and sign of `dQ/dy = β − d²ū/dy²` (feeds I-10, EVP-jet-stability) | SQ4 / SQ5 |
| D2 | ERA5 daily 500 hPa geopotential (two DJF seasons) | acquired | 2013/14, 2015/16 | Wave-phase tracking and dominant synoptic zonal wavenumber (k ≈ 4–6) for model comparison | SQ3 / SQ4 |
| D3 | NCEP/NCAR R1 daily 500 hPa height + 250 hPa wind (two DJF seasons) | acquired | 2013/14, 2015/16 | Independent second-reanalysis cross-check of D1 and D2 diagnostics | SQ3 / SQ4 / SQ5 |
| D4 | torch-harmonics spherical shallow-water cross-check | optional (not run this session) | — | Advisory independent-solver cross-check only; nothing downstream depends on it | SQ2 |
