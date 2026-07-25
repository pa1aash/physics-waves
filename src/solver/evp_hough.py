"""Hough-mode eigenfrequencies of the divergent shallow-water system (extension B).

Physics first. Section 5 of ``theory/derivations.tex`` throws the free surface
away and gets the Rossby-Haurwitz answer: a wave of total degree ``n`` drifts west
at angular speed ``-2 Omega / [n(n+1)]``, full stop. This module puts the surface
back. A fluid column can now change its depth, so material conservation of
``q = (zeta + f)/h`` no longer forces the whole planetary-vorticity change onto
relative vorticity — part of it goes into vortex stretching instead. That dilutes
the restoring mechanism, and **the wave slows**.

How much it slows is set by one number, Lamb's parameter

    eps = 4 Omega^2 R^2 / (g H) = (R / L_d)^2 ,

about 8.80 for a 10 km layer on Earth. In the nondimensional continuity equation
``eps`` multiplies the surface-height tendency outright, so ``eps -> 0`` means the
surface stores no divergence at all and section 5's answer must come back
*exactly*. That limit is this module's validation target, and it is a stronger one
than a published table because the project derives it independently.

**The formulation.** At fixed zonal order ``m``, in spectral variables
(vorticity, divergence, surface height) with ``tau = 2 Omega t``,

    d_tau zeta  =  (i m / Lam) zeta  -  B delta
    d_tau delta =   B zeta  +  (i m / Lam) delta  +  (Lam / sqrt(eps)) eta
    d_tau eta   = -delta / sqrt(eps)

with ``Lam_n = n(n+1)`` and the Coriolis coupling ``B = M - D Lam^{-1}`` built
from two Legendre matrix elements. Setting ``delta = eta = 0`` leaves a diagonal
system with eigenvalues exactly ``-m/[n(n+1)]``. This is the same operator that
``theory/sympy_checks/check_hough_epsilon_limit.py`` verifies; this module is its
production form, and ``tests/test_solver_core.py`` checks the two agree rather
than trusting that they do.

**Mode identification is the hard part, and nearest-frequency matching fails.**
By Earth's ``eps`` the Rossby frequencies of neighbouring degrees have moved close
enough together that matching an eigenvalue to the degree whose nondivergent
frequency it is nearest assigns one eigenvalue to two different degrees — and
reports a mode as *faster* than its nondivergent value, which is physically
impossible here. :func:`track_rossby_mode` instead starts at ``eps = 1e-6``, where
the Rossby and gravity branches are five orders of magnitude apart and the
labelling is unambiguous, and follows each branch continuously. That correction is
recorded in ``theory/derivations.tex`` §6 and is not optional.

**Sectoral modes are a genuine special case**, not an artefact. A mode with
``n = m`` sits at the bottom of its degree ladder and has one Coriolis coupling
partner instead of two, so it is slowed markedly less than its neighbours. §6.5 of
the derivation establishes this causally; the sweep here reports it, and the
``sectoral`` flag in the output marks the rows it applies to.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from src.solver import harness

REPO_ROOT = Path(__file__).resolve().parents[2]
EPS_CONTINUATION_START = 1.0e-6
CONTINUATION_STEPS = 60


def legendre_matrices(m: int, nmax: int):
    """The two Legendre matrix elements at zonal order ``m``, in closed form.

        M[n', n] = <P_n', mu P_n>            (mu = sin(latitude), so f = 2 Omega mu)
        D[n', n] = <P_n', (1 - mu^2) dP_n/dmu>

    Both follow from the standard recurrences

        mu P_n         =  e_{n+1} P_{n+1} + e_n P_{n-1}
        (1-mu^2) dP_n  = -n e_{n+1} P_{n+1} + (n+1) e_n P_{n-1}

    with ``e_n = sqrt((n^2 - m^2)/(4 n^2 - 1))``. The recurrence is used rather
    than quadrature because it is exact and cheaper; the two were checked against
    each other to 1e-12 in ``check_hough_epsilon_limit.py`` arm 1, which is what
    licenses using the faster one here.

    That both matrices are tridiagonal in degree is the physics: on a sphere the
    Coriolis parameter is a single spherical harmonic of degree 1, so it couples a
    mode only to its immediate neighbours on the degree ladder. Everything
    specific about sectoral modes follows from one of those two neighbours not
    existing.
    """
    degrees = np.arange(m, nmax + 1)
    size = degrees.size
    M = np.zeros((size, size))
    D = np.zeros((size, size))

    def e(n: int) -> float:
        if n <= 0 or n < abs(m):
            return 0.0
        return float(np.sqrt((n * n - m * m) / (4.0 * n * n - 1.0)))

    for j, n in enumerate(degrees):
        for i, npr in enumerate(degrees):
            if npr == n + 1:
                M[i, j] = e(n + 1)
                D[i, j] = -n * e(n + 1)
            elif npr == n - 1:
                M[i, j] = e(n)
                D[i, j] = (n + 1) * e(n)
    return M, D, degrees


def build_operator(m: int, nmax: int, eps: float):
    """Assemble ``A`` with ``d_tau x = A x`` for ``x = (zeta, delta, eta)``."""
    M, D, degrees = legendre_matrices(m, nmax)
    lam = degrees * (degrees + 1.0)
    B = M - D / lam[None, :]

    size = degrees.size
    Z = np.zeros((size, size))
    diag_im = np.diag(1j * m / lam)
    root = np.sqrt(eps)

    A = np.block(
        [
            [diag_im, -B, Z],
            [B, diag_im, np.diag(lam) / root],
            [Z, -np.eye(size) / root, Z],
        ]
    )
    return A, degrees


def spectrum(m: int, nmax: int, eps: float) -> np.ndarray:
    """Every eigenfrequency ``sigma``, nondimensionalised by ``2 Omega``.

    ``x ~ exp(-i sigma tau)`` turns ``d_tau x = A x`` into ``A x = -i sigma x``,
    so ``sigma = i * eig(A)``. The spectrum holds both the slow Rossby branch and
    the two fast gravity branches; separating them is
    :func:`track_rossby_mode`'s job.
    """
    A, _ = build_operator(m, nmax, eps)
    return 1j * np.linalg.eigvals(A)


def rossby_frequencies(m: int, nmax: int, eps: float, targets) -> dict[int, complex]:
    """Nearest-frequency identification. Valid only at small ``eps`` — see the module docstring."""
    sigma = spectrum(m, nmax, eps)
    return {n: sigma[int(np.argmin(np.abs(sigma - (-m / (n * (n + 1.0))))))] for n in targets}


def track_rossby_mode(
    m: int,
    n: int,
    eps_target: float,
    nmax: int,
    steps: int = CONTINUATION_STEPS,
) -> complex:
    """Follow one Rossby branch from ``eps = 1e-6`` to ``eps_target`` by continuation.

    The derivation verified that the answer is invariant to the length of the
    ladder and agrees with eigenvector-overlap matching, so it is a property of
    the branch and not of the tracking recipe.
    """
    if eps_target <= EPS_CONTINUATION_START:
        return rossby_frequencies(m, nmax, eps_target, [n])[n]
    ladder = np.geomspace(EPS_CONTINUATION_START, eps_target, steps)
    current = rossby_frequencies(m, nmax, ladder[0], [n])[n]
    for eps in ladder[1:]:
        sigma = spectrum(m, nmax, eps)
        current = sigma[int(np.argmin(np.abs(sigma - current)))]
    return current


def lambs_parameter(params: dict) -> float:
    """``eps = 4 Omega^2 R^2 / (g H)``, the square of the radius in deformation radii."""
    return 4 * params["Omega"] ** 2 * params["R"] ** 2 / (params["g"] * params["H"])


def angular_phase_speed(sigma: complex, m: int, Omega_si: float) -> float:
    """Convert a nondimensional frequency to a physical angular phase speed, rad/s.

    ``tau = 2 Omega t``, so a physical frequency is ``2 Omega sigma`` and the
    angular phase speed of a mode of zonal order ``m`` is ``2 Omega sigma / m``.
    Negative means westward — the sign that makes the project's first hypothesis
    falsifiable.
    """
    return float(np.real(sigma)) * 2 * Omega_si / m


def sweep(config: dict) -> dict:
    """Run the full ``(eps, m, n)`` sweep a config asks for.

    Degrees run from ``n = m`` (the sectoral mode) up to ``m + 6``, which covers
    the range the phase-speed campaign simulates and keeps the sectoral case in
    every group, so the comparison against its neighbours is available at every
    ``m``.
    """
    params = config.get("initial_condition_params") or {}
    physical = {k: float(v) for k, v in (config.get("physical") or {}).items()}
    eps_list = [float(x) for x in params["lambs_parameter_range"]]
    orders = [int(x) for x in params["azimuthal_orders"]]
    nmax = int(params["truncation"])
    degrees_per_order = int(params.get("degrees_per_order", 7))

    rows = []
    for eps in eps_list:
        for m in orders:
            for n in range(m, m + degrees_per_order):
                sigma_nd = -m / (n * (n + 1.0))
                sigma = track_rossby_mode(m, n, eps, nmax)
                rows.append(
                    {
                        "eps": eps,
                        "m": m,
                        "n": n,
                        "sectoral": n == m,
                        "sigma_nondivergent": sigma_nd,
                        "sigma_hough_real": float(np.real(sigma)),
                        "sigma_hough_imag": float(np.imag(sigma)),
                        "fractional_slowing": float(np.real(sigma)) / sigma_nd - 1.0,
                        "equivalent_barotropic": -m / (n * (n + 1.0) + eps),
                        "angular_phase_speed_rad_s": angular_phase_speed(
                            sigma, m, physical["Omega"]
                        ),
                    }
                )

    return {
        "run_id": config["run_id"],
        "lambs_parameter_earth": lambs_parameter(physical) if physical else None,
        "truncation": nmax,
        "continuation_start_eps": EPS_CONTINUATION_START,
        "continuation_steps": CONTINUATION_STEPS,
        "rows": rows,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config", nargs="?", default="configs/evp/EVP-hough.yaml")
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
    (out_dir / "hough_modes.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    earth = result["lambs_parameter_earth"]
    print(f"[evp-hough] eps(Earth) = {earth:.4f}; {len(result['rows'])} modes solved")
    print(f"[evp-hough] wrote {out_dir / 'hough_modes.json'}")
    near = [r for r in result["rows"] if abs(r["eps"] - earth) / earth < 0.05]
    if near:
        print("[evp-hough]  m   n   nondivergent      Hough      slowing")
        for r in sorted(near, key=lambda row: (row["m"], row["n"])):
            mark = "  <- sectoral" if r["sectoral"] else ""
            print(
                f"[evp-hough] {r['m']:2d} {r['n']:3d}   {r['sigma_nondivergent']:+.6f}   "
                f"{r['sigma_hough_real']:+.6f}   {100 * r['fractional_slowing']:+7.2f}%{mark}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
