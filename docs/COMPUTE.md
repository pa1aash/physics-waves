# Compute plan

This file records the compute plan so it is versioned rather than living in a
chat log.

## Solver constraints

Dedalus v3 is **CPU-only and MPI-parallel**. There is no CUDA backend. GPU
instances provide no benefit to this project and **must not be provisioned for
solver runs**. Parallelism comes from MPI ranks across CPU cores, with threading
disabled per rank (see `scripts/env.sh`).

## Where work runs

- **Local machine (Apple Silicon Mac).** Runs the L0 resolution rung, all
  analysis, all figure production, LaTeX, and version control.
- **Remote compute (RunPod CPU pod).** A `cpu5c` compute-optimised flavour,
  16–32 vCPU, 64–128 GB RAM, with a 200 GB network volume. Provisioned only for
  the production and convergence rungs; provisioning is an operator action
  tracked in `docs/SETUP_CHECKLIST.md`.

## Environment parity: native provisioning, not a container

**The parity strategy actually in use is native provisioning from the same
specification.** `scripts/pod_bootstrap.sh` builds the pod's own `pw` conda
environment from `environment.yml` — the identical file the Mac environment was
created from — and `make verify` passes on the pod. That is a real, working
parity path, and it is the one the pipeline depends on.

`Dockerfile` remains in the tree as an alternative for a future pod that needs
one. **It is not part of the current pipeline**, it is not built or tested by any
session, and nothing should be inferred from its presence about how the pod is
provisioned. The earlier description of the pod as "running the same container
as the local environment" described a plan that was superseded by what was
actually done; this section replaces it.

Reproducibility therefore rests on `environment.yml` plus the byte-level
`environment.lock.yml`, on both machines, rather than on an image digest.

## Resolution ladder and cost

From blueprint §5.4. Cost rises steeply with resolution (spectral transform cost
grows faster than linearly in truncation, and the timestep shrinks with grid
spacing), so full sweeps run at L1 and L3 is reserved for the two reference runs
(risk R4).

| Label | Nφ × Nθ | Use | Measured wall time |
|-------|---------|-----|--------------------|
| L0 | 128 × 64 | Rapid iteration, debugging (local) | 37 s (Phase-0 example, n=4; below) |
| L1 | 256 × 128 | Production baseline (pod) | 110 s (Phase-0 example, n=4; below) |
| L2 | 512 × 256 | Convergence rung (pod) | TBD — Session R1 |
| L3 | 1024 × 512 | Reference-solution generation (pod) | TBD — Session R1 |

## Phase-0 gate — first measured local timings (Session L1)

The Phase-0 gate ran Dedalus's unmodified spherical shallow-water example (the
Galewsky 2004 jet: a 15-day / 360-hour integration, `dt = 600 s`, RK222) on the
local machine. This is the **first real compute data point** for the Session R1
budget; the project's own runs will differ in length and physics, so these are a
calibration, not a final budget.

- **Machine.** MacBook Air, 8 cores (`hw.ncpu = 8`), Open MPI 5.0.10. No pod used.
- **MPI correctness.** `n = 1, 2, 4` agree to ≈ 10⁻¹⁵ relative (machine
  precision) — automatic MPI domain decomposition is sound here.

| Resolution | Procs | Wall-clock | Core-hours (procs·wall/3600) |
|------------|-------|-----------|------------------------------|
| L0 (128 × 64) | 4 | 37 s | 0.041 |
| L1 (256 × 128) | 4 | 110 s | 0.122 |

Halving each grid dimension gives ≈ 3× speedup. Extrapolating naively (transform
cost grows faster than `N²` and the stable timestep shrinks with grid spacing),
each further rung up the ladder is expected to cost several times the one below;
Session R1 measures L2/L3 on the pod directly.

### Local container parity (§8) — superseded

Recorded for history: Docker is not installed on the local machine, so no local
`docker build` was ever run. This is no longer a gap to close, because the
container path is not the parity path — see "Environment parity" above.

## Resume on failure

An interrupted run is **archived and restarted from the beginning**, not resumed
from a checkpoint. `scripts/resume_check.py` finds them and clears the way.

The decision (Session L7a) is on the evidence, not on convenience. Dedalus does
provide `solver.load_state(path, index)`, but three things stand between that
primitive and a working resume here:

1. **Nothing on disk to load.** The harness writes no checkpoint handler. Its
   snapshot stream stores `height`, `vorticity` and `divergence`; the prognostic
   velocity `u` is written only under `write_full_fields: true`, which every
   sweep config sets false. For exactly the runs a campaign produces, the state
   needed to restart was never saved.
2. **Grid-space only, and no timestepper history.** `load_state` "currently can
   only load grid space data", and a multistep scheme's history is not restored,
   so a resumed run carries a startup transient at an arbitrary point in the
   middle of the series. For fits quoted to 0.1%, that is not an artefact to
   leave undocumented.
