"""Error norms of a computed field against an exact solution (blueprint §9.1).

Physics first. A verification norm answers one question and refuses to answer any
other: **is the code solving the intended equations correctly?** It says nothing
about whether those equations describe the atmosphere. Blueprint §10 is where that
second question lives, and conflating the two is the single most common way a
computational-fluids paper overclaims.

The norms measure two different kinds of failure and both are needed. ``l2`` is an
area-weighted root-mean-square: it is dominated by errors that are *large in
aggregate*, so it detects a systematically wrong field and is insensitive to a
single bad grid point. ``l_inf`` is the worst point anywhere on the sphere: it is
dominated by errors that are *large somewhere*, so it detects a local blow-up, a
polar singularity or ringing at a discontinuity, all of which a smoothing integral
would hide. Galewsky, Scott & Polvani (2004) make exactly this point about their
own results — "the global integral in the computation of l2 is a smoothing
operation", and an ``l2`` that looks flat can sit on top of a vorticity field
visibly full of numerical noise.

**The area weight is not optional.** On a Gauss-Legendre colatitude grid the
points cluster near the poles, so an unweighted mean over grid points weights the
polar caps by an enormous factor and reports an error dominated by a region of
negligible physical area. Every integral here is

    I(f) = (1/4 pi) int_0^{2pi} int_{-pi/2}^{pi/2} f cos(phi) d(phi) d(lambda),

Galewsky et al. eq. (5), evaluated by the Gauss-Legendre quadrature the grid was
built for. Williamson et al. (1992) define the same measure in their eqs. (81)-(84)
and the vector form in eq. (97).

**Where the reference comes from matters more than the norm does.** Only three of
this project's cases have an exact solution to compare against: Williamson case 1
(the bell returns to its initial position unchanged after one revolution), case 2
(steady, so the exact solution at every time is the initial condition), and Läuter
Example 3 (unsteady and analytic at any time). For everything else — cases 5 and 6,
the jets — "verification" means comparison against a converged high-resolution run
of the same code, which is a weaker statement and is labelled as such here rather
than quietly presented as the same thing.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.special import roots_legendre

REPO_ROOT = Path(__file__).resolve().parents[2]

# Cases with a genuine analytic solution, and what it is at arbitrary time.
ANALYTIC_CASES = {
    "williamson_1": "initial field, after exactly one revolution",
    "williamson_2": "initial field, at every time (the solution is steady)",
    "lauter": "closed form at any time (precessing solid-body rotation)",
}


def gauss_weights(colatitude: np.ndarray) -> np.ndarray:
    """Quadrature weights in ``mu = cos(theta)`` for the solver's colatitude grid.

    The sphere basis places its colatitude points at the Gauss-Legendre nodes in
    ``mu``, which is what makes the latitudinal transform exact for the
    polynomials it is applied to. The weights are therefore not something to
    approximate — they are recoverable exactly from the node count. This function
    recovers them and then *checks* that the grid it was handed really is that
    grid, because silently applying Gauss-Legendre weights to, say, an equally
    spaced grid would produce a plausible number that is wrong.
    """
    theta = np.asarray(colatitude, dtype=float).ravel()
    mu, w = roots_legendre(theta.size)
    # roots_legendre returns mu ascending; colatitude descends as mu ascends.
    expected = np.arccos(mu[::-1])
    if np.max(np.abs(np.sort(theta) - np.sort(expected))) > 1e-10:
        raise ValueError(
            "colatitude grid is not the Gauss-Legendre grid these weights are for; "
            "error norms on an interpolated or dealiased grid need their own quadrature"
        )
    order = np.argsort(np.argsort(theta))
    return w[::-1][order]


def area_integral(field: np.ndarray, colatitude: np.ndarray) -> float:
    """``I(f)``: the area average over the sphere, Galewsky et al. eq. (5).

    ``field`` has shape ``(n_lon, n_lat)``. Longitude is uniform, so its average is
    a plain mean; colatitude carries the Gauss-Legendre weights, whose sum is 2 and
    which therefore need a factor of one half to give an average rather than an
    integral over ``mu``.
    """
    field = np.asarray(field, dtype=float)
    w = gauss_weights(colatitude)
    zonal_mean = field.mean(axis=0)
    return float(0.5 * np.dot(w, zonal_mean))


def l1(field: np.ndarray, reference: np.ndarray, colatitude: np.ndarray) -> float:
    """Williamson eq. (82): ``I(|f - f_ref|) / I(|f_ref|)``."""
    denom = area_integral(np.abs(reference), colatitude)
    return area_integral(np.abs(field - reference), colatitude) / denom


def l2(field: np.ndarray, reference: np.ndarray, colatitude: np.ndarray) -> float:
    """Williamson eq. (83): ``sqrt(I((f - f_ref)^2)) / sqrt(I(f_ref^2))``.

    The area-weighted relative root-mean-square error, and the norm the
    convergence study of blueprint §9.2 is run on.
    """
    denom = np.sqrt(area_integral(reference**2, colatitude))
    return float(np.sqrt(area_integral((field - reference) ** 2, colatitude)) / denom)


def linf(field: np.ndarray, reference: np.ndarray) -> float:
    """Williamson eq. (84): ``max|f - f_ref| / max|f_ref|``.

    No quadrature: a maximum is a maximum. This is deliberately the one norm that
    does not smooth, so that a single bad point survives into the number.
    """
    return float(np.max(np.abs(field - reference)) / np.max(np.abs(reference)))


def vector_l2(field: np.ndarray, reference: np.ndarray, colatitude: np.ndarray) -> float:
    """Williamson eq. (97), the velocity form of ``l2``.

    Both arguments have shape ``(2, n_lon, n_lat)``. The two components are
    combined *inside* the integral, as the published definition requires — taking
    a norm per component and combining afterwards is a different and slightly
    smaller number, and would not be comparable with the literature.
    """
    field, reference = np.asarray(field, dtype=float), np.asarray(reference, dtype=float)
    diff_sq = ((field - reference) ** 2).sum(axis=0)
    ref_sq = (reference**2).sum(axis=0)
    return float(
        np.sqrt(area_integral(diff_sq, colatitude)) / np.sqrt(area_integral(ref_sq, colatitude))
    )


def vector_linf(field: np.ndarray, reference: np.ndarray) -> float:
    """The velocity form of ``l_inf``: worst pointwise speed error, relative to peak speed."""
    field, reference = np.asarray(field, dtype=float), np.asarray(reference, dtype=float)
    err = np.sqrt(((field - reference) ** 2).sum(axis=0))
    mag = np.sqrt((reference**2).sum(axis=0))
    return float(np.max(err) / np.max(mag))


def error_norms(field, reference, colatitude, *, vector: bool = False) -> dict:
    """All the norms at once, for one field at one time."""
    if vector:
        return {
            "l2": vector_l2(field, reference, colatitude),
            "linf": vector_linf(field, reference),
        }
    return {
        "l1": l1(field, reference, colatitude),
        "l2": l2(field, reference, colatitude),
        "linf": linf(field, reference),
    }


def analytic_reference(config: dict, time_s: float = 0.0):
    """Build the exact solution for a config's case at ``time_s``, on the solver's grid.

    Rebuilt from the initial-condition modules rather than re-derived here, so
    there is exactly one transcription of every published formula in the
    repository. Returns ``(height, velocity, colatitude)`` in working units — the
    same units the run's own output is written in, so no conversion is needed
    before taking a ratio — or raises if the case has no analytic solution.

    For Williamson case 2 the returned field is time-independent, which is the
    whole content of the case: the exact solution *is* the initial condition, for
    all time. For Läuter Example 3 the closed form is evaluated at ``time_s``,
    which is why that case can test time dependence and case 2 cannot.
    """
    from src.solver.equations import build_problem
    from src.solver.initial_conditions import apply_initial_condition
    from src.solver.initial_conditions.common import set_free_surface, set_velocity
    from src.solver.initial_conditions.lauter import analytic_fields

    case = config.get("initial_condition")
    if case not in ANALYTIC_CASES:
        raise ValueError(
            f"case {case!r} has no analytic solution; verify it against a converged "
            f"high-resolution run instead. Analytic cases: {sorted(ANALYTIC_CASES)}"
        )

    swp = build_problem(config)
    if case == "lauter":
        params = config.get("initial_condition_params") or {}
        u_si, v_si, phi_free, _ = analytic_fields(swp, params, t_si=time_s)
        set_velocity(swp, swp.units.velocity(u_si), swp.units.velocity(v_si))
        set_free_surface(swp, phi_free / swp.params["g"])
    else:
        apply_initial_condition(swp, config)

    _, theta = swp.dist.local_grids(swp.basis)
    swp.h.change_scales(1)
    swp.u.change_scales(1)
    return np.array(swp.h["g"]), np.array(swp.u["g"]), np.ravel(theta)
