#!/usr/bin/env bash
# Source before any run: `source scripts/env.sh`
#
# Threading hygiene that Dedalus requires under MPI. Each MPI rank must run
# single-threaded so that BLAS and FFTW do not oversubscribe the cores already
# claimed by the rank grid. Also disables HDF5 file locking (needed on network
# volumes) and puts the repository root on PYTHONPATH so `import src...` works
# from anywhere in the tree.
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export HDF5_USE_FILE_LOCKING=FALSE
# The :- default matters: this file is sourced by scripts running under
# `set -euo pipefail`, where an unset PYTHONPATH would abort the launcher before
# it reached the solver.
export PYTHONPATH="$(git rev-parse --show-toplevel):${PYTHONPATH:-}"
