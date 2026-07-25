"""The rotating shallow-water equations on a sphere, in vector-invariant form.

Physics first. This module encodes one statement: **material conservation of
potential vorticity**, ``Dq/Dt = 0`` with ``q = (zeta + f)/h``, as derived in
``theory/derivations.tex`` §3. That conservation law is not integrated directly,
because it cannot be — it is a *consequence* of the two equations that are
integrated, and §3 proves the equivalence exactly via the identity
``h Dq/Dt = curl(M) - qC``, verified symbolically in
``theory/sympy_checks/check_pv_conservation.py``.

What is integrated is the pair from §3 — the vector-invariant momentum equation
and the free-surface continuity equation — arranged as Dedalus wants them, with
the fast linear terms on the left for implicit treatment and the slow nonlinear
terms on the right for explicit treatment:

    dt(u) + nu*L^p(u) + g*grad(h) + 2*Omega*zcross(u) = -u@grad(u)
    dt(h) + nu*L^p(h) + H*div(u)                      = -div(depth*u)

The Coriolis term uses the ``zcross = MulCosine(skew(.))`` idiom confirmed in
``docs/DEDALUS_API.md`` §5: ``skew`` supplies the 90-degree rotation ``k x`` and
``MulCosine`` supplies the ``cos(colatitude)`` weight that turns a constant
rotation rate into the latitude-dependent Coriolis parameter. **That latitudinal
weight is the beta effect** — the single mechanism this whole project studies —
and it enters the code in exactly one place, here.

**Hyperdiffusion is not physics.** ``nu*L^p`` is a numerical regulariser that
drains enstrophy at the grid scale; it has no counterpart in the derivation. Its
order and coefficient are configuration, never hardcoded, and blueprint run P-18
exists to measure how much any answer depends on them. Thuburn & Li (2000) — see
``docs/literature/ANCHOR_NOTES.md`` — found that for a shallow-water
Rossby-Haurwitz wave the appropriate coefficient depends on the flow itself, so
this is a live sensitivity rather than a formality.

**Resolution is a basis parameter, not a code branch.** The equations assembled
here are identical whether the run is an L0 smoke test or an L3 production run;
only ``shape`` changes.

Units. Lengths are scaled by the planetary radius (so ``R = 1``) and times by the
hour, matching the arrangement proven in the Phase-0 gate reference. Working in
raw SI would put ``R ~ 6e6`` and ``Omega ~ 7e-5`` into the same matrices and
condition them badly. The scaling is derived from the config's own ``physical``
block rather than hardcoded, and :class:`Units` carries the conversions so no
caller has to rediscover them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import dedalus.public as d3
import numpy as np

# Resolution ladder from the blueprint. (Nphi, Ntheta) is the spherical-harmonic
# truncation, with Nphi = 2*Ntheta so zonal and meridional resolution match.
RESOLUTIONS: dict[str, tuple[int, int]] = {
    "L0": (64, 32),
    "L1": (256, 128),
    "L2": (512, 256),
    "L3": (1024, 512),
}

# Earth values, used when a config omits the physical block. Identical to the
# Phase-0 reference so comparisons against it are meaningful.
EARTH = {"R": 6.37122e6, "Omega": 7.292e-5, "g": 9.80616, "H": 1.0e4}

TIMESTEPPERS = {
    "RK111": d3.RK111,
    "RK222": d3.RK222,
    "RK443": d3.RK443,
    "SBDF1": d3.SBDF1,
    "SBDF2": d3.SBDF2,
    "SBDF3": d3.SBDF3,
    "SBDF4": d3.SBDF4,
    "CNAB1": d3.CNAB1,
    "CNAB2": d3.CNAB2,
}


@dataclass(frozen=True)
class Units:
    """Conversion between SI and the solver's scaled working units.

    ``meter`` and ``second`` are the values of one SI metre and one SI second
    expressed in working units, so an SI quantity converts by multiplying:
    ``u_work = u_si * meter / second``.
    """

    meter: float
    hour: float = 1.0

    @property
    def second(self) -> float:
        return self.hour / 3600.0

    @classmethod
    def from_radius(cls, radius_si: float) -> Units:
        """Scale lengths so the planetary radius is exactly 1."""
        return cls(meter=1.0 / radius_si)

    def length(self, si: float) -> float:
        return si * self.meter

    def velocity(self, si: float) -> float:
        return si * self.meter / self.second

    def time(self, si_seconds: float) -> float:
        return si_seconds * self.second

    def to_si_time(self, work: float) -> float:
        return work / self.second

    def rate(self, si_per_second: float) -> float:
        """A frequency or growth rate: s^-1 -> working units."""
        return si_per_second / self.second

    def to_si_rate(self, work: float) -> float:
        return work * self.second


@dataclass
class ShallowWaterProblem:
    """Everything a caller needs to run or inspect a built problem."""

    coords: Any
    dist: Any
    basis: Any
    u: Any
    h: Any
    problem: Any
    units: Units
    params: dict[str, float]
    shape: tuple[int, int]
    topography: Any | None = None

    def build_solver(self, timestepper: str = "RK222"):
        """Build the initial-value solver with the named timestepper."""
        if timestepper not in TIMESTEPPERS:
            raise ValueError(
                f"unknown timestepper {timestepper!r}; available: {sorted(TIMESTEPPERS)}"
            )
        return self.problem.build_solver(TIMESTEPPERS[timestepper])


def physical_params(config: dict) -> dict[str, float]:
    """Read R, Omega, g, H from a config, falling back to Earth values."""
    block = dict(config.get("physical") or {})
    return {k: float(block.get(k, EARTH[k])) for k in EARTH}


def resolution_shape(config: dict) -> tuple[int, int]:
    key = config.get("resolution", "L0")
    if key not in RESOLUTIONS:
        raise ValueError(f"unknown resolution {key!r}; available: {sorted(RESOLUTIONS)}")
    return RESOLUTIONS[key]


def build_domain(config: dict, dtype=np.float64):
    """Coordinates, distributor and sphere basis for this config's resolution.

    Separate from :func:`build_problem` because the initial-condition modules and
    the eigenvalue solvers need a domain without an IVP attached to it.
    """
    params = physical_params(config)
    units = Units.from_radius(params["R"])
    shape = resolution_shape(config)
    dealias = float((config.get("numerics") or {}).get("dealias", 1.5))

    coords = d3.S2Coordinates("phi", "theta")
    dist = d3.Distributor(coords, dtype=dtype)
    basis = d3.SphereBasis(
        coords,
        shape,
        dtype=dtype,
        radius=units.length(params["R"]),
        dealias=dealias,
    )
    return coords, dist, basis, units, params, shape


def build_problem(
    config: dict, *, topography=None, advection: bool = False, dtype=np.float64
) -> ShallowWaterProblem:
    """Assemble the shallow-water IVP for one validated config.

    Parameters
    ----------
    config
        A configuration dict already validated against ``configs/_schema.yaml``.
    topography
        Optional bottom topography ``h_b`` in working units, given as a grid
        array (or an existing field on this basis). Required by Williamson case 5
        (flow over an isolated mountain) and by the Läuter case, whose source does
        not absorb the centrifugal potential into gravity; unused by every other
        case. When present the fluid column depth becomes ``H + h - h_b``, so the
        topography enters the mass flux while ``h`` remains the free-surface
        elevation that drives the pressure gradient. A grid array is accepted, and
        preferred, because the basis it must live on is created inside this
        function — a caller cannot build the field before the domain exists.
    advection
        Build the *advection-only* problem instead: a prescribed, non-evolving
        velocity transporting ``h`` as a passive tracer,

            dt(h) + nu*L^p(h) = -u@grad(h) .

        This is not a degenerate shallow-water problem, it is a different one, and
        it exists because Williamson et al. define their case 1 that way — "the
        only case of the suite that does not deal with the complete shallow water
        equations. It tests the advective component in isolation." Running case 1
        through the full system would let the height field push the wind around
        and would no longer be that test. Nothing else in the project uses this
        path.
    """
    coords, dist, basis, units, params, shape = build_domain(config, dtype=dtype)

    R = units.length(params["R"])
    Omega = params["Omega"] / units.second
    g = params["g"] * units.meter / units.second**2
    H = units.length(params["H"])

    numerics = config.get("numerics") or {}
    order = int(numerics.get("hyperdiffusion_order", 4))
    if order not in (2, 4):
        raise ValueError(
            f"hyperdiffusion_order must be 2 or 4, got {order}. Higher orders are "
            "not supported: each extra Laplacian tightens the timestep restriction "
            "by a further power of the resolution."
        )
    nu_si = numerics.get("hyperdiffusion_coefficient")
    if nu_si is None or isinstance(nu_si, str):
        raise ValueError(
            "numerics.hyperdiffusion_coefficient is unset or still a sentinel; "
            "resolve it in the config before building the problem."
        )
    # nu carries SI units of m^order / s.
    nu = float(nu_si) * units.meter**order / units.second

    u = dist.VectorField(coords, name="u", bases=basis)
    h = dist.Field(name="h", bases=basis)

    if topography is not None and not hasattr(topography, "change_scales"):
        grid = np.asarray(topography)
        topography = dist.Field(name="hb", bases=basis)
        topography["g"] = grid

    zcross = lambda A: d3.MulCosine(d3.skew(A))  # noqa: E731

    def hyper(field):
        return d3.lap(d3.lap(field)) if order == 4 else d3.lap(field)

    depth = h if topography is None else (h - topography)

    namespace = dict(
        u=u,
        h=h,
        g=g,
        H=H,
        R=R,
        Omega=Omega,
        nu=nu,
        zcross=zcross,
        hyper=hyper,
        depth=depth,
        grad=d3.grad,
        div=d3.div,
        lap=d3.lap,
        skew=d3.skew,
    )
    if advection:
        # The wind is data, not a variable: only h is evolved, and the velocity
        # field keeps whatever an initial condition wrote into it.
        problem = d3.IVP([h], namespace=namespace)
        problem.add_equation("dt(h) + nu*hyper(h) = -u@grad(h)")
        return ShallowWaterProblem(
            coords=coords,
            dist=dist,
            basis=basis,
            u=u,
            h=h,
            problem=problem,
            units=units,
            params=params,
            shape=shape,
            topography=topography,
        )

    problem = d3.IVP([u, h], namespace=namespace)

    # Momentum: pressure gradient, Coriolis and hyperdiffusion are linear and go
    # left for implicit treatment; nonlinear advection goes right.
    problem.add_equation("dt(u) + nu*hyper(u) + g*grad(h) + 2*Omega*zcross(u) = -u@grad(u)")
    # Continuity: mean-depth divergence left, perturbation mass flux right.
    problem.add_equation("dt(h) + nu*hyper(h) + H*div(u) = -div(depth*u)")

    return ShallowWaterProblem(
        coords=coords,
        dist=dist,
        basis=basis,
        u=u,
        h=h,
        problem=problem,
        units=units,
        params=params,
        shape=shape,
        topography=topography,
    )


def latitude_grid(dist, basis):
    """Return ``(phi, lat)`` broadcast-ready grids, latitude measured from the equator.

    The basis works in colatitude ``theta`` measured from the north pole, while
    every formula in ``theory/derivations.tex`` and in the papers this project
    implements uses latitude. Converting in one place stops the sign convention
    being rediscovered in six initial-condition modules.
    """
    phi, theta = dist.local_grids(basis)
    lat = np.pi / 2 - theta + 0 * phi
    return phi, lat
