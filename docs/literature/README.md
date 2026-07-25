# docs/literature/

**Operator action.** Place the reference PDFs listed below into this directory.
Filenames follow the pattern `firstauthor_year_shorttitle.pdf`. These files are
not committed (they are copyrighted third-party PDFs); this index records which
sources belong here.

Per the third-party-text rule (`docs/CONVENTIONS.md`), citations are fetched and
verified against the primary source before manuscript use. Entries marked
*(confirm citation)* carry only the identifying detail supplied to this project
and must be verified before citation.

**Every filename in the tables below is the exact name of a file that is either
present in this directory (marked **(held)** where the distinction matters) or
explicitly marked **(NOT held)**.** Audit check 32 enforces that no filename
present on disk is absent from these tables, and that no filename claimed as
held is missing. Session L3-PATCH reconciled the two after finding two files
named for the wrong paper — see the note under "Counter-propagating Rossby
waves" below.

## Benchmark suite and reference solutions

| Suggested filename | Citation |
|--------------------|----------|
| `williamson_1992_standard_test_set.pdf` | Williamson, D. L., Drake, J. B., Hack, J. J., Jakob, R., & Swarztrauber, P. N. (1992). A standard test set for numerical approximations to the shallow water equations in spherical geometry. *J. Comput. Phys.* 102(1), 211–224. |
| `jakobchien_1995_spectral_transform_solutions.pdf` | Jakob-Chien, R., Hack, J. J., & Williamson, D. L. (1995). Spectral transform solutions to the shallow water test set. *J. Comput. Phys.* 119(1), 164–187. |
| `hack_1992_ncar_tn343.pdf` | Hack, J. J., & Jakob, R. (1992). *Description of a Global Shallow Water Model Based on the Spectral Transform Method.* NCAR Technical Note NCAR/TN-343+STR. |
| `jakob_1993_ncar_tn388.pdf` | Jakob, R., Hack, J. J., & Williamson, D. L. (1993). *Solutions to the Shallow Water Test Set Using the Spectral Transform Method.* NCAR Technical Note NCAR/TN-388+STR. |

## Extension references

