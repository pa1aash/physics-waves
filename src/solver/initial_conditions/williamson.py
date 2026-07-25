"""Williamson et al. (1992) benchmark initial conditions: cases 1, 2, 5 and 6.

Physics first. These four cases walk a shallow-water solver up a ladder of
difficulty. Case 1 removes the dynamics entirely and asks only whether the code
can advect a blob without distorting it. Case 2 restores the full nonlinear
equations but chooses a flow that is an *exact steady solution*, so any evolution
at all is numerical error. Case 5 breaks that steadiness with a mountain, forcing
the flow to generate real wave structure. Case 6 is a Rossby-Haurwitz wave — an
exact travelling solution of the *nondivergent* barotropic vorticity equation,
and only an approximate one here, which is precisely why it is informative.

**Source, and a citation-identity warning that matters for page references.**
The formulae below are read from the PDF this project holds, which is
**ORNL/TM-11895**, an Oak Ridge National Laboratory technical memorandum by the
same five authors and with the same title as the *Journal of Computational
Physics* article the project cites (102(1), 211-224, doi
10.1016/0021-9991(92)90060-C). Session L4's literature campaign discovered the
mismatch; Session L5 checked what it costs.

*Finding:* the report carries the same test-case definitions and the same
parameter values as the published paper — case 1 is its §3.1, case 2 its §3.2,
case 5 its §3.5, case 6 its §3.6, with Earth parameters ``a = 6.37122e6 m``,
``Omega = 7.292e-5 /s``, ``g = 9.80616 m/s^2`` as its eqs. (72)-(74). But **the
equation numbering is the report's own and does not match the journal
article's**: the report numbers the cosine bell at eqs. (75)-(80) and the
Rossby-Haurwitz wave at (135)-(143), continuing a sequence begun in its earlier
sections. Equation numbers quoted below are therefore *report* numbers and are
marked as such. No claim in this project should cite a Williamson equation number
against the JCP article on the strength of this file. The same finding is
recorded in ``docs/literature/README.md``.

**Latitude convention.** Williamson writes ``theta`` for *latitude*, measured from
the equator. The Dedalus sphere basis uses colatitude. Everything here works in
latitude, obtained from :func:`src.solver.equations.latitude_grid`, so the
formulae transcribe without a sign change.
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

# Report eqs. (72)-(74). Held here as the case definitions' own reference values,
# kept separate from a run's configured physical block so that a config sweeping
# Omega does not silently change what "Williamson case 2" means.
A_EARTH = 6.37122e6

# Case-1 and case-2 advecting wind: report text after eq. (80), "u0 = 2 pi a /
# (12 days), which is equivalent to about 40 m/sec".
U0_12DAY = 2 * np.pi * A_EARTH / (12 * DAY)


def case1_cosine_bell(swp, params: dict) -> dict:
    """Case 1 — advection of a cosine bell (report §3.1, eqs. 75-80).

    The only case that does not use the full shallow-water system. The report is
    explicit: "This is the only case of the suite that does not deal with the
    complete shallow water equations. It tests the advective component in
    isolation." The wind is prescribed and nondivergent, so the height equation
    reduces to pure advection, and ``h`` here is an advected tracer rather than a
    free surface. The run harness honours that by building an advection-only
    problem for this case; pushing it through the full shallow-water system would
    be a different test with a different answer.

    Report eqs. (75)-(76) for the advecting wind, (79) for the bell, (80) for the
    great-circle distance. ``h0 = 1000 m``, bell radius ``a/3``, centre initially
    at ``(3 pi / 2, 0)``, and the report asks for runs at
    ``alpha = 0, 0.05, pi/2 - 0.05, pi/2``.
    """
    dist, basis, units = swp.dist, swp.basis, swp.units
    phi, lat = latitude_grid(dist, basis)

    alpha = float(params.get("alpha", 0.0))
    u0_si = float(params.get("u0", U0_12DAY))
    h0_si = float(params.get("h0", 1000.0))
    a_si = swp.params["R"]
    radius_si = float(params.get("bell_radius", a_si / 3.0))
    lam_c = float(params.get("lambda_c", 3 * np.pi / 2))
    lat_c = float(params.get("theta_c", 0.0))

    u0 = units.velocity(u0_si)
    u_east = u0 * (np.cos(lat) * np.cos(alpha) + np.sin(lat) * np.cos(phi) * np.sin(alpha))
    u_north = -u0 * np.sin(phi) * np.sin(alpha)
    set_velocity(swp, u_east, u_north)

    cosr = np.sin(lat_c) * np.sin(lat) + np.cos(lat_c) * np.cos(lat) * np.cos(phi - lam_c)
    r = a_si * np.arccos(np.clip(cosr, -1.0, 1.0))
    bell = np.where(r < radius_si, (h0_si / 2) * (1 + np.cos(np.pi * r / radius_si)), 0.0)
    swp.h["g"] = units.length(bell)

    # One full revolution is the natural integration length: "A cosine bell is
    # advected once around the sphere", and "This solution translates without any
    # change of shape", so the analytic solution at that time is the initial field
    # itself — which is what makes the error norm meaningful without a reference
    # run.
    period_si = 2 * np.pi * a_si / u0_si
    return {
        "kind": "advection",
        "mean_depth_m": None,
        "revolution_seconds": period_si,
        "analytic": "initial condition, unchanged, after one revolution",
    }


def case2_steady_zonal(swp, params: dict) -> dict:
    """Case 2 — global steady-state nonlinear zonal geostrophic flow (report §3.2).

    The workhorse of the suite, and the one this project leans on hardest: an
    *exact* steady solution of the full nonlinear shallow-water equations, so the
    correct time derivative is identically zero. Any tendency the solver reports
    at ``t = 0`` is error in the discretisation or in the balance between the wind
    and height fields, and nothing else. ``tests/test_solver_core.py`` uses
    exactly that as its physics gate.

    Report eqs. (90), (91), (95), with ``theta`` the latitude::

        u   = u0 (cos(theta) cos(alpha) + cos(lambda) sin(theta) sin(alpha))
        v   = -u0 sin(lambda) sin(alpha)
        g h = g h0 - (a Omega u0 + u0^2/2)
              (-cos(lambda) cos(theta) sin(alpha) + sin(theta) cos(alpha))^2

    with ``u0 = 2 pi a / (12 days)`` and ``g h0 = 2.94e4 m^2/s^2`` (report text
    after eq. 96).

    Note that the report's ``h`` is the *total* layer depth, whereas the solver's
    prognostic is the departure from ``H``; :func:`set_free_surface` does the
    subtraction and returns the case's own mean depth, which for the standard
    parameters is about 2.4 km and *not* the 10 km the stub configs carried. See
    ``common.py`` for why the difference is not cosmetic.
    """
    dist, basis, units = swp.dist, swp.basis, swp.units
    phi, lat = latitude_grid(dist, basis)

    alpha = float(params.get("alpha", 0.0))
    u0_si = float(params.get("u0", U0_12DAY))
    gh0_si = float(params.get("gh0", 2.94e4))
    a_si, Omega_si, g_si = swp.params["R"], swp.params["Omega"], swp.params["g"]

    u0 = units.velocity(u0_si)
    u_east = u0 * (np.cos(lat) * np.cos(alpha) + np.cos(phi) * np.sin(lat) * np.sin(alpha))
    u_north = -u0 * np.sin(phi) * np.sin(alpha)
    set_velocity(swp, u_east, u_north)

    s = -np.cos(phi) * np.cos(lat) * np.sin(alpha) + np.sin(lat) * np.cos(alpha)
    depth_si = (gh0_si - (a_si * Omega_si * u0_si + u0_si**2 / 2) * s**2) / g_si
    mean_depth = set_free_surface(swp, depth_si)

    return {
        "kind": "shallow_water",
        "mean_depth_m": mean_depth,
        "steady": True,
        "analytic": "initial condition, unchanged, for all time",
    }


def case5_mountain(swp, params: dict) -> dict:
    """Case 5 — zonal flow over an isolated mountain (report §3.5, eq. 134).

    The report: "It consists of zonal flow as in case 2 impinging on a mountain.
    The wind and height field are as in case 2, with alpha = 0, but the mean
    height is changed to h0 = 5400 m." There is no analytic solution; the physical
    point is that a steady zonal flow forced over topography must radiate, and the
    wave field it produces tests the pressure-gradient and mass-flux terms working
    together.

    Report eq. (134): ``h_s = h_s0 (1 - r/R)`` with ``h_s0 = 2000 m``,
    ``R = pi/9``, ``r^2 = min[R^2, (lambda - lambda_c)^2 + (theta - theta_c)^2]``,
    centred at ``lambda_c = -pi/2``, ``theta_c = pi/6``.

    **A known defect of the case, not of this implementation.** Galewsky, Scott &
    Polvani (2004) point out that this cone "is not a differentiable function", so
    spectral models are "likely to exhibit ringing phenomena as the resolution is
    increased", and that the mountain is "added impulsively on to an initially
    balanced flow", generating a gravity-wave adjustment that needs very small
    timesteps. Both are properties of the published test. It is implemented as
    published; the consequences belong in the discussion of V-03/V-04, not in a
    quiet smoothing of the source.

    The topography is returned under ``topography``; the harness passes it to
    :func:`src.solver.equations.build_problem`. This is the only case with one.
    """
    dist, basis, units = swp.dist, swp.basis, swp.units
    phi, lat = latitude_grid(dist, basis)

    h_s0 = float(params.get("mountain_height", 2000.0))
    Rm = float(params.get("mountain_radius", np.pi / 9))
    lam_c = float(params.get("mountain_lambda", -np.pi / 2))
    lat_c = float(params.get("mountain_theta", np.pi / 6))

    p2 = dict(params)
    p2["alpha"] = 0.0
    p2.setdefault("gh0", swp.params["g"] * float(params.get("h0", 5400.0)))
    result = case2_steady_zonal(swp, p2)

    # Wrap the longitude difference to (-pi, pi] before squaring, so a mountain
    # near the dateline is not torn in half by the branch cut.
    dlam = (phi - lam_c + np.pi) % (2 * np.pi) - np.pi
    r2 = np.minimum(Rm**2, dlam**2 + (lat - lat_c) ** 2)
    hs_si = h_s0 * (1 - np.sqrt(r2) / Rm) + 0.0 * lat

    result.update(
        {
            "steady": False,
            "analytic": None,
            "topography": units.length(hs_si),
            "mountain_mean_m": area_average(swp, hs_si),
        }
    )
    return result


def case6_rossby_haurwitz(swp, params: dict) -> dict:
    """Case 6 — the Rossby-Haurwitz wave, zonal wavenumber 4 (report §3.6).

    An exact travelling solution of the *nondivergent* barotropic vorticity
    equation, used here in the *divergent* shallow-water system where it is only
    approximate. That gap is the physics: the wave should propagate with little
    change of shape, and how much it does change measures how far the free surface
    has moved the system from the idealisation the solution was built for.

    Report eqs. (135)-(143), with ``theta`` the latitude and wavenumber ``R``::

        psi = -a^2 omega sin(theta) + a^2 K cos^R(theta) sin(theta) cos(R lambda)
        u   = a omega cos(theta)
              + a K cos^(R-1)(theta) (R sin^2(theta) - cos^2(theta)) cos(R lambda)
        v   = -a K R cos^(R-1)(theta) sin(theta) sin(R lambda)
        g h = g h0 + a^2 A + a^2 B cos(R lambda) + a^2 C cos(2 R lambda)

    with ``A``, ``B``, ``C`` as report eqs. (141)-(143) and, from the text after
    eq. (143), ``omega = K = 7.848e-6 /s``, ``h0 = 8e3 m``, ``R = 4``. The height
    comes "from the stream function by solving the balance equation so the initial
    tendency of the divergence is zero", which is what eqs. (140)-(143) express in
    closed form for this particular streamfunction.

    Report eq. (136) gives the pattern's angular velocity,

        nu = [R (3 + R) omega - 2 Omega] / [(1 + R) (2 + R)],

    which for the standard parameters comes out westward. It is returned as a
    prediction for the phase-speed diagnostic to test rather than assume.

    **A caveat this project must carry, from limitation L3 of the derivation.**
    Williamson chose wavenumber 4 because it was believed stable — the report says
    "Unstable waves are not chosen since slightly different perturbations may lead
    to growth of different unstable modes". Thuburn & Li (2000) later showed the
    shallow-water wavenumber-4 Rossby-Haurwitz wave *is* dynamically unstable,
    breaking down when perturbed with an e-folding time of order 1.3 days. So this
    is not a clean steady benchmark over arbitrary integration length.
    :func:`stable_window_seconds` gives the window over which it may be treated as
    one, and the harness warns when a config asks for longer.
    """
    dist, basis, units = swp.dist, swp.basis, swp.units
    phi, lat = latitude_grid(dist, basis)

    omega_si = float(params.get("omega", 7.848e-6))
    K_si = float(params.get("K", 7.848e-6))
    Rw = int(params.get("wavenumber", 4))
    h0_si = float(params.get("h0", 8.0e3))
    a_si, Omega_si, g_si = swp.params["R"], swp.params["Omega"], swp.params["g"]

    c, s = np.cos(lat), np.sin(lat)

    # report eqs. (137)-(138)
    u_si = a_si * omega_si * c + a_si * K_si * c ** (Rw - 1) * (Rw * s**2 - c**2) * np.cos(Rw * phi)
    v_si = -a_si * K_si * Rw * c ** (Rw - 1) * s * np.sin(Rw * phi)
    set_velocity(swp, units.velocity(u_si), units.velocity(v_si))

    # report eqs. (141)-(143). The cos^-2 term in A is singular at the poles but
    # is multiplied by cos^(2R), which vanishes far faster for R >= 1, so the
    # product is finite. Evaluate it grouped as cos^(2R-2) rather than as a
    # quotient, to avoid a spurious inf at polar grid points.
    A = (omega_si / 2) * (2 * Omega_si + omega_si) * c**2 + 0.25 * K_si**2 * (
        c ** (2 * Rw) * ((Rw + 1) * c**2 + (2 * Rw**2 - Rw - 2)) - 2 * Rw**2 * c ** (2 * Rw - 2)
    )
    B = (
        (2 * (Omega_si + omega_si) * K_si)
        / ((Rw + 1) * (Rw + 2))
        * c**Rw
        * ((Rw**2 + 2 * Rw + 2) - (Rw + 1) ** 2 * c**2)
    )
    C = 0.25 * K_si**2 * c ** (2 * Rw) * ((Rw + 1) * c**2 - (Rw + 2))

    depth_si = (
        g_si * h0_si
        + a_si**2 * A
        + a_si**2 * B * np.cos(Rw * phi)
        + a_si**2 * C * np.cos(2 * Rw * phi)
    ) / g_si
    mean_depth = set_free_surface(swp, depth_si)

    nu_si = (Rw * (3 + Rw) * omega_si - 2 * Omega_si) / ((1 + Rw) * (2 + Rw))
    return {
        "kind": "shallow_water",
        "mean_depth_m": mean_depth,
        "steady": False,
        "predicted_angular_velocity_rad_s": nu_si,
        "max_stable_window_s": stable_window_seconds(params),
    }


def stable_window_seconds(params: dict | None = None) -> float:
    """How long Williamson case 6 may be treated as a clean propagating benchmark.

    Not a property of the discretisation — a property of the *solution*. Thuburn &
    Li (2000), recorded in ``docs/literature/ANCHOR_NOTES.md``, measured
    exponential growth with an **e-folding time of 1.3 days**. The default window
    is three e-folding times: a disturbance seeded at round-off has grown by a
    factor of about twenty by then and is still far below the wave itself, while
    one seeded at the per-cent level would not be.

    Configurable rather than hardcoded, because the growth rate depends on the
    hyperdiffusion coefficient — Thuburn & Li found the outcome sensitive to it —
    so a later session that measures the rate for this project's own settings can
    set the window from its own data rather than from theirs.
    """
    params = params or {}
    e_fold_days = float(params.get("rh_efold_days", 1.3))
    n_folds = float(params.get("rh_stable_efolds", 3.0))
    return e_fold_days * n_folds * DAY
