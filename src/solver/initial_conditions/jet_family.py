"""Parameterised zonal-jet base states for the instability campaign (blueprint §8.3).

Physics first. The instability campaign asks two questions the Galewsky anchor
alone cannot answer: *how much shear does a jet need before it goes unstable*
(runs I-01 to I-05), and *how much does rotation suppress that instability* (runs
I-06 to I-09). Both need a one-parameter family of jets, not a single jet, so that
one thing varies at a time.

**The family, and the fact that it is the project's own choice.** The shape is
taken from Galewsky, Scott & Polvani (2004) eq. (2) — compactly supported and
infinitely differentiable, for the reasons set out in ``galewsky.py`` — and only
the amplitude is varied:

    ubar(phi ; S) = S * u_Galewsky(phi),     S = umax / 80 m/s.

``S = 1`` is therefore the Galewsky jet exactly, which is what makes the anchor
run I-00 the calibration point of the whole ladder. **This scaling is a project
decision, not something read from a paper**, and it is recorded as such: no
source is cited for it, because none defines it. What *is* taken from the
literature is the profile shape and the criterion used to interpret the ladder.

**Why amplitude is the right knob.** The Rayleigh-Kuo diagnostic is

    dQ/dy = beta - d^2 ubar / dy^2,

derived at ``theory/derivations.tex`` eq. (dQdy). The planetary term ``beta`` does
not depend on the jet at all, while the curvature term is exactly linear in ``S``.
So the ladder in ``S`` is a clean ladder in *the ratio of the two terms that
compete in the criterion*, and the critical value can be located in closed form
rather than bracketed by trial and error — see :func:`critical_shear_parameter`.
That is a stronger position than a shape parameter would give, since changing the
width would move ``beta``'s relevance and the curvature together.

**The criterion is necessary, not sufficient.** A sign change in ``dQ/dy`` means
instability is *permitted*, not that it occurs, and the whole point of running the
ladder is to find out where it actually does. ``theory/derivations.tex`` §8.3 and
§9 make that distinction; nothing here should be read as predicting growth.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from src.solver.equations import latitude_grid
from src.solver.initial_conditions.common import (
    balanced_zonal_height,
    set_free_surface,
    set_velocity,
)
from src.solver.initial_conditions.galewsky import (
    PHI0,
    PHI1,
    UMAX,
    height_perturbation,
    jet_profile,
)


def rayleigh_kuo_diagnostic(
    lat: np.ndarray,
    u_si: np.ndarray,
    R_si: float,
    Omega_si: float,
) -> dict:
    """Evaluate ``dQ/dy = beta - d^2 ubar/dy^2`` on a latitude grid.

    The meridional coordinate is arc length ``y = R phi``, so ``d/dy =
    (1/R) d/dphi`` and the curvature carries a ``1/R^2``; the planetary gradient
    is ``beta = df/dy = (2 Omega / R) cos(phi)`` with ``f = 2 Omega sin(phi)``.
    Dropping either metric factor changes the answer by orders of magnitude, so
    they are written out rather than assumed.

    Returns the profile and the minimum, together with whether a sign change
    occurs — the necessary condition of Rayleigh (1880) and Kuo (1949).
    """
    dphi = float(lat[1] - lat[0])
    d2u = np.gradient(np.gradient(u_si, dphi), dphi) / R_si**2
    beta = (2 * Omega_si / R_si) * np.cos(lat)
    dQdy = beta - d2u
    return {
        "lat": lat,
        "dQdy": dQdy,
        "min_dQdy": float(np.min(dQdy)),
        "sign_change": bool(np.any(dQdy < 0)),
    }


def critical_shear_parameter(
    R_si: float,
    Omega_si: float,
    phi0: float = PHI0,
    phi1: float = PHI1,
    umax_ref: float = UMAX,
    n_points: int = 200_001,
) -> float:
    """The smallest ``S`` at which ``dQ/dy`` first changes sign.

    Because the curvature term is linear in ``S`` while ``beta`` is not affected
    by the jet at all, ``dQ/dy(S) = beta - S * c(phi)`` with ``c`` the curvature
    of the reference jet. The condition ``dQ/dy < 0`` somewhere is therefore

        S > min over {phi : c(phi) > 0} of beta(phi) / c(phi),

    an exact expression, not a bracketing search. It is what centres the I-01 to
    I-05 ladder: a ladder that straddles this value measures the transition, while
    one that sits entirely above or below it measures nothing.
    """
    lat = np.linspace(-np.pi / 2, np.pi / 2, n_points)
    dphi = float(lat[1] - lat[0])
    u_ref = jet_profile(lat, umax_ref, phi0, phi1)
    curvature = np.gradient(np.gradient(u_ref, dphi), dphi) / R_si**2
    beta = (2 * Omega_si / R_si) * np.cos(lat)
    # Restrict to curvature that is a meaningful fraction of its own peak. In the
    # jet's exponential tails the curvature underflows towards zero, and dividing
    # beta by a denormal there produces a spurious enormous ratio (and an
    # overflow warning) from a region where the jet does not exist.
    positive = curvature > 1e-12 * curvature.max()
    if not np.any(positive):
        return float("inf")
    return float(np.min(beta[positive] / curvature[positive]))


def idealised_jet(swp, params: dict) -> dict:
    """A balanced zonal jet of the Galewsky shape at shear parameter ``S``.

    ``shear_parameter_S`` scales the peak speed against the 80 m/s anchor. The
    balanced height comes from the same gradient-wind integration Galewsky et al.
    specify, so the unperturbed state is steady at every ``S``; the perturbation
    is theirs too, so a growth rate measured here differs from I-00 only through
    the amplitude of the jet.

    ``omega_multiplier`` is *not* handled here. Rotation is a property of the
    planet, not of the initial condition, and it enters through ``physical.Omega``
    in the config, which is how runs I-06 to I-09 vary it. The multiplier is
    carried in ``initial_condition_params`` only as documentation of intent; the
    harness checks that the two agree rather than letting them drift apart.
    """
    dist, basis, units = swp.dist, swp.basis, swp.units
    phi, lat = latitude_grid(dist, basis)

    S = float(params.get("shear_parameter_S", 1.0))
    umax_ref = float(params.get("umax_reference", UMAX))
    phi0 = float(params.get("phi0", PHI0))
    phi1 = float(params.get("phi1", PHI1))
    umax = S * umax_ref
    mean_depth_si = float(params.get("mean_depth", swp.params["H"]))

    u_si = jet_profile(lat, umax, phi0, phi1)
    set_velocity(swp, units.velocity(u_si), 0.0 * u_si)

    depth_si = balanced_zonal_height(
        swp,
        lambda x: jet_profile(x, umax, phi0, phi1),
        support=(phi0, phi1),
        mean_depth_si=mean_depth_si,
    )

    pert = params.get("perturbation", True)
    pert_params = dict(pert) if isinstance(pert, dict) else {}
    if pert is not False:
        seed = params.get("seed")
        if seed is not None:
            # I-12 varies only the seed. A random height field of the same
            # amplitude as eq. (4)'s bump replaces the deterministic bump, so
            # that "spread across seeds" measures sensitivity of the growth rate
            # to the shape of the disturbance and not merely to its position.
            rng = np.random.default_rng(int(seed))
            amp = float(pert_params.get("h_hat", 120.0))
            noise = rng.standard_normal(np.shape(lat + 0 * phi))
            depth_si = depth_si + amp * np.cos(lat) * noise / np.max(np.abs(noise))
        else:
            depth_si = depth_si + height_perturbation(phi, lat, pert_params)

    mean_depth = set_free_surface(swp, depth_si)

    lat_fine = np.linspace(-np.pi / 2, np.pi / 2, 20_001)
    rk = rayleigh_kuo_diagnostic(
        lat_fine,
        jet_profile(lat_fine, umax, phi0, phi1),
        swp.params["R"],
        swp.params["Omega"],
    )
    return {
        "kind": "shallow_water",
        "mean_depth_m": mean_depth,
        "steady": pert is False,
        "shear_parameter_S": S,
        "jet_umax_m_s": umax,
        "rayleigh_kuo_sign_change": rk["sign_change"],
        "rayleigh_kuo_min_dQdy": rk["min_dQdy"],
        "critical_shear_parameter": critical_shear_parameter(
            swp.params["R"], swp.params["Omega"], phi0, phi1, umax_ref
        ),
    }


def reanalysis_jet(swp, params: dict) -> dict:
    """A balanced jet built from an observed zonal-mean profile (run I-10).

    The observational profile is not produced here. ``src/analysis/
    process_reanalysis.py`` (pipeline stage 9, Session L6) extracts the seasonally
    averaged zonal-mean zonal wind at the jet-core level and writes it as a
    two-column table of latitude and ``ubar``; this function reads that table,
    interpolates it onto the solver grid, and balances it exactly as the idealised
    jet is balanced.

    **Smoothing is not optional and is not cosmetic.** The Rayleigh-Kuo diagnostic
    involves a second derivative, so an unsmoothed reanalysis profile — which
    carries grid-scale noise from a finite-difference archive — produces a
    ``d^2 ubar/dy^2`` dominated by that noise and a sign change that means nothing.
    The smoothing must therefore be applied upstream, where the noise level is
    known, and this function refuses a profile that has not been through it rather
    than smoothing an unknown quantity by an arbitrary amount here.
    """
    profile_path = params.get("profile_path")
    if profile_path is None:
        raise ValueError(
            "reanalysis_jet needs initial_condition_params.profile_path pointing at "
            "the zonal-mean profile written by src/analysis/process_reanalysis.py. "
            "That stage is Session L6; run I-10 cannot execute before it."
        )
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(
            f"zonal-mean profile {path} not found. Generate it with "
            "src/analysis/process_reanalysis.py before running I-10."
        )

    data = np.load(path)
    lat_src, u_src = np.asarray(data["lat"]), np.asarray(data["ubar"])
    if not bool(data.get("smoothed", np.array(False))):
        raise ValueError(
            f"{path} is not marked as smoothed. A second derivative of a raw "
            "reanalysis profile is noise; smooth it upstream, where the noise "
            "level is known, and record the filter in the file."
        )

    dist, basis, units = swp.dist, swp.basis, swp.units
    _, lat = latitude_grid(dist, basis)
    order = np.argsort(lat_src)
    lat_src, u_src = lat_src[order], u_src[order]

    def u_of_lat(x):
        return np.interp(np.asarray(x, dtype=float), lat_src, u_src, left=0.0, right=0.0)

    set_velocity(swp, units.velocity(u_of_lat(lat)), 0.0 * np.asarray(lat))
    depth_si = balanced_zonal_height(swp, u_of_lat, mean_depth_si=swp.params["H"])

    pert = params.get("perturbation", True)
    if pert is not False:
        phi, _ = latitude_grid(dist, basis)
        depth_si = depth_si + height_perturbation(phi, lat, pert if isinstance(pert, dict) else {})
    mean_depth = set_free_surface(swp, depth_si)

    rk = rayleigh_kuo_diagnostic(lat_src, u_src, swp.params["R"], swp.params["Omega"])
    return {
        "kind": "shallow_water",
        "mean_depth_m": mean_depth,
        "steady": pert is False,
        "profile_path": str(path),
        "rayleigh_kuo_sign_change": rk["sign_change"],
        "rayleigh_kuo_min_dQdy": rk["min_dQdy"],
    }
