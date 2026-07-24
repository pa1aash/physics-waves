#!/usr/bin/env bash
# Writes the Copernicus CDS API credentials file to the user's home directory.
# Usage:  scripts/setup_cds_credentials.sh <PERSONAL-ACCESS-TOKEN>
# The token is never stored inside this repository.
set -euo pipefail

TOKEN="${1:-${CDS_TOKEN:-}}"
RC="${HOME}/.cdsapirc"
URL="https://cds.climate.copernicus.eu/api"

if [ -z "${TOKEN}" ]; then
  echo "No token supplied. Usage: $0 <PERSONAL-ACCESS-TOKEN>" >&2
  exit 1
fi

if [ -f "${RC}" ]; then
  if grep -q "^url: ${URL}$" "${RC}" && grep -qE '^key: [0-9a-f-]{36}$' "${RC}"; then
    echo "Existing ${RC} already uses the current format. Leaving it unchanged."
    chmod 600 "${RC}"
    exit 0
  fi
  cp "${RC}" "${RC}.backup.$(date -u +%Y%m%dT%H%M%SZ)"
  echo "Existing ${RC} was in a legacy format; backed up before rewriting."
fi

printf 'url: %s\nkey: %s\n' "${URL}" "${TOKEN}" > "${RC}"
chmod 600 "${RC}"
echo "Wrote ${RC} (mode 600)."
