#!/usr/bin/env bash
# Run one config under MPI.
#
# The harness (src/solver/harness.py) knows how to integrate one config; this
# script knows how to launch it on this machine. Keeping the two apart means the
# solver never has to reason about rank counts and the launcher never has to
# reason about physics.
#
# WHY scripts/env.sh IS SOURCED FIRST, AND WHY THAT IS NOT OPTIONAL:
# every MPI rank must run single-threaded. If BLAS and FFTW each spawn threads
# inside a rank that already owns one core, the ranks oversubscribe the machine
# and every rank slows down -- but the run still completes, and still writes a
# provenance record carrying a wall_seconds field that is now measuring thread
# contention rather than the solver. That number then feeds the cost log and
# Session R1's resolution-ladder calibration. An oversubscribed run does not fail
# loudly; it quietly produces wrong timing data, which is worse.
#
# WHY `python` AND NOT `python3`:
# on the development Mac, `python3` resolves to a system framework interpreter
# outside the conda environment even when `pw` is active, while `python` resolves
# inside it. `make run` uses `python` for the same reason. Override with
# PYTHON=... if a machine needs something else.
#
# Usage:
#   scripts/run_mpi.sh configs/phase_speed/P-12.yaml
#   scripts/run_mpi.sh configs/verification/V-02.yaml --dry-run
#   RANKS=8 scripts/run_mpi.sh configs/verification/V-04.yaml
#
# Environment:
#   RANKS    override the rank count chosen from the config's resolution
#   PYTHON   interpreter to launch (default: python)
#   MPIEXEC  launcher to use (default: mpiexec)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# shellcheck source=scripts/env.sh
source scripts/env.sh

CONFIG="${1:-}"
if [ -z "${CONFIG}" ]; then
  echo "usage: scripts/run_mpi.sh <config.yaml> [harness args...]" >&2
  echo "  e.g. scripts/run_mpi.sh configs/phase_speed/P-12.yaml --update-registry" >&2
  exit 2
fi
shift

if [ ! -f "${CONFIG}" ]; then
  echo "run_mpi: no such config: ${CONFIG}" >&2
  exit 2
fi

PYTHON="${PYTHON:-python}"
MPIEXEC="${MPIEXEC:-mpiexec}"

# Rank count from the config's resolution rung. This is a HEURISTIC, and it is
# labelled as one everywhere it appears: the only measured data point this
# project has is the Phase-0 gate, which ran L0 and L1 on 4 ranks (docs/COMPUTE.md).
# Above L1 it assumes each rung can usefully absorb twice the ranks, because the
# spectral transform work grows faster than the halo communication does. Session
# R1 measures the real scaling on the pod and replaces these with earned numbers.
# The same table lives in scripts/sweep.py; a plan and a launch must not disagree
# about how many cores a run claims, so this reads it from there rather than
# keeping a second copy.
if [ -n "${RANKS:-}" ]; then
  ranks="${RANKS}"
  rank_source="RANKS environment override"
else
  ranks="$("${PYTHON}" - "${CONFIG}" <<'PY_EOF'
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
import yaml

from scripts.sweep import RANKS_BY_RESOLUTION

config = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(RANKS_BY_RESOLUTION[config["resolution"]])
PY_EOF
)"
  rank_source="resolution heuristic (Session R1 refines)"
fi

# Never claim more ranks than the machine has cores. An MPI job that oversubscribes
# physical cores measures scheduler contention, which is the same wrong-timing
# failure mode scripts/env.sh exists to prevent, arriving by a different route.
if command -v nproc >/dev/null 2>&1; then
  cores="$(nproc)"
else
  cores="$(sysctl -n hw.ncpu)"
fi
if [ "${ranks}" -gt "${cores}" ]; then
  echo "run_mpi: ${ranks} ranks requested but only ${cores} cores present; using ${cores}" >&2
  ranks="${cores}"
  rank_source="capped at the core count"
fi

echo "== run_mpi =="
echo "  config  ${CONFIG}"
echo "  ranks   ${ranks}  (${rank_source})"
echo "  python  $(command -v "${PYTHON}")"
echo "  threads OMP=${OMP_NUM_THREADS} OPENBLAS=${OPENBLAS_NUM_THREADS} MKL=${MKL_NUM_THREADS}"
echo

exec "${MPIEXEC}" -n "${ranks}" "${PYTHON}" -m src.solver.harness "${CONFIG}" "$@"
