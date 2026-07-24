# Project conventions

This document is the versioned constitution for the project. It states the
standards that govern how work is done here, in tool-neutral terms. Where it and
`PROJECT_BLUEPRINT.md` disagree, the blueprint governs on scientific matters and
this document governs on process.

## Framing

This is a **physics** paper. Mathematical depth is expected and welcome, but
physics is the through-line, not mathematics for its own sake. Every derivation,
diagnostic, figure and sentence must answer "what is the fluid doing, and why."
Wherever this session writes prose — manifests, conventions, README, metadata —
it frames choices in physical terms: mechanism, regime, scale, conservation.

This directive is standing: every later session inherits it. When a choice can
be justified either mathematically or physically, the physical justification is
the one that is written down, and the mathematics is the machinery that serves
it.

## Authoritative source

`PROJECT_BLUEPRINT.md` is the single authoritative knowledge source. Any change
to sections 6, 8 or 16 of the blueprint is logged in the revision note at the
foot of the relevant section, and the change is committed separately with a
`docs:` subject.

## Authorship

All work on this project is authored by **Palaash Gang**. Commits, code
comments, documentation and manuscript metadata carry that name and no other.
No automated-tooling attribution — no assistant bylines, no authorship
trailers, no "produced-by" footer lines, no tool emblems — appears anywhere in
the repository tree or its commit history. Copyright lines read
`© 2026 Palaash Gang`. The repository owner is `pa1aash`.

A commit-message guard (`scripts/hooks/commit-msg`, mirrored into the local
`.git/hooks/`) and a staged-content guard (the `forbidden-attribution` hook in
`.pre-commit-config.yaml`) enforce this automatically and reject any commit that
violates it.

## Third-party text (standing rule)

Canonical third-party text is never reproduced by transcription. This includes
software licences, LaTeX class files and journal templates, published reference
tables, and bibliography entries. The authoritative source is pointed to and the
text is fetched at the point of need. If a fetch is impossible, a pointer is
written and the outstanding fetch is logged in `docs/SETUP_CHECKLIST.md`.

Consequences already applied: `LICENSE-DATA` is a pointer to the CC BY 4.0 legal
code, whose full text is fetched by `make licenses` into `LICENSE-DATA.full`
before the release deposit; the Springer Nature manuscript class is downloaded
into `manuscript/template/` rather than vendored; and reference PDFs are placed
into `docs/literature/` by the operator rather than transcribed.

## Authorised extensions to the blueprint

The following additions to blueprint section 8 are authorised for this project
and are scaffolded in the repository. Each is a genuine strengthening of the
scientific programme, not a change of scope.

| Ext | Addition | Scaffolding |
|-----|----------|-------------|
| **A** | The Galewsky, Scott & Polvani (2004) barotropic-instability initial-value problem is adopted as the canonical anchor of the instability campaign, entering the run matrix as **I-00**. | `configs/instability/I-00.yaml`; `src/solver/initial_conditions/galewsky.py` |
| **B** | The exact linear eigenmodes of the *divergent* shallow-water system on the sphere (Hough functions / Laplace's tidal equations, after Longuet-Higgins 1968) are computed as an eigenvalue problem and used as an exact analytic target alongside the nondivergent Rossby-Haurwitz prediction. | `configs/evp/EVP-hough.yaml`; `src/analysis/hough.py`; `src/solver/evp_hough.py` |
| **C** | A linear stability eigenvalue problem is solved about each zonal base state `ū(φ)`, yielding exact growth rates `σ(m)` and eigenmode structure, closing the "necessary but not sufficient" gap left by the Rayleigh-Kuo test. | `configs/evp/EVP-jet-stability.yaml`; `src/solver/evp_stability.py`; `src/analysis/stability_evp.py` |

One verification run is added: **V-09**, the unsteady analytic solution of
Läuter, Handorf & Dethloff (2005), a time-dependent exact solution of the
spherical shallow-water equations that complements the steady Williamson case 2.

**References** (to be verified against the primary sources before manuscript
citation, per the blueprint reference note):

- Galewsky, J., Scott, R. K., & Polvani, L. M. (2004). *Tellus A*, 56(5), 429–440.
- Longuet-Higgins, M. S. (1968). The eigenfunctions of Laplace's tidal equations
  over a sphere. *Philosophical Transactions of the Royal Society A*, 262, 511–607.
- Läuter, M., Handorf, D., & Dethloff, K. (2005). *Journal of Computational
  Physics*, 210(2), 535–553.

**Justification.**

- *Extension A* gives the instability campaign a published, widely reproduced
  reference case with a documented onset time and vorticity structure, so that
  in-house growth-rate measurements can be checked against an external anchor
  rather than only against internally generated jets.
- *Extension B* supplies an *exact* analytic target for the divergent system
  actually being solved. The nondivergent Rossby-Haurwitz speed `-2Ω/[n(n+1)]`
  is only asymptotically correct at finite deformation radius; the Hough
  eigenfrequencies quantify the very departure the blueprint flags as its most
  interesting predicted result (H5), turning a caveat into a measurement.
- *Extension C* replaces a one-sided necessary condition with a solved
  eigenvalue problem. Rayleigh-Kuo can only say a jet *might* be unstable; the
  stability EVP returns the actual growth rate and dominant wavenumber against
  which the nonlinear runs are validated.

### Two contrasting DJF seasons for observational comparison

The blueprint specifies a single DJF season for the observational comparison.
DJF 2015/16 was the strongest El Niño on record: the Northern Hemisphere jet
that winter was displaced equatorward and strengthened relative to climatology,
and the stationary-wave pattern was correspondingly anomalous. Validating a
zonally symmetric idealised model against one strongly perturbed season tests
robustness against exactly the wrong thing.

The observational comparison therefore uses **two contrasting DJF seasons**:

- **DJF 2013/14** — ENSO-neutral, a typical background state.
- **DJF 2015/16** — strong El Niño, a strongly perturbed background state.

The 30-year monthly climatology (D1) remains the primary source for the
zonal-mean jet `ū(φ)`, its curvature `d²ū/dy²`, and the sign structure of the
background potential-vorticity gradient `dQ/dy = β − d²ū/dy²`. The two individual
seasons supply wave-phase tracking and dominant-wavenumber comparison.

**The physical argument for doing this.** The modelled dispersion relation
depends on the planetary vorticity gradient, which is a property of the rotating
sphere and is indifferent to ENSO. If the observed westward phase speed and
dominant zonal wavenumber agree with the model in both a neutral and a strongly
perturbed winter, the agreement is attributable to the *mechanism* rather than
to a coincidence of one season's background flow. Both reanalyses (ERA5 and
NCEP/NCAR R1) cover both seasons, so every observational diagnostic is computed
twice independently; where the two reanalyses disagree, that spread is reported
as observational uncertainty rather than concealed.