3. **It fights immutability.** Resuming means reopening a directory whose
   provenance record was deliberately made read-only — disabling the tripwire
   that exists to catch a run being silently rewritten.

Wiring resume up would therefore mean new solver-side code (a checkpoint
handler, a schema field, provenance changes, transient characterisation), which
is out of scope for a tooling session. Archiving costs wall-clock and nothing
else: nothing is deleted, the run ID is freed so the harness's refusal never has
to be overridden with `--force`, and the restarted run is one continuous
integration with no seam in it.

## Running a campaign on the pod

    python scripts/sweep.py phase_speed         # plan: validate + scale cadences
    python scripts/resume_check.py              # clear any half-finished runs
    scripts/run_mpi.sh configs/phase_speed/P-12.yaml
    python scripts/cost_log.py --update-doc     # record what it cost

`scripts/run_mpi.sh` sources `scripts/env.sh` first — non-negotiable. An
oversubscribed run does not fail; it completes and writes a `wall_seconds` that
measures thread contention rather than the solver, and that number feeds both
the cost log and Session R1's ladder calibration.

Rank counts are a **heuristic** (`RANKS_BY_RESOLUTION` in `scripts/sweep.py`):
4 ranks at L0/L1, anchored on the Phase-0 gate above, doubling per rung beyond.
Session R1's timing calibration on the pod replaces them with measured values.

**The harness runs correctly on more than one rank as of Session L7a**, and did
not before. Two bugs hid behind the fact that every run to date had been serial:
the area average was rank-local (`IndexError` on every rank but one, in every
initial condition), and every rank raced to write the provenance record, so the
first to arrive set the read-only tripwire and the next tripped it. Both aborted
before any physics ran, so neither could have produced a wrong number — but both
made the pod unusable. `tests/test_mpi_harness.py` locks them. A 4-rank and a
1-rank integration of V-02 now agree bit for bit.

## Cost tracking

The budget is a **Fermi estimate of 60–150 core-hours** for the whole project,
made before any run existed. Tracking it exists to find out early if it was
wrong: a campaign 40% through its runs and 90% through its budget needs its
remaining resolution ladder rethought *before* the L3 reference runs, not after.

`scripts/cost_log.py` derives the running total from the runs themselves —
`outcome.wall_seconds` and `environment.mpi_size` are already in every
provenance record, so nothing has to be instrumented or remembered:

    core-hours = ranks × wall_seconds / 3600

Core-hours rather than wall-clock, because a pod is billed for the cores it
holds rather than the cores a run uses. Runs that failed are counted and
reported separately: they were paid for, and a budget that forgets its failed
attempts reads as healthy right up to the point it is not.

    python scripts/cost_log.py                # table across all campaigns
    python scripts/cost_log.py --update-doc   # rewrite the block below

The block below is generated. Everything outside the markers is hand-written.

<!-- cost-log:begin -->

*Generated by `scripts/cost_log.py` from run provenance on 2026-07-27. Do not edit by hand — rerun `python scripts/cost_log.py --update-doc`.*

| Campaign | Runs | Core-hours | Output |
|----------|-----:|-----------:|-------:|
| instability | 1 | 0.045 | 81.8 MB |
| phase_speed | 1 | 0.003 | 2.1 MB |
| verification | 1 | 0.001 | 0.7 MB |
| **total** | **3** | **0.049** | |

Measured against the Fermi estimate of 60–150 core-hours for the whole project, this is **0.0%** of the upper bound.

Mean wall time per completed run, by rung — this is what Session R1's calibration refines and what the rank heuristic in `scripts/sweep.py` is currently guessing from:

| Rung | Runs | Mean wall (s) | Core-hours |
|------|-----:|--------------:|-----------:|
| L0 | 2 | 7.1 | 0.004 |
| L1 | 1 | 163.4 | 0.045 |

<!-- cost-log:end -->

## Storage policy

Raw HDF5 output lives on the pod network volume and is **never committed**. A
curated subset is deposited to Zenodo at release. Nothing writes back into
`data/raw/` or `data/reference/` after a run completes.

## Environment provenance

The conda environment was created with the first path of the fallback ladder,
directly from the human-editable specification:

```
mamba env create -f environment.yml
```

- **Result:** success on the first attempt. No fallback path was needed.
- **Platform:** `osx-arm64` (from `conda info`).
- **Tooling:** conda 26.1.1, mamba 2.5.0.
- **Environment Python:** 3.12.13.
- **Key solver stack:** Dedalus 3.0.5, mpi4py 4.1.2, h5py 3.16.0 with MPI
  enabled (`h5py.get_config().mpi is True`), FFTW via conda-forge, NumPy 2.5.1,
  SciPy 1.18.0, SymPy 1.14.0.

The byte-level lock is `environment.lock.yml`, produced with
`conda env export --no-builds` from the solved environment. Regenerate the lock
on any dependency change and commit it together with `environment.yml`.
