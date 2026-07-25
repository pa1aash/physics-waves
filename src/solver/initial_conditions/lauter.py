"""Läuter, Handorf & Dethloff (2005) unsteady analytic solution, Example 3 (run V-09).

Physics first. Every other verification case in this project is either steady
(Williamson case 2) or has no closed form (cases 5 and 6). That leaves a gap: a
solver can hold a steady state perfectly and still get the *time* dependence
wrong. This case closes it. It is solid body rotation about an axis ``c`` that is
tilted away from the Earth's rotation axis, so the flow is steady in the inertial
frame and therefore **precesses westward once per day in the rotating frame** —
an exact, non-trivial, time-dependent solution of the full nonlinear shallow-water
equations against which error can be measured at any instant, not only at ``t=0``.

The paper's own summary: "All derived solutions describe a precession around the
Earth's axis with a time period of 1 day." Setting the tilt ``alpha = 0`` recovers
Williamson case 2 — the paper says so explicitly, "For alpha = 0, Example 3
corresponds to [Williamson case 2], but with a different orography" — which gives
this module a free internal consistency check, exercised in
``tests/test_solver_core.py``.

Source: *Journal of Computational Physics* **210**(2), 535-553, read from
``docs/literature/lauter_2005_unsteady_analytical_solutions.pdf``, Example 3 on
journal pages 543-545. Parameters from the paper's own application in its §5:
``alpha = pi/4``, ``u0 = 2 pi a / (12 days)``, ``k1 = 133681 m^2/s^2``,
``k2 = 0``.

**The orography is not optional, and it is large.** Läuter et al. do not absorb
the centrifugal potential into an effective gravity. Their solution therefore
carries a bottom geopotential ``Phi_B = (a Omega sin(lat))^2 / 2 + k2``, which is
zero at the equator and about 11 km at the poles — the centrifugal bulge of the
reference surface, expressed as topography. This project's equations use effective
gravity with a flat bottom, so that bulge must be supplied explicitly as
``topography``. Omitting it does not give a slightly different answer; it gives a
different problem, and the solution below is not a solution of it.

**A transcription note, because the source PDF loses minus signs.** The text layer
of the archived PDF drops several minus signs (they extract as empty glyphs).
Rather than guess, the sign of every term was fixed by requiring the ``alpha = 0``
reduction to reproduce Williamson et al. (1992) report eq. (95) — the reduction
the paper itself asserts. The signs used here are the unique choice that does so,
and ``tests/test_solver_core.py`` re-checks it numerically rather than trusting
this paragraph.
"""

from __future__ import annotations

import numpy as np

from src.solver.equations import latitude_grid
from src.solver.initial_conditions.common import (
    DAY,
    area_average,
    set_free_surface,
    set_velocity,
)

ALPHA = np.pi / 4
K1 = 133681.0
K2 = 0.0


def _axis_projections(phi, lat, alpha: float, Omega_si: float, t_si: float):
    """The three projections of the rotated axis, paper eq. (22) with ``a -> c``.

    With ``c = -sin(alpha) e1 + cos(alpha) e3`` and ``u_t`` the rotation by
    ``Omega t`` about ``e3``, the components onto the local eastward ``i``,
    northward ``j`` and radial ``n`` unit vectors collapse to functions of the
    single combination ``lambda + Omega t``. That is the whole content of the
    solution: the pattern is rigid in ``lambda + Omega t``, so in the rotating
    frame it drifts west at exactly the planetary rotation rate.
    """
    chi = np.asarray(phi) + Omega_si * t_si
    sa, ca = np.sin(alpha), np.cos(alpha)
    c_i = sa * np.sin(chi)
    c_j = sa * np.sin(lat) * np.cos(chi) + ca * np.cos(lat)
    c_n = -sa * np.cos(lat) * np.cos(chi) + ca * np.sin(lat)
    return c_i, c_j, c_n


def analytic_fields(swp, params: dict, t_si: float = 0.0):
    """The Example-3 velocity (m/s) and free-surface geopotential (m^2/s^2) at time ``t``.

    Returned in SI on the solver's grid, so the error-norm machinery can call it
    at any output time without rebuilding the case::

        u   = u0 (c . j)
        v   = -u0 (c . i)
        Phi = -[u0 (c . n) + a Omega sin(lat)]^2 / 2
              + [a Omega sin(lat)]^2 / 2 + k1
        Phi_B = [a Omega sin(lat)]^2 / 2 + k2
    """
    phi, lat = latitude_grid(swp.dist, swp.basis)
    alpha = float(params.get("alpha", ALPHA))
    a_si, Omega_si = swp.params["R"], swp.params["Omega"]
    u0_si = float(params.get("u0", 2 * np.pi * a_si / (12 * DAY)))
    k1 = float(params.get("k1", K1))
    k2 = float(params.get("k2", K2))

    c_i, c_j, c_n = _axis_projections(phi, lat, alpha, Omega_si, t_si)
    u_si = u0_si * c_j
    v_si = -u0_si * c_i

    centrifugal = a_si * Omega_si * np.sin(lat)
    phi_free = -0.5 * (u0_si * c_n + centrifugal) ** 2 + 0.5 * centrifugal**2 + k1
    phi_bottom = 0.5 * centrifugal**2 + k2
    return u_si, v_si, phi_free + 0.0 * np.asarray(phi), phi_bottom + 0.0 * np.asarray(phi)


def lauter_unsteady(swp, params: dict) -> dict:
    """Initialise Example 3 at ``t = 0``, returning its topography and analytic solution.

    The precession period is ``2 pi / Omega`` — one sidereal day — so an
    integration of a day should return the fields to their initial values. That is
    a sharper test than an error norm at a single instant, because a solver with a
    systematic phase error passes the instantaneous norm at small ``t`` and fails
    the round trip.
    """
    units = swp.units
    u_si, v_si, phi_free, phi_bottom = analytic_fields(swp, params, t_si=0.0)
    set_velocity(swp, units.velocity(u_si), units.velocity(v_si))

    g_si = swp.params["g"]
    surface_si = phi_free / g_si
    mean_surface = set_free_surface(swp, surface_si)

    thickness = surface_si - phi_bottom / g_si
    return {
        "kind": "shallow_water",
        "mean_depth_m": mean_surface,
        "steady": False,
        "topography": units.length(phi_bottom / g_si),
        "precession_period_s": 2 * np.pi / swp.params["Omega"],
        "mean_thickness_m": area_average(swp, thickness),
        "min_thickness_m": float(np.min(thickness)),
        "analytic": "src.solver.initial_conditions.lauter.analytic_fields",
    }
