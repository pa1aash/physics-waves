"""Detecting an interrupted run, without needing an interrupted run to detect.

The detection logic reads one field of one JSON file, so it can be exercised
against fabricated provenance records — which is the point: waiting for a real
Dedalus run to die in order to test the thing that handles runs dying would make
this untestable in practice, and untestable-in-practice recovery code is how a
campaign discovers on the pod that its recovery path does not work.

Session L7a chose clean-restart-from-archive over checkpoint-resume; see
``scripts/resume_check.py`` for why. These tests therefore assert that an
incomplete run is *identified* and *moved aside intact*, never that its state is
reconstructed.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest

from scripts.resume_check import (
    ARCHIVE_DIRNAME,
    archive,
    inspect_run,
    main,
    scan,
)


def write_run(
    runs_root: Path,
    run_id: str,
    status: str | None,
    *,
    error: str | None = None,
    with_output: bool = False,
    read_only: bool = True,
) -> Path:
    """Fabricate a run directory carrying the provenance the harness would write."""
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True)

    if with_output:
        (run_dir / "snapshots").mkdir()
        (run_dir / "snapshots" / "snapshots_s1.h5").write_bytes(b"\x00" * 2048)

    if status is not None:
        record = {
            "run_id": run_id,
            "campaign": "phase_speed",
            "config_path": f"configs/phase_speed/{run_id}.yaml",
            "started_utc": "2026-07-27T00:00:00+00:00",
            "outcome": {"status": status, "error": error},
        }
        path = run_dir / "provenance.json"
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        if read_only:
            # The harness makes the record read-only; anything that handles a
            # run directory afterwards has to cope with that.
            path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    return run_dir


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------


def test_a_failed_run_is_identified(tmp_path):
    """The fabricated-failure case the session brief asks for, exactly."""
    run_dir = write_run(tmp_path, "P-05", "failed", error="RuntimeError: NaN in h")

    found = inspect_run(run_dir)

    assert found is not None
    assert found.run_id == "P-05"
    assert found.status == "failed"
    assert found.error == "RuntimeError: NaN in h"
    assert "raised during integration" in found.diagnosis


def test_a_killed_run_is_identified_by_its_unrewritten_record(tmp_path):
    """``started`` is the OOM / wall-clock-limit / vanished-pod signature.

    A process that raises rewrites its record as ``failed``. A process that is
    killed never gets to rewrite anything, so the record still says ``started`` —
    which makes the two distinguishable, and worth distinguishing, because they
    call for different remedies.
    """
    found = inspect_run(write_run(tmp_path, "P-06", "started"))

    assert found is not None
    assert found.status == "started"
    assert "killed rather than raising" in found.diagnosis


def test_a_run_with_no_record_at_all_is_identified(tmp_path):
    found = inspect_run(write_run(tmp_path, "P-07", None, with_output=True))

    assert found is not None
    assert found.status == "missing"
    assert found.output_files == 1


def test_an_unreadable_record_is_treated_as_interrupted(tmp_path):
    """Truncated JSON is what a process killed mid-write leaves behind."""
    run_dir = write_run(tmp_path, "P-08", "completed", read_only=False)
    (run_dir / "provenance.json").write_text('{"run_id": "P-08", "outc', encoding="utf-8")

    found = inspect_run(run_dir)

    assert found is not None
    assert found.status == "unreadable"


@pytest.mark.parametrize("status", ["completed", "dry_run"])
def test_terminal_runs_need_no_action(tmp_path, status):
    assert inspect_run(write_run(tmp_path, "V-02", status)) is None


def test_scan_separates_the_two_kinds_and_skips_non_run_directories(tmp_path):
    write_run(tmp_path, "V-01", "completed")
    write_run(tmp_path, "V-02", "dry_run")
    write_run(tmp_path, "P-01", "failed")
    write_run(tmp_path, "P-02", "started")
    (tmp_path / "_sweep_plans").mkdir()
    (tmp_path / "_sweep_plans" / "phase_speed_x.json").write_text("{}", encoding="utf-8")
    (tmp_path / ARCHIVE_DIRNAME).mkdir()

    report = scan(tmp_path)

    assert report.scanned == 4
    assert report.complete == 2
    assert sorted(run.run_id for run in report.incomplete) == ["P-01", "P-02"]


def test_eigenvalue_runs_are_not_reported_as_interrupted(tmp_path):
    """EVP runs have no provenance because the harness never made them.

    They write their own results JSON and are complete. Reported as interrupted
    they would be permanent false positives, and a recovery check that always
    fires is a recovery check nobody reads.
    """
    (tmp_path / "EVP-hough").mkdir()
    (tmp_path / "EVP-hough" / "hough_modes.json").write_text("{}", encoding="utf-8")
    (tmp_path / "EVP-jet-stability").mkdir()
    (tmp_path / "EVP-jet-stability" / "growth_rates.json").write_text("{}", encoding="utf-8")
    write_run(tmp_path, "P-05", "failed")

    report = scan(tmp_path)

    assert report.scanned == 1
    assert [run.run_id for run in report.incomplete] == ["P-05"]


def test_scan_of_a_missing_runs_directory_is_empty_not_an_error(tmp_path):
    report = scan(tmp_path / "not-there")
    assert report.scanned == 0
    assert report.incomplete == []


# --------------------------------------------------------------------------
# The action taken: archive, never delete
# --------------------------------------------------------------------------


def test_archiving_moves_the_run_aside_and_keeps_everything(tmp_path):
    write_run(tmp_path, "P-05", "failed", error="RuntimeError: NaN in h", with_output=True)
    run = scan(tmp_path).incomplete[0]

    destination = archive(run, runs_root=tmp_path, stamp="20260727T000000Z")

    # The run ID is free again, so the harness's immutability refusal never has
    # to be overridden with --force.
    assert not (tmp_path / "P-05").exists()

    # And nothing was lost: the record and the partial output both moved.
    assert destination == tmp_path / ARCHIVE_DIRNAME / "P-05_failed_20260727T000000Z"
    assert (destination / "snapshots" / "snapshots_s1.h5").stat().st_size == 2048
    record = json.loads((destination / "provenance.json").read_text(encoding="utf-8"))
    assert record["outcome"]["error"] == "RuntimeError: NaN in h"


def test_the_archived_record_is_still_read_only(tmp_path):
    """The tripwire survives the move. An archived failure is still evidence."""
    write_run(tmp_path, "P-05", "failed")
    run = scan(tmp_path).incomplete[0]

    destination = archive(run, runs_root=tmp_path, stamp="20260727T000000Z")

    assert not (destination / "provenance.json").stat().st_mode & stat.S_IWUSR


def test_archiving_refuses_to_merge_two_runs_into_one_destination(tmp_path):
    write_run(tmp_path, "P-05", "failed")
    run = scan(tmp_path).incomplete[0]
    archive(run, runs_root=tmp_path, stamp="20260727T000000Z")

    write_run(tmp_path, "P-05", "failed")
    again = scan(tmp_path).incomplete[0]

    with pytest.raises(FileExistsError):
        archive(again, runs_root=tmp_path, stamp="20260727T000000Z")


def test_a_second_failure_of_the_same_run_archives_alongside_the_first(tmp_path):
    """Two attempts, two archives. Neither overwrites the other."""
    for stamp in ("20260727T000000Z", "20260727T010000Z"):
        write_run(tmp_path, "P-05", "failed")
        archive(scan(tmp_path).incomplete[0], runs_root=tmp_path, stamp=stamp)

    archived = sorted(p.name for p in (tmp_path / ARCHIVE_DIRNAME).iterdir())
    assert archived == ["P-05_failed_20260727T000000Z", "P-05_failed_20260727T010000Z"]


# --------------------------------------------------------------------------
# The command-line contract a pod script depends on
# --------------------------------------------------------------------------


def test_the_default_invocation_changes_nothing_and_signals_outstanding_work(tmp_path, capsys):
    write_run(tmp_path, "P-05", "failed")

    exit_code = main(["--runs-root", str(tmp_path)])

    assert exit_code == 1, "a campaign must be able to gate on this without parsing output"
    assert (tmp_path / "P-05").exists(), "the report-only default must not move anything"
    assert "would archive" in capsys.readouterr().out


def test_apply_archives_and_reports_success(tmp_path, capsys):
    write_run(tmp_path, "P-05", "failed")

    exit_code = main(["--runs-root", str(tmp_path), "--apply"])

    assert exit_code == 0
    assert not (tmp_path / "P-05").exists()
    assert "archived ->" in capsys.readouterr().out


def test_a_clean_runs_directory_exits_zero(tmp_path, capsys):
    write_run(tmp_path, "V-01", "completed")

    assert main(["--runs-root", str(tmp_path)]) == 0
    assert "nothing to do" in capsys.readouterr().out


def test_the_json_report_carries_what_a_caller_needs(tmp_path, capsys):
    write_run(tmp_path, "P-05", "failed", error="RuntimeError: NaN in h")

    main(["--runs-root", str(tmp_path), "--json"])
    report = json.loads(capsys.readouterr().out)

    assert report["scanned"] == 1
    assert report["applied"] is False
    assert report["incomplete"][0]["config_path"] == "configs/phase_speed/P-05.yaml"
