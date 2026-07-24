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
  16–32 vCPU, 64–128 GB RAM, with a 200 GB network volume, running the same
  container as the local environment (see `Dockerfile`). Provisioned only for the
  production and convergence rungs; provisioning is an operator action tracked in
  `docs/SETUP_CHECKLIST.md`.

## Resolution ladder and cost

From blueprint §5.4. Cost rises steeply with resolution (spectral transform cost
grows faster than linearly in truncation, and the timestep shrinks with grid
spacing), so full sweeps run at L1 and L3 is reserved for the two reference runs
(risk R4).

| Label | Nφ × Nθ | Use | Measured wall time |
|-------|---------|-----|--------------------|
| L0 | 128 × 64 | Rapid iteration, debugging (local) | TBD — Session R1 |
| L1 | 256 × 128 | Production baseline (pod) | TBD — Session R1 |
| L2 | 512 × 256 | Convergence rung (pod) | TBD — Session R1 |
| L3 | 1024 × 512 | Reference-solution generation (pod) | TBD — Session R1 |

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
