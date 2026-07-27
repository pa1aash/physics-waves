"""The Mac-to-pod sync, exercised against a stand-in directory with no pod reachable.

`runs/` is gitignored, so completed run output has no route between machines
except this script. That makes its flags and exclusions load-bearing in a way
that is easy to miss: a wrong exclusion pattern does not fail, it silently
transfers eighty megabytes of the wrong thing, or silently omits the one file
that mattered.

`POD_HOST=""` makes both sides local paths, which is what lets every one of
those behaviours be checked here rather than discovered against a live pod. What
is *not* checked here is ssh transport itself; that is Session L7b's job, on the
real pod.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "sync_pod.sh"

pytestmark = pytest.mark.skipif(shutil.which("rsync") is None, reason="no rsync on this machine")


def build_stand_in_pod(root: Path, run_id: str = "P-12") -> Path:
    """A directory shaped like the pod's repository, holding one completed run."""
    run_dir = root / "runs" / run_id
    (run_dir / "snapshots").mkdir(parents=True)
    (run_dir / "snapshots" / "snapshots_s1.h5").write_bytes(b"\x00" * 4096)
    (run_dir / "slices").mkdir()
    (run_dir / "slices" / "slices_s1.h5").write_bytes(b"\x00" * 1024)
    (run_dir / "__pycache__").mkdir()
    (run_dir / "__pycache__" / "junk.pyc").write_bytes(b"\x00" * 16)
    (run_dir / ".DS_Store").write_bytes(b"\x00" * 8)
    (run_dir / "provenance.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "outcome": {"status": "completed", "wall_seconds": 421.0},
                "environment": {"mpi_size": 4},
                "git": {"commit": "0123456789abcdef"},
                "outputs": [{"path": "snapshots/snapshots_s1.h5", "bytes": 4096}],
            }
        ),
        encoding="utf-8",
    )
    return run_dir


def run_sync(
    *args: str, pod_path: Path, cwd: Path, dry_run: bool = True
) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "POD_HOST": "",  # both sides local: no pod needed
        "POD_PATH": str(pod_path),
        "DRY_RUN": "1" if dry_run else "0",
    }
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def workspace(tmp_path):
    """A throwaway git repository standing in for the Mac, and one for the pod."""
    mac = tmp_path / "mac"
    mac.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=mac, check=True)
    (mac / "runs").mkdir()

    pod = tmp_path / "pod"
    pod.mkdir()
    build_stand_in_pod(pod)
    return mac, pod


def test_the_dry_run_lists_the_expected_files_and_writes_nothing(workspace):
    """The check the session brief asks for: right flags, right file list, no writes."""
    mac, pod = workspace

    result = run_sync("pull", "P-12", pod_path=pod, cwd=mac)

    assert result.returncode == 0, result.stderr
    output = result.stdout
    assert "DRY RUN" in output
    assert "provenance.json" in output
    assert "snapshots/snapshots_s1.h5" in output
    assert "slices/slices_s1.h5" in output

    # Nothing was created. A dry run that creates the destination directory is
    # not a dry run.
    assert not (mac / "runs" / "P-12").exists()


def test_the_dry_run_excludes_caches_and_platform_droppings(workspace):
    mac, pod = workspace

    output = run_sync("pull", "P-12", pod_path=pod, cwd=mac).stdout

    assert "__pycache__" not in output
    assert ".DS_Store" not in output


def test_a_real_pull_brings_the_run_across_intact(workspace):
    mac, pod = workspace

    result = run_sync("pull", "P-12", pod_path=pod, cwd=mac, dry_run=False)

    assert result.returncode == 0, result.stderr
    destination = mac / "runs" / "P-12"
    assert (destination / "snapshots" / "snapshots_s1.h5").stat().st_size == 4096
    assert (destination / "slices" / "slices_s1.h5").stat().st_size == 1024
    assert not (destination / "__pycache__").exists()

    # The summary is read off the record that came with the data, so a pull that
    # silently brought back a failed run says so.
    assert "status   completed" in result.stdout
    assert "4 rank(s)" in result.stdout


def test_pull_refuses_to_overwrite_a_run_that_already_exists_locally(workspace):
    """Immutability, enforced at the machine boundary as well as inside the harness."""
    mac, pod = workspace
    (mac / "runs" / "P-12").mkdir(parents=True)

    result = run_sync("pull", "P-12", pod_path=pod, cwd=mac, dry_run=False)

    assert result.returncode == 3
    assert "already exists locally" in result.stderr
    assert "Run IDs are immutable" in result.stderr


def test_pull_warns_when_a_run_arrives_without_its_provenance(workspace, tmp_path):
    mac, pod = workspace
    (pod / "runs" / "P-13" / "snapshots").mkdir(parents=True)
    (pod / "runs" / "P-13" / "snapshots" / "s1.h5").write_bytes(b"\x00" * 512)

    result = run_sync("pull", "P-13", pod_path=pod, cwd=mac, dry_run=False)

    assert result.returncode == 0
    assert "no provenance.json" in result.stderr


def test_pull_list_reports_what_the_pod_holds(workspace):
    mac, pod = workspace

    result = run_sync("pull", "--list", pod_path=pod, cwd=mac)

    assert result.returncode == 0
    assert "P-12" in result.stdout


def test_push_never_carries_run_output_or_raw_data_to_the_pod(workspace):
    """Output travels one way only. Pushing it back would not be a mirror, it would
    be a second copy of the authoritative data on the machine that did not make it."""
    mac, pod = workspace
    (mac / "runs" / "V-99").mkdir(parents=True)
    (mac / "runs" / "V-99" / "big.h5").write_bytes(b"\x00" * 2048)
    (mac / "src").mkdir()
    (mac / "src" / "solver.py").write_text("# code\n", encoding="utf-8")

    output = run_sync("push", pod_path=pod, cwd=mac).stdout

    assert "src/solver.py" in output
    assert "V-99" not in output
    assert "big.h5" not in output


def test_no_arguments_prints_usage_rather_than_guessing(workspace):
    mac, pod = workspace

    result = run_sync(pod_path=pod, cwd=mac)

    assert result.returncode == 2
    assert "usage: scripts/sync_pod.sh" in result.stderr
