"""Fetch ERA5 reanalysis datasets D1 and D2 from the Copernicus CDS.

D1 — ERA5 monthly means, DJF climatology (u, v, geopotential at 250/300/500 hPa,
     1991–2020, months 12/01/02). Small; retrieved synchronously.
D2 — ERA5 daily 500 hPa geopotential for **two contrasting DJF seasons**
     (2013/14, ENSO-neutral; 2015/16, strong El Niño), per the two-season
     observational design in ``docs/CONVENTIONS.md``. Each season is submitted as
     three monthly requests so a failure costs one month rather than a season;
     the three monthly files of a complete season are concatenated along time
     into one season file, and the monthly files are retained as the reproducible
     download units.

Credentials are read from ``~/.cdsapirc``, which must point at the current CDS
endpoint ``https://cds.climate.copernicus.eu/api``. A legacy URL raises a clear
error naming the file.

The monthly requests are issued with the blocking client. cdsapi 0.7.x wraps the
new CADS ``datapi`` backend and its ``Result`` object no longer exposes the
``reply``/``state`` queue fields an asynchronous poll loop would need; the
blocking client is the reliable interface and prints its own status transitions.
Because the requests are split one-per-month, a failure still costs a single
month, which is the robustness the split was for. Each month is retried up to
three times with exponential backoff before it is recorded as failed; a season
with any failed month is left un-concatenated and the gap is recorded.

Behaviour matches the project fetcher contract: idempotent (verified files are
skipped by checksum), never overwrites a verified file, and on success writes a
provenance record and appends a SHA-256 to ``data/external/``.

Usage
-----
    python src/data/fetch_era5.py            # D1 and D2
    python src/data/fetch_era5.py --only d1  # just the monthly climatology
    python src/data/fetch_era5.py --only d2  # just the daily seasons
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

CHUNK = 1 << 20
REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = REPO_ROOT / "data" / "external"
PROVENANCE = EXTERNAL / "_provenance_era5.json"
CHECKSUMS = EXTERNAL / "checksums.sha256"
CDS_LOG = REPO_ROOT / "logs" / "cds_requests.log"
CDS_ENDPOINT = "https://cds.climate.copernicus.eu/api"

D1_DATASET = "reanalysis-era5-pressure-levels-monthly-means"
D1_TARGET = "era5_monthly_djf_1991-2020_uvz_250-300-500.nc"

D2_DATASET = "reanalysis-era5-pressure-levels"
# Two contrasting DJF seasons -> (year, month) parts. Each season is Dec + Jan +
# Feb, spanning two calendar years.
D2_SEASONS: dict[str, list[tuple[int, int]]] = {
    "2013-2014": [(2013, 12), (2014, 1), (2014, 2)],
    "2015-2016": [(2015, 12), (2016, 1), (2016, 2)],
}
# 31 + 31 + 28 = 90 (2014 not a leap year); 31 + 31 + 29 = 91 (2016 is).
D2_EXPECTED_STEPS = {"2013-2014": 90, "2015-2016": 91}
D2_RETRIES = 3


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def _append_checksum(path: Path, digest: str) -> None:
    CHECKSUMS.parent.mkdir(parents=True, exist_ok=True)
    rel = path.name
    kept = []
    if CHECKSUMS.exists():
        kept = [ln for ln in CHECKSUMS.read_text().splitlines() if ln and not ln.endswith(rel)]
    kept.append(f"{digest}  {rel}")
    CHECKSUMS.write_text("\n".join(kept) + "\n")


def _load_provenance() -> dict:
    if PROVENANCE.exists():
        return json.loads(PROVENANCE.read_text())
    return {
        "dataset_ids": ["D1", "D2"],
        "source": "ERA5, Copernicus Climate Change Service (C3S), Climate Data Store",
        "citation": "Hersbach et al. (2020), Q. J. R. Meteorol. Soc. 146, 1999-2049",
        "licence": (
            "Copernicus Climate Change Service (C3S) Climate Data Store. "
            "ERA5 must be attributed to C3S; not redistributed via this repository."
        ),
        "files": {},
    }


def _save_provenance(record: dict) -> None:
    PROVENANCE.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def _log_request(message: str) -> None:
    CDS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with CDS_LOG.open("a") as fh:
        fh.write(f"{_utc_now()}  {message}\n")


def check_credentials() -> None:
    """Assert ~/.cdsapirc exists and points at the current CDS endpoint."""
    rc = Path.home() / ".cdsapirc"
    if not rc.exists():
        raise SystemExit(
            f"{rc} not found. Register at https://cds.climate.copernicus.eu, "
            "accept the ERA5 licences, and create the file. See docs/SETUP_CHECKLIST.md."
        )
    text = rc.read_text()
    if CDS_ENDPOINT not in text:
        raise SystemExit(
            f"{rc} does not point at the current CDS endpoint '{CDS_ENDPOINT}'. "
            "Legacy CDS URLs no longer work; update the 'url:' line."
        )


def _record_file(record: dict, name: str, dataset: str, extra: dict) -> None:
    """Checksum a downloaded/derived file and write its provenance entry."""
    path = EXTERNAL / name
    digest = _sha256(path)
    _append_checksum(path, digest)
    entry = {
        "status": "ok",
        "dataset": dataset,
        "sha256": digest,
        "bytes": path.stat().st_size,
        "retrieved_utc": _utc_now(),
    }
    entry.update(extra)
    record["files"][name] = entry
    _save_provenance(record)
    print(f"    recorded {name}: {path.stat().st_size:,} bytes  sha256={digest[:16]}...")


def _already_have(record: dict, name: str) -> bool:
    path = EXTERNAL / name
    prior = record["files"].get(name)
    if path.exists() and prior and prior.get("sha256") == _sha256(path):
        print(f"    {name} already present and verified; skipping")
        return True
    return False


# --------------------------------------------------------------------------- D1
def fetch_d1(record: dict) -> None:
    import cdsapi

    print(f"[D1] ERA5 monthly means DJF climatology -> {D1_TARGET}")
    if _already_have(record, D1_TARGET):
        return
    request = {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": ["u_component_of_wind", "v_component_of_wind", "geopotential"],
        "pressure_level": ["250", "300", "500"],
        "year": [str(y) for y in range(1991, 2021)],
        "month": ["12", "01", "02"],
        "time": ["00:00"],
        "grid": [1.0, 1.0],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    client = cdsapi.Client()
    _log_request(f"D1 submit {D1_DATASET}")
    client.retrieve(D1_DATASET, request, str(EXTERNAL / D1_TARGET))
    _record_file(record, D1_TARGET, D1_DATASET, {"request": request})


# --------------------------------------------------------------------------- D2
def _days_of(year: int, month: int) -> list[str]:
    """Day-of-month strings from calendar.monthrange (handles leap years)."""
    n = calendar.monthrange(year, month)[1]
    return [f"{d:02d}" for d in range(1, n + 1)]


def _d2_month_name(year: int, month: int) -> str:
    return f"era5_daily_z500_{year}-{month:02d}.nc"


def _d2_season_name(season: str) -> str:
    return f"era5_daily_z500_djf_{season}.nc"


def _d2_request(year: int, month: int) -> dict:
    return {
        "product_type": ["reanalysis"],
        "variable": ["geopotential"],
        "pressure_level": ["500"],
        "year": [str(year)],
        "month": [f"{month:02d}"],
        "day": _days_of(year, month),
        "time": ["00:00"],
        "grid": [1.0, 1.0],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def _fetch_month(client, record: dict, year: int, month: int) -> bool:
    """Retrieve one month of daily z500, with retry. Returns True on success."""
    name = _d2_month_name(year, month)
    if _already_have(record, name):
        return True
    target = EXTERNAL / name
    part = target.with_suffix(target.suffix + ".part")
    request = _d2_request(year, month)
    start = time.time()
    for attempt in range(1, D2_RETRIES + 1):
        try:
            _log_request(f"D2 submit {name} (attempt {attempt})")
            print(f"    {name}: submitting (attempt {attempt}/{D2_RETRIES}) ...", flush=True)
            client.retrieve(D2_DATASET, request, str(part))
            part.replace(target)
            _log_request(f"D2 download {name} ({int(time.time() - start)}s)")
            print(f"    {name}: downloaded in {int(time.time() - start)}s")
            return True
        except Exception as err:  # noqa: BLE001 - retry then record failure
            if part.exists():
                part.unlink()  # never leave an unverified partial
            backoff = 2**attempt
            print(f"    {name}: attempt {attempt} failed ({err}); retry in {backoff}s")
            if attempt < D2_RETRIES:
                time.sleep(backoff)
    print(f"    {name}: FAILED after {D2_RETRIES} attempts")
    return False


def _concat_season(parts: list[Path], target: Path, expected_steps: int) -> int:
    """Concatenate monthly parts along time; assert monotonic, gap-free, sized."""
    import numpy as np
    import xarray as xr

    ds = xr.open_mfdataset([str(p) for p in parts], combine="by_coords")
    tname = next(
        (c for c in list(ds.coords) + list(ds.dims) if np.issubdtype(ds[c].dtype, np.datetime64)),
        None,
    )
    if tname is None:
        raise RuntimeError(f"{target.name}: no datetime coordinate found")
    ds = ds.sortby(tname)
    t = ds[tname].values
    n = int(len(t))
    if n != expected_steps:
        raise RuntimeError(f"{target.name}: expected {expected_steps} steps, got {n}")
    diffs = np.diff(t)
    if not (diffs > np.timedelta64(0, "s")).all():
        raise RuntimeError(f"{target.name}: time axis not strictly increasing")
    one_day = np.timedelta64(1, "D")
    if not (diffs == one_day).all():
        bad = [str(t[i])[:10] for i in range(len(diffs)) if diffs[i] != one_day]
        raise RuntimeError(f"{target.name}: non-daily gap(s) near {bad}")
    ds.load()
    if target.exists():
        target.unlink()
    ds.to_netcdf(target)
    ds.close()
    return n


def fetch_d2(record: dict) -> None:
    import cdsapi

    print("[D2] ERA5 daily 500 hPa geopotential, two contrasting DJF seasons")
    client = cdsapi.Client()
    for season, months in D2_SEASONS.items():
        print(f"  season {season}: {len(months)} monthly requests")
        ok_parts: list[Path] = []
        failed: list[str] = []
        for year, month in months:
            name = _d2_month_name(year, month)
            if _fetch_month(client, record, year, month):
                _record_file(
                    record,
                    name,
                    D2_DATASET,
                    {"note": "monthly download unit", "season": season},
                )
                ok_parts.append(EXTERNAL / name)
            else:
                failed.append(name)

        if failed:
            print(f"  season {season}: NOT concatenating; failed months: {failed}")
            record.setdefault("gaps", []).append(
                {
                    "season": season,
                    "failed_months": failed,
                    "note": "monthly request(s) failed; season left un-concatenated",
                }
            )
            _save_provenance(record)
            continue

        target = EXTERNAL / _d2_season_name(season)
        steps = _concat_season(sorted(ok_parts), target, D2_EXPECTED_STEPS[season])
        _record_file(
            record,
            target.name,
            D2_DATASET,
            {
                "note": f"season {season} concatenation of {len(ok_parts)} monthly files",
                "time_steps": steps,
                "derived_from": [p.name for p in sorted(ok_parts)],
            },
        )
        print(
            f"  season {season}: concatenated {len(ok_parts)} months -> "
            f"{target.name} ({steps} steps)"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch ERA5 datasets D1 and D2.")
    parser.add_argument("--only", choices=["d1", "d2"], help="fetch only one dataset")
    args = parser.parse_args(argv)

    check_credentials()
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    record = _load_provenance()
    try:
        if args.only in (None, "d1"):
            fetch_d1(record)
        if args.only in (None, "d2"):
            fetch_d2(record)
    except Exception as err:  # noqa: BLE001 - record and surface the failure
        record.setdefault("errors", []).append({"when": _utc_now(), "error": str(err)})
        _save_provenance(record)
        print(f"ERROR: {err}", file=sys.stderr)
        return 1

    record["last_run_utc"] = _utc_now()
    _save_provenance(record)
    print("\nERA5 acquisition complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
