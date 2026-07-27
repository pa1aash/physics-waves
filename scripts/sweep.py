#!/usr/bin/env python
"""Plan a campaign: validate every config, scale its cadences, order the runs.

This is the thing that stands between a campaign and the two ways a sweep goes
wrong before it has computed anything.

**The first is silent, and it is why this script exists.** The phase-speed
campaign varies the rotation rate over a factor of sixteen, and the westward
phase speed of a Rossby-Haurwitz mode is linear in that rate. Every ``P-*`` stub
nevertheless states the same Earth-rate output cadence, so at ``4 Omega_0`` the
snapshot stream samples the wave past Nyquist and the measured phase speed comes
back wrong by a factor of four with the sign reversed — while every check
computable from the output alone reports the sampling as comfortable. That
failure cannot be diagnosed after the fact and it cannot be left to whoever reads
the config next, so it is fixed here, once, for every run the campaign will ever
plan. ``src/solver/cadence.py`` carries the physics and the derivation.

**The second is ordinary.** A config that does not validate, or that still holds
a ``TBD_SESSION_L5`` placeholder, fails at the moment the solver reaches it —
which on a pod is after the queue ahead of it has already been paid for. Every
config in the plan is validated up front, and a campaign with a bad config
produces no plan at all.

**This script executes nothing.** It emits a plan file; ``scripts/run_mpi.sh``
executes one entry of it. Keeping the two apart means a plan can be read,
diffed and committed before any compute is spent, and it means the plan is a
record of what was *intended* that survives independently of what happened.

**Runs are ordered, and they run one at a time.** Each entry claims several MPI
ranks, so running configs concurrently on a single 32-core pod would have them
contend for the same cores and corrupt exactly the wall-clock numbers Session R1
needs. Sequential-by-default is the simple choice, and it stays until there is a
specific reason to parallelise across configs rather than within one.

Usage
-----
    python scripts/sweep.py phase_speed
    python scripts/sweep.py verification --dry-run
    python scripts/sweep.py configs/phase_speed/P-12.yaml configs/phase_speed/P-11.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.solver.cadence import CADENCE_KEYS, EARTH_OMEGA, plan_cadences  # noqa: E402
from src.solver.equations import RESOLUTIONS  # noqa: E402
from src.solver.harness import TBD_SENTINEL, load_config  # noqa: E402

CONFIG_ROOT = REPO_ROOT / "configs"
PLAN_ROOT = REPO_ROOT / "runs" / "_sweep_plans"

#: The campaigns that produce timestepped runs. ``evp`` is excluded on purpose:
#: an eigenvalue problem has no timestep, no output cadence and no MPI rank grid,
#: so there is nothing here for it to plan.
CAMPAIGNS: tuple[str, ...] = ("verification", "phase_speed", "instability")

#: Ranks per resolution. A **heuristic**, not a measurement: it follows the one
#: real data point this project has (Phase-0 ran L0 and L1 on 4 ranks) and then
#: assumes each rung up the ladder can usefully absorb twice the ranks, because
#: the transform work grows faster than the communication does. Session R1
#: measures the actual scaling on the pod and replaces these numbers with
#: something earned. Until then a plan carries them labelled as a guess.
RANKS_BY_RESOLUTION: dict[str, int] = {"L0": 4, "L1": 4, "L2": 8, "L3": 16}

RANK_HEURISTIC_NOTE = (
    "ranks are a heuristic anchored on the Phase-0 gate (L0 and L1 measured on 4 ranks, "
    "docs/COMPUTE.md), doubling per rung above L1; Session R1's timing calibration on the "
    "pod replaces them with measured values"
)


@dataclass
class PlannedRun:
    """One config's place in the plan: what to run, how, and what was changed."""

    run_id: str
    config_path: str
    campaign: str
    description: str
    resolution: str
    resolution_shape: list[int]
    mpi_ranks: int
    omega: float
    omega_ratio: float
    stop_sim_time_s: float | None
    cadences: dict[str, float]
    cadence_overrides: dict[str, float]
    would_have_aliased: list[str]
    cadence_detail: dict[str, dict] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def campaign_configs(campaign: str) -> list[Path]:
    """Every config of one campaign, in run-ID order."""
    directory = CONFIG_ROOT / campaign
    if not directory.is_dir():
        raise SystemExit(f"no such campaign directory: {directory}")
    return sorted(p for p in directory.glob("*.yaml") if not p.name.startswith("_"))


