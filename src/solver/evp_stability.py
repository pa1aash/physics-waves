"""Linear stability eigenvalues about a zonal base state ubar(phi) (extension C).

Physics first. The Rayleigh-Kuo criterion says only what instability is *not*: if
the background absolute-vorticity gradient ``dQ/dy`` never changes sign, no
normal mode can grow. It says nothing about how fast anything grows when the sign
does change, or which zonal wavenumber wins. This module closes that gap by
solving the eigenvalue problem itself, ``theory/derivations.tex`` eq. (genevp):

    [ ubar_a L_m + (1/(R^2 cos phi)) dQ/dphi ] Psi  =  c_a L_m Psi ,

a generalised eigenvalue problem for the complex *angular* phase speed ``c_a`` at
each zonal wavenumber ``m``, whose growth rate is ``sigma(m) = m Im(c_a)`` and
whose eigenfunction is the meridional structure the instability will take.

**There are no boundary conditions, and that is a feature.** The sphere is closed.
What replaces boundaries is regularity at the poles, and the clean way to impose
it is not to impose it at all: expanding ``Psi`` in surface spherical harmonics of
order ``m`` makes every basis function regular by construction. In that basis the
right-hand operator is diagonal and the left needs only two multiplication
matrices, both by Gauss-Legendre quadrature in ``mu = sin(phi)``.

**Spurious modes are guaranteed, and are filtered by resolution doubling.** A
finite discretisation of a problem with a continuous spectrum always produces
eigenvalues that are artefacts of the grid, and for a barotropic jet these
masquerade as weakly growing modes. The filter is to solve at truncation ``N`` and
at ``2N`` and keep only what does not move. At ``N = 240/480`` on the Galewsky jet
this separates cleanly: growth rates for ``m <= 8`` agree to better than
``2e-4`` relative while ``m >= 9`` move by ``1e-3`` or more.

**SCOPE, decided in Session L4b and not to be re-litigated: this problem is
NONDIVERGENT.** The simulations it is compared against are not. Extending the
eigenvalue problem to the full divergent system was investigated and found to be
established ground — Paldor, Shamir & Garfinkel (2020) published exactly that
comparison — so the nondivergent scope is a considered choice, recorded in
``docs/literature/DIVERGENT_STABILITY_DECISION.md``. The consequence must travel
with every number this module produces: **the nondivergent calculation
overestimates growth rates**, one-signed, by an amount those authors measure at
more than 50% for depths of 5-10 km (with the qualification that their jets are
polar and equatorial rather than mid-latitude). A growth rate here is an upper
bound with a known direction of bias, not a prediction to be matched.

**And a normal-mode calculation is not a stability proof.** The operator is
non-normal, so an all-real spectrum forbids a growing normal mode and does not
exclude finite-time transient amplification. :func:`ripa_diagnostics` reports the
one genuinely *sufficient* condition the project has access to — Ripa's (1983) —
alongside, so the distinction is visible in the output rather than only in prose.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import scipy.linalg as sla
from scipy.special import assoc_legendre_p_all, roots_legendre

from src.solver import harness
from src.solver.initial_conditions.galewsky import PHI0, PHI1, UMAX, jet_profile_derivatives

REPO_ROOT = Path(__file__).resolve().parents[2]

# Resolution-doubling filter: a growth rate counts as resolved only if it moves
# by less than this relative amount when the truncation is doubled. The value and
# the N = 240/480 pair are those derivations.tex §9.2 specifies.
PERSIST_RTOL = 1.0e-3
DEFAULT_TRUNCATION = (240, 480)
QUADRATURE_POINTS = 1024


def base_state_fields(lat, profile, R_si: float, Omega_si: float):
    """``(ubar_angular, dQ/dphi)`` for a zonal profile on the given latitudes.

    ``ubar_a = ubar / (R cos phi)`` is the base flow's *angular* velocity, which is
    the quantity the eigenvalue is measured against — on a sphere it is angular
    speeds, not linear ones, that a wave pattern has to match to phase-lock.

    The background absolute-vorticity gradient is written out from
    ``zeta_bar = -u'/R + u tan(phi)/R`` and ``f = 2 Omega sin(phi)``:

        dQ/dphi = 2 Omega cos(phi) - u''/R + u' tan(phi)/R + u/(R cos^2 phi)

    Every one of those four terms is O(1) relative to the others near the jet, and
    the last two are the spherical metric; dropping them is the standard way to
    get a plausible but wrong answer.
    """
    u, du, d2u = profile(lat)
    cos = np.cos(lat)
    ubar_a = u / (R_si * cos)
    dQ = 2 * Omega_si * cos - d2u / R_si + du * np.tan(lat) / R_si + u / (R_si * cos**2)
    return ubar_a, dQ


def stability_evp(
    m: int,
    nmax: int,
    profile,
    R_si: float,
    Omega_si: float,
    nq: int = QUADRATURE_POINTS,
    return_vectors: bool = False,
):
    """Solve eq. (genevp) at zonal order ``m``; return the complex angular phase speeds.

    Galerkin in surface spherical harmonics of order ``m``, so pole regularity is
    built into the basis. ``B = diag(-Lam_n / R^2)`` is the Laplacian, diagonal
    here; ``A = U B + W`` needs the two multiplication matrices
    ``<P_n', ubar_a P_n>`` and ``<P_n', W P_n>`` with
    ``W = (dQ/dphi) / (R^2 cos phi)``.

    ``W`` looks singular at the poles and is not: for any jet of compact support
    ``dQ/dphi -> 2 Omega cos(phi)`` there, and the cosines cancel.
    """
    mu, w = roots_legendre(nq)
    lat = np.arcsin(mu)
    cos = np.cos(lat)

    table = assoc_legendre_p_all(nmax, m, mu, norm=True, diff_n=0)
    degrees = np.arange(m, nmax + 1)
    P = np.array([table[0, n, m] for n in degrees])
    P = P / np.sqrt((P**2 * w).sum(axis=1))[:, None]

    ubar_a, dQ = base_state_fields(lat, profile, R_si, Omega_si)
    W = dQ / (R_si**2 * cos)
    lam = degrees * (degrees + 1.0)

    U = (P * w) @ (ubar_a * P).T
    Wm = (P * w) @ (W * P).T

    B = np.diag(-lam / R_si**2)
    A = U @ B + Wm
    if return_vectors:
        vals, vecs = sla.eig(A, B)
        finite = np.isfinite(vals)
        return vals[finite], vecs[:, finite], degrees
    vals = sla.eig(A, B, right=False)
    return vals[np.isfinite(vals)]


def eigenfunction_on_latitudes(vector, degrees, m: int, lat) -> np.ndarray:
    """Evaluate a spectral eigenvector ``Psi(phi) = sum a_n P_n^m(sin phi)`` on a grid.

    The eigenvectors :func:`stability_evp` returns are coefficients in the same
    normalised associated-Legendre basis the operator was built in, so turning one
    into a meridional profile means summing that series — and it has to be summed
    with *that* normalisation, not a textbook one, or the shape comes out subtly
    wrong. Keeping the evaluation next to the basis that defines it is what stops
    the two from drifting apart.

    Returns the complex profile; its modulus is the disturbance amplitude against
    latitude and its argument is the meridional phase tilt, which is the part that
    carries the momentum flux.
    """
    lat = np.asarray(lat, dtype=float)
    mu = np.sin(lat)
    table = assoc_legendre_p_all(int(np.max(degrees)), m, mu, norm=True, diff_n=0)
    quad_mu, quad_w = roots_legendre(QUADRATURE_POINTS)
    quad_table = assoc_legendre_p_all(int(np.max(degrees)), m, quad_mu, norm=True, diff_n=0)
    profile = np.zeros(lat.shape, dtype=complex)
    for coefficient, n in zip(np.asarray(vector), np.asarray(degrees), strict=True):
        norm = np.sqrt((quad_table[0, n, m] ** 2 * quad_w).sum())
        profile = profile + coefficient * table[0, n, m] / norm
    return profile


def resolved_growth_rate(m: int, profile, R_si: float, Omega_si: float, truncation=None) -> dict:
    """Fastest growth rate at order ``m``, with the resolution-doubling verdict.

    Returns the rate computed at the finer truncation, the relative movement
    between the two, and whether that movement is small enough for the mode to
    count as resolved. An unresolved row is reported, not silently dropped: a
    reader has to be able to see where the discretisation stopped supporting the
    answer.
    """
    n_coarse, n_fine = truncation or DEFAULT_TRUNCATION
    coarse = float(np.max(stability_evp(m, n_coarse, profile, R_si, Omega_si).imag))
    fine_vals = stability_evp(m, n_fine, profile, R_si, Omega_si)
    fine = float(np.max(fine_vals.imag))
    rel = abs(coarse - fine) / max(abs(fine), 1e-30)
    idx = int(np.argmax(fine_vals.imag))
    return {
        "m": m,
        "growth_rate_s": m * fine,
        "c_angular_real_rad_s": float(fine_vals[idx].real),
        "c_angular_imag_rad_s": fine,
        "e_folding_days": (1.0 / (m * fine)) / 86400 if m * fine > 0 else None,
        "truncation_movement": rel,
        "resolved": bool(rel < PERSIST_RTOL),
    }


def ripa_diagnostics(profile, physical: dict, lat=None) -> dict:
    """Ripa's (1983) two *sufficient* conditions for stability, evaluated.

    Everything else in this module is a necessary-condition or a normal-mode
    statement. Ripa's is the one result the project has that can certify a flow
    *stable* — and it is stated for the divergent system, which is the system the
    simulations actually solve. Reporting it beside the eigenvalues keeps the
    logical status of each number visible.

    As read from the abstract (the paper itself is ``ABSTRACT-VERIFIED``, not
    read — see ``docs/literature/RIPA_HAYASHI_YOUNG_NOTES.md``), the conditions
    are

        (i)  (dQ/dy)(c0 - ubar) >= 0 everywhere, for some constant c0
        (ii) |c0 - ubar| <= sqrt(g H) everywhere.

    Condition (i) is the Fjortoft-strengthened classical criterion; (ii) is a
    gravity-wave criticality condition with no nondivergent analogue, which
    disappears as ``sqrt(gH) -> infinity``.

    **The choice of ``c0`` is not free, and choosing it badly turns a certificate
    into a false negative.** Condition (i) is a statement about the *sign* of a
    product, so when ``dQ/dy`` is single-signed it forces ``c0`` outside the range
    of ``ubar`` — above ``max(ubar)`` if ``dQ/dy >= 0``, below ``min(ubar)`` if
    ``dQ/dy <= 0``. Picking the midpoint of the velocity range instead, which is
    the choice that would minimise the burden on condition (ii), puts ``c0``
    *inside* the range and fails (i) for a flow the theorem would otherwise
    certify. So ``c0`` is chosen here to satisfy (i) first, at the boundary value
    that then leaves condition (ii) as much margin as possible. When ``dQ/dy``
    changes sign no constant ``c0`` satisfies (i) at all, and the theorem is
    simply silent.

    **Both must hold to certify stability. Failing them proves nothing** — they
    are sufficient, not necessary. For the Galewsky jet condition (i) fails, so
    Ripa's theorem says nothing about it, and the comfortable margin on condition
    (ii) reported below is *not* evidence of stability.
    """
    if lat is None:
        lat = np.linspace(-np.pi / 2 + 1e-6, np.pi / 2 - 1e-6, 20001)
    u, _, _ = profile(lat)
    _, dQ = base_state_fields(lat, profile, physical["R"], physical["Omega"])
    dQdy = dQ / physical["R"]

    u_max, u_min = float(np.max(u)), float(np.min(u))
    wave_speed = float(np.sqrt(physical["g"] * physical["H"]))

    if bool(np.all(dQdy >= 0)):
        c0, condition_i = u_max, True
    elif bool(np.all(dQdy <= 0)):
        c0, condition_i = u_min, True
    else:
        # No constant c0 makes the product single-signed; report the midpoint so
        # the criticality number is still available, but (i) has failed.
        c0, condition_i = 0.5 * (u_max + u_min), False

    worst = max(abs(c0 - u_max), abs(c0 - u_min))
    condition_ii = bool(worst <= wave_speed)
    return {
        "c0_m_s": c0,
        "c0_choice": (
            "max(ubar)"
            if condition_i and c0 == u_max
            else ("min(ubar)" if condition_i else "midpoint (condition (i) already failed)")
        ),
        "gravity_wave_speed_m_s": wave_speed,
        "max_abs_c0_minus_ubar_m_s": worst,
        "criticality_margin": wave_speed / worst if worst > 0 else float("inf"),
        "pv_gradient_sign_change": bool(np.any(dQdy < 0) and np.any(dQdy > 0)),
        "condition_i_pv_gradient": condition_i,
        "condition_ii_criticality": condition_ii,
        "certifies_stable": condition_i and condition_ii,
        "note": (
            "Sufficient, not necessary. Failure certifies nothing; only the "
            "conjunction of both conditions certifies stability."
        ),
    }


def profile_for_run(run_id: str, configs_root: Path | None = None):
    """Build the base-state profile function named by a run ID.

    The eigenvalue problem is solved about the *same* base states the instability
    campaign integrates, so it reads their configs rather than carrying its own
    copy of the jet parameters. If the two ever drift apart, they drift apart in
    one place.
    """
    configs_root = configs_root or REPO_ROOT / "configs"
    matches = sorted(configs_root.glob(f"*/{run_id}.yaml"))
    if not matches:
        raise FileNotFoundError(f"no config for base state {run_id!r} under {configs_root}")
    config = harness.load_config(matches[0])
    params = config.get("initial_condition_params") or {}
    umax = float(params.get("shear_parameter_S", 1.0)) * float(params.get("umax_reference", UMAX))
    if config.get("initial_condition") == "galewsky":
        umax = float(params.get("umax", UMAX))
    phi0 = float(params.get("phi0", PHI0))
    phi1 = float(params.get("phi1", PHI1))
    physical = {k: float(v) for k, v in (config.get("physical") or {}).items()}

    def profile(lat):
        return jet_profile_derivatives(lat, umax, phi0, phi1)

    return profile, physical, {"run_id": run_id, "umax_m_s": umax}


def solid_body_profile(u0: float):
    """Solid-body rotation, whose ``dQ/dy`` has no sign change at any ``u0``.

    Kept here because it is the negative control: hypothesis H7 as a
    *prohibition*. Every eigenvalue of this base state must come out real, and a
    complex pair would falsify the criterion rather than reveal an instability.
    """

    def profile(lat):
        lat = np.asarray(lat, dtype=float)
        return u0 * np.cos(lat), -u0 * np.sin(lat), -u0 * np.cos(lat)

    return profile


def sweep(config: dict) -> dict:
    """Solve the eigenvalue problem for every base state and order a config names."""
    params = config.get("initial_condition_params") or {}
    orders = [int(x) for x in params["azimuthal_orders"]]
    truncation = params.get("truncation", list(DEFAULT_TRUNCATION))
    truncation = tuple(
        int(x)
        for x in (truncation if isinstance(truncation, list) else [truncation, 2 * truncation])
    )

    results = []
    for run_id in params["base_states"]:
        profile, physical, meta = profile_for_run(run_id)
        rows = [
            resolved_growth_rate(m, profile, physical["R"], physical["Omega"], truncation)
            for m in orders
        ]
        resolved = [r for r in rows if r["resolved"] and r["growth_rate_s"] > 0]
        peak = max(resolved, key=lambda r: r["growth_rate_s"]) if resolved else None
        results.append(
            {
                **meta,
                "physical": physical,
                "modes": rows,
                "m_star": peak["m"] if peak else None,
                "sigma_max_s": peak["growth_rate_s"] if peak else None,
                "e_folding_days": peak["e_folding_days"] if peak else None,
                "ripa": ripa_diagnostics(profile, physical),
            }
        )

    return {
        "run_id": config["run_id"],
        "formulation": "nondivergent barotropic (Session L4b scope decision, Option B)",
        "bias": (
            "Nondivergent modal growth rates overestimate the divergent ones; the "
            "bias is one-signed. See docs/literature/DIVERGENT_STABILITY_DECISION.md."
        ),
        "truncation": list(truncation),
        "persist_rtol": PERSIST_RTOL,
        "base_states": results,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", nargs="?", default="configs/evp/EVP-jet-stability.yaml")
    parser.add_argument("--output-root", default=None)
    args = parser.parse_args(argv)

    config = harness.load_config(args.config)
    result = sweep(config)
    result["git"] = harness.git_record()
    result["environment"] = harness.environment_record()
    result["config_sha256"] = config["_source_sha256"]
    result["finished_utc"] = datetime.now(UTC).isoformat(timespec="seconds")

    root = Path(args.output_root) if args.output_root else REPO_ROOT / "runs"
    out_dir = root / config["run_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "growth_rates.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )

    print(f"[evp-stability] NONDIVERGENT growth rates; truncation {result['truncation']}")
    for base in result["base_states"]:
        ripa = base["ripa"]
        print(
            f"[evp-stability] {base['run_id']:6s} umax={base['umax_m_s']:6.2f} m/s  "
            f"m*={base['m_star']}  sigma={base['sigma_max_s'] or 0:.4e} 1/s  "
            f"e-fold={base['e_folding_days'] or float('nan'):.2f} d  "
            f"Ripa certifies stable: {ripa['certifies_stable']}"
        )
    print(f"[evp-stability] wrote {out_dir / 'growth_rates.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
