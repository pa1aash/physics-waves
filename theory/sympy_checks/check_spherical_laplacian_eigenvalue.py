"""Check: the horizontal Laplacian of a spherical harmonic returns -n(n+1)/R^2.

Physics. Section 5 of ``theory/derivations.tex`` replaces the horizontal
Laplacian by a number the moment a spherical harmonic is substituted into the
linearised vorticity equation. That single substitution is what turns a partial
differential equation into an algebraic dispersion relation, so the eigenvalue

    nabla^2 Y_n^m = -n(n+1)/R^2 * Y_n^m

is load-bearing: it is the reason the Rossby-Haurwitz angular phase speed
depends on the total degree ``n`` alone and not on the zonal order ``m``. The
physical reading is that ``n(n+1)/R^2`` is the squared total wavenumber of the
mode on a sphere of radius ``R`` -- the spherical replacement for the plane
wave's ``k^2 + l^2`` -- and modes of the same ``n`` share a horizontal scale
however that scale is partitioned between the zonal and meridional directions.

What is checked.

1. Symbolically, for several small ``(n, m)``: build ``Y_n^m`` explicitly as
   ``P_n^m(sin phi) exp(i m lambda)``, apply the spherical Laplacian written in
   its metric form

       nabla^2 = 1/(R^2 cos^2 phi) d^2/dlambda^2
               + 1/(R^2 cos phi) d/dphi ( cos phi d/dphi )

   and confirm the result is exactly ``-n(n+1)/R^2`` times the original, with a
   symbolically zero residual (not a numerically small one).

2. Numerically, over a broader range of ``(n, m)``: with ``mu = sin phi`` the
   operator reduces to the associated Legendre operator, so the check becomes

       d/dmu[(1 - mu^2) dP/dmu] - m^2 P/(1 - mu^2) + n(n+1) P = 0

   evaluated with exact derivatives at Gauss-Legendre nodes, normalised by the
   size of the individual terms so the tolerance means something.

Run: ``python theory/sympy_checks/check_spherical_laplacian_eigenvalue.py``
Prints VERIFIED or MISMATCH and exits non-zero on MISMATCH.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import sympy as sp
from scipy.special import assoc_legendre_p_all, roots_legendre

# Relative tolerance for the numerical arm. The residual is normalised by the
# largest individual term in the identity, so this is a genuine relative error
# and not an absolute one that a small-amplitude mode could pass trivially.
NUMERIC_RTOL = 1e-9

SYMBOLIC_CASES = [(1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (3, 1), (3, 3), (4, 2)]
NUMERIC_MAX_DEGREE = 40


def spherical_laplacian(expr, lam, phi, R):
    """Horizontal Laplacian on a sphere of radius ``R``, latitude ``phi``."""
    zonal = sp.diff(expr, lam, 2) / (R**2 * sp.cos(phi) ** 2)
    meridional = sp.diff(sp.cos(phi) * sp.diff(expr, phi), phi) / (R**2 * sp.cos(phi))
    return zonal + meridional


def symbolic_arm() -> list[tuple[int, int, bool, sp.Expr]]:
    lam, phi, R = sp.symbols("lambda phi R", real=True, positive=False)
    R = sp.Symbol("R", positive=True)
    results = []
    for n, m in SYMBOLIC_CASES:
        Y = sp.assoc_legendre(n, m, sp.sin(phi)) * sp.exp(sp.I * m * lam)
        residual = sp.simplify(
            spherical_laplacian(Y, lam, phi, R) + sp.Rational(n * (n + 1)) * Y / R**2
        )
        results.append((n, m, residual == 0, residual))
    return results


def numeric_arm() -> tuple[float, int, int]:
    """Return (worst relative residual, argmax n, argmax m) over the sweep."""
    # Gauss-Legendre nodes in mu = sin(phi); they avoid the poles exactly, where
    # the 1/(1 - mu^2) factor of the operator is singular for m != 0.
    mu, _ = roots_legendre(256)
    nmax = NUMERIC_MAX_DEGREE
    worst, worst_n, worst_m = 0.0, -1, -1

    for m in range(0, 9):
        # shape (3, nmax+1, 2m+1, len(mu)): derivative order, degree, order, node
        table = assoc_legendre_p_all(nmax, m, mu, norm=True, diff_n=2)
        for n in range(max(m, 1), nmax + 1):
            P = table[0, n, m]
            dP = table[1, n, m]
            d2P = table[2, n, m]
            t1 = (1.0 - mu**2) * d2P
            t2 = -2.0 * mu * dP
            t3 = -(m**2) * P / (1.0 - mu**2)
            t4 = n * (n + 1) * P
            residual = t1 + t2 + t3 + t4
            scale = np.max(np.abs([t1, t2, t3, t4]))
            rel = float(np.max(np.abs(residual)) / scale)
            if rel > worst:
                worst, worst_n, worst_m = rel, n, m
    return worst, worst_n, worst_m


def main() -> int:
    lines: list[str] = []
    ok = True

    lines.append("check_spherical_laplacian_eigenvalue")
    lines.append("=" * 60)
    lines.append("Claim: nabla^2 Y_n^m = -n(n+1)/R^2 Y_n^m on a sphere of radius R.")
    lines.append("")
    lines.append("Arm 1 - symbolic, exact zero residual required")
    lines.append("-" * 60)
    for n, m, passed, residual in symbolic_arm():
        status = "exact zero" if passed else f"NONZERO: {residual}"
        lines.append(f"  (n, m) = ({n}, {m}):  residual {status}")
        ok = ok and passed

    lines.append("")
    lines.append("Arm 2 - numeric, associated Legendre operator form")
    lines.append("-" * 60)
    worst, wn, wm = numeric_arm()
    lines.append(f"  degrees swept: 1 <= n <= {NUMERIC_MAX_DEGREE}, orders 0 <= m <= 8")
    lines.append("  nodes: 256 Gauss-Legendre points in mu = sin(phi)")
    lines.append(f"  worst relative residual: {worst:.3e} at (n, m) = ({wn}, {wm})")
    lines.append(f"  tolerance: {NUMERIC_RTOL:.1e}")
    numeric_ok = worst < NUMERIC_RTOL
    ok = ok and numeric_ok

    lines.append("")
    verdict = "VERIFIED" if ok else "MISMATCH"
    lines.append(f"VERDICT: {verdict}")
    if not ok:
        lines.append("  A failing arm is shown above with its discrepancy.")

    report = "\n".join(lines) + "\n"
    print(report, end="")

    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    (out / (Path(__file__).stem + ".txt")).write_text(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
