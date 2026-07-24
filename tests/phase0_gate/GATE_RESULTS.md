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

_(The §7 acceptance verdict is appended below.)_
