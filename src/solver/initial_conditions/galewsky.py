"""Galewsky, Scott & Polvani (2004) barotropic-instability initial condition (run I-00).

Physics first. This is a mid-latitude jet that is *unstable*, set up so that the
instability is the thing being measured rather than an artefact. Three properties
do that work, and all three are deliberate:

1. **The jet is compactly supported and infinitely differentiable.** It is
   identically zero outside a latitude band, so it introduces no structure at the
   poles, and every derivative vanishes at its edges, so the background
   absolute-vorticity gradient tends smoothly to ``beta`` outside the jet. The
   Rayleigh-Kuo reversal is confined to the jet's flanks, where the physics is,
   with no spurious edge feature to contaminate it. The paper is explicit that
   "commonly used functions, such as a hyperbolic secant, a truncated cosine or a
   Gaussian function, either do not go to zero at the poles or are not infinitely
   differentiable".

2. **The height field is balanced.** A jet dropped onto a flat surface radiates
   gravity waves immediately, and the growth one then measures is contaminated by
   that transient. Integrating the gradient-wind relation gives the height field
   whose pressure gradient exactly supports the jet, so the unperturbed state is
   steady. Galewsky et al. confirm this numerically: with the unperturbed
   balanced height "all fields remained identical to the initial ones to machine
   precision for the entire 120 h".

3. **The perturbation is localised in longitude, and unbalanced.** Being
   localised it projects onto a broad band of zonal wavenumbers, so it excites
   whichever mode actually grows fastest instead of presupposing one — which is
   what makes the measured ``m*`` a result rather than an input.

Source: *Tellus* **56A**(5), 429-440, read from
``docs/literature/galewsky_2004_initial_value_problem.pdf``. Equation numbers
below are the paper's. Constants from its §2: ``umax = 80 m/s``,
``phi0 = pi/7``, ``phi1 = pi/2 - phi0``, ``en = exp[-4/(phi1-phi0)^2]``,
``a = 6.37122e6 m``, ``Omega = 7.292e-5 /s``, ``g = 9.80616 m/s^2``, global mean
layer depth 10 km, and for the perturbation ``h_hat = 120 m``, ``phi2 = pi/4``,
``alpha = 1/3``, ``beta = 1/15``.

**One difference from the paper, stated because it changes a number.** Galewsky
et al. work with ``nabla^2`` viscosity (their eq. 1) and present their headline
results inviscid. This project integrates with ``nabla^4`` hyperdiffusion, as the
shipped Dedalus reference does. The consequence — a small shift in the onset time
of the instability — was measured in the Phase-0 gate and is recorded in
``tests/phase0_gate/galewsky_comparison.md``. It is expected, not a failure, but
it means onset times are not directly comparable to the paper's figures.
"""

from __future__ import annotations

import numpy as np

from src.solver.equations import latitude_grid
from src.solver.initial_conditions.common import (
    balanced_zonal_height,
    set_free_surface,
    set_velocity,
)

# Paper §2. UMAX is also the reference amplitude that the idealised jet family in
# jet_family.py scales against, so that its S = 1 is this jet exactly.
UMAX = 80.0
PHI0 = np.pi / 7
PHI1 = np.pi / 2 - PHI0
MEAN_DEPTH = 1.0e4


def jet_profile(lat, umax: float = UMAX, phi0: float = PHI0, phi1: float = PHI1):
    """Paper eq. (2): the compactly supported, C-infinity zonal jet.

        u(phi) = (umax / en) exp[ 1 / ((phi - phi0)(phi - phi1)) ]   on (phi0, phi1)
               = 0                                                   otherwise

    with ``en = exp[-4/(phi1-phi0)^2]`` normalising the peak to ``umax`` at the
    jet's mid-point. Accepts a scalar or an array: the balance quadrature needs
    the scalar path, the grid evaluation needs the array path.
    """
    en = np.exp(-4.0 / (phi1 - phi0) ** 2)
    lat = np.asarray(lat, dtype=float)
    if lat.ndim == 0:
        x = float(lat)
        if not (phi0 < x < phi1):
            return 0.0
        return float(umax / en * np.exp(1.0 / ((x - phi0) * (x - phi1))))
    inside = (lat > phi0) & (lat < phi1)
    out = np.zeros_like(lat)
    p = lat[inside]
    out[inside] = umax / en * np.exp(1.0 / ((p - phi0) * (p - phi1)))
    return out


def height_perturbation(phi, lat, params: dict):
    """Paper eq. (4): the localised, deliberately unbalanced height bump.

        h'(lambda, phi) = h_hat cos(phi) exp[-(lambda/alpha)^2]
                                         exp[-((phi2 - phi)/beta)^2]

    for ``-pi < lambda < pi``. The ``cos(phi)`` factor forces the perturbation to
    zero at the poles. Returned in metres.

    The longitude is wrapped into ``(-pi, pi]`` before use, because the paper
    defines the bump on that interval while the solver's azimuthal grid runs over
    ``[0, 2pi)``. Without the wrap the bump would be cut in half at the grid seam
    and the run would be seeded by a discontinuity rather than by eq. (4).
    """
    h_hat = float(params.get("h_hat", 120.0))
    lat2 = float(params.get("phi2", np.pi / 4))
    alpha = float(params.get("alpha", 1.0 / 3.0))
    beta = float(params.get("beta", 1.0 / 15.0))
    lam = (np.asarray(phi) + np.pi) % (2 * np.pi) - np.pi
    return (
        h_hat * np.cos(lat) * np.exp(-((lam / alpha) ** 2)) * np.exp(-(((lat2 - lat) / beta) ** 2))
    )


def galewsky_jet(swp, params: dict) -> dict:
    """Build the full initial condition: jet, balanced height, and perturbation.

    ``params`` may switch the perturbation off (``perturbation: false``) to
    reproduce the paper's own balance check — the 120-hour integration in which
    every field must stay identical to machine precision. That is a genuine test
    of the balance construction, so it is worth having available as a config and
    not only as a unit test.
    """
    dist, basis, units = swp.dist, swp.basis, swp.units
    phi, lat = latitude_grid(dist, basis)

    umax = float(params.get("umax", UMAX))
    phi0 = float(params.get("phi0", PHI0))
    phi1 = float(params.get("phi1", PHI1))
    mean_depth_si = float(params.get("mean_depth", MEAN_DEPTH))

    u_si = jet_profile(lat, umax, phi0, phi1)
    set_velocity(swp, units.velocity(u_si), 0.0 * u_si)

    depth_si = balanced_zonal_height(
        swp,
        lambda x: jet_profile(x, umax, phi0, phi1),
        support=(phi0, phi1),
        mean_depth_si=mean_depth_si,
    )

    pert = params.get("perturbation", True)
    pert_params = pert if isinstance(pert, dict) else {}
    if pert is not False:
        depth_si = depth_si + height_perturbation(phi, lat, pert_params)

    mean_depth = set_free_surface(swp, depth_si)
    return {
        "kind": "shallow_water",
        "mean_depth_m": mean_depth,
        "steady": pert is False,
        "perturbed": pert is not False,
        "jet_umax_m_s": umax,
        "jet_support_lat_rad": [phi0, phi1],
    }
