"""Longitude-time (Hovmöller) diagrams from a finished run.

Physics first. A Hovmöller diagram is the instrument that makes a phase speed
visible. Plot longitude across and time down, and a propagating wave draws a
straight line whose slope *is* its speed: leaning towards decreasing longitude for
a westward wave, towards increasing longitude for an eastward one. A standing
oscillation draws vertical stripes. A wave that disperses draws a fan. None of
that is recoverable from snapshots at a few times, and none of it needs the whole
sphere — one latitude circle, sampled often, carries it all.

That is why the run harness writes slices at a far higher cadence than snapshots:
a phase line needs temporal resolution, a structure needs spatial resolution, and
they are cheap in opposite directions.

**Two ways to get a circle, and they are not equivalent.** A run stores a small
number of *slice tasks* at fixed latitudes, written every hour. It also stores
whole-sphere *snapshots*, written daily. For any latitude the harness thought to
record, the slice is the right source — hourly sampling is what keeps a fast mode
clear of the aliasing that would otherwise wreck the fit
(:mod:`src.analysis.fit_phase_speed` explains why aliasing cannot be detected
after the fact). For any other latitude the only option is to interpolate the
snapshots, and the cost is a hundredfold coarser sampling in time. This module
does both and says which it did, because a phase speed fitted from daily samples
deserves more suspicion than one fitted from hourly samples.

**A note on interpolation.** Snapshot latitudes are Gauss-Legendre nodes, which
cluster towards the poles and leave the tropics comparatively sparse. Linear
interpolation between them is adequate for a smooth field — checked at 0.02% for
the steady case-2 run — but it is interpolation, and this module marks the result
as such rather than presenting it as data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.diagnostics import slices


@dataclass
class HovmollerDiagram:
    """A longitude-time field on one latitude circle, with its provenance."""

    values: np.ndarray  # (n_time, n_longitude)
    time_s: np.ndarray
    lon_rad: np.ndarray
    latitude_rad: float
    field: str
    source: str  # "slice" or "interpolated snapshots"
    run_id: str

    @property
    def latitude_deg(self) -> float:
        return float(np.degrees(self.latitude_rad))

    @property
    def cadence_s(self) -> float:
        return float(np.median(np.diff(self.time_s))) if self.time_s.size > 1 else float("nan")

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "field": self.field,
            "source": self.source,
            "latitude_deg": self.latitude_deg,
            "n_time": int(self.time_s.size),
            "n_longitude": int(self.lon_rad.size),
            "cadence_s": self.cadence_s,
            "span_days": float((self.time_s[-1] - self.time_s[0]) / 86400),
        }


def available_slice_latitudes(run) -> dict[str, float]:
    """Latitudes (radians) at which this run stored a high-cadence circle.

    ``slices.slice_latitude_rad`` already returns a *latitude*; converting again
    would be a colatitude flip too many. Worth stating because 45 degrees is the
    fixed point of that flip, so the error is invisible on the one slice this
    project looks at most and appears only at the equator.
    """
    return {task: slices.slice_latitude_rad(task) for task in slices.available_tasks(run, "slices")}


def extract_hovmoller(
    run,
    latitude_deg: float = 45.0,
    field: str = "height",
    prefer_slices: bool = True,
    tolerance_deg: float = 1.0,
) -> HovmollerDiagram:
    """Build a Hovmöller diagram for one latitude from a completed run.

    Uses a stored slice task when one exists within ``tolerance_deg`` of the
    requested latitude, because those are sampled roughly a hundred times more
    often; otherwise interpolates the snapshot maps. The source is recorded in the
    result either way.
    """
    run_id = slices.load_provenance(run).run_id

    if prefer_slices:
        candidates = available_slice_latitudes(run)
        target = np.radians(latitude_deg)
        for task, lat in sorted(candidates.items(), key=lambda kv: abs(kv[1] - target)):
            if abs(np.degrees(lat - target)) <= tolerance_deg and field in task:
                diagram = slices.hovmoller(run, task=task)
                return HovmollerDiagram(
                    values=np.asarray(diagram.values),
                    time_s=np.asarray(diagram.time_s),
                    lon_rad=np.asarray(diagram.lon_rad),
                    latitude_rad=float(lat),
                    field=field,
                    source=f"slice task {task!r}",
                    run_id=run_id,
                )

    handler = slices.read_handler(run, "snapshots", tasks=[field])
    values = np.asarray(handler.tasks[field])
    colatitude = np.asarray(handler.colatitude_rad)
    target_colat = np.pi / 2 - np.radians(latitude_deg)
    # Colatitude descends as latitude ascends; np.interp needs ascending nodes.
    order = np.argsort(colatitude)
    circle = np.empty((values.shape[0], values.shape[1]))
    for t in range(values.shape[0]):
        for j in range(values.shape[1]):
            circle[t, j] = np.interp(target_colat, colatitude[order], values[t, j][order])

    return HovmollerDiagram(
        values=circle,
        time_s=np.asarray(handler.time_s),
        lon_rad=np.asarray(handler.lon_rad),
        latitude_rad=float(np.radians(latitude_deg)),
        field=field,
        source="interpolated snapshots",
        run_id=run_id,
    )