| Suggested filename | Citation |
|--------------------|----------|
| `galewsky_2004_initial_value_problem.pdf` | Galewsky, J., Scott, R. K., & Polvani, L. M. (2004). An initial-value problem for testing numerical models of the global shallow-water equations. *Tellus A* 56(5), 429–440. **Confirmed** (read; DOI [10.3402/tellusa.v56i5.14436](https://doi.org/10.3402/tellusa.v56i5.14436)). |
| `lauter_2005_unsteady_analytical_solutions.pdf` | Läuter, M., Handorf, D., & Dethloff, K. (2005). *J. Comput. Phys.* 210(2), 535–553. |
| `thuburn_2000_numerical_simulations_rossby_haurwitz.pdf` | Thuburn, J., & Li, Y. (2000). Numerical simulations of Rossby–Haurwitz waves. *Tellus A* 52(2). **Confirmed** (read). Its reference list is the verified source for the Haurwitz (1940b) page range 254–267. |
| `longuethiggins_1968_laplace_tidal_eigenfunctions.pdf` | Longuet-Higgins, M. S. (1968). The eigenfunctions of Laplace's tidal equations over a sphere. *Phil. Trans. R. Soc. A* 262, 511–607. *(confirm citation)* |
| `swarztrauber_1985_vector_harmonic_analysis.pdf` | Swarztrauber, P. N., & Kasahara, A. (1985). Vector harmonic analysis of Laplace's tidal equations. *SIAM J. Sci. Stat. Comput.* 6. *(confirm citation)* |

> **`longuethiggins_1968_…` and `swarztrauber_1985_…` could not be obtained.**
> See [`MISSING.md`](MISSING.md) for full citations, DOIs, why the project is not
> blocked (the extension-B eigenfrequencies are derived and solved numerically,
> not read from a table), and the open-access substitutes to chase —
> `kasahara_1976_normal_modes_ultralong_waves.pdf` and
> `paldor_2015_shallow_water_waves.pdf`.

## Counter-propagating Rossby waves and shear instability

| Filename | Citation |
|----------|----------|
| `heifetz_1999_counter_propagating_rossby_waves.pdf` | **(held)** Heifetz, E., Bishop, C. H., & Alpert, P. (1999). Counter-propagating Rossby waves in the barotropic Rayleigh model of shear instability. *Q. J. R. Meteorol. Soc.* 125(560), 2835–2853. DOI [10.1002/qj.49712556004](https://doi.org/10.1002/qj.49712556004). Page 2838 is the verified source for the three CRW benchmark constants used in `theory/sympy_checks/check_crw_two_interface.py`. |
| `bretherton_1966_critical_layer_instability.pdf` | **(held)** Bretherton, F. P. (1966). Critical layer instability in baroclinic flows. *Q. J. R. Meteorol. Soc.* 92(393), 325–334. DOI [10.1002/qj.49709239302](https://doi.org/10.1002/qj.49709239302). Read in full; p. 331 Eq. (13) is the eddy-PV-flux integral and the Charney–Stern generalisation. |
| `heifetz_2004_crw_perspective_part1.pdf` | **(NOT held, and not cited)** Heifetz, E., Methven, J., Hoskins, B. J., & Bishop, C. H. (2004). The counter-propagating Rossby-wave perspective on baroclinic instability. I. *Q. J. R. Meteorol. Soc.* 130(596), 211–231. Named in an early session brief, but nothing in the derivation depends on it — the constants it was assumed to supply are in the 1999 paper above. |

> **Filename corrections applied in Session L3-PATCH.** Two files were named for
> the wrong paper, and both names have been fixed:
>
> - `haurwitz_1940_motion_of_atmospheric_disturbances.pdf` →
>   `haurwitz_1940a_beta_plane_extension.pdf`. The file is Haurwitz (1940a), the
>   beta-plane paper, not the spherical one the old name implied.
> - `heifetz_2004_counter_propagating_rossby_waves.pdf` →
>   `heifetz_1999_counter_propagating_rossby_waves.pdf`. The file is
>   Heifetz, Bishop & Alpert (1999). The citation in `derivations.tex` was
>   always to the 1999 paper; only the filename was wrong.

## Numerical framework

| Suggested filename | Citation |
|--------------------|----------|
| `burns_2020_dedalus.pdf` | Burns, K. J., Vasil, G. M., Oishi, J. S., Lecoanet, D., & Brown, B. P. (2020). Dedalus: A flexible framework for numerical simulations with spectral methods. *Phys. Rev. Research* 2, 023068. |
| `vasil_2019_tensor_calculus_spheres.pdf` | Vasil, G. M., Lecoanet, D., Burns, K. J., Oishi, J. S., & Brown, B. P. (2019). Tensor calculus in spherical coordinates using Jacobi polynomials. *J. Comput. Phys. X* 3, 100013. |

## Theory

| Suggested filename | Citation |
|--------------------|----------|
| `rossby_1939_relation_between_variations.pdf` | Rossby, C.-G. (1939). Relation between variations in the intensity of the zonal circulation of the atmosphere and the displacements of the semi-permanent centers of action. *J. Mar. Res.* 2, 38–55. |
| `haurwitz_1940a_beta_plane_extension.pdf` | **(held)** Haurwitz, B. (1940a). The motion of atmospheric disturbances. *J. Mar. Res.* 3(1), 35–50. The beta-plane, finite-lateral-extent extension of Rossby (1939). Its own text defers the spherical case "to a later paper". |
| `haurwitz_1940b_spherical_rossby_haurwitz_waves.pdf` | **(NOT held — operator action)** Haurwitz, B. (1940b). The motion of atmospheric disturbances on the spherical Earth. *J. Mar. Res.* 3(3), 254–267. This is the paper containing the spherical Rossby–Haurwitz result the project cites. Freely available, one browser click: [EliScholar record](https://elischolar.library.yale.edu/journal_of_marine_research/575/). Automated retrieval is blocked (the bepress platform answers scripted requests with HTTP 403), so it needs a human download. Not blocking: §5 of `theory/derivations.tex` derives the result from first principles and `check_rh_dispersion.py` verifies it symbolically. |
| `kuo_1949_dynamic_instability.pdf` | Kuo, H.-L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. *J. Meteorol.* 6(2), 105–122. |
| `hoskins_1985_isentropic_potential_vorticity.pdf` | **(held)** Hoskins, B. J., McIntyre, M. E., & Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. *Q. J. R. Meteorol. Soc.* 111(470), 877–946. DOI [10.1002/qj.49711147002](https://doi.org/10.1002/qj.49711147002). |
| `rhines_1975_waves_and_turbulence_beta_plane.pdf` | **(held)** Rhines, P. B. (1975). Waves and turbulence on a beta-plane. *J. Fluid Mech.* 69(3), 417–443. DOI [10.1017/S0022112075001504](https://doi.org/10.1017/S0022112075001504). |
| `vallis_1993_generation_of_mean_flows_and_jets.pdf` | **(held)** Vallis, G. K., & Maltrud, M. E. (1993). Generation of mean flows and jets on a beta plane and over topography. *J. Phys. Oceanogr.* 23(7), 1346–1362. DOI [10.1175/1520-0485(1993)023<1346:GOMFAJ>2.0.CO;2](https://doi.org/10.1175/1520-0485(1993)023%3C1346:GOMFAJ%3E2.0.CO;2). |
| `pedlosky_1987_gfd.pdf` | **(NOT held)** Pedlosky, J. (1987). *Geophysical Fluid Dynamics*, 2nd ed. Springer. No claim in `theory/derivations.tex` is attributed to it. |
| `vallis_2017_aofd.pdf` | **(NOT held)** Vallis, G. K. (2017). *Atmospheric and Oceanic Fluid Dynamics*, 2nd ed. Cambridge University Press. No claim in `theory/derivations.tex` is attributed to it. |
| `zeitlin_2018_gfd_rsw.pdf` | **(NOT held)** Zeitlin, V. (2018). *Geophysical Fluid Dynamics: Understanding (almost) Everything with Rotating Shallow Water Models.* Oxford University Press. No claim in `theory/derivations.tex` is attributed to it. |

## Observational data

| Suggested filename | Citation |
|--------------------|----------|
| `hersbach_2020_era5_global_reanalysis.pdf` | Hersbach, H., et al. (2020). The ERA5 global reanalysis. *Q. J. R. Meteorol. Soc.* 146(730), 1999–2049. |
| `kalnay_1996_ncep_ncar_reanalysis.pdf` | Kalnay, E., et al. (1996). The NCEP/NCAR 40-year reanalysis project. *Bull. Amer. Meteor. Soc.* 77(3), 437–471. |
