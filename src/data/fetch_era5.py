"""Fetch ERA5 reanalysis datasets D1 and D2 from the Copernicus CDS.

D1 — ERA5 monthly means, DJF climatology (u, v, geopotential at 250/300/500 hPa,
     1991–2020, months 12/01/02). Small; retrieved synchronously.
D2 — ERA5 daily 500 hPa geopotential for one DJF season (2015-12 … 2016-02).
     Submitted as three monthly requests, asynchronously, so a failure costs one
     month rather than the whole season.

Credentials are read from ``~/.cdsapirc``, which must point at the current CDS
endpoint ``https://cds.climate.copernicus.eu/api``. A legacy URL raises a clear
error naming the file.

Behaviour matches the project fetcher contract: idempotent (verified files are
skipped by checksum), never overwrites a verified file, and on success writes a
provenance record and appends a SHA-256 to ``data/external/``.

Usage
-----
    python src/data/fetch_era5.py            # D1 and D2
    python src/data/fetch_era5.py --only d1  # just the monthly climatology
    python src/data/fetch_era5.py --only d2  # just the daily season
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CHUNK = 1 << 20
REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = REPO_ROOT / "data" / "external"
PROVENANCE = EXTERNAL / "_provenance_era5.json"
CHECKSUMS = EXTERNAL / "checksums.sha256"
CDS_LOG = REPO_ROOT / "logs" / "cds_requests.log"
CDS_ENDPOINT = "https://cds.climate.copernicus.eu/api"

D1_TARGET = "era5_monthly_djf_1991-2020_uvz_250-300-500.nc"
D2_TARGET = "era5_daily_z500_djf_2015-2016.nc"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _record_success(record: dict, name: str, dataset: str, request: dict) -> None:
    path = EXTERNAL / name
    digest = _sha256(path)
    _append_checksum(path, digest)
    record["files"][name] = {
        "status": "ok",
        "dataset": dataset,
        "request": request,
        "sha256": digest,
        "bytes": path.stat().st_size,
        "retrieved_utc": _utc_now(),
    }
    _save_provenance(record)
    print(f"    done: {path.stat().st_size:,} bytes  sha256={digest[:16]}...")


def _already_have(record: dict, name: str) -> bool:
    path = EXTERNAL / name
    prior = record["files"].get(name)
    if path.exists() and prior and prior.get("sha256") == _sha256(path):
        print(f"    {name} already present and verified; skipping")
        return True
    return False


def fetch_d1(record: dict) -> None:
    import cdsapi

    print(f"[D1] ERA5 monthly means DJF climatology -> {D1_TARGET}")
    if _already_have(record, D1_TARGET):
        return
    dataset = "reanalysis-era5-pressure-levels-monthly-means"
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
    _log_request(f"D1 submit {dataset}")
    client.retrieve(dataset, request, str(EXTERNAL / D1_TARGET))
    _record_success(record, D1_TARGET, dataset, request)


def _d2_month_requests() -> list[tuple[str, dict]]:
    dataset = "reanalysis-era5-pressure-levels"
    base = {
        "product_type": ["reanalysis"],
        "variable": ["geopotential"],
        "pressure_level": ["500"],
        "time": ["00:00"],
        "grid": [1.0, 1.0],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    months = [
        ("2015", "12", [f"{d:02d}" for d in range(1, 32)]),
        ("2016", "01", [f"{d:02d}" for d in range(1, 32)]),
        ("2016", "02", [f"{d:02d}" for d in range(1, 30)]),
    ]
    out = []
    for year, month, days in months:
        req = dict(base, year=[year], month=[month], day=days)
        out.append((dataset, req))
    return out


def fetch_d2(record: dict) -> None:
    """Fetch D2 as three monthly requests, submitted asynchronously and polled."""
    import cdsapi

    print(f"[D2] ERA5 daily 500 hPa geopotential DJF 2015/16 -> {D2_TARGET}")
    parts_dir = EXTERNAL / "_era5_z500_parts"
    parts_dir.mkdir(parents=True, exist_ok=True)

    client = cdsapi.Client(wait_until_complete=False)
    remotes = []
    for dataset, req in _d2_month_requests():
        tag = f"{req['year'][0]}-{req['month'][0]}"
        target = parts_dir / f"z500_{tag}.nc"
        if target.exists() and target.stat().st_size > 0:
            print(f"    part {tag} already present; skipping submit")
            remotes.append((tag, None, target))
            continue
        remote = client.retrieve(dataset, req)
        rid = getattr(remote, "reply", {}).get("request_id", "unknown")
        _log_request(f"D2 submit {tag} request_id={rid}")
        print(f"    submitted {tag}: request_id={rid}")
        remotes.append((tag, remote, target))

    for tag, remote, target in remotes:
        if remote is None:
            continue
        delay = 15
        while True:
            try:
                remote.update()
                state = remote.reply.get("state")
            except Exception as err:  # noqa: BLE001 - report and keep polling
                print(f"    {tag}: poll error ({err}); retrying")
                state = None
            if state == "completed":
                remote.download(str(target))
                _log_request(f"D2 download {tag} -> {target.name}")
                print(f"    {tag}: downloaded")
                break
            if state == "failed":
                raise RuntimeError(f"D2 request {tag} failed: {remote.reply}")
            pos = remote.reply.get("request_position") if remote.reply else None
            where = f" queue position {pos}" if pos is not None else ""
            print(f"    {tag}: state={state}{where}; waiting {delay}s")
            time.sleep(delay)
            delay = min(delay * 2, 300)

    _concat_d2_parts(parts_dir, EXTERNAL / D2_TARGET)
    _record_success(record, D2_TARGET, "reanalysis-era5-pressure-levels",
                    {"note": "three monthly requests concatenated", "levels": ["500"]})


def _concat_d2_parts(parts_dir: Path, target: Path) -> None:
    import xarray as xr

    parts = sorted(parts_dir.glob("z500_*.nc"))
    if not parts:
        raise RuntimeError("no D2 monthly parts to concatenate")
    print(f"    concatenating {len(parts)} monthly parts -> {target.name}")
    ds = xr.open_mfdataset(parts, combine="by_coords")
    ds.to_netcdf(target)
    ds.close()


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
