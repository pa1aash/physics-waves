# Phase-0 gate — execution record and verdict

The blueprint Phase-0 exit gate: run Dedalus's own **unmodified** spherical
shallow-water example (the Galewsky et al. 2004 barotropically-unstable jet) and
confirm the toolchain behaves as the physics demands. This file records the
execution, timings, MPI-correctness check, and the physical-acceptance verdict.

- **Machine.** MacBook Air, 8 cores (`hw.ncpu = 8`), local (no pod).
- **Software.** Dedalus 3.0.5, Open MPI 5.0.10, `pw` conda environment.
- **Reference.** `dedalus_reference/shallow_water.py`, fetched unmodified from
  upstream `v3.0.5` (see its `ATTRIBUTION.md`; the conda build ships an empty
  examples archive). Resolution 256×128, `stop_sim_time = 360 h` (15 days),
  `dt = 600 s`, RK222, hourly HDF5 snapshots of height and vorticity.
- **Thread hygiene.** `scripts/env.sh` (OMP/BLAS threads = 1) sourced for every
  run so MPI ranks do not oversubscribe cores.

## §5.1 Serial smoke

`python shallow_water.py` (serial) initialised (balanced-height LBVP + RK222 IVP
solver built against the installed 3.0.5 API), started the main loop, and wrote
snapshots — **no API error**. The unmodified reference runs on this toolchain.

## §5.2 Parallel correctness (MPI domain decomposition)

`n = 1, 2, 4` were run and their height/vorticity fields compared at matching
output times (sim time 0–9 h, 10 writes). Spectral MPI reorders operations, so
agreement is to round-off, not bit-identical.

| Field | worst \|Δ\| across n=1/2/4 | relative to field max |
|-------|---------------------------|-----------------------|
| height | 1.9 × 10⁻¹⁹ | 1.3 × 10⁻¹⁵ |
| vorticity | 3.9 × 10⁻¹⁶ | 9.7 × 10⁻¹⁶ |

**Max pointwise disagreement ≈ 10⁻¹⁵ relative** → machine precision. MPI
domain decomposition is sound on this machine.

## §5.3 Timings

Clean, dedicated runs (nothing else competing), `n = 4`:

| Resolution | Procs | Wall-clock | Dedalus solver run-time | Core-hours (procs·wall/3600) |
|------------|-------|-----------|-------------------------|------------------------------|
| 256 × 128 (full) | 4 | **110 s** | 102.5 s (setup 0.54 s, warmup 1.03 s) | **0.122** |
| 128 × 64 (half)  | 4 | **37 s**  | 33.8 s (setup 0.19 s) | **0.041** |

Halving each dimension gives a ≈ 3× speedup. The full 15-day integration at the
example's own resolution costs about **0.12 core-hours** on this laptop — the
first real data point for the Session R1 compute-budget estimate. The half-res
copy is a modified-for-timing-only file (`shallow_water_L0.py`); the gate itself
used the unmodified original.

## §7 Physical acceptance criteria

Evaluated by `analyze_gate.py` on the clean full-resolution `n = 4` run (360
hourly snapshots). The reference saves only height and vorticity, so kinetic
energy is reconstructed from vorticity via the non-divergent streamfunction
(`lap ψ = ζ`, `KE = −½H·∫ψζ dA`); this captures essentially all of the nearly
balanced flow's KE. All quantities are in the reference's simulation units, so
constants and stored fields are consistent and the *relative* drifts are
unit-independent.

**1. Mass conservation — PASS.** Max relative drift of total mass = **1.4 × 10⁻¹⁶**
(≪ 10⁻⁶). The shallow-water continuity conserves `∫h dA` to round-off, as it must
(hyperdiffusion, `H·div u`, and `div(hu)` each integrate to zero over the sphere).

**2. Energy behaviour — consistent.** `KE(0) ≈ 2.4 × PE(0)` (a kinetic-energy-
dominated jet, as expected). Total `KE + PE` drifts **slowly** to ≈ −2 % by day 4,
then declines **faster** (to ≈ −6.6 % by day 8) **coinciding with the instability
onset**, then plateaus — exactly the expected signature of hyperdiffusion removing
the enstrophy that cascades to small scales as the mean-flow energy converts to
eddies. PE rises as KE falls, the barotropic energy conversion.

**3. Instability development — PASS.** The initially smooth, near-zonal vorticity
(two zonal `ζ` bands at ≈ 40° N and ≈ 50° N on day 1) undulates at zonal
wavenumber ≈ 5–6 by **day 4**, rolls up into discrete vortices with tight
filamentary gradients by **day 6**, and matures into developed vortical
turbulence by days 8–14. The eddy (non-zonal) enstrophy grows **exponentially**
from day 1 (×11 day 2, ×170 day 3, ×2500 day 4, ×17 000 day 5, peak ×30 600 day
6), then saturates. Visible roll-up over **days 4–6** matches Galewsky et al.
(2004) Fig. 4. (The dissipation operator differs — `∇⁴` here vs. Galewsky's
`∇²` — so exact onset timing may differ slightly; see `galewsky_comparison.md`.)

**4. Consistency with the pre-run Rayleigh-Kuo prediction — PASS.** The
instability grows at latitude **≈ 44° N**, inside the band **32–58° N** where
`predict_rayleigh_kuo.py` (run *before* the simulation) found the background
PV gradient `β − d²ū/dy²` reverses. The loop closes: a necessary condition
predicted flank instability, and the simulation develops it exactly there.

Diagnostic figures (validation, not manuscript; reproducible, so gitignored):
`diagnostics/vorticity_panels.png`, `diagnostics/conservation_series.png`, and
the pre-run `diagnostics/rayleigh_kuo_prediction.png`.

## Verdict

**PHASE-0 GATE: PASSED** (2026-07-25). The toolchain correctly solves the
rotating shallow-water barotropic-instability problem on the sphere: mass
conserved to machine precision, energy drift physically consistent, the Galewsky
instability develops on schedule at the predicted latitudes, and the pre-run
Rayleigh-Kuo necessary condition is confirmed by the simulation. Every later
session may rely on this validated toolchain.
