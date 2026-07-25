"""Machinery shared by every initial condition: balance, means, and conventions.

Physics first. An initial condition for a rotating shallow-water flow is not a
free choice of two fields. If the height field is not the one whose pressure
gradient supports the given wind, the fluid is not in balance and it will say so
immediately by radiating gravity waves — fast, large-amplitude, and completely
uninteresting for a study of Rossby waves and barotropic instability. Every
module in this package therefore either takes its height field from an analytic
balance given in a published source, or constructs one here.

Two constructions live in this file, and they are not interchangeable:

* :func:`balanced_zonal_height` integrates the **gradient-wind relation**
  meridionally. It applies only to a purely zonal base flow ``ubar(lat)``, and it
  is exact for one. This is the construction Galewsky, Scott & Polvani (2004)
  specify in their eq. (3), and the one ``theory/derivations.tex`` §11 derives as
  its eq. (balint).

* :func:`solve_balanced_height` solves the divergence of the full **nonlinear
  balance relation** as a two-dimensional linear boundary-value problem. It
  applies to any flow, zonal or not, and is what a spectral solver does
  naturally. It is the only option for a non-zonal initial condition such as a
  single spherical harmonic.

``theory/derivations.tex`` §11.2 states that the two agree to numerical precision
for a zonal flow; ``tests/test_solver_core.py`` checks that claim rather than
repeating it.

**The height convention, stated once.** The solver's prognostic ``h`` is the free
surface measured from the mean depth ``H``, so the total fluid column is
``H + h`` (or ``H + h - h_b`` over topography) and the pressure gradient is
``g grad(h)``. A published case that gives a total depth ``h_case`` therefore
enters as ``h = h_case - H``. This matters: adding a constant to ``h`` is *not*
harmless in general, because it changes the mass the continuity equation carries
even though it changes no gradient. :func:`set_free_surface` performs the
subtraction in one place and reports what the case's own mean depth was, so the
harness can warn when a config's ``H`` disagrees with it.
"""

from __future__ import annotations

import dedalus.public as d3
import numpy as np
from scipy.integrate import quad
from scipy.special import roots_legendre

from src.solver.equations import latitude_grid

DAY = 86400.0


def set_velocity(swp, u_east, u_north) -> None:
    """Write eastward/northward components into the Dedalus vector field.

    Component 0 is azimuthal (eastward). Component 1 is colatitudinal, which
    points *south*, so a northward velocity enters with a minus sign. Getting
    this wrong flips the sign of every Coriolis interaction, so it lives in
    exactly one place in the project.

    Both arguments are in working units.
    """
    swp.u["g"][0] = u_east
    swp.u["g"][1] = -u_north


def area_average(swp, field) -> float:
    """Area-weighted mean of a grid array over the sphere.

    Not ``np.mean``. The colatitude grid is Gauss-Legendre in ``cos(theta)``, so
    a plain arithmetic mean over grid points weights the poles far too heavily.
    The correct weight is the Gauss-Legendre quadrature weight in
    ``mu = cos(theta)``, uniform in azimuth.
    """
    scratch = swp.dist.Field(bases=swp.basis)
    scratch["g"] = field
    averaged = d3.Average(scratch, swp.coords).evaluate()
    averaged.change_scales(1)
    return float(np.ravel(averaged["g"])[0])


def set_free_surface(swp, surface_si) -> float:
    """Set ``h`` so that ``H + h`` is the case's free surface. Return its area mean.

    ``surface_si`` is the free-surface elevation above the flat reference bottom,
    in metres; with no topography that is also the total layer depth. The returned
    value is the case's own area mean, which is the value ``physical.H`` *should*
    carry — the harness compares the two and warns on a material disagreement,
    because the equations stay exact but the implicit/explicit split stops being
    sensible when they diverge.
    """
    H_si = swp.params["H"]
    surface = np.asarray(surface_si) + 0.0 * np.asarray(swp.h["g"])
    swp.h["g"] = swp.units.length(surface - H_si)
    return area_average(swp, surface)


def gradient_wind_integrand(lat: float, u_of_lat, R_si: float, Omega_si: float) -> float:
    """The integrand of the meridional gradient-wind balance, in SI.

    From ``theory/derivations.tex`` eq. (gradwind), identical to Galewsky, Scott &
    Polvani (2004) eq. (3):

        d(g h)/d(lat) = -R ubar(lat) [ f(lat) + ubar(lat) tan(lat) / R ]

    The two terms are the Coriolis force on the zonal flow and the centripetal
    requirement of following a latitude circle. The second is the metric term of
    the spherical momentum equation in its physical guise, and dropping it — an
    easy mistake, since it is small — leaves the jet unbalanced at the per-cent
    level and seeds a gravity-wave transient.
    """
    u = u_of_lat(lat)
    f = 2 * Omega_si * np.sin(lat)
    return R_si * u * (f + u * np.tan(lat) / R_si)