def _surviving_placeholders(config: dict) -> list[str]:
    """Every ``TBD_SESSION_L5`` still in the config, by dotted key path.

    The harness refuses to start on these. Finding them here instead means the
    campaign is rejected before the queue starts rather than in the middle of it.
    """
    found: list[str] = []

    def walk(node, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else str(key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")
        elif node == TBD_SENTINEL:
            found.append(path)

    walk(config, "")
    return found


def plan_one(config_path: Path, baseline: dict[str, float] | None = None) -> PlannedRun:
    """Validate one config and decide everything the runner needs to know.

    ``load_config`` is the harness's own loader, so the plan validates against
    exactly the schema the solver will validate against — not a second copy of it
    that can drift.
    """
    config = load_config(config_path)

    placeholders = _surviving_placeholders(config)
    if placeholders:
        raise SystemExit(
            f"{config_path}: unresolved placeholders at {', '.join(placeholders)}. "
            "Run `make configs` to derive them from the stated policy; the harness "
            "will refuse this config anyway, and refusing it now costs no compute."
        )

    campaign = config["campaign"]
    if campaign not in CAMPAIGNS:
        raise SystemExit(
            f"{config_path}: campaign {campaign!r} is not a timestepped campaign. "
            f"Plannable campaigns are {', '.join(CAMPAIGNS)}."
        )

    resolution = config["resolution"]
    shape = RESOLUTIONS[resolution]

    cadence_plan = plan_cadences(config, baseline=baseline)

    outputs = config.get("outputs") or {}
    applied = {
        key: (
            cadence_plan.decisions[key].applied_s
            if key in cadence_plan.decisions
            else float(outputs.get(key) or 0.0)
        )
        for key in CADENCE_KEYS
    }

    numerics = config.get("numerics") or {}
    stop_sim_time = numerics.get("stop_sim_time")

    return PlannedRun(
        run_id=config["run_id"],
        config_path=str(config_path.relative_to(REPO_ROOT)),
        campaign=campaign,
        description=config.get("description", ""),
        resolution=resolution,
        resolution_shape=list(shape),
        mpi_ranks=RANKS_BY_RESOLUTION[resolution],
        omega=cadence_plan.omega,
        omega_ratio=cadence_plan.omega_ratio,
        stop_sim_time_s=float(stop_sim_time) if stop_sim_time is not None else None,
        cadences=applied,
        cadence_overrides=cadence_plan.overrides,
        would_have_aliased=cadence_plan.would_have_aliased,
        cadence_detail={k: d.as_dict() for k, d in cadence_plan.decisions.items()},
        notes=list(cadence_plan.notes),
    )


def earth_rate_baseline(configs: list[Path]) -> dict[str, float] | None:
    """The Earth-rate member's cadences, which the rest of the sweep scales from.

    A rotation sweep states its cadences once, at Earth rate, and then repeats
    them; reading the baseline off the Earth-rate member and scaling it recovers
    the intent those stubs had before the sweep was written. When no member sits
    at Earth rate there is nothing to anchor on and each config is scaled from
    its own stated values instead.
    """
    for path in configs:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
        omega = ((config or {}).get("physical") or {}).get("Omega")
        if omega is None:
            continue
        if abs(float(omega) / EARTH_OMEGA - 1.0) < 1e-6:
            outputs = config.get("outputs") or {}
            baseline = {
                key: float(outputs[key])
                for key in CADENCE_KEYS
                if isinstance(outputs.get(key), int | float) and outputs[key] > 0
            }
            if baseline:
                return baseline
    return None


def build_plan(name: str, configs: list[Path]) -> dict:
    baseline = earth_rate_baseline(configs)
    runs = [plan_one(path, baseline=baseline) for path in configs]
    return {
        "campaign": name,
        "created_utc": datetime.now(UTC).isoformat(),
        "execution": "sequential",
        "execution_note": (
            "one config at a time, each on several MPI ranks. Running configs concurrently "
            "on one pod would have them contend for the same cores and corrupt the very "
            "wall-clock numbers Session R1 needs to calibrate the ladder."
        ),
        "cadence_reference_omega": EARTH_OMEGA,
        "rank_heuristic_note": RANK_HEURISTIC_NOTE,
        "runs": [asdict(run) for run in runs],
    }


#: How a cadence's binding constraint is marked in the printed table.
BOUND_MARKER = {"stated": "", "density": "*", "nyquist": "!"}


def format_table(plan: dict) -> str:
    header = f"{'run':<8} {'res':<4} {'ranks':>5} {'Omega/Omega_0':>13}  cadences (s)"
    lines = [header, "-" * len(header)]
    for run in plan["runs"]:
        cadences = " ".join(
            f"{key.split('_')[0]}={run['cadences'][key]:g}"
            + BOUND_MARKER.get(run["cadence_detail"].get(key, {}).get("bound_by", "stated"), "")
            for key in CADENCE_KEYS
            if run["cadences"].get(key)
        )
        lines.append(
            f"{run['run_id']:<8} {run['resolution']:<4} {run['mpi_ranks']:>5} "
            f"{run['omega_ratio']:>13.4g}  {cadences}"
        )
    lines.append("")
    lines.append(
        "* = tightened to hold sampling density constant across the rotation sweep, "
        "eq. (cadscale).\n"
        "! = tightened because the mode itself outruns the stated interval, eq. (cadsafe)."
    )

    aliased = [
        (r["run_id"], r["would_have_aliased"]) for r in plan["runs"] if r["would_have_aliased"]
    ]
    if aliased:
        lines.append("")
        lines.append(
            "PAST NYQUIST AS CONFIGURED -- as written these would have returned a confident, "
            "precise phase speed of the wrong magnitude and, most likely, the wrong sign:"
        )
        for run_id, keys in aliased:
            lines.append(f"  {run_id}: {', '.join(keys)}")
        lines.append("  (all are corrected in the cadences above)")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "targets",
        nargs="+",
        help=f"a campaign name ({', '.join(CAMPAIGNS)}) or explicit config paths",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="where to write the plan (default: runs/_sweep_plans/<campaign>_<timestamp>.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate and print the plan without writing it",
    )
    args = parser.parse_args(argv)

    if len(args.targets) == 1 and args.targets[0] in CAMPAIGNS:
        name = args.targets[0]
        configs = campaign_configs(name)
    else:
        name = "custom"
        configs = [Path(t).resolve() for t in args.targets]
        missing = [str(p) for p in configs if not p.is_file()]
        if missing:
            raise SystemExit(f"no such config: {', '.join(missing)}")

    if not configs:
        raise SystemExit("no configs to plan")

    plan = build_plan(name, configs)
    print(format_table(plan))

    if args.dry_run:
        print("\n[sweep] --dry-run: plan not written")
        return 0

    if args.output:
        destination = Path(args.output)
    else:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        destination = PLAN_ROOT / f"{name}_{stamp}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"\n[sweep] {len(plan['runs'])} runs -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
