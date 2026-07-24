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
  lon 0…357.5, Δ = 2.5° covering the full 360°). Latitude spans both poles.
- **Vertical.** All 17 standard pressure levels (10–1000 hPa). Both 500 hPa
  (`hgt`, level of interest) and 250 hPa (`uwnd`, level of interest) are present
  in every file; the selection is applied downstream.
- **`hgt` units.** Geopotential **height** in metres (NCEP convention: the field
  is `Z`, not the geopotential `Φ`), confirmed by the `units` attribute (`m`) and
  by magnitude (500 hPa values ≈ 5.5 × 10³ m). This differs from ERA5, whose
  archived variable is the geopotential `Φ` in m² s⁻² — see D1 below.
- **Temporal coverage.** Daily. **Two contrasting DJF winters** are covered, per
  the two-season observational design (see `docs/CONVENTIONS.md`, "Two
  contrasting DJF seasons"): **DJF 2013/14** (ENSO-neutral, a typical background
  state) and **DJF 2015/16** (strong El Niño, a strongly perturbed background
  state). Files are per calendar year: 2013, 2014 and 2015 (365 days each) and
  2016 (366 days, leap year). Each winter's Dec–Jan–Feb season is spanned by its
  two bracketing calendar-year files. Every file's time axis is gap-free from
  Jan 1 to Dec 31 of its year.
- **Format.** NetCDF.
- **Retrieved (UTC).** 2015/16 files 2026-07-24 (Session 00); 2013/14 files
  2026-07-24 (this session).

DJF 2015/16 season (Session 00):

| Local filename | Bytes | SHA-256 |
|----------------|-------|---------|
| `hgt.2015.nc`  | 85,192,630  | `ddff5514c5f72292939c19a64a5ef8b2a8827bafa0c3db81f520995650256640` |
| `hgt.2016.nc`  | 85,486,470  | `f36b57f7c6dada285380945e695bb1244b9a19431b9d0313538e5fc1db9fc7ce` |
| `uwnd.2015.nc` | 156,826,090 | `4050e2bc434881dbb5f2d04b3b0c37ef45da0515f820a2857383df0829a6b0e2` |
| `uwnd.2016.nc` | 156,746,731 | `02175bfd31e4fa487a1b3351fcd632be5840b1e9ac1be8eb031e829a3130cf81` |

DJF 2013/14 season (this session):

| Local filename | Bytes | SHA-256 |
|----------------|-------|---------|
| `hgt.2013.nc`  | 84,752,852  | `57d938a92bfba3db75a4143db0e3ae83494dbe3733e61a0739bddcaada9b1ca4` |
| `hgt.2014.nc`  | 84,885,420  | `3e1cf6ef52fbbadf6170410d72771bac2fa87a7bdb7206d33763d2fce117e838` |
| `uwnd.2013.nc` | 165,259,853 | `effea491b9369fb2f71178375bca9ca62c8a218dd8b6d93596f8d5ee5fe835a1` |
| `uwnd.2014.nc` | 163,439,156 | `05c67e80994c0fb78ffe4812c5d87404b1a216d523d68574fc204cec11e061e6` |

The winter-2013/14 files were fetched with `make data-ncep YEARS="2013 2014"`,
which routes the year list through a Makefile variable rather than hard-coding it
in the fetcher. Machine-readable record: `_provenance_ncep.json`.

---

## D1 — ERA5 monthly means, DJF climatology (acquired)

- **Status.** Acquired this session. The Copernicus licence for the
  monthly-means dataset was probed `OK` before download
  (`src/data/probe_cds_licence.py`).
- **Source.** ERA5, Copernicus Climate Change Service (C3S), Climate Data Store.
- **Citation.** Hersbach, H., et al. (2020). The ERA5 global reanalysis.
  *Q. J. R. Meteorol. Soc.* 146(730), 1999–2049.
- **Request (dataset `reanalysis-era5-pressure-levels-monthly-means`).**
  product_type `monthly_averaged_reanalysis`; variables u-component of wind,
  v-component of wind, geopotential; pressure levels 250/300/500 hPa; years
  1991–2020; months 12/01/02; time 00:00; grid 1.0° × 1.0°; NetCDF, unarchived.
- **Coverage.** 90 monthly-mean time steps (30 years × 3 DJF months,
  1991-01 … 2020-12). Global 1° grid: latitude 181 points (−90…+90), longitude
  360 points (0…359, Δ = 1°). Three pressure levels, stored descending
  (500, 300, 250) in the archived file and reindexed to ascending
  (250, 300, 500) at read time — note this before any level indexing downstream.
- **Geopotential units.** The archived variable `z` is the **geopotential Φ in
  m² s⁻²** (units attribute `m**2 s**-2`; mean |Φ| at 500 hPa = 5.39 × 10⁴
  m² s⁻²), *not* geopotential height. See the dedicated subsection below.
- **Physical sanity check (printed).** The DJF-mean zonal-mean zonal wind at
  250 hPa peaks at **39.1 m s⁻¹ at 31° N** — the subtropical jet, in the
  expected place (≈ 30° N) and within the expected 25–40 m s⁻¹ range.
- **No all-NaN slices** in `u`, `v` or `z`.
- **CDS request ID.** `2f6bdc56-2d57-4753-83d8-00701f9383b7`. Queue + processing
  ≈ 80 s; download ≈ 105 s.
- **Retrieved (UTC).** 2026-07-24T16:03:15Z.

| Local filename | Bytes | SHA-256 |
|----------------|-------|---------|
| `era5_monthly_djf_1991-2020_uvz_250-300-500.nc` | 96,718,158 | `bf10af34cdcd3e29df78ad20b504728b0de1c44b69228e151e15ec178981e67f` |

Machine-readable record: `_provenance_era5.json`.

### Geopotential units — ERA5 Φ (m² s⁻²) vs NCEP Z (m)

This distinction is a known trap and is recorded here explicitly because getting
it wrong corrupts the jet and geostrophic-wind diagnostics by a factor of about
`g = 9.80665 m s⁻²`.

- **ERA5** (D1, D2): the archived geopotential variable `z` is the geopotential
  **Φ**, in **m² s⁻²**. Confirmed two independent ways — the `units` attribute
  reads `m**2 s**-2`, and the magnitude at 500 hPa is `⟨|z|⟩ ≈ 5.39 × 10⁴`,
  which is `Φ`, not the height `Z ≈ 5.5 × 10³ m`. To obtain geopotential height,
  divide by `g` exactly once: `Z = Φ / g`.
- **NCEP/NCAR R1** (D3): the archived variable `hgt` is already the geopotential
  **height Z**, in **metres** (`units = m`, magnitude ≈ 5.5 × 10³ m at 500 hPa).
  It must **not** be divided by `g`.

Physically the two carry the same information — Φ is the work per unit mass to
raise a parcel to a pressure surface, and `Z = Φ/g` expresses that as a height —
but the numerical factor differs by ~9.8. Any code that mixes the two reanalyses
(for example, the two-season cross-check) must convert ERA5 `z` to height before
comparing it with NCEP `hgt`. Session L8 divides ERA5 `z` by `g` **once**;
doing so twice, or not at all, is the failure this note guards against.

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
