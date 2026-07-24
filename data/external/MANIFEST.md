# External data manifest

Provenance for every external dataset used by the project. The binary files
themselves are **not committed** (they are gitignored); this manifest, the
`checksums.sha256` file, and the machine-readable `_provenance_*.json` records
are what is tracked. Reproduce every download with `make data`.

## Licence and redistribution

Neither ERA5 nor NCEP/NCAR raw files are redistributed through this repository.
Any user must re-download them under the providers' own licence terms:

- **ERA5** is provided by the Copernicus Climate Change Service (C3S) via the
  Climate Data Store and must be attributed to C3S accordingly.
- **NCEP/NCAR Reanalysis 1** is provided by NOAA PSL, Boulder, Colorado, and
  should be credited to NOAA/OAR/ESRL PSL.

---

## D3 — NCEP/NCAR Reanalysis 1 (acquired)

- **Source.** NCEP/NCAR Reanalysis 1, NOAA Physical Sciences Laboratory (PSL).
- **Citation.** Kalnay, E., et al. (1996). The NCEP/NCAR 40-year reanalysis
  project. *Bull. Amer. Meteor. Soc.* 77(3), 437–471.
- **Access.** Plain HTTPS, no credentials. The PSL directory layout was
  discovered by probing candidate patterns; the working pattern was:
  `https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis/Dailies/pressure/{var}.{year}.nc`
- **Variables.** `hgt` (geopotential height; level of interest **500 hPa**) and
  `uwnd` (zonal wind; level of interest **250 hPa**). Files carry all 17
  pressure levels (10–1000 mb); the level selection is applied downstream.
- **Spatial grid.** 2.5° global, 73 latitudes × 144 longitudes (lat +90…−90,
  lon 0…357.5). Latitude spans both poles.
- **Temporal coverage.** Daily; calendar years 2015 (365 days) and 2016
  (366 days), covering the full DJF 2015/16 season.
- **Format.** NetCDF.
- **Retrieved (UTC).** 2026-07-24.

| Local filename | Bytes | SHA-256 |
|----------------|-------|---------|
| `hgt.2015.nc`  | 85,192,630  | `ddff5514c5f72292939c19a64a5ef8b2a8827bafa0c3db81f520995650256640` |
| `hgt.2016.nc`  | 85,486,470  | `f36b57f7c6dada285380945e695bb1244b9a19431b9d0313538e5fc1db9fc7ce` |
| `uwnd.2015.nc` | 156,826,090 | `4050e2bc434881dbb5f2d04b3b0c37ef45da0515f820a2857383df0829a6b0e2` |
| `uwnd.2016.nc` | 156,746,731 | `02175bfd31e4fa487a1b3351fcd632be5840b1e9ac1be8eb031e829a3130cf81` |

Machine-readable record: `_provenance_ncep.json`.

---

## D1 — ERA5 monthly means, DJF climatology (deferred)

- **Status.** Deferred in Session 00 — no `~/.cdsapirc` credentials present.
  Run `make data-era5` after configuring credentials (see
  `docs/SETUP_CHECKLIST.md`).
- **Source.** ERA5, Copernicus Climate Change Service (C3S), Climate Data Store.
- **Citation.** Hersbach, H., et al. (2020). The ERA5 global reanalysis.
  *Q. J. R. Meteorol. Soc.* 146(730), 1999–2049.
- **Request (dataset `reanalysis-era5-pressure-levels-monthly-means`).**
  product_type `monthly_averaged_reanalysis`; variables u-component of wind,
  v-component of wind, geopotential; pressure levels 250/300/500 hPa; years
  1991–2020; months 12/01/02; time 00:00; grid 1.0° × 1.0°; NetCDF, unarchived.
- **Target filename.** `era5_monthly_djf_1991-2020_uvz_250-300-500.nc`.

---

## D2 — ERA5 daily 500 hPa geopotential, one DJF season (deferred)

- **Status.** Deferred in Session 00 — no credentials present.
- **Source / citation.** As D1.
- **Request (dataset `reanalysis-era5-pressure-levels`).** product_type
  `reanalysis`; variable geopotential; pressure level 500 hPa; dates
  2015-12-01 … 2016-02-29; time 00:00; grid 1.0° × 1.0°; NetCDF, unarchived.
  Submitted as three monthly requests; CDS request IDs are logged to
  `logs/cds_requests.log`.
- **Target filename.** `era5_daily_z500_djf_2015-2016.nc`.

---

## D4 — torch-harmonics spherical shallow-water cross-check (optional)

- **Status.** Optional; not attempted in Session 00. Enable with
  `python src/data/fetch_torch_harmonics.py --include-d4`.
- **Source.** Independent spectral shallow-water solver in the `torch-harmonics`
  package (blueprint §7.5). Never a dependency of any downstream stage.
- **Path selection.** The fetcher probes the installed package API and records
  whether a packaged dataset was used or a short Earth-matched reference
  integration was produced. That choice is written to
  `_provenance_torch_harmonics.json` and must be echoed here when D4 is run.
