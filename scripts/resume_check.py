#!/usr/bin/env python
"""Find runs that did not finish, and clear the way for a clean re-run.

Session L5's harness deliberately refuses to reopen a run directory: a run ID
that means two different things is worse than no record at all. That refusal is
correct and stays. What it left open was the other half — an *interrupted* run
leaves a directory behind, and the next attempt at that config hits the refusal
and stops. This script is that other half.

WHY THIS RESTARTS RATHER THAN RESUMES
-------------------------------------
Dedalus does offer a restart primitive: ``solver.load_state(path, index)``,
which returns the write number and timestep it loaded. Three things stand
between that primitive and a working resume here, and together they make it
new solver work rather than a wiring job:

1. **There is nothing on disk to load.** ``load_state`` reads the prognostic
   variables back out of a savefile, and the harness writes no checkpoint
   handler at all. Its snapshot stream stores ``height``, ``vorticity`` and
   ``divergence``; the velocity field ``u`` is written *only* when a config sets
   ``write_full_fields: true``, and every sweep config sets it false because
   full fields are the expensive output. So for exactly the runs a campaign
   produces, the state needed to restart was never saved.

2. **Its own documentation limits it.** ``load_state`` "currently can only load
   grid space data", and a multistep timestepper's history is not restored at
   all, so a resumed run takes a startup transient that a continuous one does
   not. For a study measuring phase speeds and growth rates to 0.1%, an
   artefact injected at an arbitrary point in the middle of the series is not
   an acceptable thing to leave undocumented.

3. **It fights the immutability rule.** The provenance record is made read-only
   the moment it is written. Resuming means reopening that directory, appending
   to its output files and rewriting its record — that is, disabling the exact
   tripwire that exists to catch a run being silently rewritten.

Session L7a's brief authorises the conservative path explicitly, and this is it:
**archive the incomplete directory under a timestamped name and re-run from the
beginning.** Nothing is deleted, so a partial run stays available for
inspection; the run ID is freed, so the harness's refusal never has to be
overridden with ``--force``; and the restarted run is a single continuous
integration with no seam in it. The cost is wall-clock, and wall-clock is the
cheapest thing this project can spend.

WHAT COUNTS AS INCOMPLETE
-------------------------
The provenance record is written *before* the run starts and rewritten when it
ends, so ``outcome.status`` distinguishes the cases by itself:

===============  ==========================================================
``completed``    finished; left alone
``dry_run``      built and validated, never integrated; left alone
``failed``       raised during integration; the record says so
``started``      the record was never rewritten, so the process was killed
                 -- an OOM, a timeout, a pod that went away
(no record)      the process died between creating the directory and writing
                 the record, or the directory is not a run at all
===============  ==========================================================

Usage
-----
    python scripts/resume_check.py                 # report only; changes nothing
    python scripts/resume_check.py --apply         # archive what it found
    python scripts/resume_check.py --json          # machine-readable report
"""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_RUNS_ROOT = REPO_ROOT / "runs"
ARCHIVE_DIRNAME = "_archive"

#: Statuses that need no action. Everything else is a run to clear.
TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "dry_run"})

#: Directories under ``runs/`` that are not runs.
NON_RUN_DIRS: frozenset[str] = frozenset({ARCHIVE_DIRNAME, "_sweep_plans"})

#: Run-ID prefix of the eigenvalue campaign. Those runs are not produced by the
#: harness — an eigenvalue problem has no timestep, no output cadence and no
#: provenance record; ``EVP-hough`` and ``EVP-jet-stability`` write their own
#: results JSON and are complete. Without this they would be reported as
#: interrupted for ever, on the strength of a provenance file that was never
#: supposed to exist. ``scripts/sweep.py`` excludes the same campaign for the
#: same reason.
EVP_PREFIX = "EVP-"


@dataclass
class IncompleteRun:
    """One run directory that cannot be re-run until it is moved aside."""

    run_id: str
    path: str
    status: str
    diagnosis: str
    config_path: str | None = None
    error: str | None = None
    started_utc: str | None = None
    output_files: int = 0
    output_bytes: int = 0
    archived_to: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ResumeReport:
    runs_root: str
    scanned: int = 0
    complete: int = 0
    incomplete: list[IncompleteRun] = field(default_factory=list)
    applied: bool = False

    def as_dict(self) -> dict:
        return {
            "runs_root": self.runs_root,
            "scanned": self.scanned,
            "complete": self.complete,
            "applied": self.applied,
            "incomplete": [run.as_dict() for run in self.incomplete],
        }


def _output_totals(run_dir: Path) -> tuple[int, int]:
    """How much data the interrupted run had already written."""
    files = list(run_dir.rglob("*.h5"))
    return len(files), sum(path.stat().st_size for path in files)


