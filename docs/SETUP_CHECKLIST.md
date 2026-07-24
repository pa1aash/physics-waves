# Setup checklist

Operator actions still outstanding after Session 00. Each is a manual step the
repository cannot perform for itself.

## Identity and metadata

- [ ] Supply an ORCID and replace `ORCID_PLACEHOLDER` in **`CITATION.cff`** and
  **`codemeta.json`**.

## Manuscript

- [ ] Download the Springer Nature LaTeX bundle (v3.1, December 2024 or later)
  and unpack it into `manuscript/template/` (see that directory's README). Do
  not transcribe it — fetch it.

## Literature

- [ ] Place the reference PDFs listed in `docs/literature/README.md` into that
  directory, named `firstauthor_year_shorttitle.pdf`. Verify each *(confirm
  citation)* entry against its primary source.

## Data

- [ ] Configure `~/.cdsapirc` for the Copernicus Climate Data Store and run
  `make data-era5` to acquire ERA5 datasets D1 and D2. These were **deferred** in
  Session 00 because no credentials were present. Required form:

  ```
  url: https://cds.climate.copernicus.eu/api
  key: <PERSONAL-ACCESS-TOKEN>
  ```

  Register at <https://cds.climate.copernicus.eu>, accept the licence on both the
  ERA5 hourly and monthly-means pressure-level dataset pages, then re-run.
  NCEP/NCAR Reanalysis 1 (D3) has already been acquired and is a sufficient
  fallback for every diagnostic in blueprint §7.3 — the project is **not
  blocked**.

## Compute

- [ ] Provision the RunPod CPU pod (`cpu5c` flavour, 16–32 vCPU, 64–128 GB RAM,
  200 GB network volume) for the L1–L3 rungs. Build the container from
  `Dockerfile`. Do not provision a GPU instance — Dedalus has no CUDA backend.

## Run matrix

- [ ] Confirm which entries in `configs/RUN_REGISTRY.md` are final. Row counts in
  the phase-speed and instability campaigns are provisional until the first L0
  exploratory runs (blueprint §8 revision notes).

## Release

- [ ] Before the Zenodo deposit (Session L13), run `make licenses` to fetch the
  CC BY 4.0 legal code into `LICENSE-DATA.full`, and include it in the deposit.
  `LICENSE-DATA` itself is only a pointer, per the third-party-text rule in
  `docs/CONVENTIONS.md`.
