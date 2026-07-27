"""Core-hours are derived, not maintained, so the derivation is what needs testing.

The arithmetic is one multiplication, which is exactly why it is worth pinning:
a cost total that is quietly wrong by the rank count looks entirely plausible,
and it is the number a decision about the resolution ladder gets made on.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.cost_log import (
    DOC_BEGIN,
    DOC_END,
    collect,
    main,
    update_doc,
)


def write_run(
    runs_root: Path,
    run_id: str,
    *,
    status: str = "completed",
    ranks: int = 4,
    wall: float = 3600.0,
    campaign: str = "phase_speed",
    resolution: str = "L1",
    output_bytes: int = 0,
) -> None:
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "run_id": run_id,
        "campaign": campaign,
        "config": {"resolution": resolution},
        "environment": {"mpi_size": ranks},
        "outcome": {"status": status, "wall_seconds": wall, "finished_utc": "2026-07-27T00:00:00Z"},
        "outputs": [{"path": "snapshots/s1.h5", "bytes": output_bytes}] if output_bytes else [],
    }
    (run_dir / "provenance.json").write_text(json.dumps(record), encoding="utf-8")


def test_core_hours_are_ranks_times_wall_not_wall_alone(tmp_path):
    """The failure mode this test exists for: forgetting the rank factor."""
    write_run(tmp_path, "P-01", ranks=8, wall=1800.0)

    report = collect(tmp_path)

    assert report.total_core_hours == pytest.approx(4.0)  # 8 * 1800 / 3600
    assert report.runs[0].core_hours != pytest.approx(0.5), "rank count was dropped"


def test_a_dry_run_costs_nothing_because_it_has_no_wall_time(tmp_path):
    run_dir = tmp_path / "V-02"
    run_dir.mkdir()
    (run_dir / "provenance.json").write_text(
        json.dumps({"run_id": "V-02", "outcome": {"status": "dry_run"}}), encoding="utf-8"
    )

    assert collect(tmp_path).runs == []


def test_failed_runs_are_counted_but_reported_apart(tmp_path):
    """They were paid for. A budget that forgets them reads healthy until it isn't."""
    write_run(tmp_path, "P-01", status="completed", ranks=4, wall=3600.0)
    write_run(tmp_path, "P-02", status="failed", ranks=4, wall=1800.0)

    report = collect(tmp_path)

    assert report.total_core_hours == pytest.approx(6.0)
    assert report.completed_core_hours == pytest.approx(4.0)
    assert report.wasted_core_hours == pytest.approx(2.0)
    assert [r.run_id for r in report.wasted] == ["P-02"]


def test_archived_runs_still_count(tmp_path):
    """An interrupted run moved aside by resume_check consumed real compute."""
    write_run(tmp_path, "P-01", ranks=4, wall=3600.0)
    write_run(tmp_path / "_archive", "P-02_failed_20260727T000000Z", status="failed", wall=3600.0)

    report = collect(tmp_path)

    assert len(report.runs) == 2
    assert report.total_core_hours == pytest.approx(8.0)


def test_grouping_by_campaign_and_by_rung(tmp_path):
    write_run(tmp_path, "P-01", campaign="phase_speed", resolution="L1", ranks=4, wall=3600.0)
    write_run(tmp_path, "P-02", campaign="phase_speed", resolution="L1", ranks=4, wall=7200.0)
    write_run(tmp_path, "V-01", campaign="verification", resolution="L0", ranks=4, wall=900.0)

    report = collect(tmp_path)

    assert report.by_campaign()["phase_speed"]["runs"] == 2
    assert report.by_campaign()["phase_speed"]["core_hours"] == pytest.approx(12.0)
    assert report.by_resolution()["L1"]["mean_wall_seconds"] == pytest.approx(5400.0)


def test_an_empty_runs_directory_reports_zero_rather_than_failing(tmp_path):
    report = collect(tmp_path)
    assert report.total_core_hours == 0.0
    assert main(["--runs-root", str(tmp_path)]) == 0


def test_update_doc_rewrites_only_between_the_markers(tmp_path):
    write_run(tmp_path, "P-01", ranks=4, wall=3600.0, output_bytes=2_000_000)
    doc = tmp_path / "COMPUTE.md"
    doc.write_text(
        f"# Compute plan\n\nhand-written before\n\n{DOC_BEGIN}\nstale\n{DOC_END}\n\n"
        "hand-written after\n",
        encoding="utf-8",
    )

    assert update_doc(collect(tmp_path), path=doc) is True

    text = doc.read_text(encoding="utf-8")
    assert "hand-written before" in text
    assert "hand-written after" in text
    assert "stale" not in text
    assert "4.000" in text


def test_update_doc_refuses_a_document_with_no_block(tmp_path):
    """Placing the block is an editorial decision, not one a script should make."""
    doc = tmp_path / "COMPUTE.md"
    doc.write_text("# Compute plan\n\nno markers here\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="no <!-- cost-log:begin -->"):
        update_doc(collect(tmp_path), path=doc)


def test_the_repository_compute_doc_carries_the_block():
    """The real docs/COMPUTE.md must stay updatable."""
    from scripts.cost_log import COMPUTE_DOC

    text = COMPUTE_DOC.read_text(encoding="utf-8")
    assert DOC_BEGIN in text and DOC_END in text
