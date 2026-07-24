"""Probe Copernicus CDS dataset licences before committing to long downloads.

Copernicus requires the licence to be accepted **per dataset**, through the web
interface, while logged in. A missing acceptance returns HTTP 403 with a message
that does not identify which dataset is at fault -- and it does so only after the
request has cleared the queue. Discovering that after a forty-minute queue wastes
an evening, so this module probes first.

For each dataset it issues the smallest possible request -- one variable, one
level, one timestamp, a 1 deg x 1 deg ``area`` box -- to a temporary file, then
deletes it. The outcome is classified per dataset:

* ``OK``                     -- the request was accepted (and a file returned).
* ``LICENCE_NOT_ACCEPTED``   -- HTTP 403, or any response mentioning a licence or
                                terms of use. Remediation is a one-time click on
                                the dataset's "Terms of use" and cannot be
                                automated.
* ``AUTH_FAILED``            -- HTTP 401, or a 403 that names the token. The
                                credentials are wrong or revoked.
* ``OTHER``                  -- anything else, reported with the verbatim message.

Nothing here downloads a science-sized file: the probe requests are a single
grid cell. Run it standalone::

    python src/data/probe_cds_licence.py           # both datasets
    python src/data/probe_cds_licence.py --json     # machine-readable summary

The process exit code is the number of datasets that were not ``OK`` (0 = all
clear), so a Makefile or orchestration step can branch on it.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

OK = "OK"
LICENCE_NOT_ACCEPTED = "LICENCE_NOT_ACCEPTED"
AUTH_FAILED = "AUTH_FAILED"
OTHER = "OTHER"

# The two ERA5 pressure-level datasets the project depends on. Each probe is the
# smallest request the dataset will accept: one variable, one level, one time,
# and a 1 deg x 1 deg area box [North, West, South, East].
PROBE_REQUESTS: dict[str, dict] = {
    "reanalysis-era5-pressure-levels": {
        "product_type": ["reanalysis"],
        "variable": ["geopotential"],
        "pressure_level": ["500"],
        "year": ["2020"],
        "month": ["01"],
        "day": ["01"],
        "time": ["00:00"],
        "area": [1, 0, 0, 1],
        "data_format": "netcdf",
        "download_format": "unarchived",
    },
    "reanalysis-era5-pressure-levels-monthly-means": {
        "product_type": ["monthly_averaged_reanalysis"],
        "variable": ["geopotential"],
        "pressure_level": ["500"],
        "year": ["2020"],
        "month": ["01"],
        "time": ["00:00"],
        "area": [1, 0, 0, 1],
        "data_format": "netcdf",
        "download_format": "unarchived",
    },
}

_LICENCE_WORDS = (
    "licence",
    "license",
    "terms of use",
    "terms and conditions",
    "not accepted",
    "required licences",
    "required licenses",
    "accept the",
)
_AUTH_WORDS = (
    "401",
    "unauthor",
    "authentication",
    "invalid api key",
    "invalid token",
    "invalid key",
    "not authenticated",
    "authorization",
)


def _status_code(err: BaseException) -> int | None:
    """Best-effort HTTP status code from an exception or its message."""
    resp = getattr(err, "response", None)
    code = getattr(resp, "status_code", None)
    if isinstance(code, int):
        return code
    m = re.search(r"\b(40[0-9]|41[0-9]|5[0-9][0-9])\b", str(err))
    return int(m.group(1)) if m else None


def classify(err: BaseException) -> tuple[str, str]:
    """Map a retrieve exception to (status, verbatim message)."""
    msg = str(err).strip() or repr(err)
    low = msg.lower()
    code = _status_code(err)
    mentions_licence = any(w in low for w in _LICENCE_WORDS)
    mentions_auth = any(w in low for w in _AUTH_WORDS)
    mentions_token = "token" in low or "api key" in low or "apikey" in low

    if code == 401 or mentions_auth:
        return AUTH_FAILED, msg
    if code == 403 and mentions_token and not mentions_licence:
        return AUTH_FAILED, msg
    if mentions_licence:
        return LICENCE_NOT_ACCEPTED, msg
    if code == 403:
        return LICENCE_NOT_ACCEPTED, msg
    return OTHER, msg


def probe_one(dataset: str, request: dict) -> tuple[str, str]:
    """Issue the smallest request for *dataset* and classify the outcome."""
    import cdsapi

    tmp = Path(tempfile.NamedTemporaryFile(suffix=".nc", delete=False).name)
    try:
        client = cdsapi.Client()
        client.retrieve(dataset, request, str(tmp))
        return OK, "request accepted; a file was returned"
    except Exception as err:  # noqa: BLE001 - classification handles every case
        return classify(err)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def _print_licence_block(dataset: str) -> None:
    print(
        f"\n[INPUT REQUIRED] -- Copernicus licence not accepted for: {dataset}\n\n"
        "The credentials file is valid; the licence for this dataset has not been accepted.\n"
        "This is a one-time click and cannot be automated.\n\n"
        "  1. Log in at https://cds.climate.copernicus.eu\n"
        f"  2. Open the dataset page for: {dataset}\n"
        '  3. Select the "Download" tab\n'
        '  4. Scroll to "Terms of use" and click to accept\n'
        "  5. Re-run:  make data-era5\n\n"
        "Both of these must be accepted separately:\n"
        "  reanalysis-era5-pressure-levels\n"
        "  reanalysis-era5-pressure-levels-monthly-means\n\n"
        "NCEP/NCAR R1 covers both target winters and is a sufficient fallback for every\n"
        "diagnostic in blueprint section 7.3. The project is not blocked.\n"
    )


def _print_auth_block(dataset: str) -> None:
    print(
        f"\n[INPUT REQUIRED] -- Copernicus authentication failed for: {dataset}\n\n"
        "The token in ~/.cdsapirc was rejected (HTTP 401, or a 403 naming the token).\n"
        "It is wrong or revoked. Re-run the bootstrap with a valid token:\n\n"
        "  bash scripts/setup_cds_credentials.sh <PERSONAL-ACCESS-TOKEN>\n\n"
        "Then re-run:  make data-era5\n"
    )


def probe_all() -> dict[str, dict]:
    results: dict[str, dict] = {}
    for dataset, request in PROBE_REQUESTS.items():
        print(f"[probe] {dataset} ...", flush=True)
        status, message = probe_one(dataset, request)
        results[dataset] = {"status": status, "message": message}
        print(f"    -> {status}")
        if status == LICENCE_NOT_ACCEPTED:
            _print_licence_block(dataset)
        elif status == AUTH_FAILED:
            _print_auth_block(dataset)
        elif status == OTHER:
            print(f"    verbatim: {message}")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe Copernicus CDS dataset licences.")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable summary")
    args = parser.parse_args(argv)

    results = probe_all()
    not_ok = sum(1 for r in results.values() if r["status"] != OK)

    print("\n== licence probe summary ==")
    for dataset, r in results.items():
        print(f"  {dataset}: {r['status']}")

    if args.json:
        print("\nJSON " + json.dumps(results, sort_keys=True))

    return not_ok


if __name__ == "__main__":
    raise SystemExit(main())