def balanced_zonal_height(swp, u_of_lat, *, support=None, mean_depth_si=None):
    """Total layer depth in SI balancing a zonal profile ``u_of_lat`` (latitude, rad).

    Integrates the gradient-wind relation from the south pole:

        g h(lat) = g h0 - integral_{-pi/2}^{lat} R ubar [ f + ubar tan / R ] dlat'

    and fixes ``h0`` by requiring a prescribed area-mean depth (Galewsky et al.
    use 10 km; the default here is the config's own ``H``, so the two agree unless
    a caller deliberately overrides). ``support`` optionally gives the latitude
    interval ``(lat0, lat1)`` outside which ``u_of_lat`` vanishes, which lets the
    quadrature skip the identically-zero part of the range instead of asking an
    adaptive integrator to discover it.

    Galewsky et al. note that "h can be computed to machine precision using
    standard Gaussian quadratures with something of the order of a hundred
    points, pole-to-pole"; the adaptive quadrature used here is at least as
    accurate and does not require choosing that count in advance.

    Returns the depth on the solver's own latitude grid, in metres.
    """
    R_si, Omega_si, g_si = swp.params["R"], swp.params["Omega"], swp.params["g"]
    if mean_depth_si is None:
        mean_depth_si = swp.params["H"]

    lo, hi = (-np.pi / 2, np.pi / 2) if support is None else support

    def integral_to(lat: float) -> float:
        """The accumulated geopotential deficit up to latitude ``lat``."""
        upper = min(max(lat, lo), hi)
        if upper <= lo:
            return 0.0
        value, _ = quad(
            gradient_wind_integrand,
            lo,
            upper,
            args=(u_of_lat, R_si, Omega_si),
            limit=400,
        )
        return value

    # The area mean of a zonal field is (1/2) * integral over mu = sin(lat), so
    # Gauss-Legendre in mu gives it exactly for a smooth profile.
    mu_nodes, mu_weights = roots_legendre(256)
    lat_nodes = np.arcsin(np.clip(mu_nodes, -1.0, 1.0))
    deficit_nodes = np.array([integral_to(x) for x in lat_nodes])
    mean_deficit = 0.5 * float(np.dot(mu_weights, deficit_nodes))
    gh0 = g_si * mean_depth_si + mean_deficit

    _, lat = latitude_grid(swp.dist, swp.basis)
    lat_1d = np.unique(np.asarray(lat).ravel())
    depth_1d = (gh0 - np.array([integral_to(x) for x in lat_1d])) / g_si
    depth = np.interp(np.asarray(lat), lat_1d, depth_1d)
    return depth


def solve_balanced_height(swp, *, mean_height: float = 0.0) -> None:
    """Set ``h`` to the nonlinear-balance height field for the velocity already in ``u``.

    Solves the divergence of the momentum equation with the time derivative
    dropped,

        g lap(h) + c = -div( u@grad(u) + 2 Omega zcross(u) ),

    as a linear boundary-value problem, with ``ave(h) = mean_height`` closing the
    system. The auxiliary constant ``c`` is a solvability multiplier, not physics:
    the Laplacian on a closed sphere has a one-dimensional null space (the
    constants), so the right-hand side must have zero mean for a solution to
    exist, and ``c`` absorbs whatever mean the discretisation leaves behind.

    This is the general balance, valid for a non-zonal flow, and it is the
    construction the shipped Dedalus shallow-water example uses for the Galewsky
    jet. Its physical content is that the initial divergence tendency vanishes —
    which is exactly the condition Williamson et al. (1992) impose in their case 6
    (their eq. 140 text, "solving the balance equation so the initial tendency of
    the divergence is zero").
    """
    dist, units, params = swp.dist, swp.units, swp.params
    g = params["g"] * units.meter / units.second**2
    Omega = params["Omega"] / units.second

    c = dist.Field(name="c_balance")
    zcross = lambda A: d3.MulCosine(d3.skew(A))  # noqa: E731
    namespace = dict(h=swp.h, c=c, u=swp.u, g=g, Omega=Omega, zcross=zcross)
    problem = d3.LBVP([swp.h, c], namespace=namespace)
    problem.add_equation("g*lap(h) + c = - div(u@grad(u) + 2*Omega*zcross(u))")
    problem.add_equation(f"ave(h) = {units.length(mean_height)}")
    problem.build_solver().solve()


def streamfunction_velocity(swp, psi_grid) -> None:
    """Set ``u`` from a streamfunction given on the grid, in working units.

    On the sphere a nondivergent flow is ``u = k x grad(psi)``, which in
    (eastward, northward) components is

        u_east  = -(1/R) d(psi)/d(lat),
        u_north =  (1/(R cos lat)) d(psi)/d(lon).

    Rather than differentiate by hand, the spectral operators do it: ``skew`` is
    the ``k x`` rotation confirmed in ``docs/DEDALUS_API.md`` §5, so
    ``skew(grad(psi))`` is exactly that field, differentiated to spectral
    accuracy. The resulting relative vorticity is ``lap(psi)`` identically, which
    is what makes a single spherical harmonic an exact Rossby-Haurwitz mode.
    """
    psi = swp.dist.Field(name="psi", bases=swp.basis)
    psi["g"] = psi_grid
    velocity = d3.skew(d3.grad(psi)).evaluate()
    # An evaluated operator comes back on the dealiased grid; rescale to the
    # coefficient-matched grid before copying, or the shapes disagree.
    velocity.change_scales(1)
    swp.u["g"] = velocity["g"]
    return psi
