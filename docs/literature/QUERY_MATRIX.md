# Query matrix

**Session L4, Step 2.** Search strings organised by theory area, so Step 3's
retrieval is systematic rather than ad hoc. Every row names the theory sections
(`theory/derivations.tex`) and hypotheses it serves, so Step 5's corpus-adequacy
audit can check coverage row by row.

Queries are executed against **OpenAlex** and **Crossref** as the primary
engines, because both return a DOI with structured metadata in the same call —
which is what makes the paper-trail rule in the scope contract enforceable. Web
search is used only for open-access PDF location, never as a source of
bibliographic facts.

Rows marked **[T]** carry a targeted deliverable promoted by the Step 1
critique.

| # | Theory area | Serves | Query strings |
|---|-------------|--------|---------------|
| Q1 | Benchmark suite and reference solutions | §11, H6 | `shallow water equations spherical geometry standard test set`; `spectral transform shallow water test suite error norms`; `numerical approximations shallow water sphere benchmark`; `shallow water model intercomparison sphere` |
| Q2 | Rossby-wave dispersion on the sphere | §5, H1–H4 | `Rossby Haurwitz wave sphere dispersion relation`; `barotropic vorticity equation spherical harmonics normal modes`; `planetary waves rotating sphere phase speed`; `nondivergent barotropic Rossby wave westward propagation` |
| Q3 | Divergent correction, Laplace tidal equations, Hough modes **[T]** | §6, H5, a1/a2 | `Laplace tidal equations Hough functions sphere`; `Lamb parameter shallow water sphere eigenfrequencies`; `normal modes ultralong waves atmosphere`; `divergent barotropic dispersion deformation radius`; `Hough mode eigenfrequency shallow water sphere`; `free oscillations rotating atmosphere spherical` |
| Q4 | Barotropic instability, Rayleigh–Kuo | §8, H7–H9, b1 | `barotropic instability zonal jet Rayleigh Kuo criterion`; `Charney Stern theorem potential vorticity gradient`; `necessary condition instability barotropic shear flow`; `barotropic instability sphere spherical geometry`; `inflection point criterion rotating shear flow` |
| Q5 | Linear stability eigenvalue problems for jets **[T]** | §9, b1/b2 | `linear stability eigenvalue problem barotropic jet sphere`; `normal mode instability zonal flow spherical harmonics growth rate`; `stability Rossby Haurwitz wave`; `barotropic instability normal mode spectrum numerical`; `non-normal transient growth shear flow` |
| Q6 | Counter-propagating Rossby waves | §10, d | `counter propagating Rossby waves shear instability`; `potential vorticity thinking isentropic maps`; `Rossby edge wave phase locking instability`; `critical layer instability baroclinic flow`; `Bretherton potential vorticity sheet boundary` |
| Q7 | Rhines scale, jet formation, zonostrophic regime **[T]** | §7 | `Rhines scale beta plane turbulence arrest`; `zonal jet formation rotating turbulence`; `zonostrophic turbulence jet spacing`; `beta plane turbulence anisotropy zonal flow`; `Jovian banding zonal jets turbulence` |
| Q8 | Spectral methods, Dedalus, spherical numerics | §2, §9 | `Dedalus spectral framework partial differential equations`; `tensor calculus spherical coordinates Jacobi polynomials`; `spherical harmonic transform numerical method sphere`; `sphere spectral method pole problem` |
| Q9 | Galewsky jet and its forward citations **[T]** | §11, b2 | `initial value problem testing numerical models global shallow water`; `Galewsky barotropic instability test case`; `barotropic instability test case shallow water models comparison` |
| Q10 | Reanalysis and observed eddy phenomenology **[T]** | §12, c1–c3, H10 | `ERA5 global reanalysis`; `NCEP NCAR reanalysis project`; `space time spectral analysis atmospheric waves Hayashi`; `observed phase speed spectra extratropical eddies`; `wavenumber frequency spectrum geopotential height`; `stationary and transient eddy phase speed troposphere` |
| Q11 | Barotropic vs baroclinic scope boundary | X1 | `barotropic model limitations atmospheric dynamics`; `baroclinic instability energy source extratropical cyclone`; `equivalent barotropic level atmosphere` |
| Q12 | Machine-learning weather models (acknowledgement only) | X4 | `spherical harmonic neural operator weather`; `machine learning global weather forecasting model` |

## Targeted deliverables

Three items promoted by the Step 1 critique are searched for by name, not by
topic, because their presence or absence changes what the paper may claim:

1. **Kasahara (1976)**, *J. Atmos. Sci.* 33, 408–424, "Normal modes of ultralong
   waves in the atmosphere" — the open-access source closest to fragment a1's
   prior art, and the substitute `MISSING.md` flags for the two unobtainable
   Extension-B references.
2. **A published normal-mode spectrum of the Galewsky (2004) jet** — sought via a
   forward-citation sweep on that paper. If one exists, fragment b2 is a
   reproduction and must be reported as such.
3. **Randel & Held (1991)** or equivalent — observed eddy phase-speed spectra, the
   X1 boundary case that lets the Hayashi decomposition in
   `docs/CONVENTIONS.md` be defended rather than asserted.

## Retrieval protocol

For each query string:

1. Query OpenAlex (`api.openalex.org/works?search=…`), take the top results by
   relevance and by citation count.
2. Record title, first authors, year, venue, DOI, the query string that surfaced
   it, and a UTC retrieval timestamp into `CANDIDATE_POOL.csv`.
3. De-duplicate on DOI.
4. Verification (Step 4) is a *separate* pass: resolve each DOI against the
   Crossref work record and require the returned title to match the recorded
   title. Resolution alone is not verification.
