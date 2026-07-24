# Container for compute-pod parity with the local environment.
# Build later (not in Session 00):  docker build -t physics-waves .
#
# Note: environment.lock.yml is generated on the development platform. If it does
# not solve on linux-64, regenerate the lock inside this image from
# environment.yml and commit the linux lock alongside it.
FROM condaforge/miniforge3:latest

# Recreate the pinned environment.
COPY environment.lock.yml /tmp/environment.lock.yml
RUN mamba env create -f /tmp/environment.lock.yml && mamba clean -afy

# Threading hygiene (mirror of scripts/env.sh): one thread per MPI rank.
ENV OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    VECLIB_MAXIMUM_THREADS=1 \
    HDF5_USE_FILE_LOCKING=FALSE

# Default to running inside the pw environment.
SHELL ["conda", "run", "--no-capture-output", "-n", "pw", "/bin/bash", "-c"]
WORKDIR /workspace
