# Beta-Effect Control of Barotropic Rossby-Wave Dispersion and Zonal-Jet Instability on a Rotating Sphere

A fully computational spectral study of how the latitudinal gradient of
planetary vorticity governs the westward propagation, meridional structure and
shear instability of large-scale barotropic waves in a rotating shallow-water
fluid on a sphere.

## Status

Phase 0 complete — repository initialised, environment reproducible, external
data acquired.

(Reanalysis tier: NCEP/NCAR Reanalysis 1 acquired locally; ERA5 acquisition is
deferred until Copernicus CDS credentials are configured — see
`docs/SETUP_CHECKLIST.md`. NCEP/NCAR is a sufficient fallback for every
diagnostic in the plan.)

## Abstract

Large-scale atmospheric motion is dominated by slow, planetary-scale waves that
propagate systematically westward relative to the mean flow. Their existence
follows from the beta-effect, the latitudinal variation of the Coriolis
parameter on a rotating sphere, which supplies a restoring gradient of planetary
vorticity. This project quantifies how strongly that gradient controls wave
behaviour, using a purely computational approach with no laboratory component.
The rotating shallow-water equations are solved on the full sphere by a spectral
Galerkin method in a spherical-harmonic basis, with implicit-explicit
Runge-Kutta time integration. The governing system is first derived in
vector-invariant form and linearised twice, about a state of rest to obtain the
barotropic Rossby-wave dispersion relation, and about a zonal jet to obtain the
barotropic instability problem and the Rayleigh-Kuo necessary condition. The
solver is verified against the standard spherical shallow-water benchmark suite,
using closed-form solutions where they exist and a self-generated high-resolution
reference where they do not, together with a spectral-convergence study and
conservation diagnostics for mass, energy and potential enstrophy. Controlled
numerical experiments then sweep planetary rotation rate and zonal wavenumber,
measuring westward phase speed from space-time diagrams and comparing it against
the analytic Rossby-Haurwitz prediction. Meridional structure and turning
latitudes are extracted, and model scales are compared against wave signatures
diagnosed from ERA5 reanalysis. Finally, zonal jets of varying meridional shear,
including a profile derived from observations, are perturbed to measure
exponential growth rates and dominant unstable wavenumbers against linear
stability theory. Numerical uncertainty is quantified by resolution convergence
and parameter sensitivity.

## What this is

The atmosphere at mid-latitudes is organised not by small-scale turbulence but
by slow, coherent, planetary-scale waves whose defining property is that they
always propagate westward relative to the background flow — a direct consequence
of the beta-effect. This project is a controlled, systematically verified
numerical isolation of the beta-effect as a single independent variable,
spanning the regime from linear wave propagation through to nonlinear shear
instability, in one consistent shallow-water model and one consistent spectral
framework. Verification and validation are treated as separate, explicitly
reported activities; the rotation rate is swept as a free parameter; and the
idealised model result is closed back against reanalysis observations of the
real atmosphere.

## Repository layout

| Path | Holds |
|------|-------|
| `PROJECT_BLUEPRINT.md` | The authoritative project knowledge source; governs every decision. |
| `configs/` | One YAML per run; the single source of truth for every simulation. |
| `src/` | Solver setup, runtime diagnostics, analysis pipeline, figure production, data fetchers. |
| `data/` | External downloads (`external/`) and generated output (`raw/`, `reference/`, `processed/`); binary contents are not committed. |
| `theory/` | Derivations (`derivations.tex`) and schematic figures. |
| `figures/` | Final publication figure set with provenance sidecars. |
| `manuscript/` | Springer Nature manuscript sources (template supplied by operator). |
| `logs/` | Run logs and provenance records. |
| `scripts/` | Environment, sync, audit and git-hook infrastructure. |
| `tests/` | Environment and repository-hygiene tests. |
| `docs/` | Conventions, setup checklist, compute plan, literature index. |

## Quickstart

```bash
git clone git@github.com:pa1aash/physics-waves.git
cd physics-waves
make env            # create the pinned conda environment (name: pw)
conda activate pw
make test           # run environment + repository-hygiene tests
make data           # fetch external reanalysis datasets (NCEP always; ERA5 if CDS configured)
```

## Reproducing results

Each final figure will map to a single `make` target that regenerates it from
committed configs and fetched or regenerated data.

| Figure | Target | Description |
|--------|--------|-------------|
| — | — | *to be completed at Phase 10* |

## Data

Three tiers, following the project data architecture:

- **Tier 1 — self-generated simulation output (primary).** HDF5 field snapshots,
  conservation series, spectra and Hovmöller slices, written per run ID under
  `data/raw/` and `data/reference/`. This is the primary dataset.
- **Tier 2 — benchmark verification data.** The Williamson et al. (1992)
  spherical shallow-water test set; cases without closed-form solutions are
  reproduced in-house as L3 reference solutions.
- **Tier 3 — observational reanalysis (external).** ERA5 (Copernicus Climate
  Change Service) and, as a queue-free fallback, NCEP/NCAR Reanalysis 1
  (NOAA PSL), used for jet-profile extraction and scale comparison only.

Raw simulation output and reanalysis downloads are **not committed**. They are
reproducible byte-for-byte via `make data` and the run configs; the fetchers,
provenance manifest and SHA-256 checksums under `data/external/` are what is
tracked. A curated subset will be deposited to Zenodo at release.

Zenodo DOI: `to be assigned at release`.

## Citation

```bibtex
@software{gang_physics_waves_2026,
  author = {Gang, Palaash},
  title  = {Beta-Effect Control of Barotropic Rossby-Wave Dispersion and
            Zonal-Jet Instability on a Rotating Sphere},
  year   = {2026},
  url    = {https://github.com/pa1aash/physics-waves},
  note   = {Manuscript in preparation}
}
```

## Licence

Code in `src/`, `configs/`, `scripts/` and `tests/` is released under the MIT
License (`LICENSE`). Data products in `data/processed/`, figures in `figures/`
and derivations in `theory/` are released under the Creative Commons Attribution
4.0 International License (`LICENSE-DATA`).

## Author

Palaash Gang
