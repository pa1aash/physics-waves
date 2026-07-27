#!/usr/bin/env python
"""What the campaign has actually cost, read off the runs themselves.

Every completed run already records the two numbers this needs —
``outcome.wall_seconds`` and ``environment.mpi_size`` — so there is nothing to
instrument and nothing to remember to log. The cost of a campaign is a property
of the runs it produced, and it is derived here rather than maintained by hand,
because a hand-maintained total is one someone eventually forgets to update.

    core-hours = ranks * wall_seconds / 3600

**Why core-hours and not wall-clock.** A pod is billed for the cores it holds,
not for the cores a run happens to use, so an eight-rank run that finishes in
half the time of a four-rank run costs the same. Wall-clock answers "when will
this be done"; core-hours answers "what did it cost", and the ladder in
``docs/COMPUTE.md`` is written in the second.

**The estimate this is measured against is a Fermi estimate**, 60-150 core-hours
for the whole project, and the point of tracking is to find out early if it was
wrong. A campaign that is at 40% of its runs and 90% of its budget is a campaign
whose remaining resolution ladder needs rethinking, and that is worth knowing
before the L3 reference runs rather than after.

**Runs that failed still cost money.** They are counted, and reported separately
rather than folded into the total, because the budget question and the "how much
of this was useful" question have different answers and both matter.

Usage
-----
    python scripts/cost_log.py                    # table across all campaigns
    python scripts/cost_log.py --json             # machine-readable
    python scripts/cost_log.py --update-doc       # rewrite the COMPUTE.md section
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_RUNS_ROOT = REPO_ROOT / "runs"
COMPUTE_DOC = REPO_ROOT / "docs" / "COMPUTE.md"

#: The Fermi estimate from the original compute plan, in core-hours. A bracket,
#: not a number: the spread is what an estimate made before any run existed is
#: honestly worth.
BUDGET_LOW_CORE_HOURS = 60.0
BUDGET_HIGH_CORE_HOURS = 150.0

#: Markers delimiting the generated block in docs/COMPUTE.md. Everything between
#: them is rewritten by --update-doc; everything outside is hand-written and is
#: never touched.
DOC_BEGIN = "<!-- cost-log:begin -->"
DOC_END = "<!-- cost-log:end -->"


@dataclass
class RunCost:
    run_id: str
    campaign: str
    resolution: str
    status: str
    ranks: int
    wall_seconds: float
    core_hours: float
    output_bytes: int = 0
    finished_utc: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class CostReport:
    runs: list[RunCost] = field(default_factory=list)
    generated_utc: str = ""

    @property
    def completed(self) -> list[RunCost]:
        return [r for r in self.runs if r.status == "completed"]

    @property
    def wasted(self) -> list[RunCost]:
        """Runs that consumed time without producing a usable result."""
        return [r for r in self.runs if r.status not in ("completed", "dry_run")]

    @property
    def total_core_hours(self) -> float:
        return sum(r.core_hours for r in self.runs)

    @property
    def completed_core_hours(self) -> float:
        return sum(r.core_hours for r in self.completed)

    @property
    def wasted_core_hours(self) -> float:
        return sum(r.core_hours for r in self.wasted)

    def by_campaign(self) -> dict[str, dict]:
        grouped: dict[str, dict] = defaultdict(
            lambda: {"runs": 0, "core_hours": 0.0, "wall_seconds": 0.0, "output_bytes": 0}
        )
        for run in self.runs:
            entry = grouped[run.campaign]
            entry["runs"] += 1
            entry["core_hours"] += run.core_hours
            entry["wall_seconds"] += run.wall_seconds
            entry["output_bytes"] += run.output_bytes
        return dict(grouped)

    def by_resolution(self) -> dict[str, dict]:
        grouped: dict[str, dict] = defaultdict(
            lambda: {"runs": 0, "core_hours": 0.0, "wall_seconds": 0.0}
        )
        for run in self.completed:
            entry = grouped[run.resolution]
            entry["runs"] += 1
            entry["core_hours"] += run.core_hours
            entry["wall_seconds"] += run.wall_seconds
        for entry in grouped.values():
            entry["mean_wall_seconds"] = entry["wall_seconds"] / entry["runs"]
        return dict(grouped)

    def as_dict(self) -> dict:
        return {
            "generated_utc": self.generated_utc,
            "budget_core_hours": [BUDGET_LOW_CORE_HOURS, BUDGET_HIGH_CORE_HOURS],
            "total_core_hours": self.total_core_hours,
            "completed_core_hours": self.completed_core_hours,
            "wasted_core_hours": self.wasted_core_hours,
            "n_runs": len(self.runs),
            "n_completed": len(self.completed),
            "by_campaign": self.by_campaign(),
            "by_resolution": self.by_resolution(),
            "runs": [run.as_dict() for run in self.runs],
        }


def cost_of(record: dict, run_dir: Path) -> RunCost | None:
    """Derive one run's cost from its provenance record.

    ``None`` for a record with no wall time — a dry run, or a run whose record
    was never rewritten. There is nothing to charge for either.
    """
    outcome = record.get("outcome") or {}
    wall = outcome.get("wall_seconds")
    if wall is None:
        return None

    environment = record.get("environment") or {}
    ranks = int(environment.get("mpi_size") or 1)
    wall = float(wall)

    outputs = record.get("outputs") or []
    output_bytes = sum(int(entry.get("bytes", 0)) for entry in outputs)

    return RunCost(
        run_id=str(record.get("run_id", run_dir.name)),
        campaign=str(record.get("campaign", "unknown")),
        resolution=str((record.get("config") or {}).get("resolution", "?")),
        status=str(outcome.get("status", "unknown")),
        ranks=ranks,
        wall_seconds=wall,
        core_hours=ranks * wall / 3600.0,
        output_bytes=output_bytes,
        finished_utc=outcome.get("finished_utc"),
    )


def collect(runs_root: Path = DEFAULT_RUNS_ROOT) -> CostReport:
    """Every run under ``runs_root`` that recorded a wall time, archives included.

    Archived runs are counted deliberately: they were paid for. A budget that
    silently forgets the attempts that failed is a budget that reads as healthy
    right up to the point it is not.
    """
    report = CostReport(generated_utc=datetime.now(UTC).isoformat(timespec="seconds"))
    if not runs_root.is_dir():
        return report

    for provenance_path in sorted(runs_root.rglob("provenance.json")):
        try:
            record = json.loads(provenance_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        cost = cost_of(record, provenance_path.parent)
        if cost is not None:
            report.runs.append(cost)
    return report


def format_report(report: CostReport) -> str:
    lines = ["== compute cost to date =="]
    if not report.runs:
        lines.append("  no runs with a recorded wall time yet.")
        return "\n".join(lines)

    lines.append("")
    lines.append(f"  {'run':<20} {'camp':<13} {'res':<4} {'ranks':>5} {'wall s':>9} {'core-h':>8}")
    lines.append("  " + "-" * 64)
    for run in sorted(report.runs, key=lambda r: (r.campaign, r.run_id)):
        flag = "" if run.status == "completed" else f"  [{run.status}]"
        lines.append(
            f"  {run.run_id:<20} {run.campaign:<13} {run.resolution:<4} {run.ranks:>5} "
            f"{run.wall_seconds:>9.1f} {run.core_hours:>8.3f}{flag}"
        )

    lines.append("")
    lines.append("  by resolution rung (completed runs only):")
    for label, entry in sorted(report.by_resolution().items()):
        lines.append(
            f"    {label:<4} {entry['runs']:>3} run(s)  "
            f"mean {entry['mean_wall_seconds']:>8.1f} s  "
            f"{entry['core_hours']:>7.3f} core-h"
        )

    total = report.total_core_hours
    lines.append("")
    lines.append(f"  total          {total:.3f} core-hours")
    lines.append(f"    completed    {report.completed_core_hours:.3f}")
    if report.wasted:
        lines.append(
            f"    unusable     {report.wasted_core_hours:.3f} "
            f"({len(report.wasted)} run(s) that failed or were interrupted)"
        )
    lines.append(
        f"  against the {BUDGET_LOW_CORE_HOURS:.0f}-{BUDGET_HIGH_CORE_HOURS:.0f} core-hour "
        f"Fermi estimate: {100 * total / BUDGET_HIGH_CORE_HOURS:.1f}% of the upper bound, "
        f"{100 * total / BUDGET_LOW_CORE_HOURS:.1f}% of the lower"
    )
    return "\n".join(lines)


def doc_block(report: CostReport) -> str:
    """The generated Markdown that lives between the markers in COMPUTE.md."""
    total = report.total_core_hours
    lines = [
        DOC_BEGIN,
        "",
        f"*Generated by `scripts/cost_log.py` from run provenance on "
        f"{report.generated_utc[:10]}. Do not edit by hand — rerun "
        f"`python scripts/cost_log.py --update-doc`.*",
        "",
    ]

    if not report.runs:
        lines += ["No runs have recorded a wall time yet.", "", DOC_END]
        return "\n".join(lines)

    lines += [
        "| Campaign | Runs | Core-hours | Output |",
        "|----------|-----:|-----------:|-------:|",
    ]
    for campaign, entry in sorted(report.by_campaign().items()):
        lines.append(
            f"| {campaign} | {entry['runs']} | {entry['core_hours']:.3f} | "
            f"{entry['output_bytes'] / 1e6:.1f} MB |"
        )
    lines += [
        f"| **total** | **{len(report.runs)}** | **{total:.3f}** | |",
        "",
        f"Measured against the Fermi estimate of {BUDGET_LOW_CORE_HOURS:.0f}–"
        f"{BUDGET_HIGH_CORE_HOURS:.0f} core-hours for the whole project, this is "
        f"**{100 * total / BUDGET_HIGH_CORE_HOURS:.1f}%** of the upper bound.",
    ]

    if report.wasted:
        lines += [
            "",
            f"Of that, {report.wasted_core_hours:.3f} core-hours went to "
            f"{len(report.wasted)} run(s) that failed or were interrupted. Those are "
            "counted: they were paid for.",
        ]

    by_resolution = report.by_resolution()
    if by_resolution:
        lines += [
            "",
            "Mean wall time per completed run, by rung — this is what Session R1's "
            "calibration refines and what the rank heuristic in `scripts/sweep.py` "
            "is currently guessing from:",
            "",
            "| Rung | Runs | Mean wall (s) | Core-hours |",
            "|------|-----:|--------------:|-----------:|",
        ]
        for label, entry in sorted(by_resolution.items()):
            lines.append(
                f"| {label} | {entry['runs']} | {entry['mean_wall_seconds']:.1f} | "
                f"{entry['core_hours']:.3f} |"
            )

    lines += ["", DOC_END]
    return "\n".join(lines)


def update_doc(report: CostReport, path: Path = COMPUTE_DOC) -> bool:
    """Replace the generated block in ``path``. Returns whether anything changed.

    The markers must already exist. Creating them here would let this script
    decide where in a hand-written document its output belongs, and that is an
    editorial decision, not a scripted one.
    """
    text = path.read_text(encoding="utf-8")
    if DOC_BEGIN not in text or DOC_END not in text:
        raise SystemExit(
            f"{path} has no {DOC_BEGIN} / {DOC_END} block. Add one where the cost "
            "table belongs; this script fills it in but does not place it."
        )

    pattern = re.compile(
        re.escape(DOC_BEGIN) + r".*?" + re.escape(DOC_END),
        re.DOTALL,
    )
    updated = pattern.sub(lambda _: doc_block(report), text, count=1)
    if updated == text:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs-root", default=str(DEFAULT_RUNS_ROOT))
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    parser.add_argument(
        "--update-doc",
        action="store_true",
        help="rewrite the generated cost block in docs/COMPUTE.md",
    )
    args = parser.parse_args(argv)

    report = collect(Path(args.runs_root))

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(format_report(report))

    if args.update_doc:
        changed = update_doc(report)
        print(f"\n[cost_log] {COMPUTE_DOC.name}: {'updated' if changed else 'already current'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
