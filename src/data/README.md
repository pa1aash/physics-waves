# src/data/

External-dataset fetchers (implemented): `fetch_ncep.py` (NCEP/NCAR Reanalysis 1,
D3), `fetch_era5.py` (ERA5 monthly and daily, D1/D2), `fetch_torch_harmonics.py`
(optional cross-check, D4). Each is config-driven, idempotent and resumable, and
writes provenance plus a SHA-256 to `data/external/`. Never commits binary data.