def inspect_run(run_dir: Path) -> IncompleteRun | None:
    """Classify one run directory. ``None`` means it needs no action."""
    provenance_path = run_dir / "provenance.json"

    if not provenance_path.exists():
        n_files, n_bytes = _output_totals(run_dir)
        return IncompleteRun(
            run_id=run_dir.name,
            path=str(run_dir),
            status="missing",
            diagnosis=(
                "no provenance record. The harness writes the record before it starts, "
                "so the process died between creating this directory and its first write."
            ),
            output_files=n_files,
            output_bytes=n_bytes,
        )

    try:
        record = json.loads(provenance_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        n_files, n_bytes = _output_totals(run_dir)
        return IncompleteRun(
            run_id=run_dir.name,
            path=str(run_dir),
            status="unreadable",
            diagnosis=f"provenance.json is not valid JSON ({exc}); treat as interrupted",
            output_files=n_files,
            output_bytes=n_bytes,
        )

    outcome = record.get("outcome") or {}
    status = str(outcome.get("status", "missing"))
    if status in TERMINAL_STATUSES:
        return None

    diagnosis = {
        "failed": "the run raised during integration and recorded the error",
        "started": (
            "the record was never rewritten, so the process was killed rather than "
            "raising -- an out-of-memory, a wall-clock limit, or a pod that went away"
        ),
    }.get(status, f"unrecognised outcome status {status!r}")

    n_files, n_bytes = _output_totals(run_dir)
    return IncompleteRun(
        run_id=str(record.get("run_id", run_dir.name)),
        path=str(run_dir),
        status=status,
        diagnosis=diagnosis,
        config_path=record.get("config_path"),
        error=outcome.get("error"),
        started_utc=record.get("started_utc"),
        output_files=n_files,
        output_bytes=n_bytes,
    )


def scan(runs_root: Path = DEFAULT_RUNS_ROOT) -> ResumeReport:
    """Every run directory under ``runs_root``, classified."""
    report = ResumeReport(runs_root=str(runs_root))
    if not runs_root.is_dir():
        return report

    for run_dir in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        if (
            run_dir.name in NON_RUN_DIRS
            or run_dir.name.startswith(".")
            or run_dir.name.startswith(EVP_PREFIX)
        ):
            continue
        report.scanned += 1
        found = inspect_run(run_dir)
        if found is None:
            report.complete += 1
        else:
            report.incomplete.append(found)
    return report


def archive(
    run: IncompleteRun, runs_root: Path = DEFAULT_RUNS_ROOT, stamp: str | None = None
) -> Path:
    """Move an incomplete run aside under a timestamped name. Nothing is deleted.

    The destination sits inside ``runs/`` so the move is a rename on one
    filesystem rather than a copy — atomic, and it cannot half-succeed and leave
    two partial copies of the same run.
    """
    source = Path(run.path)
    stamp = stamp or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = runs_root / ARCHIVE_DIRNAME / f"{source.name}_{run.status}_{stamp}"
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        raise FileExistsError(f"{destination} already exists; refusing to merge two runs")

    # The provenance record is read-only by design. Archiving does not rewrite
    # it -- the record of a failed run is exactly what makes the failure
    # explicable later -- but the move itself needs the directory writable.
    provenance = source / "provenance.json"
    if provenance.exists():
        provenance.chmod(stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    shutil.move(str(source), str(destination))

    moved = destination / "provenance.json"
    if moved.exists():
        moved.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

    run.archived_to = str(destination)
    return destination


def format_report(report: ResumeReport) -> str:
    lines = [
        f"== resume check: {report.runs_root} ==",
        f"  {report.scanned} run directories, {report.complete} complete, "
        f"{len(report.incomplete)} needing action",
    ]
    if not report.incomplete:
        lines.append("  nothing to do.")
        return "\n".join(lines)

    for run in report.incomplete:
        lines.append("")
        lines.append(f"  {run.run_id}  [{run.status}]")
        lines.append(f"    {run.diagnosis}")
        if run.error:
            lines.append(f"    error: {run.error}")
        if run.output_files:
            lines.append(
                f"    {run.output_files} output file(s), "
                f"{run.output_bytes / 1e6:.1f} MB already written"
            )
        if run.archived_to:
            lines.append(f"    archived -> {run.archived_to}")
            if run.config_path:
                lines.append(f"    re-run with: scripts/run_mpi.sh {run.config_path}")
        else:
            lines.append("    would archive (re-run with --apply to do it)")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--runs-root", default=str(DEFAULT_RUNS_ROOT), help="directory of run directories"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="archive the incomplete runs found (default: report only, change nothing)",
    )
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = parser.parse_args(argv)

    runs_root = Path(args.runs_root)
    report = scan(runs_root)

    if args.apply:
        report.applied = True
        for run in report.incomplete:
            archive(run, runs_root=runs_root)

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(format_report(report))

    # A non-zero exit when action is still outstanding, so a pod script can gate
    # a campaign on "no half-finished runs in the way" without parsing anything.
    return 1 if report.incomplete and not args.apply else 0


if __name__ == "__main__":
    raise SystemExit(main())
