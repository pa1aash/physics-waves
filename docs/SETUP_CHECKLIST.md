# Setup checklist

Operator actions still outstanding after Session 00. Each is a manual step the
repository cannot perform for itself.

## Identity and metadata

- [x] Supply the author ORCID and fill it into **`CITATION.cff`** and
  **`codemeta.json`**. ORCID `0009-0006-7448-9488`; affiliation Indus
  International School, Pune, India; corresponding email
  `palaash.gang@indusschoolpune.com`. Full declarations in
  `manuscript/METADATA.yaml`.

## Manuscript

- [ ] Download the Springer Nature LaTeX bundle (v3.1, December 2024 or later)
  and unpack it into `manuscript/template/` (see that directory's README). Do
  not transcribe it — fetch it.

## Literature

- [ ] Place the reference PDFs listed in `docs/literature/README.md` into that
  directory, named `firstauthor_year_shorttitle.pdf`. Verify each *(confirm
  citation)* entry against its primary source.
- [ ] **Two extension-B references are unobtainable** (Longuet-Higgins 1968;
  Swarztrauber & Kasahara 1985) — recorded with DOIs and mitigation in
  `docs/literature/MISSING.md`. Not blocking. Obtain the open-access substitutes
  if possible (Kasahara 1976; Paldor 2015) and flag both for the Session L4
  corpus-adequacy audit.

## Data

- [x] Configure `~/.cdsapirc` for the Copernicus Climate Data Store
  (`scripts/setup_cds_credentials.sh`; file written mode 600 outside the repo).
  Both ERA5 dataset licences (hourly and monthly-means pressure levels) were
  probed `OK` (`src/data/probe_cds_licence.py`).
- [x] Acquire **D1** (ERA5 monthly DJF climatology 1991–2020) and **D2** (ERA5
  daily 500 hPa geopotential, two DJF seasons 2013/14 and 2015/16) via
  `make data-era5`. Both acquired, verified and provenance-tracked.
- [x] Acquire **D3** (NCEP/NCAR R1) for both DJF winters —
  `make data-ncep YEARS="2013 2014"` extended the Session-00 2015/16 pull.
- [x] **Rotate the Copernicus personal access token** now that acquisition is
  complete. Done in Session 00c: a freshly issued token replaced the old one via
  `scripts/setup_cds_credentials.sh`, the old token was invalidated on
  regeneration, and the `scripts/audit.sh` check-18 guard fragment was updated to
  the new prefix. The token lives only in `~/.cdsapirc` (never in the repository).
- [ ] *(optional)* **D4** torch-harmonics cross-check — not run this session.
  Enable in an isolated environment with
  `python src/data/fetch_torch_harmonics.py --include-d4` (advisory only).

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
