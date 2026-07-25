"""Windows onto a finished run: latitude-circle slices and whole-sphere snapshot maps.

Physics first. A completed simulation is not a pile of arrays. It is a set of
windows cut onto a moving fluid, and the two cuts this project takes answer
different physical questions.

*A slice is a latitude circle watched through time.* Stand on the 45 degree
parallel and record the free surface going past. A crest that arrives at
successively smaller longitudes is a wave travelling **west**, and the slope of
its phase line in the longitude-time plane *is* the phase speed — the single
number the phase-speed campaign exists to measure, and the quantity the
Rossby-Haurwitz relation ``c_ang = -2 Omega / [n(n+1)]`` predicts. That plot is
the Hovmoller diagram, and it is built from exactly the array :func:`hovmoller`
returns. The equatorial circle is the control: the restoring mechanism is the
meridional gradient of planetary vorticity, so a circle where the jet is absent
and ``f`` vanishes is meant to look different.

*A snapshot map is the whole sphere at one instant.* Speed is invisible in it,
but structure is not: the zonal wavenumber of a pattern, the meridional tilt of a
trough that says momentum is being fluxed, the roll-up of a sheared jet into
discrete vortices. A run writes both cuts because neither contains what the other
shows, and it writes the slice far more often than the map because a phase line
needs temporal resolution while a structure needs spatial resolution.

This module is the project's single place that knows how those windows are laid
out on disk. Everything downstream — conservation series, spectra, Hovmoller
figures, error norms — reads a run through here, so the layout is understood once
rather than rediscovered by every consumer.

**What the layout is, and the three places it will trip a reader.**

1. *Time is written in the solver's working units, where one unit is one hour.*
   ``scales/sim_time`` is therefore not seconds. Every array this module returns
   carries time in **seconds**, converted using the run's own ``units`` block from
   ``provenance.json`` rather than a hardcoded factor, so a run scaled differently
   would still come back correct.

2. *The coordinate arrays are stored under content-hashed names* —
   ``scales/phi_hash_<hex>`` and ``scales/theta_hash_<hex>``. The digest changes
   with the grid, so the datasets are found by prefix and never by literal name.
   ``phi`` is longitude in radians on ``[0, 2 pi)``; ``theta`` is **colatitude**
   measured from the north pole, so latitude is ``pi/2 - theta`` and
   ``cos(theta) = sin(latitude)`` is the Gauss-Legendre quadrature variable. The
   grids differ between handlers — snapshot tasks are written on the
   coefficient-matched grid, slice tasks on the dealiased one — so the grid is
   always taken from the file being read.

3. *For the 1-D slice tasks the stored colatitude array does not give the slice
   latitude.* Interpolating a field to one latitude leaves a degenerate colatitude
   axis, and what Dedalus writes for it is that degenerate basis rendered at the
   dealiasing factor: two Gauss-Legendre nodes at ``mu = +/- 1/sqrt(3)``, i.e.
   +/- 35.26 degrees, identical in every run regardless of resolution and
   unrelated to where the slice was actually cut. That knowledge lives in the
   *task name* and in the handler definition in ``src/solver/harness.py``, so it is
   tabulated here in :data:`SLICE_COLATITUDE_RAD` and :func:`hovmoller` reports it
   from there. The claim was checked against the data rather than assumed: for the
   steady Williamson case 2 run V-02 the ``height_45N`` series matches the
   snapshot height interpolated to 45 degrees north to 0.02 per cent, which is the
   error of interpolating a 32-point Gaussian grid linearly.

A handler may also be split across several files, ``<handler>_s1.h5``,
``<handler>_s2.h5``, and so on. They are concatenated in the order of the
``set_number`` attribute Dedalus writes into each file, not in filename order,
because filename order puts ``_s10`` before ``_s2``.

Units. The solver works in scaled units where the planetary radius is 1 and the
hour is 1, so the raw numbers on disk are not SI. The conversions follow the same
convention as :class:`src.solver.equations.Units` — ``meter`` and ``hour`` are the
values of one SI metre and one SI hour *in working units*, so an SI quantity
converts by multiplying — and they are restated here rather than imported so that
reading a finished run needs only ``h5py`` and ``numpy``, never Dedalus.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS_ROOT = REPO_ROOT / "runs"

#: The three file handlers ``src/solver/harness.py`` attaches to every run.
HANDLERS = ("snapshots", "slices", "spectra")

_PHI_PREFIX = "phi_hash_"
_THETA_PREFIX = "theta_hash_"
_SECONDS_PER_HOUR = 3600.0

#: Where each 1-D slice task was cut, in colatitude. This cannot be read off the
#: file (see the module docstring, point 3); it is the interpolation point the
#: harness passes to ``h(theta=...)``, and the two must be changed together.
SLICE_COLATITUDE_RAD: dict[str, float] = {
    "height_45N": np.pi / 4,
    "height_equator": np.pi / 2,
}

#: Physical dimension of every task a run writes, as ``(length, time)`` exponents.
#: This is what makes a working-unit array convertible to SI. ``mass`` is the
#: area-averaged column depth ``H + h``, a length; ``energy`` is the area-averaged
#: depth-integrated energy per unit density, ``L^3 T^-2``; ``potential_enstrophy``
#: is the area average of ``(zeta + f)^2 / depth``, ``L^-1 T^-2``.
TASK_DIMENSIONS: dict[str, tuple[int, int]] = {
    "height": (1, 0),
    "vorticity": (0, -1),
    "divergence": (0, -1),
    "velocity": (1, -1),
    "height_45N": (1, 0),
    "height_equator": (1, 0),
    "mass": (1, 0),
    "energy": (3, -2),
    "potential_enstrophy": (-1, -2),
}


# --------------------------------------------------------------------------- #
# units and provenance
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class RunUnits:
    """The scaling between a run's working units and SI.

    ``meter`` and ``hour`` are the values of one SI metre and one SI hour
    expressed in working units, so an SI quantity converts *into* working units by
    multiplying and a stored quantity converts *out* by dividing. The solver sets
    ``meter = 1/R`` and ``hour = 1`` — lengths measured in planetary radii, times
    in hours — because raw SI would put ``R ~ 6e6`` and ``Omega ~ 7e-5`` into the
    same matrices and condition them badly.
    """

    meter: float
    hour: float = 1.0

    @property
    def second(self) -> float:
        return self.hour / _SECONDS_PER_HOUR

    def to_si(self, value, *, length: int = 0, time: int = 0) -> np.ndarray:
        """Convert a stored array of dimension ``L^length T^time`` into SI."""
        if length and not np.isfinite(self.meter):
            raise ValueError(
                "this run's length scaling is unknown, so a length cannot be "
                "converted to SI; provenance.json is missing or has no units block"
            )
        return np.asarray(value, dtype=float) / (self.meter**length * self.second**time)

    def seconds(self, sim_time) -> np.ndarray:
        """Working-unit simulation time -> seconds."""
        return self.to_si(sim_time, time=1)


#: Used when a run directory carries no provenance record. The hour is still 1 by
#: construction of the solver, so time converts; a length does not, and
#: :meth:`RunUnits.to_si` says so rather than returning a silent NaN.
UNKNOWN_UNITS = RunUnits(meter=float("nan"), hour=1.0)


@dataclass(frozen=True)
class Provenance:
    """One run's tracked record: what was asked for, and how it was scaled.

    The bulk HDF5 beside it is reproducible and gitignored; this record is what
    makes it reproducible, which is why every reader starts here.
    """

    run_id: str
    path: Path
    record: dict
    units: RunUnits

    @property
    def config(self) -> dict:
        return dict(self.record.get("config") or {})

    @property
    def physical(self) -> dict:
        """``R``, ``Omega``, ``g``, ``H`` in SI, as the config declared them."""
        return dict(self.config.get("physical") or {})

    @property
    def resolution_shape(self) -> tuple[int, ...]:
        """``(Nphi, Ntheta)``, the spherical-harmonic truncation the run used."""
        return tuple(int(x) for x in (self.record.get("resolution_shape") or []))

    @property
    def initial_condition_metadata(self) -> dict:
        return dict(self.record.get("initial_condition_metadata") or {})

    @property
    def outcome(self) -> dict:
        return dict(self.record.get("outcome") or {})

    @property
    def completed(self) -> bool:
        return self.outcome.get("status") == "completed"


def run_directory(run, runs_root: Path | None = None) -> Path:
    """Resolve a run ID (``"V-02"``) or an explicit path to a run directory."""
    candidate = Path(run)
    if candidate.is_dir() and (candidate / "provenance.json").exists():
        return candidate
    root = Path(runs_root) if runs_root is not None else DEFAULT_RUNS_ROOT
    directory = root / str(run)
    if directory.is_dir():
        return directory
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError(f"no run directory for {run!r} (looked in {root})")


def load_provenance(run, runs_root: Path | None = None) -> Provenance:
    """Read a run's ``provenance.json`` and expose its unit conversions.

    A run with no record is still readable — the time axis needs only the hour,
    which the solver fixes at 1 — but nothing on it can be converted to a physical
    length until the record says what one metre was worth.
    """
    directory = run_directory(run, runs_root)
    path = directory / "provenance.json"
    if not path.exists():
        return Provenance(run_id=directory.name, path=path, record={}, units=UNKNOWN_UNITS)
    record = json.loads(path.read_text(encoding="utf-8"))
    block = record.get("units") or {}
    units = RunUnits(
        meter=float(block.get("meter", float("nan"))),
        hour=float(block.get("hour", 1.0)),
    )
    return Provenance(
        run_id=str(record.get("run_id", directory.name)),
        path=path,
        record=record,
        units=units,
    )


# --------------------------------------------------------------------------- #
# the files a handler wrote
# --------------------------------------------------------------------------- #


def _set_number(path: Path) -> int:
    """The write-set index Dedalus stamped into a file, for ordering in time."""
    with h5py.File(path, "r") as handle:
        value = handle.attrs.get("set_number")
    if value is None:
        match = re.search(r"_s(\d+)\.h5$", path.name)
        if match is None:
            raise ValueError(f"{path} carries no set_number and its name encodes none")
        return int(match.group(1))
    return int(value)


def handler_files(run, handler: str, runs_root: Path | None = None) -> list[Path]:
    """Every HDF5 file one handler wrote, ordered in time.

    Ordered by the ``set_number`` attribute rather than by filename, because a run
    long enough to reach a tenth write set would otherwise have ``_s10`` sorted
    before ``_s2`` and its time axis silently scrambled.
    """
    directory = run_directory(run, runs_root) / handler
    if not directory.is_dir():
        raise FileNotFoundError(f"{directory} does not exist; this run has no {handler!r} handler")
    files = sorted(directory.glob(f"{handler}_s*.h5"))
    if not files:
        raise FileNotFoundError(f"no {handler}_s*.h5 files under {directory}")
    return [path for _, path in sorted((_set_number(path), path) for path in files)]


def _grid_by_prefix(handle: h5py.File, prefix: str) -> np.ndarray:
    """The one coordinate array whose hashed dataset name starts with ``prefix``."""
    scales = handle["scales"]
    names = sorted(name for name in scales if name.startswith(prefix))
    if len(names) != 1:
        raise ValueError(
            f"expected exactly one scales/{prefix}* dataset in {handle.filename}, "
            f"found {len(names)}: {names}. The tasks in this handler do not share "
            "one grid, so each task's grid must be taken from its own dimension "
            "scale instead."
        )
    return np.asarray(scales[names[0]], dtype=float)


def available_tasks(run, handler: str, runs_root: Path | None = None) -> list[str]:
    """The task names one handler holds, without reading any bulk data."""
    first = handler_files(run, handler, runs_root)[0]
    with h5py.File(first, "r") as handle:
        return sorted(handle["tasks"].keys())


# --------------------------------------------------------------------------- #
# reading a handler
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class HandlerOutput:
    """Everything one handler wrote, concatenated across its files.

    ``time_s`` is in seconds. ``tasks`` maps a task name to an array whose leading
    axis is time. ``lon_rad`` and ``colatitude_rad`` are the grid *as stored in
    this handler's files*, which is not the same grid in every handler.

    ``grid_matches_tasks`` is the honest flag on that last point. It is ``False``
    for the ``slices`` handler, whose stored colatitude array is the degenerate
    interpolated axis rendered at the dealiasing factor rather than the latitude
    the slice was cut at — use :data:`SLICE_COLATITUDE_RAD`, or :func:`hovmoller`,
    for that.
    """

    run_id: str
    handler: str
    time_s: np.ndarray
    tasks: dict[str, np.ndarray]
    lon_rad: np.ndarray
    colatitude_rad: np.ndarray
    iteration: np.ndarray
    files: tuple[Path, ...]
    units: RunUnits
    si: bool
    grid_matches_tasks: bool = field(default=True)

    @property
    def lat_rad(self) -> np.ndarray:
        """Latitude from the equator, ``pi/2 - theta``."""
        return np.pi / 2 - self.colatitude_rad

    @property
    def lat_deg(self) -> np.ndarray:
        return np.degrees(self.lat_rad)

    @property
    def lon_deg(self) -> np.ndarray:
        return np.degrees(self.lon_rad)

    @property
    def time_days(self) -> np.ndarray:
        return self.time_s / 86400.0

    @property
    def n_times(self) -> int:
        return int(self.time_s.size)


def _task_to_si(name: str, values: np.ndarray, units: RunUnits) -> np.ndarray:
    """Convert one task from working units to SI, refusing to guess."""
    if name not in TASK_DIMENSIONS:
        raise ValueError(
            f"task {name!r} has no entry in TASK_DIMENSIONS, so its physical "
            "dimension is unknown and it cannot be converted to SI. Add it there "
            "(the task is defined in src/solver/harness.py) or pass to_si=False."
        )
    length, time = TASK_DIMENSIONS[name]
    return units.to_si(values, length=length, time=time)


def read_handler(
    run,
    handler: str,
    *,
    tasks: list[str] | None = None,
    to_si: bool = True,
    runs_root: Path | None = None,
) -> HandlerOutput:
    """Read one handler of one run: its time axis in seconds, its tasks, its grid.

    This is the function every other diagnostic in the project is built on. It
    concatenates the handler's files in write order, checks that they agree about
    the grid and that the resulting time axis is strictly increasing, and converts
    time — and, by default, the tasks themselves — out of the solver's scaled
    working units into SI.

    ``to_si=False`` returns the numbers exactly as stored, which is what a test
    comparing against a raw file wants, and what a relative quantity such as a
    conservation drift does not care about either way.
    """
    if handler not in HANDLERS:
        raise ValueError(f"unknown handler {handler!r}; this project writes {list(HANDLERS)}")

    paths = handler_files(run, handler, runs_root)
    provenance = load_provenance(run, runs_root)

    times: list[np.ndarray] = []
    iterations: list[np.ndarray] = []
    collected: dict[str, list[np.ndarray]] = {}
    lon = colat = None

    for path in paths:
        with h5py.File(path, "r") as handle:
            file_lon = _grid_by_prefix(handle, _PHI_PREFIX)
            file_colat = _grid_by_prefix(handle, _THETA_PREFIX)
            if lon is None:
                lon, colat = file_lon, file_colat
            elif not (
                lon.shape == file_lon.shape
                and colat.shape == file_colat.shape
                and np.allclose(lon, file_lon)
                and np.allclose(colat, file_colat)
            ):
                raise ValueError(
                    f"{path} was written on a different grid from {paths[0]}; the "
                    "files of one handler cannot be concatenated"
                )

            times.append(np.asarray(handle["scales/sim_time"], dtype=float))
            iterations.append(np.asarray(handle["scales/iteration"]))
            names = sorted(handle["tasks"].keys()) if tasks is None else list(tasks)
            for name in names:
                if name not in handle["tasks"]:
                    raise KeyError(
                        f"{path} has no task {name!r}; it holds {sorted(handle['tasks'])}"
                    )
                collected.setdefault(name, []).append(np.asarray(handle["tasks"][name]))

    time_work = np.concatenate(times)
    order = np.argsort(time_work, kind="stable")
    time_s = provenance.units.seconds(time_work[order])
    if time_s.size > 1 and not np.all(np.diff(time_s) > 0):
        raise ValueError(
            f"the {handler!r} time axis of {provenance.run_id} is not strictly "
            "increasing after ordering by write set; its files overlap in time"
        )

    merged: dict[str, np.ndarray] = {}
    for name, chunks in collected.items():
        values = np.concatenate(chunks, axis=0)[order]
        merged[name] = _task_to_si(name, values, provenance.units) if to_si else values

    reference = next(iter(merged.values()), None)
    matches = reference is None or reference.shape[-1] == colat.size

    return HandlerOutput(
        run_id=provenance.run_id,
        handler=handler,
        time_s=time_s,
        tasks=merged,
        lon_rad=lon,
        colatitude_rad=colat,
        iteration=np.concatenate(iterations)[order],
        files=tuple(paths),
        units=provenance.units,
        si=to_si,
        grid_matches_tasks=bool(matches),
    )


# --------------------------------------------------------------------------- #
# the two windows
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Hovmoller:
    """A latitude circle through time: longitude on one axis, time on the other.

    ``values`` has shape ``(n_times, n_longitudes)``. A westward-propagating wave
    draws phase lines of negative slope in this plane, and the angular phase speed
    is that slope; the linear speed along the circle is ``c = c_ang R cos(lat)``.
    """

    run_id: str
    task: str
    time_s: np.ndarray
    lon_rad: np.ndarray
    values: np.ndarray
    latitude_rad: float
    si: bool

    @property
    def latitude_deg(self) -> float:
        return float(np.degrees(self.latitude_rad))

    @property
    def lon_deg(self) -> np.ndarray:
        return np.degrees(self.lon_rad)

    @property
    def time_days(self) -> np.ndarray:
        return self.time_s / 86400.0


def slice_latitude_rad(task: str) -> float:
    """The latitude a named slice task was cut at, in radians.

    Read from :data:`SLICE_COLATITUDE_RAD`, never from the file: an interpolated
    field leaves a degenerate colatitude axis whose stored coordinate array
    describes that basis, not the interpolation point.
    """
    if task not in SLICE_COLATITUDE_RAD:
        raise KeyError(
            f"the latitude of slice task {task!r} is not recorded. It cannot be "
            "recovered from the file; add it to SLICE_COLATITUDE_RAD to match the "
            "handler definition in src/solver/harness.py."
        )
    return float(np.pi / 2 - SLICE_COLATITUDE_RAD[task])


def hovmoller(
    run,
    task: str = "height_45N",
    *,
    handler: str = "slices",
    to_si: bool = True,
    runs_root: Path | None = None,
) -> Hovmoller:
    """The longitude-time array for one latitude circle — the Hovmoller diagram.

    This is the primary measurement of the phase-speed campaign. The circle is
    sampled at the slice cadence, which is one to two orders of magnitude finer
    than the snapshot cadence, because resolving the *slope* of a phase line needs
    time resolution rather than space resolution.
    """
    output = read_handler(run, handler, tasks=[task], to_si=to_si, runs_root=runs_root)
    values = output.tasks[task]
    if values.ndim != 3 or values.shape[-1] != 1:
        raise ValueError(
            f"task {task!r} has shape {values.shape}, which is not a 1-D slice "
            "(time, longitude, 1); a Hovmoller diagram needs one latitude circle"
        )
    return Hovmoller(
        run_id=output.run_id,
        task=task,
        time_s=output.time_s,
        lon_rad=output.lon_rad,
        values=values[:, :, 0],
        latitude_rad=slice_latitude_rad(task),
        si=to_si,
    )


@dataclass(frozen=True)
class SnapshotMap:
    """One field over the whole sphere at one instant.

    ``values`` has shape ``(n_longitudes, n_colatitudes)`` — longitude first, as
    stored. ``time_s`` is the output time actually used, the one nearest the
    request; ``requested_time_s`` is what was asked for, so the gap between them is
    visible rather than assumed to be zero.
    """

    run_id: str
    field: str
    values: np.ndarray
    lon_rad: np.ndarray
    colatitude_rad: np.ndarray
    time_s: float
    requested_time_s: float
    index: int
    si: bool

    @property
    def lat_rad(self) -> np.ndarray:
        return np.pi / 2 - self.colatitude_rad

    @property
    def lat_deg(self) -> np.ndarray:
        return np.degrees(self.lat_rad)

    @property
    def lon_deg(self) -> np.ndarray:
        return np.degrees(self.lon_rad)

    @property
    def time_days(self) -> float:
        return self.time_s / 86400.0


def snapshot_map(
    run,
    field_name: str = "vorticity",
    *,
    time_s: float | None = None,
    index: int | None = None,
    component: int | str | None = None,
    handler: str = "snapshots",
    to_si: bool = True,
    runs_root: Path | None = None,
) -> SnapshotMap:
    """One 2-D map of a named field at (or nearest to) a requested time.

    Snapshots are written at a coarse cadence, so the nearest available output is
    returned and both times are reported. Asking for a time outside the run is not
    an error — it clamps to the first or last write — because the honest answer is
    "the run ended here", and the returned ``time_s`` states it.

    ``component`` selects one component of a vector task such as ``velocity``.
    Component 0 is eastward and component 1 is *colatitudinal*, which points
    south; ``component="north"`` returns the physically northward component, with
    the sign flip applied here so it is not rediscovered downstream. Getting that
    sign wrong flips every Coriolis interaction in an interpretation.
    """
    output = read_handler(run, handler, tasks=[field_name], to_si=to_si, runs_root=runs_root)
    values = output.tasks[field_name]

    if index is None:
        if time_s is None:
            raise ValueError("give either time_s (seconds) or index")
        index = int(np.argmin(np.abs(output.time_s - float(time_s))))
    index = int(index)
    requested = float(time_s) if time_s is not None else float(output.time_s[index])

    frame = values[index]
    if frame.ndim == 3:
        if component is None:
            raise ValueError(
                f"{field_name!r} is a vector field with shape {frame.shape}; pass "
                "component=0 (eastward), 1 (colatitudinal, southward) or 'north'"
            )
        if component in ("east", "eastward"):
            frame = frame[0]
        elif component in ("north", "northward"):
            frame = -frame[1]
        elif component in ("south", "colatitudinal"):
            frame = frame[1]
        else:
            frame = frame[int(component)]
    elif frame.ndim != 2:
        raise ValueError(f"{field_name!r} frame has shape {frame.shape}, which is not a map")

    return SnapshotMap(
        run_id=output.run_id,
        field=field_name,
        values=frame,
        lon_rad=output.lon_rad,
        colatitude_rad=output.colatitude_rad,
        time_s=float(output.time_s[index]),
        requested_time_s=requested,
        index=index,
        si=to_si,
    )


def describe_run(run, runs_root: Path | None = None) -> dict:
    """An inventory of what one run holds, for orientation and debugging.

    Reports, per handler, the files, the task shapes, the number of output times
    and the span covered — the questions anyone asks first on opening a run
    directory they did not create.
    """
    provenance = load_provenance(run, runs_root)
    summary: dict = {
        "run_id": provenance.run_id,
        "resolution_shape": list(provenance.resolution_shape),
        "completed": provenance.completed,
        "handlers": {},
    }
    for handler in HANDLERS:
        try:
            paths = handler_files(run, handler, runs_root)
        except FileNotFoundError:
            continue
        with h5py.File(paths[0], "r") as first:
            shapes = {name: list(first["tasks"][name].shape[1:]) for name in first["tasks"]}
        output = read_handler(run, handler, tasks=[], to_si=False, runs_root=runs_root)
        summary["handlers"][handler] = {
            "files": [path.name for path in paths],
            "task_shape_per_write": shapes,
            "n_times": output.n_times,
            "time_span_days": [
                float(output.time_s[0] / 86400.0),
                float(output.time_s[-1] / 86400.0),
            ],
            "n_longitudes": int(output.lon_rad.size),
            "n_colatitudes": int(output.colatitude_rad.size),
        }
    return summary