### Extension B validation — the ε → 0 limit and the missing references

Two classical sources for extension B — Longuet-Higgins (1968) and Swarztrauber
& Kasahara (1985) — could not be obtained. Both are recorded with full
citations, DOIs and their mitigation in `docs/literature/MISSING.md`. Their
absence does not block the project: the Hough-mode eigenfrequencies are not read
from a published table but derived from first principles in Session L3 and solved
numerically in Dedalus, so the validation target is internal and stronger than an
external table would be.

The physical argument that makes this validation self-contained is the `ε → 0`
limit. Lamb's parameter can be written

    ε = 4 Ω² R² / (g H) = (R / L_d)²

where `L_d = √(gH) / (2Ω)` is the external deformation radius, so ε is the squared
ratio of planetary radius to deformation radius. Physically, `ε → 0` means
`L_d ≫ R`: the free surface behaves rigidly, columns cannot stretch, and material
conservation of potential vorticity must be satisfied entirely by changes in
relative vorticity. In that limit the divergent eigenfrequencies must reduce
exactly to the nondivergent Rossby–Haurwitz result

    c_ang → − 2Ω / [n(n+1)]

which is precisely hypotheses H1 and H2 of the blueprint. The eigenvalue solver
is therefore validated against a closed-form limit the project derives
independently. Sweeping ε upward then measures how the wave slows as a growing
share of the potential-vorticity budget is absorbed by vortex stretching rather
than by relative vorticity — the physical content of hypothesis H5, expressed as
a curve rather than an assertion.

## Run identifiers

Run IDs are immutable once a run has executed. The scheme follows blueprint
section 8, extended with `I-00`, `V-09`, and the `EVP-*` family (`EVP-hough`,
`EVP-jet-stability`). Output directories are named by run ID only, never by date
or description.

## Configs are the single source of truth

No parameter is ever set by editing a script. Every run is fully specified by
one YAML file under `configs/`, validated against `configs/_schema.yaml`.

## Raw data is immutable

Raw simulation output is immutable once written. Reprocessing writes to
`data/processed/`; nothing ever writes back into `data/raw/` or
`data/reference/`.

## Data discipline

Binary scientific data (NetCDF, HDF5, GRIB) is never committed. What is
committed is the fetcher script, the provenance manifest and the SHA-256
checksums — enough to reproduce every download byte-for-byte. `data/raw/`,
`data/reference/`, `data/processed/` and `data/external/*.nc` are gitignored;
their `README.md`, `MANIFEST.md` and checksum files are tracked.

## Figure provenance

Every figure carries a sidecar JSON recording the run IDs, processed-data files,
config hashes and git commit it was built from. The helper that writes it lives
in `src/figures/style.py`.

## Verification gate

No experimental campaign begins until every criterion in blueprint section 9.4
is met. This gate is not negotiable, and every downstream result inherits its
validity from it.

## Uncertainty reporting

No headline number is reported without an accompanying uncertainty and a named
dominant source, per blueprint section 11.6.

## Commit protocol

Every logical change is committed and pushed immediately. Commit subjects follow
the conventional-commit style (`chore:`, `docs:`, `feat:`, `build:`, `test:`),
are at most 72 characters, and carry no trailers. Pushes are never batched.

## Environment

`environment.lock.yml` is authoritative for reproduction; `environment.yml` is
the human-editable specification. The lock is regenerated on any dependency
change and both files are committed together.

## Authorised deviations

Recorded here per blueprint section 14. Each is a conservative choice made to
satisfy a hard constraint of this repository.

1. **Guard files express screened tokens indirectly.** The forbidden-attribution
   guards (`scripts/hooks/commit-msg`, `scripts/audit.sh`,
   `tests/test_repo_hygiene.py`, and the `forbidden-attribution` hook in
   `.pre-commit-config.yaml`) must reference the strings they screen for. They
   express those tokens as bracketed character classes or bytes assembled at run
   time, so the guards match real occurrences without themselves containing the
   literal strings under the whole-tree forbidden-string audit.
2. **`.gitignore` negation exceptions.** The directory guides (`README.md`) and
   placeholders (`.gitkeep`) in `data/raw/`, `data/reference/` and
   `data/processed/` are re-included by explicit negation so they stay tracked
   while the binary contents of those directories remain ignored.
3. **`LICENSE-DATA` is a pointer.** Under the third-party-text rule above, the
   data licence file points to the CC BY 4.0 legal code rather than transcribing
   it; the full text is fetched via `make licenses` before the Zenodo deposit.
