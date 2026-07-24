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

## D2 — ERA5 daily 500 hPa geopotential, two contrasting DJF seasons (acquired)

- **Status.** Acquired this session; licence probed `OK` before download.
- **Source / citation.** As D1 (ERA5, C3S; Hersbach et al. 2020).
- **Request (dataset `reanalysis-era5-pressure-levels`).** product_type
  `reanalysis`; variable geopotential; pressure level 500 hPa; time 00:00; grid
  1.0° × 1.0°; NetCDF, unarchived. Issued as **six monthly requests** (three per
  season) so a failure costs one month, not a season; day lists built from
  `calendar.monthrange` (2016 is a leap year, 2014 is not). All six succeeded;
  **no gaps.**
- **Seasons** (two-season design; see `docs/CONVENTIONS.md`): **DJF 2013/14**
  (ENSO-neutral) and **DJF 2015/16** (strong El Niño).
- **Geopotential units.** Variable `z` is the geopotential **Φ in m² s⁻²** (as
  D1); divide by `g` once for height. See the geopotential-units subsection above.
- **Grid.** Global 1°, latitude 181 (−90…+90), longitude 360 (0…359),
  pressure level 500 hPa (singleton). Each monthly file's day axis is daily.
- **Concatenation.** The three monthly files of each complete season are
  concatenated along time into one season file, asserted strictly increasing and
  gap-free at exactly one-day cadence, with the expected step count (90 for
  2013/14, 91 for the 2015/16 leap-year season). The monthly files are **retained**
  as the reproducible download units; the concatenated season files are derived.

Season **DJF 2013/14** (ENSO-neutral) — monthly units and the derived season file:

| Local filename | Steps | CDS request ID | Bytes | SHA-256 |
|----------------|-------|----------------|-------|---------|
| `era5_daily_z500_2013-12.nc` | 31 | `998f2eb2-fb77-4d6b-a153-e8ad7a5be259` | 3,096,571 | `f649fa278b530412d5171beafe2e7c18dd9d3f3a9ea3d1269c24f9dba4fe2d1a` |
| `era5_daily_z500_2014-01.nc` | 31 | `8c876e33-b4f0-4ad8-a7e4-6bd2e3e5b788` | 3,094,051 | `83db909e9e4ee74a7786cd7d833be219dfa0a3df17a9f1bb6c0b98191930553a` |
| `era5_daily_z500_2014-02.nc` | 28 | `a46b1195-3a22-498e-b1aa-78ca58e8c830` | 2,799,613 | `f0d4cd7ad02fb2057ae561520443ecbe6b086a40d531749539c10a2299dad7bc` |
| `era5_daily_z500_djf_2013-2014.nc` | **90** | (derived) | 9,062,923 | `3fd2589e2da9e012059acac8e85d4ef2560d67cb18ae363a1041f1849e686f2f` |

Season **DJF 2015/16** (strong El Niño) — monthly units and the derived season file:

| Local filename | Steps | CDS request ID | Bytes | SHA-256 |
|----------------|-------|----------------|-------|---------|
| `era5_daily_z500_2015-12.nc` | 31 | `79d117ff-f568-4866-a460-7260a2689db9` | 3,087,596 | `13ca8440f8dd0afe2e9d56d19bd22e1398ed3d157859fda6b7646c985574ca60` |
| `era5_daily_z500_2016-01.nc` | 31 | `ab238668-3ff6-41dd-818b-9b80dfc7393b` | 3,104,519 | `243cd2f0b33831acbfc0d1d3245268f4f540126ade8d8f3fe9d390ac6948efa1` |
| `era5_daily_z500_2016-02.nc` | 29 | `da41c6dd-135d-4a3e-975a-6758e0e8e07f` | 2,901,619 | `65cb3d3ea6a5887a0265c7f40b30295d2818612355f245ccbbbc0ff08b6ceffd` |
| `era5_daily_z500_djf_2015-2016.nc` | **91** | (derived) | 9,165,393 | `d913bd37c2c053f25ad8943d14ec12907759fab45afae42c147a9dcb479305a7` |

Retrieved 2026-07-24; each monthly request cleared the CDS queue in ≈ 30–46 s.
Machine-readable record: `_provenance_era5.json`.

### Dominant zonal wavenumber sanity check (D2)

The 500 hPa geopotential **height** anomaly about the seasonal mean at 50° N was
zonally Fourier-transformed for each season. Two spectra are reported because
they answer different physical questions:

| Season | Total-transient top-3 k | Synoptic band (high-pass <~10 d) top-3 k |
|--------|-------------------------|------------------------------------------|
| DJF 2013/14 (neutral) | 3, 2, 4 | **4, 5, 6** |
| DJF 2015/16 (El Niño) | 4, 3, 2 | **5, 4, 6** |

The **total** transient variance is dominated by planetary scales (k ≈ 3–4),
which is the expected mid-latitude behaviour — low-frequency planetary waves
carry most of the variance. When the low-frequency component is removed with a
centred 11-day high-pass, the **synoptic** storm-track band emerges with dominant
zonal wavenumbers **k = 4–6 in both seasons**, inside the anticipated 4–7 range.
The synoptic wavenumber is the observational quantity the idealised model is later
compared against, and it is essentially unchanged between the neutral and the
strongly perturbed winter — the robustness the two-season design was built to
test. The data are therefore fit for purpose; downstream comparison (Session L)
should use the synoptic-band wavenumber, not the raw total-variance peak.

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
