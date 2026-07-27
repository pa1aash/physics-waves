"""The harness must survive being run on more than one rank.

Every run this project has recorded so far was serial, and two bugs hid behind
that. Both were found in Session L7a by pointing the new MPI runner at a real
config, and both aborted the run *before the physics started*, so neither could
ever have produced a wrong number — but both made the pod unusable, which was
the point of the session that found them.

1. **The area average was rank-local.** Reducing a field to a scalar leaves that
   scalar on exactly one rank; the others hold an array of shape ``(1, 0)``.
   ``float(np.ravel(...)[0])`` raised ``IndexError`` on every rank but one, and
   every initial condition in the project calls it.

2. **Every rank wrote the provenance record.** The first rank to arrive made the
   file read-only — the deliberate immutability tripwire — and the next rank to
   arrive tripped it, so a healthy run died with a permission error that looked
   exactly like the corruption the tripwire exists to detect.

These tests spawn real MPI jobs, because the failures are invisible in-process:
a single-rank pytest run exercises neither code path. They are skipped where no
launcher is available rather than passing vacuously.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RANKS = 2

pytestmark = pytest.mark.skipif(
    shutil.which("mpiexec") is None, reason="no mpiexec on this machine"
)


def run_under_mpi(script: str, tmp_path: Path, ranks: int = RANKS) -> subprocess.CompletedProcess:
    """Execute a snippet on ``ranks`` MPI ranks and return the finished process."""
    script_path = tmp_path / "under_mpi.py"
    script_path.write_text(script, encoding="utf-8")
    env = {
        "PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin",
        "PYTHONPATH": str(REPO_ROOT),
        # The same thread hygiene scripts/env.sh sets. Without it Dedalus warns
        # on every rank and the ranks oversubscribe the test machine.
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "HDF5_USE_FILE_LOCKING": "FALSE",
        "HOME": str(tmp_path),
    }
    return subprocess.run(
        ["mpiexec", "-n", str(ranks), sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )


def test_the_area_average_returns_the_same_value_on_every_rank(tmp_path):
    """Bug 1. A mean that differs between ranks is worse than one that crashes.

    Two ranks that disagree about a case's mean depth are integrating two
    different fluids, so this asserts agreement, not merely survival.
    """
    script = """
import numpy as np
from mpi4py import MPI

from src.solver.equations import build_problem
from src.solver.initial_conditions.common import area_average

config = {
    "resolution": "L0",
    "physical": {"R": 6371220.0, "Omega": 7.292e-05, "g": 9.80616, "H": 10000.0},
    "numerics": {"timestepper": "RK222", "dt": 600.0, "dealias": 1.5,
                 "hyperdiffusion_order": 4, "hyperdiffusion_coefficient": 0.0,
                 "stop_sim_time": 600.0},
}
swp = build_problem(config)

# A constant field: its area average is that constant, on every rank, exactly.
value = area_average(swp, np.ones_like(swp.h["g"]) * 7.5)
gathered = MPI.COMM_WORLD.allgather(value)
assert all(abs(v - 7.5) < 1e-10 for v in gathered), gathered
assert len(set(gathered)) == 1, f"ranks disagree about the area average: {gathered}"
print("AREA_AVERAGE_OK", MPI.COMM_WORLD.rank, value)
"""
    result = run_under_mpi(script, tmp_path)
    assert result.returncode == 0, result.stderr[-4000:]
    assert result.stdout.count("AREA_AVERAGE_OK") == RANKS, result.stdout


def test_a_run_writes_exactly_one_provenance_record_under_mpi(tmp_path):
    """Bug 2. The immutability tripwire must not fire on a healthy parallel run."""
    output_root = tmp_path / "runs"
    script = f"""
from mpi4py import MPI

from src.solver.harness import run

result = run("configs/verification/V-02.yaml", output_root={str(output_root)!r}, dry_run=True)
assert result.provenance["outcome"]["status"] == "dry_run", result.provenance["outcome"]
print("PROVENANCE_OK", MPI.COMM_WORLD.rank)
"""
    result = run_under_mpi(script, tmp_path)
    assert result.returncode == 0, result.stderr[-4000:]
    assert result.stdout.count("PROVENANCE_OK") == RANKS, result.stdout

    records = list(output_root.rglob("provenance.json"))
    assert len(records) == 1, [str(p) for p in records]
    # And the tripwire is still armed afterwards: the record is read-only.
    assert not records[0].stat().st_mode & 0o222
