#!/usr/bin/env bash
# Mirror the working tree to the compute pod (blueprint / docs/COMPUTE.md).
#
# Code, configs and scripts are pushed; git internals, environments, caches and
# the (large, regenerable) data and output directories are excluded. Raw output
# lives on the pod network volume and is never synced back into the repository.
#
# Configure the destination via environment variables:
#   POD_HOST   ssh host or alias for the RunPod CPU pod (required)
#   POD_PATH   destination path on the pod (default: ~/physics-waves)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

: "${POD_HOST:?set POD_HOST to the compute pod ssh host (see docs/SETUP_CHECKLIST.md)}"
POD_PATH="${POD_PATH:-~/physics-waves}"

rsync -avz --delete \
  --exclude '.git/' \
  --exclude '.[Cc]laude/' \
  --exclude '.remember/' \
  --exclude '__pycache__/' \
  --exclude '.pytest_cache/' \
  --exclude 'data/raw/' \
  --exclude 'data/reference/' \
  --exclude 'data/processed/' \
  --exclude 'data/external/*.nc' \
  --exclude '*.h5' \
  --exclude '*.hdf5' \
  ./ "${POD_HOST}:${POD_PATH}/"
