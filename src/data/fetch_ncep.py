"""Fetch NCEP/NCAR Reanalysis 1 daily pressure-level fields (dataset D3).

Downloads 500 hPa geopotential height (``hgt``) and 250 hPa zonal wind
(``uwnd``) as daily pressure-level files from NOAA PSL over plain HTTPS. The
per-year files carry every pressure level; the level selection (500 hPa,
250 hPa) is applied downstream at analysis time. Requires no credentials and no
queueing, which is why this dataset is the observational fallback for the
reanalysis diagnostics (blueprint section 7.3) and the mitigation for risk R1.

Behaviour
---------
* Config-driven: the year list is a command-line argument (default 2015, 2016,
  covering the DJF 2015/16 season).
* Idempotent: a file whose recorded SHA-256 still matches is skipped.
* Resumable: partial downloads continue via HTTP range requests.
* Never overwrites a verified file.
* On success writes a machine-readable provenance record to
  ``data/external/_provenance_ncep.json`` and appends a checksum line to
  ``data/external/checksums.sha256``.

The PSL directory layout has been reorganised historically, so the download
URL is discovered by probing a list of candidate patterns with HTTP HEAD and,
if all fail, by scraping the dataset landing page. The pattern that worked is
recorded in the provenance file so the next person does not repeat the search.

Usage
-----
    python src/data/fetch_ncep.py --years 2015 2016
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

try:
    from tqdm import tqdm
except Exception:  # pragma: no cover - tqdm is a declared dependency
    tqdm = None

# --- fixed acquisition spec (blueprint section 7.3) -------------------------
VARIABLES = ("hgt", "uwnd")
DEFAULT_YEARS = (2015, 2016)
LEVELS_OF_INTEREST = {"hgt": "500 hPa", "uwnd": "250 hPa"}

URL_PATTERNS = (
    "https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis/Dailies/pressure/{var}.{year}.nc",
    "https://downloads.psl.noaa.gov/Datasets/ncep.reanalysis.dailies/pressure/{var}.{year}.nc",
    "https://psl.noaa.gov/thredds/fileServer/Datasets/ncep.reanalysis/Dailies/pressure/{var}.{year}.nc",
)
LANDING_PAGE = "https://psl.noaa.gov/data/gridded/data.ncep.reanalysis.pressure.html"

USER_AGENT = "physics-waves-fetcher/0.1 (research; contact palaashgang@gmail.com)"
RETRIES = 3
CHUNK = 1 << 20  # 1 MiB

REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = REPO_ROOT / "data" / "external"
PROVENANCE = EXTERNAL / "_provenance_ncep.json"
CHECKSUMS = EXTERNAL / "checksums.sha256"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def _head(url: str) -> int | None:
    """Return the Content-Length for *url* if a HEAD returns 200, else None."""
    req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                length = resp.headers.get("Content-Length")
                return int(length) if length is not None else -1
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None
    return None


def _discover_url(var: str, year: int) -> tuple[str | None, int | None, str]:
    """Probe candidate patterns, then the landing page. Return (url, size, note)."""
    for pattern in URL_PATTERNS:
        url = pattern.format(var=var, year=year)
        size = _head(url)
        if size is not None:
            return url, size, f"candidate pattern: {pattern}"
    # fallback: scrape the landing page for a matching link
    try:
        req = Request(LANDING_PAGE, headers={"User-Agent": USER_AGENT})
        with urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
        needle = f"{var}.{year}.nc"
        idx = html.find(needle)
        if idx != -1:
            start = html.rfind('"', 0, idx) + 1
            end = html.find('"', idx)
            href = html[start:end]
            if href.startswith("/"):
                href = "https://psl.noaa.gov" + href
            size = _head(href)
            if size is not None:
                return href, size, f"discovered on landing page: {LANDING_PAGE}"
    except (HTTPError, URLError, TimeoutError):
        pass
    return None, None, "no working URL found"


def _download(url: str, dest: Path, expected_size: int | None) -> None:
    """Stream *url* to *dest*, resuming a partial file via a range request."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    existing = part.stat().st_size if part.exists() else 0

    headers = {"User-Agent": USER_AGENT}
    if existing:
        headers["Range"] = f"bytes={existing}-"

    req = Request(url, headers=headers)
    with urlopen(req, timeout=120) as resp:
        resuming = resp.status == 206
        mode = "ab" if resuming and existing else "wb"
        if mode == "wb":
            existing = 0
        total = expected_size if expected_size and expected_size > 0 else None
        bar = None
        if tqdm is not None:
            bar = tqdm(
                total=total,
                initial=existing,
                unit="B",
                unit_scale=True,
                desc=dest.name,
                leave=False,
            )
        with part.open(mode) as fh:
            while True:
                block = resp.read(CHUNK)
                if not block:
                    break
                fh.write(block)
                if bar is not None:
                    bar.update(len(block))
        if bar is not None:
            bar.close()
    part.replace(dest)


