"""Run harness: build and integrate one simulation from one YAML config.

Physics first. What this module does is take a statement about a fluid — a
rotating shallow layer of a given depth on a sphere of a given size and rotation
rate, started in a given state — and integrate it forward. Everything else here
exists to make sure that statement, and the answer it produced, can still be read
off unambiguously in a year.

**Nothing about the physics is set here.** The equations live in
``equations.py``, the states in ``initial_conditions/``, and every number that
selects between them lives in a config file. This module contains no physical
constant and no default a run could silently inherit. That is the project's
"configs are the single source of truth" rule made structural rather than
aspirational: if a parameter is not in the config, the run does not start.

**Provenance is written before the run, not after.** A record written only on
success describes exactly the runs that need explaining least. The record here is
opened at the start with the config, its hash, the git commit, the resolved
environment and the machine; the outcome is appended when the run ends, whether
it ended by finishing or by raising. A crashed run leaves a record saying so.

**Output is immutable.** A run directory that already carries a completed
provenance record is not reopened. Re-running the same config either goes to a
new directory or is refused, because a run ID that means two different things is
worse than no record at all. The provenance file is made read-only after writing,
so an accidental overwrite fails loudly instead of quietly rewriting history.

**Three warnings the harness raises, all of them physics.** They are warnings and
not errors because in each case the run is still well posed — it just is not
answering the question the config appears to ask.

1. *Mean-depth disagreement.* Every initial condition reports its own area-mean
   free surface. When that differs materially from ``physical.H``, the equations
   remain exact but the split between the implicit ``H div(u)`` term and the
   explicit mass flux stops reflecting the actual fluid, and the timestep
   restriction the timestepper was chosen for no longer applies.

2. *Integration beyond a case's validity window.* Williamson case 6 is a
   benchmark only for as long as its own instability stays small (see
   ``williamson.stable_window_seconds``). Past that, error against a reference is
   measuring an instability, not a scheme.

3. *Rotation declared twice.* Runs I-06 to I-09 vary ``Omega``. If a config
   carries an ``omega_multiplier`` in its initial-condition parameters that
   disagrees with ``physical.Omega``, one of the two is stale, and the run would
   be labelled with a rotation rate it did not use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import stat
import subprocess
import sys
import time
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import dedalus.public as d3
import numpy as np
import yaml

from src.solver.equations import RESOLUTIONS, build_problem, physical_params
from src.solver.initial_conditions import apply_initial_condition

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "configs" / "_schema.yaml"
REGISTRY_PATH = REPO_ROOT / "configs" / "RUN_REGISTRY.md"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "runs"

# The sentinel Session 00 wrote into every config for values that could not be
# chosen before a solver existed. A run must not start while any survive.
TBD_SENTINEL = "TBD_SESSION_L5"

# Relative disagreement between a case's own mean depth and physical.H that is
# tolerated silently. Chosen at 5% because the balance constructions leave errors
# far below it, so anything larger is a config statement rather than round-off.
MEAN_DEPTH_TOLERANCE = 0.05


class ConfigError(ValueError):
    """A configuration that cannot be run as written."""


@dataclass
class RunResult:
    run_id: str
    output_dir: Path
    provenance: dict


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #


def load_config(path) -> dict:
    """Read one config, validate it against the schema, and reject sentinels."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    config = yaml.safe_load(text)
    if not isinstance(config, dict):
        raise ConfigError(f"{path} does not contain a YAML mapping")

    _validate_against_schema(config, path)
    unresolved = sorted(_find_sentinels(config))
    if unresolved:
        raise ConfigError(
            f"{path} still carries the Session-00 placeholder at: {', '.join(unresolved)}. "
            "Resolve them in the config; the harness will not invent a value."
        )
    resolved = path.resolve()
    config["_source_path"] = str(
        resolved.relative_to(REPO_ROOT) if resolved.is_relative_to(REPO_ROOT) else resolved
    )
    config["_source_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return config


def _validate_against_schema(config: dict, path: Path) -> None:
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - jsonschema is a pinned dependency
        warnings.warn(f"jsonschema unavailable; {path} not validated", stacklevel=2)
        return
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(config, schema)


def _find_sentinels(node, trail: str = "") -> list[str]:
    """Every dotted path at which the unresolved-value sentinel still appears."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            found += _find_sentinels(value, f"{trail}.{key}" if trail else str(key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found += _find_sentinels(value, f"{trail}[{i}]")
    elif node == TBD_SENTINEL:
        found.append(trail or "<root>")
    return found


# --------------------------------------------------------------------------- #
# provenance
# --------------------------------------------------------------------------- #


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def environment_record() -> dict:
    """Everything about this machine and toolchain that could change an answer."""
    import dedalus
    import scipy

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "hostname": socket.gethostname(),
        "dedalus": dedalus.__version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "mpi_size": int(os.environ.get("OMPI_COMM_WORLD_SIZE", "1")),
        "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
    }


def git_record() -> dict:
    """The commit a run was produced from, and whether the tree was clean.

    ``dirty`` is the honest field. A run made from an edited working tree cannot
    be reproduced from its commit alone, and recording that is more useful than
    recording a commit hash that does not describe the code that ran.
    """
    status = _git("status", "--porcelain")
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(status),
        "dirty_paths": status.splitlines()[:20],
    }


def _write_provenance(path: Path, record: dict, comm=None) -> None:
    """Write the record and make it read-only.

    Read-only is not security; it is a tripwire. Anything that later tries to
    rewrite a run's provenance hits a permission error at the point of the
    mistake rather than silently producing a record that no longer describes the
    data beside it.

    **One rank writes; all ranks wait.** The tripwire and MPI interact badly if
    every rank writes: the first rank to arrive makes the file read-only and the
    next one to arrive trips the tripwire it just set, killing a healthy run with
    a permission error that looks exactly like the corruption the tripwire exists
    to catch. Rank 0 owns the record, and the barrier afterwards keeps any rank
    from running ahead of a record that is only half written.
    """
    if comm is None or comm.rank == 0:
        if path.exists():
            path.chmod(stat.S_IWUSR | stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        path.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    if comm is not None and comm.size > 1:
        comm.Barrier()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# physics warnings
# --------------------------------------------------------------------------- #


def check_physics_consistency(config: dict, metadata: dict) -> list[str]:
    """Return human-readable warnings about a config that is internally at odds."""
    messages: list[str] = []
    params = physical_params(config)

    mean_depth = metadata.get("mean_depth_m")
    if mean_depth is not None and params["H"] > 0:
        relative = abs(mean_depth - params["H"]) / params["H"]
        if relative > MEAN_DEPTH_TOLERANCE:
            messages.append(
                f"physical.H = {params['H']:.1f} m but the initial condition's own mean "
                f"free surface is {mean_depth:.1f} m ({relative:.0%} apart). The equations "
                "stay exact, but H no longer describes this fluid, so the implicit "
                "H*div(u) term and the timestep restriction it implies are mismatched."
            )

    window = metadata.get("max_stable_window_s")
    stop = (config.get("numerics") or {}).get("stop_sim_time")
    if window is not None and isinstance(stop, int | float) and stop > window:
        messages.append(
            f"stop_sim_time = {stop / 86400:.2f} d exceeds this case's validity window of "
            f"{window / 86400:.2f} d. Past the window the case's own instability grows, so "
            "error against a reference measures that instability rather than the scheme. "
            "Integrating anyway; the run is not truncated."
        )

    ic_params = config.get("initial_condition_params") or {}
    multiplier = ic_params.get("omega_multiplier")
    if isinstance(multiplier, int | float):
        from src.solver.equations import EARTH

        expected = multiplier * EARTH["Omega"]
        if abs(params["Omega"] - expected) > 1e-3 * abs(expected):
            messages.append(
                f"initial_condition_params.omega_multiplier = {multiplier} implies "
                f"Omega = {expected:.6e} /s, but physical.Omega = {params['Omega']:.6e} /s. "
                "One of the two is stale and the run would be labelled with a rotation "
                "rate it did not use."
            )
    return messages


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #


def build_run(config: dict):
    """Build the problem and apply the initial condition, honouring topography.

    Topography enters the equations rather than the state, so a case that has one
    forces a rebuild: the initial condition is constructed once on a flat-bottom
    problem to discover the topography, then the problem is rebuilt with it and
    the initial condition is applied again. Wasteful by one construction, and far
    cheaper than a bottom that silently is not there.
    """
    probe = build_problem(config)
    metadata = apply_initial_condition(probe, config)

    advection = metadata.get("kind") == "advection"
    topography = metadata.get("topography")
    if topography is None and not advection:
        return probe, metadata

    swp = build_problem(config, topography=topography, advection=advection)
    metadata = apply_initial_condition(swp, config)
    return swp, metadata


def _add_outputs(swp, solver, config: dict, output_dir: Path):
    """Attach the analysis handlers this campaign needs.

    The three cadences are separate because they answer different questions and
    cost different amounts. Full fields are the expensive one and are written only
    when a config asks: the verification campaign needs them to compute error
    norms, the phase-speed campaign does not.
    """
    outputs = config.get("outputs") or {}
    units = swp.units
    handlers = {}

    def cadence(key):
        value = outputs.get(key)
        return None if value in (None, False) else units.time(float(value))

    snapshot_dt = cadence("snapshot_cadence")
    if snapshot_dt:
        handler = solver.evaluator.add_file_handler(
            str(output_dir / "snapshots"), sim_dt=snapshot_dt, max_writes=50
        )
        handler.add_task(swp.h, name="height")
        handler.add_task(-d3.div(d3.skew(swp.u)), name="vorticity")
        handler.add_task(d3.div(swp.u), name="divergence")
        if outputs.get("write_full_fields"):
            handler.add_task(swp.u, name="velocity")
        handlers["snapshots"] = handler

    slice_dt = cadence("slice_cadence")
    if slice_dt:
        handler = solver.evaluator.add_file_handler(
            str(output_dir / "slices"), sim_dt=slice_dt, max_writes=1000
        )
        # A Hovmoller diagram needs height along one latitude circle at high
        # cadence; that is the phase-speed campaign's primary measurement, and it
        # is two orders of magnitude cheaper than a full snapshot.
        handler.add_task(swp.h(theta=np.pi / 4), name="height_45N")
        handler.add_task(swp.h(theta=np.pi / 2), name="height_equator")
        handlers["slices"] = handler

    spectra_dt = cadence("spectra_cadence")
    if spectra_dt:
        handler = solver.evaluator.add_file_handler(
            str(output_dir / "spectra"), sim_dt=spectra_dt, max_writes=1000
        )
        # Conservation diagnostics: mass, energy and potential enstrophy are the
        # blueprint §9.3 criteria, and potential enstrophy is the early warning.
        H = units.length(swp.params["H"])
        g = swp.params["g"] * units.meter / units.second**2
        Omega = swp.params["Omega"] / units.second
        zeta = -d3.div(d3.skew(swp.u))
        depth = H + swp.h
        handler.add_task(d3.Average(H + swp.h, swp.coords), name="mass")
        handler.add_task(
            d3.Average(depth * (swp.u @ swp.u) / 2 + g * swp.h * swp.h / 2, swp.coords),
            name="energy",
        )
        handler.add_task(
            d3.Average((zeta + 2 * Omega * d3.MulCosine(_ones(swp))) ** 2 / depth, swp.coords),
            name="potential_enstrophy",
        )
        handlers["spectra"] = handler

    return handlers


def _ones(swp):
    """A unit scalar field, so ``MulCosine`` can build the Coriolis parameter.

    ``MulCosine`` multiplies by ``cos(colatitude) = sin(latitude)``, which is what
    turns ``2 Omega`` into ``f``. It needs a field to act on, and the constant one
    is that field.
    """
    field = swp.dist.Field(bases=swp.basis)
    field["g"] = 1.0
    return field


def run(config_path, *, output_root=None, force: bool = False, dry_run: bool = False) -> RunResult:
    """Execute one config end to end and return its provenance record."""
    config = load_config(config_path)
    run_id = config["run_id"]
    output_root = Path(output_root) if output_root else DEFAULT_OUTPUT_ROOT
    output_dir = output_root / run_id
    provenance_path = output_dir / "provenance.json"

    if provenance_path.exists() and not force:
        existing = json.loads(provenance_path.read_text(encoding="utf-8"))
        if existing.get("outcome", {}).get("status") == "completed":
            raise ConfigError(
                f"{provenance_path} already records a completed run of {run_id}. "
                "Run IDs are immutable; use a new run ID, a different --output-root, "
                "or --force if this record is known to be junk."
            )
    output_dir.mkdir(parents=True, exist_ok=True)

    swp, metadata = build_run(config)
    # Every provenance write below is collective: see _write_provenance.
    comm = swp.dist.comm
    warnings_raised = check_physics_consistency(config, metadata)
    for message in warnings_raised:
        print(f"[harness] WARNING: {message}", file=sys.stderr)

    numerics = config.get("numerics") or {}
    record = {
        "run_id": run_id,
        "campaign": config.get("campaign"),
        "description": config.get("description"),
        "started_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "config": {k: v for k, v in config.items() if not k.startswith("_")},
        "config_path": config["_source_path"],
        "config_sha256": config["_source_sha256"],
        "git": git_record(),
        "environment": environment_record(),
        "resolution_shape": list(swp.shape),
        "units": {"meter": swp.units.meter, "hour": swp.units.hour},
        "initial_condition_metadata": _jsonable(metadata),
        "warnings": warnings_raised,
        "outcome": {"status": "started"},
    }
    _write_provenance(provenance_path, record, comm=comm)

    if dry_run:
        record["outcome"] = {"status": "dry_run", "note": "built and validated, not integrated"}
        _write_provenance(provenance_path, record, comm=comm)
        return RunResult(run_id, output_dir, record)

    if metadata.get("kind") == "advection":
        raise ConfigError(
            f"{run_id} uses {metadata.get('initial_condition')}, which the source defines as "
            "an advection-only test rather than a shallow-water one. The advection problem "
            "is not built by src/solver/equations.py; see the Session L5 report."
        )

    solver = swp.build_solver(numerics["timestepper"])
    solver.stop_sim_time = swp.units.time(float(numerics["stop_sim_time"]))
    timestep = swp.units.time(float(numerics["dt"]))
    _add_outputs(swp, solver, config, output_dir)

    wall_start = time.time()
    status, error = "completed", None
    try:
        while solver.proceed:
            solver.step(timestep)
    except Exception as exc:  # noqa: BLE001 - recorded then re-raised
        status, error = "failed", f"{type(exc).__name__}: {exc}"
        raise
    finally:
        record["outcome"] = {
            "status": status,
            "error": error,
            "iterations": int(solver.iteration),
            "final_sim_time_s": float(swp.units.to_si_time(solver.sim_time)),
            "wall_seconds": round(time.time() - wall_start, 3),
            "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        # The output files are written by every rank; hashing one before its
        # last write has landed would record the hash of a truncated file.
        if comm is not None and comm.size > 1:
            comm.Barrier()
        record["outputs"] = _output_manifest(output_dir)
        _write_provenance(provenance_path, record, comm=comm)

    return RunResult(run_id, output_dir, record)


def _output_manifest(output_dir: Path) -> list[dict]:
    """Every data file the run produced, with its size and hash."""
    manifest = []
    for path in sorted(output_dir.rglob("*.h5")):
        manifest.append(
            {
                "path": str(path.relative_to(output_dir)),
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return manifest


def _jsonable(value):
    """Strip the non-serialisable parts of an initial condition's metadata."""
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items() if k != "topography"}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, np.floating | np.integer):
        return value.item()
    if isinstance(value, np.ndarray):
        return None
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


