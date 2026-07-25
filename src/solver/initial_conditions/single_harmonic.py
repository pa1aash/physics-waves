"""A single spherical-harmonic Rossby-Haurwitz mode (phase-speed campaign, P-01 to P-18).

Physics first. The phase-speed campaign exists to test one prediction — the
Rossby-Haurwitz dispersion relation of ``theory/derivations.tex`` eq. (rhdisp),

    c_ang = -2 Omega / [n (n + 1)] ,

the *angular* westward phase speed of a nondivergent barotropic Rossby wave of
total degree ``n`` on a sphere. Two features of that formula are what the campaign
measures: it is negative for every ``n`` (waves go west, always), and it depends
on ``n`` alone, not on the zonal order ``m``.

**Why a single harmonic and not a wave packet.** In the nondivergent barotropic
vorticity equation a single surface spherical harmonic is an exact solution of the
*full nonlinear* problem, not merely the linearised one: the Jacobian
``J(psi, lap psi) = J(psi, -n(n+1) psi / R^2)`` vanishes identically because a
function is everywhere parallel to itself. So the mode rotates rigidly westward at
``c_ang`` at any amplitude, and there is nothing to disentangle — no dispersion of
a packet, no nonlinear steepening, no ambiguity about which wave was measured.

**And why the answer here will not be exactly that.** This project integrates the
*divergent* shallow-water system, where the free surface adds a restoring
mechanism the derivation covers in §6: the mode becomes a Hough mode, and its
frequency is shifted by Lamb's parameter ``eps = 4 Omega^2 R^2 / (g H)``, about
8.8 for Earth. The size of that shift is a result of the campaign, not an input to
it. Runs P-01 to P-07 sweep ``n``, P-08 to P-12 sweep ``Omega`` (which moves
``eps`` too), and P-13 to P-15 vary amplitude to confirm that what is being
measured is a linear wave speed and not a nonlinear artefact.

**The zonal order.** ``order_m`` defaults to 2, matching the ``m = 2`` ladder that
``theory/derivations.tex`` §6 uses for its divergent-correction investigation and
that ``docs/DEDALUS_API.md`` §11 confirmed against the analytic ``n(n+1)``
spectrum, so the simulation and the eigenvalue calculation are asking about the
same modes. Note that P-01 (``n = 2``) is then **sectoral** (``n = m``), which §6.5
identifies as a genuine special case — a sectoral mode sits at the bottom of its
degree ladder and has one Coriolis coupling partner instead of two, so it is
slowed less by divergence than its neighbours. That is a prediction P-01 tests, not
a defect of the configuration.
"""

from __future__ import annotations

import numpy as np
from scipy.special import assoc_legendre_p_all

from src.solver.equations import latitude_grid
from src.solver.initial_conditions.common import (
    solve_balanced_height,
    streamfunction_velocity,
)


def harmonic_streamfunction(phi, lat, n: int, m: int, amplitude: float = 1.0):
    """``P_n^m(sin lat) cos(m lon)``, normalised to unit maximum, times ``amplitude``.

    The real form is used rather than the complex ``Y_n^m``: the solver's
    initial-value path is real-valued, and a real standing pattern of order ``m``
    is the superposition of the eastward and westward travelling members of the
    same degree. Since the nondivergent problem sends both west at the same speed,
    the pattern travels west rigidly and the phase-speed diagnostic sees a single
    unambiguous drift.
    """
    if not 0 <= m <= n:
        raise ValueError(f"need 0 <= m <= n; got n={n}, m={m}")
    mu = np.sin(np.asarray(lat, dtype=float))
    table = assoc_legendre_p_all(n, m, mu, norm=True, diff_n=0)
    P = table[0, n, m]
    pattern = P * np.cos(m * np.asarray(phi))
    peak = float(np.max(np.abs(pattern)))
    return amplitude * pattern / peak


def single_harmonic(swp, params: dict) -> dict:
    """Initialise one Rossby-Haurwitz mode of degree ``n`` and order ``m``.

    ``amplitude`` is specified as the **peak wind speed in m/s**, not as a
    streamfunction amplitude. That is the physically legible knob: it says how
    fast the fluid moves, it is what the linearity ladder P-13 to P-15 varies, and
    it can be compared directly against the wave's own phase speed to say whether
    the run is in the linear regime at all. The streamfunction is scaled to hit it
    by measuring the velocity the unit-amplitude pattern produces and dividing —
    exact, because the map from streamfunction to velocity is linear.

    The height field comes from the nonlinear balance boundary-value problem, so
    the mode starts balanced and does not radiate a gravity-wave transient that
    would swamp a 1 m/s signal.
    """
    dist, basis, units = swp.dist, swp.basis, swp.units
    phi, lat = latitude_grid(dist, basis)

    n = int(params.get("degree_n", 4))
    m = int(params.get("order_m", 2))
    amplitude_si = float(params.get("amplitude", 1.0))

    psi_pattern = harmonic_streamfunction(phi, lat, n, m, amplitude=1.0)

    # Scale so the peak speed is `amplitude`. One evaluation at unit amplitude
    # tells us the constant of proportionality exactly.
    streamfunction_velocity(swp, psi_pattern)
    peak_speed = float(np.max(np.abs(swp.u["g"])))
    if peak_speed == 0.0:
        raise ValueError(f"degree n={n}, order m={m} produced an identically zero velocity")
    scale = units.velocity(amplitude_si) / peak_speed
    streamfunction_velocity(swp, scale * psi_pattern)

    solve_balanced_height(swp, mean_height=0.0)

    Omega_si, R_si = swp.params["Omega"], swp.params["R"]
    g_si, H_si = swp.params["g"], swp.params["H"]
    c_ang = -2 * Omega_si / (n * (n + 1))
    eps = 4 * Omega_si**2 * R_si**2 / (g_si * H_si)
    return {
        "kind": "shallow_water",
        "mean_depth_m": H_si,
        "steady": False,
        "degree_n": n,
        "order_m": m,
        "sectoral": n == m,
        "amplitude_m_s": amplitude_si,
        # Nondivergent prediction, eq. (rhdisp). The divergent system will not
        # reproduce it exactly; the difference is the measurement.
        "predicted_angular_phase_speed_rad_s": c_ang,
        "predicted_equatorial_phase_speed_m_s": c_ang * R_si,
        "lambs_parameter": eps,
        "westward_period_s": abs(2 * np.pi / (m * c_ang)) if m else float("inf"),
    }