def _fetch_with_retries(url: str, dest: Path, expected_size: int | None) -> None:
    last_err: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            _download(url, dest, expected_size)
            return
        except (HTTPError, URLError, TimeoutError) as err:
            last_err = err
            backoff = 2 ** attempt
            print(f"    attempt {attempt}/{RETRIES} failed ({err}); retrying in {backoff}s")
            time.sleep(backoff)
    raise RuntimeError(f"download failed after {RETRIES} attempts: {url}") from last_err


def _sanity_check(path: Path) -> dict:
    """Open with xarray, print a summary, and assert the grid spans both poles."""
    import xarray as ds_mod  # imported lazily so probing does not need xarray

    with ds_mod.open_dataset(path) as ds:
        dims = {k: int(v) for k, v in ds.sizes.items()}
        lat_name = "lat" if "lat" in ds else ("latitude" if "latitude" in ds else None)
        lon_name = "lon" if "lon" in ds else ("longitude" if "longitude" in ds else None)
        summary = {"dims": dims, "data_vars": list(ds.data_vars)}
        print(f"    dims: {dims}")
        for coord in filter(None, (lat_name, lon_name, "level", "time")):
            if coord in ds:
                c = ds[coord]
                units = c.attrs.get("units", "")
                try:
                    lo, hi = float(c.min()), float(c.max())
                    print(f"    {coord}: [{lo:.3f}, {hi:.3f}] {units}")
                    summary[coord] = {"min": lo, "max": hi, "units": units}
                except Exception:
                    print(f"    {coord}: (non-numeric) {units}")
        if lat_name is not None:
            lat = ds[lat_name]
            assert float(lat.max()) >= 89.0 and float(lat.min()) <= -89.0, (
                "latitude coordinate does not span both poles"
            )
            print("    latitude spans both poles: OK")
    return summary


def _append_checksum(path: Path, digest: str) -> None:
    CHECKSUMS.parent.mkdir(parents=True, exist_ok=True)
    line = f"{digest}  {path.relative_to(EXTERNAL)}\n"
    existing = CHECKSUMS.read_text() if CHECKSUMS.exists() else ""
    kept = [ln for ln in existing.splitlines() if not ln.endswith(str(path.relative_to(EXTERNAL)))]
    CHECKSUMS.write_text("\n".join(kept + [line.rstrip()]) + "\n" if kept else line)


def _load_provenance() -> dict:
    if PROVENANCE.exists():
        return json.loads(PROVENANCE.read_text())
    return {"dataset_id": "D3", "files": {}}


def _save_provenance(record: dict) -> None:
    PROVENANCE.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def fetch(years: list[int]) -> int:
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    record = _load_provenance()
    record.setdefault("dataset_id", "D3")
    record.setdefault("source", "NCEP/NCAR Reanalysis 1 (NOAA PSL)")
    record.setdefault("citation", "Kalnay et al. (1996), Bull. Amer. Meteor. Soc. 77, 437-471")
    record.setdefault("licence", "NOAA PSL, freely available; cite NOAA/OAR/ESRL PSL.")
    record.setdefault("files", {})
    failures = 0

    for var in VARIABLES:
        for year in years:
            name = f"{var}.{year}.nc"
            dest = EXTERNAL / name
            print(f"[{name}] level of interest: {LEVELS_OF_INTEREST[var]}")

            prior = record["files"].get(name)
            if dest.exists() and prior and prior.get("sha256"):
                if _sha256(dest) == prior["sha256"]:
                    print("    already present and verified; skipping")
                    continue
                print("    checksum mismatch; re-downloading")

            url, size, note = _discover_url(var, year)
            if url is None:
                print(f"    ERROR: {note}")
                failures += 1
                record["files"][name] = {"status": "failed", "note": note,
                                         "attempted": _utc_now()}
                _save_provenance(record)
                continue
            print(f"    {note}")
            print(f"    downloading: {url}")
            try:
                _fetch_with_retries(url, dest, size)
            except RuntimeError as err:
                print(f"    ERROR: {err}")
                failures += 1
                record["files"][name] = {"status": "failed", "url": url,
                                         "note": str(err), "attempted": _utc_now()}
                _save_provenance(record)
                continue

            digest = _sha256(dest)
            summary = _sanity_check(dest)
            _append_checksum(dest, digest)
            record["files"][name] = {
                "status": "ok",
                "url": url,
                "url_note": note,
                "sha256": digest,
                "bytes": dest.stat().st_size,
                "level_of_interest": LEVELS_OF_INTEREST[var],
                "retrieved_utc": _utc_now(),
                **summary,
            }
            _save_provenance(record)
            print(f"    done: {dest.stat().st_size:,} bytes  sha256={digest[:16]}...")

    record["last_run_utc"] = _utc_now()
    _save_provenance(record)
    print(f"\nprovenance written to {PROVENANCE.relative_to(REPO_ROOT)}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch NCEP/NCAR Reanalysis 1 (D3).")
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=list(DEFAULT_YEARS),
        help="calendar years to download (default: 2015 2016)",
    )
    args = parser.parse_args(argv)
    failures = fetch(args.years)
    if failures:
        print(f"\n{failures} file(s) failed; see provenance record.", file=sys.stderr)
        return 1
    print("\nD3 acquisition complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