# --------------------------------------------------------------------------- #
# registry
# --------------------------------------------------------------------------- #


def update_registry(run_id: str, status: str, registry_path: Path | None = None) -> bool:
    """Advance one run's Status cell in ``configs/RUN_REGISTRY.md``.

    The registry is the human-readable index of what has been done. Updating it
    by hand after each run is exactly the kind of bookkeeping that drifts, so the
    harness does it — but only for the row whose first cell is this run ID, and
    only by replacing the last cell of that row, so a hand-written note anywhere
    else in the table survives.
    """
    registry_path = registry_path or REGISTRY_PATH
    lines = registry_path.read_text(encoding="utf-8").splitlines()
    changed = False
    for i, line in enumerate(lines):
        if not line.startswith("| "):
            continue
        cells = line.split("|")
        if len(cells) < 3 or cells[1].strip() != run_id:
            continue
        cells[-2] = f" {status} "
        lines[i] = "|".join(cells)
        changed = True
    if changed:
        registry_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", help="path to a run configuration under configs/")
    parser.add_argument("--output-root", default=None, help="where run directories are created")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="build the problem and the initial condition, write provenance, do not integrate",
    )
    parser.add_argument(
        "--force", action="store_true", help="overwrite an existing completed run record"
    )
    parser.add_argument(
        "--update-registry",
        action="store_true",
        help="advance this run's Status cell in configs/RUN_REGISTRY.md on success",
    )
    args = parser.parse_args(argv)

    result = run(args.config, output_root=args.output_root, force=args.force, dry_run=args.dry_run)
    outcome = result.provenance["outcome"]
    print(f"[harness] {result.run_id}: {outcome['status']} -> {result.output_dir}")
    if outcome["status"] == "completed":
        print(
            f"[harness] {outcome['iterations']} iterations, "
            f"{outcome['final_sim_time_s'] / 86400:.3f} simulated days, "
            f"{outcome['wall_seconds']:.1f} s wall"
        )
        if args.update_registry:
            date = datetime.now(UTC).date().isoformat()
            update_registry(result.run_id, f"complete {date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# Referenced so the resolution ladder is importable from the harness for tests
# that assert the config's resolution key is one the equations module knows.
__all__ = [
    "RESOLUTIONS",
    "ConfigError",
    "RunResult",
    "load_config",
    "main",
    "run",
    "update_registry",
]
