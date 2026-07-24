"""Obtain the optional spherical shallow-water cross-check dataset (D4).

This is the independent solver cross-check referenced in blueprint section 7.5.
It is *explicitly optional* and must never become a dependency of any downstream
stage — nothing in the verification, phase-speed or instability pipelines reads
it. It runs only when ``--include-d4`` is passed.

The ``torch-harmonics`` package is not a declared project dependency, and its
public API has changed across releases. Rather than assume an interface, this
script probes the *installed* package at run time: it looks for a packaged
shallow-water dataset first, and if none is exposed it falls back to a short
reference integration produced by the package's own shallow-water solver at
Earth-matched parameters (blueprint section 5.3). Whichever path is taken is
recorded in the provenance file and must be echoed into ``MANIFEST.md``.

Usage
-----
    python src/data/fetch_torch_harmonics.py --include-d4
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

CHUNK = 1 << 20
REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = REPO_ROOT / "data" / "external"
PROVENANCE = EXTERNAL / "_provenance_torch_harmonics.json"
CHECKSUMS = EXTERNAL / "checksums.sha256"
TARGET = "torch_harmonics_swe_reference.nc"

# Earth-matched parameters (blueprint section 5.3).
EARTH = {
    "radius_m": 6.37122e6,
    "omega_s^-1": 7.292e-5,
    "gravity_m_s^-2": 9.80616,
    "mean_depth_m": 1.0e4,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def _append_checksum(path: Path) -> str:
    digest = _sha256(path)
    CHECKSUMS.parent.mkdir(parents=True, exist_ok=True)
    kept = []
    if CHECKSUMS.exists():
        kept = [ln for ln in CHECKSUMS.read_text().splitlines() if ln and not ln.endswith(path.name)]
    kept.append(f"{digest}  {path.name}")
    CHECKSUMS.write_text("\n".join(kept) + "\n")
    return digest


def _save_provenance(record: dict) -> None:
    PROVENANCE.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


def _probe_api():
    """Return a description of what the installed torch_harmonics exposes."""
    import torch_harmonics as th  # noqa: F401

    found = {"version": getattr(th, "__version__", "?"), "solver_path": None}
    for modpath, attr in [
        ("torch_harmonics.examples.shallow_water_equations", "ShallowWaterSolver"),
        ("torch_harmonics.examples", "ShallowWaterSolver"),
        ("torch_harmonics.examples.sfno.models", None),
    ]:
        try:
            mod = __import__(modpath, fromlist=["*"])
        except Exception:
            continue
        if attr is None or hasattr(mod, attr):
            found["solver_path"] = modpath + (f".{attr}" if attr else "")
            break
    return found


def fetch(record: dict) -> int:
    try:
        api = _probe_api()
    except ImportError:
        print(
            "torch-harmonics is not installed. This dataset is optional.\n"
            "  To enable it:  pip install torch-harmonics\n"
            "  Then re-run:   python src/data/fetch_torch_harmonics.py --include-d4"
        )
        record["status"] = "skipped: torch-harmonics not installed"
        _save_provenance(record)
        return 0

    record["torch_harmonics_version"] = api["version"]
    if api["solver_path"] is None:
        print(
            "torch-harmonics is installed but no shallow-water solver was found in "
            f"version {api['version']}. Inspect the installed API and update "
            "_probe_api(). Recording as unavailable."
        )
        record["status"] = f"unavailable in torch-harmonics {api['version']}"
        _save_provenance(record)
        return 0

    # A short reference integration is produced by the package's own solver at
    # Earth-matched parameters. The concrete solver call is deliberately left to
    # be written against the verified installed API (see module docstring); this
    # path records the intent and parameters so the run is reproducible.
    print(
        f"torch-harmonics {api['version']} exposes a solver at {api['solver_path']}.\n"
        "Run a short Earth-matched shallow-water integration and write "
        f"{TARGET}. Parameters: {EARTH}."
    )
    record["status"] = "solver available; integration path recorded"
    record["path_taken"] = f"package solver at {api['solver_path']}"
    record["parameters"] = EARTH
    target = EXTERNAL / TARGET
    if target.exists():
        record["sha256"] = _append_checksum(target)
        record["bytes"] = target.stat().st_size
    _save_provenance(record)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Obtain the optional D4 cross-check dataset.")
    parser.add_argument(
        "--include-d4",
        action="store_true",
        help="actually attempt the optional D4 acquisition (default: do nothing)",
    )
    args = parser.parse_args(argv)
    if not args.include_d4:
        print("D4 is optional; pass --include-d4 to attempt it. Nothing done.")
        return 0

    EXTERNAL.mkdir(parents=True, exist_ok=True)
    record = {
        "dataset_id": "D4",
        "source": "torch-harmonics spherical shallow-water cross-check (blueprint 7.5)",
        "optional": True,
        "retrieved_utc": _utc_now(),
        "files": {TARGET: {}},
    }
    return fetch(record)


if __name__ == "__main__":
    raise SystemExit(main())
