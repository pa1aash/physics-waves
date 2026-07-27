#!/usr/bin/env bash
# Move work between the Mac and the compute pod.
#
#   push          mirror the working tree to the pod (code, configs, scripts)
#   pull <RUN_ID> bring one completed run's output back to the Mac
#
# Code travels by git and by this script's `push`; run output cannot. `runs/` is
# gitignored -- raw HDF5 has no business in version control, it is bulk binary
# that is reproducible from the config beside it -- so a completed run's data has
# no route back to the Mac unless one is built. This is that route.
#
# PULL PRESERVES THE IMMUTABILITY CONVENTION.
# The harness refuses to reopen a run directory that already carries a completed
# record, because a run ID meaning two different things is worse than no record
# at all. A sync that overwrote a local run would defeat that from the outside:
# the provenance would still describe run P-12 while the HDF5 beside it came from
# a different execution. So `pull` refuses an existing local run ID outright.
# Clear it with scripts/resume_check.py --apply, or pull to a different root.
#
# Configure the destination via environment variables:
#   POD_HOST   ssh host or alias for the pod (default: runpod-physics-waves)
#   POD_PATH   repository path on the pod (default: /workspace/physics-waves)
#   DRY_RUN    set to 1 to pass --dry-run to rsync and change nothing
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

POD_HOST="${POD_HOST-runpod-physics-waves}"
POD_PATH="${POD_PATH:-/workspace/physics-waves}"

# An empty POD_HOST means both sides are local paths. That is what lets the
# flags and exclusions be exercised against a throwaway directory standing in
# for the pod, with no pod reachable -- see tests/test_sync_pod.py. Note the
# `${POD_HOST-...}` form rather than `${POD_HOST:-...}`: an explicitly empty
# POD_HOST must stay empty rather than falling back to the default.
if [ -n "${POD_HOST}" ]; then
  POD_PREFIX="${POD_HOST}:${POD_PATH}"
else
  POD_PREFIX="${POD_PATH}"
fi

rsync_flags=(-avz --human-readable)
if [ "${DRY_RUN:-0}" = "1" ]; then
  rsync_flags+=(--dry-run)
  echo "== DRY RUN: nothing will be written =="
fi

usage() {
  cat >&2 <<'USAGE'
usage: scripts/sync_pod.sh <command> [args]

  push              mirror the working tree to the pod
  pull <RUN_ID>     copy runs/<RUN_ID>/ from the pod into the local runs/
  pull --list       list the run directories present on the pod

environment:
  POD_HOST   ssh host or alias   (default: runpod-physics-waves)
  POD_PATH   path on the pod     (default: /workspace/physics-waves)
  DRY_RUN=1  pass --dry-run to rsync
USAGE
  exit 2
}

# --------------------------------------------------------------------------
# push: code out to the pod
# --------------------------------------------------------------------------
# The exclusions are the point. Git internals, caches and environments are
# either reproducible or machine-specific; the data directories and every HDF5
# file are large and regenerable, and raw output must never travel back into the
# repository tree.
do_push() {
  rsync "${rsync_flags[@]}" --delete \
    --exclude '.git/' \
    --exclude '.[Cc]laude/' \
    --exclude '.remember/' \
    --exclude '__pycache__/' \
    --exclude '.pytest_cache/' \
    --exclude '.ruff_cache/' \
    --exclude '.DS_Store' \
    --exclude 'runs/' \
    --exclude 'data/raw/' \
    --exclude 'data/reference/' \
    --exclude 'data/processed/' \
    --exclude 'data/external/*.nc' \
    --exclude '*.h5' \
    --exclude '*.hdf5' \
    ./ "${POD_PREFIX}/"
}

# --------------------------------------------------------------------------
# pull: one run's output back to the Mac
# --------------------------------------------------------------------------
do_pull() {
  local run_id="${1:-}"
  [ -n "${run_id}" ] || usage

  if [ "${run_id}" = "--list" ]; then
    echo "== run directories under ${POD_PREFIX}/runs =="
    if [ -n "${POD_HOST}" ]; then
      ssh "${POD_HOST}" "ls -1 ${POD_PATH}/runs 2>/dev/null || echo '(none)'"
    else
      ls -1 "${POD_PATH}/runs" 2>/dev/null || echo '(none)'
    fi
    return 0
  fi

  local destination="runs/${run_id}"

  # Immutability, enforced at the boundary rather than trusted.
  if [ -e "${destination}" ] && [ "${DRY_RUN:-0}" != "1" ]; then
    echo "sync_pod: ${destination} already exists locally." >&2
    echo "  Run IDs are immutable: overwriting it would leave a provenance record" >&2
    echo "  describing one execution beside data from another. Archive the local" >&2
    echo "  copy first (scripts/resume_check.py --apply) or pull elsewhere." >&2
    exit 3
  fi

  mkdir -p runs

  # --ignore-existing is belt to the check above's braces: if a file somehow
  # exists it is left alone rather than silently replaced.
  # --partial keeps a half-transferred multi-gigabyte HDF5 resumable.
  rsync "${rsync_flags[@]}" --partial --ignore-existing \
    --exclude '__pycache__/' \
    --exclude '.DS_Store' \
    "${POD_PREFIX}/runs/${run_id}/" "${destination}/"

  if [ "${DRY_RUN:-0}" = "1" ]; then
    echo "== DRY RUN complete: ${destination} not created =="
    return 0
  fi

  echo
  echo "== pulled ${run_id} -> ${destination} =="
  if [ -f "${destination}/provenance.json" ]; then
    python - "${destination}/provenance.json" <<'PY_EOF'
import json
import sys

record = json.loads(open(sys.argv[1], encoding="utf-8").read())
outcome = record.get("outcome", {})
print(f"   status   {outcome.get('status')}")
print(f"   wall     {outcome.get('wall_seconds')} s on {record.get('environment', {}).get('mpi_size')} rank(s)")
print(f"   commit   {record.get('git', {}).get('commit', '')[:12]}")
print(f"   outputs  {len(record.get('outputs') or [])} file(s)")
PY_EOF
  else
    {
      echo "   WARNING: no provenance.json came with this run. It is not a complete"
      echo "   run record, and nothing downstream will read it."
    } >&2
  fi
}

case "${1:-}" in
  push) shift; do_push "$@" ;;
  pull) shift; do_pull "$@" ;;
  *) usage ;;
esac
