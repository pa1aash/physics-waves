"""Check: the divergent (Hough) eigenfrequencies reduce to Rossby-Haurwitz as eps -> 0.

Physics. Section 6 keeps the free surface that section 5 threw away. A column can
now change its depth, so material conservation of ``q = (zeta + f)/h`` no longer
forces the whole planetary-vorticity change onto the relative vorticity: some of
it is absorbed by vortex stretching instead. That dilutes the restoring
mechanism, so the wave slows. Lamb's parameter

    eps = 4 Omega^2 R^2 / (g H) = (R / L_d)^2 ,   L_d = sqrt(gH) / (2 Omega)

is the single number that sets how much of the potential-vorticity budget the
surface can take. In the nondimensional continuity equation ``eps`` multiplies
the surface-height tendency outright, so ``eps -> 0`` means the surface cannot
store any divergence at all: the flow becomes nondivergent and section 5's answer
must be recovered *exactly*. That limit is the validation target for extension B,
and it is stronger than a published table because it is a closed form the project
derives independently.

What is checked. The linearised divergent system on the sphere, written as a
genuine linear eigenvalue problem in the spectral variables
(vorticity, divergence, surface height) at fixed zonal order ``m``:

    d_tau zeta  =  (i m / Lam) zeta  -  B delta
    d_tau delta =   B zeta  +  (i m / Lam) delta  +  (Lam / sqrt(eps)) eta
    d_tau eta   = -delta / sqrt(eps)

with ``tau = 2 Omega t``, ``Lam_n = n(n+1)``, and the coupling matrix
``B = M - D Lam^{-1}`` built from the two Legendre matrix elements

    M_{n n'} = <P_n, mu P_n'> ,     D_{n n'} = <P_n, (1 - mu^2) dP_n'/dmu> .

Setting ``delta = eta = 0`` leaves the diagonal system whose eigenvalues are
exactly ``sigma = -m/[n(n+1)]``, i.e. section 5. The script therefore does not
assume the limit; it solves the full divergent problem and measures how the
Rossby branch approaches it.

Arms:

1. The Legendre matrix elements agree with their closed-form recurrences, and
   satisfy the adjoint identity ``D^T = -D + 2M`` forced by integration by parts.
2. Truncation convergence: the answer at fixed ``eps`` stops moving as the
   spectral truncation ``N`` is raised.
3. The ``eps -> 0`` sweep: the error ``|sigma(eps) - sigma_0|`` is fitted against
   ``eps`` on a log-log scale and the *convergence rate* reported, not merely a
   pass/fail at one small value.
4. A physically relevant readout at Earth's ``eps`` (about 8.8 for H = 10 km):
   how much the free surface actually slows the wave. That number is the
   quantitative content of hypothesis H5.

Run: ``python theory/sympy_checks/check_hough_epsilon_limit.py``
Prints VERIFIED or MISMATCH and exits non-zero on MISMATCH.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.special import assoc_legendre_p_all, roots_legendre

# --- tolerances, stated once so the review document can quote them ------------
# Arm 1: closed-form recurrences vs. quadrature. Machine-precision claim.
MATRIX_ATOL = 1e-12
# Arm 2: relative change in sigma when the truncation is doubled.
TRUNCATION_RTOL = 1e-10
# Arm 3: the fitted log-log convergence rate must lie in this window. The
# expected behaviour is first order (rate 1): the leading divergent correction
# to the Rossby frequency enters at O(eps), as the equivalent-barotropic form
# sigma ~ -m/(Lam + eps) already suggests.
RATE_WINDOW = (0.90, 1.10)
# Arm 3: the smallest-eps error must actually be small in absolute terms too,
# so a clean power law through large errors cannot pass on rate alone.
SMALLEST_EPS_RTOL = 1e-5

EPS_SWEEP = [1e-2, 1e-3, 1e-4, 1e-5, 1e-6]
EPS_EARTH = 4 * (7.292e-5) ** 2 * (6.37122e6) ** 2 / (9.80616 * 1.0e4)


def legendre_matrices(m: int, nmax: int):
    """Return (M, D, degrees) for orders n = m..nmax at zonal order m.

    ``M[i, j] = <P_ni, mu P_nj>`` and ``D[i, j] = <P_ni, (1 - mu^2) dP_nj/dmu>``
    computed by Gauss-Legendre quadrature in ``mu = sin(phi)``. Both integrands
    are polynomials of degree at most ``2*nmax + 1``, so the quadrature is exact.
    """
    nq = nmax + 8
    mu, w = roots_legendre(nq)
    table = assoc_legendre_p_all(nmax, m, mu, norm=True, diff_n=1)

    degrees = np.arange(m, nmax + 1)
    P = np.array([table[0, n, m] for n in degrees])
    dP = np.array([table[1, n, m] for n in degrees])

    # Normalise to unit L2 norm on mu in [-1, 1] whatever convention scipy uses.
    norms = np.sqrt((P**2 * w).sum(axis=1))
    P = P / norms[:, None]
    dP = dP / norms[:, None]

    M = (P * w) @ (mu * P).T
    D = (P * w) @ ((1.0 - mu**2) * dP).T
    return M, D, degrees


def closed_form_matrices(m: int, nmax: int):
    """Closed-form recurrence values, for the arm-1 cross-check.

    mu P_n           =  e_{n+1} P_{n+1} + e_n P_{n-1}
    (1-mu^2) dP_n    = -n e_{n+1} P_{n+1} + (n+1) e_n P_{n-1}
    with e_n = sqrt((n^2 - m^2) / (4 n^2 - 1)).
    """
    degrees = np.arange(m, nmax + 1)
    size = len(degrees)
    M = np.zeros((size, size))
    D = np.zeros((size, size))

    def e(n):
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
    """Assemble A with d_tau x = A x for x = (zeta, delta, eta)."""
    M, D, degrees = legendre_matrices(m, nmax)
    lam = degrees * (degrees + 1.0)
    B = M - D / lam[None, :]

    size = len(degrees)
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


def spectrum(m: int, nmax: int, eps: float):
    """All eigenfrequencies sigma of the divergent system at this eps."""
    A, _ = build_operator(m, nmax, eps)
    # d_tau x = A x with x ~ exp(-i sigma tau) gives A x = -i sigma x,
    # hence sigma = i * eigenvalue.
    return 1j * np.linalg.eigvals(A)


def rossby_frequencies(m: int, nmax: int, eps: float, targets):
    """Return sigma for the Rossby-branch mode nearest each target degree.

    Valid only while the branches are well separated, i.e. at small eps. For
    larger eps use ``track_rossby_mode``, which follows the branch continuously
    from a small-eps starting point where the labelling is unambiguous.
    """
    sigma = spectrum(m, nmax, eps)
    out = {}
    for n in targets:
        expected = -m / (n * (n + 1.0))
        idx = int(np.argmin(np.abs(sigma - expected)))
        out[n] = sigma[idx]
    return out


def track_rossby_mode(m: int, n: int, eps_target: float, nmax: int, steps: int = 60):
    """Follow one Rossby branch from eps = 1e-6 up to ``eps_target``.

    At eps = 1e-6 the Rossby and gravity branches are separated by five orders of
    magnitude in frequency, so the mode of degree ``n`` is identified without
    ambiguity as the eigenvalue nearest ``-m/[n(n+1)]``. The branch is then
    followed by nearest-neighbour matching along a geometric sequence in eps.
    Continuation, rather than nearest-frequency matching at the target eps, is
    required because by Earth's eps (about 8.8) the Rossby frequencies of
    neighbouring degrees have moved close enough together that a bare nearest
    match assigns one eigenvalue to two different degrees.
    """
    eps_start = 1e-6
    if eps_target <= eps_start:
        return rossby_frequencies(m, nmax, eps_target, [n])[n]
    ladder = np.geomspace(eps_start, eps_target, steps)
    current = rossby_frequencies(m, nmax, ladder[0], [n])[n]
    for eps in ladder[1:]:
        sigma = spectrum(m, nmax, eps)
        current = sigma[int(np.argmin(np.abs(sigma - current)))]
    return current


def main() -> int:
    lines: list[str] = []
    ok = True
    lines.append("check_hough_epsilon_limit")
    lines.append("=" * 72)
    lines.append("Claim: the divergent (Laplace tidal / Hough) eigenfrequencies converge")
    lines.append("to sigma = -m/[n(n+1)] as Lamb's parameter eps -> 0.")
    lines.append("")

    # ---- Arm 1 ------------------------------------------------------------
    lines.append("Arm 1 - Legendre matrix elements: quadrature vs. closed form")
    lines.append("-" * 72)
    worst_m, worst_d, worst_adj = 0.0, 0.0, 0.0
    for m in (1, 2, 3, 5):
        Mq, Dq, _ = legendre_matrices(m, 30)
        Mc, Dc, _ = closed_form_matrices(m, 30)
        worst_m = max(worst_m, float(np.max(np.abs(Mq - Mc))))
        worst_d = max(worst_d, float(np.max(np.abs(Dq - Dc))))
        worst_adj = max(worst_adj, float(np.max(np.abs(Dq.T + Dq - 2 * Mq))))
    lines.append(f"  max |M_quadrature - M_recurrence| : {worst_m:.3e}")
    lines.append(f"  max |D_quadrature - D_recurrence| : {worst_d:.3e}")
    lines.append(f"  max |D^T + D - 2M| (adjoint identity): {worst_adj:.3e}")
    lines.append(f"  tolerance: {MATRIX_ATOL:.1e}")
    arm1 = max(worst_m, worst_d, worst_adj) < MATRIX_ATOL
    ok = ok and arm1

    # ---- Arm 2 ------------------------------------------------------------
    lines.append("")
    lines.append("Arm 2 - spectral truncation convergence (m = 1, eps = 1e-3)")
    lines.append("-" * 72)
    targets = [2, 3, 4, 5]
    prev = None
    worst_trunc = 0.0
    for nmax in (20, 40, 80):
        got = rossby_frequencies(1, nmax, 1e-3, targets)
        if prev is not None:
            rel = max(abs(got[n] - prev[n]) / abs(prev[n]) for n in targets)
            worst_trunc = max(worst_trunc, float(rel))
            lines.append(f"  N = {nmax:3d}: max relative change from previous N: {rel:.3e}")
        else:
            lines.append(f"  N = {nmax:3d}: baseline")
        prev = got
    lines.append(f"  tolerance: {TRUNCATION_RTOL:.1e}")
    arm2 = worst_trunc < TRUNCATION_RTOL
    ok = ok and arm2

    # ---- Arm 3 ------------------------------------------------------------
    lines.append("")
    lines.append("Arm 3 - the eps -> 0 sweep and its convergence rate")
    lines.append("-" * 72)
    nmax = 60
    arm3 = True
    for m in (1, 2):
        lines.append(f"  zonal order m = {m}")
        for n in (2, 3, 5):
            sigma0 = -m / (n * (n + 1.0))
            errs = []
            for eps in EPS_SWEEP:
                s = rossby_frequencies(m, nmax, eps, [n])[n]
                errs.append(abs(s - sigma0) / abs(sigma0))
            slope, _ = np.polyfit(np.log(EPS_SWEEP), np.log(errs), 1)
            in_window = RATE_WINDOW[0] <= slope <= RATE_WINDOW[1]
            small_ok = errs[-1] < SMALLEST_EPS_RTOL
            arm3 = arm3 and in_window and small_ok
            lines.append(
                f"    n = {n}: sigma_0 = {sigma0:+.8f}   "
                f"rel. err {errs[0]:.2e} (eps=1e-2) -> {errs[-1]:.2e} (eps=1e-6)"
            )
            lines.append(
                f"           fitted convergence rate d(log err)/d(log eps) = "
                f"{slope:.4f}   "
                f"[{'in' if in_window else 'OUTSIDE'} window "
                f"{RATE_WINDOW[0]}-{RATE_WINDOW[1]}]"
            )
    lines.append("")
    lines.append("  Rate ~ 1 is the expected physics: the divergent correction enters at")
    lines.append("  first order in eps, the surface absorbing a share of the PV budget")
    lines.append("  proportional to how compliant it is.")
    lines.append(f"  tolerance on the smallest-eps error: {SMALLEST_EPS_RTOL:.1e}")
    ok = ok and arm3

    # ---- Arm 4 ------------------------------------------------------------
    lines.append("")
    lines.append("Arm 4 - readout at Earth's Lamb parameter (hypothesis H5)")
    lines.append("-" * 72)
    lines.append(
        f"  eps_Earth = 4 Omega^2 R^2 / (g H) = {EPS_EARTH:.4f} "
        f"for H = 10 km, i.e. R / L_d = {np.sqrt(EPS_EARTH):.3f}"
    )
    lines.append("  Branches followed by continuation from eps = 1e-6 (see" " track_rossby_mode).")
    lines.append("")
    lines.append("   m   n   nondivergent      Hough        slowing    -m/(Lam+eps)")
    arm4_monotone = True
    for m in (1, 2):
        for n in (2, 3, 5, 8):
            if n < m:
                continue
            lam = n * (n + 1.0)
            sigma0 = -m / lam
            s = track_rossby_mode(m, n, EPS_EARTH, 60)
            frac = (abs(s.real) - abs(sigma0)) / abs(sigma0) * 100.0
            eqbt = -m / (lam + EPS_EARTH)
            arm4_monotone = arm4_monotone and (abs(s.real) < abs(sigma0))
            lines.append(
                f"  {m:2d}  {n:2d}   {sigma0:+.6f}     {s.real:+.6f}   "
                f"{frac:+7.2f}%     {eqbt:+.6f}"
            )
    lines.append("")
    lines.append("  Every mode is slowed, and the fractional slowing is largest at low n")
    lines.append("  -- the largest scales, closest to the deformation radius. This is H5")
    lines.append("  as a curve rather than as an assertion.")
    lines.append("  The last column is the equivalent-barotropic estimate -m/(Lam + eps),")
    lines.append("  shown for orientation only: it captures the sense and rough size of")
    lines.append("  the effect but is not the Hough answer, which is what the project")
    lines.append("  actually validates against.")
    lines.append(
        f"  every listed mode slowed by the free surface: "
        f"{'yes' if arm4_monotone else 'NO -- unexpected, inspect'}"
    )
    lines.append("  (Arm 4 is a physical readout, not a pass/fail gate.)")

    lines.append("")
    lines.append(f"VERDICT: {'VERIFIED' if ok else 'MISMATCH'}")
    if not ok:
        lines.append(f"  arm1={arm1}  arm2={arm2}  arm3={arm3}  (see the failing arm above)")

    report = "\n".join(lines) + "\n"
    print(report, end="")

    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    (out / (Path(__file__).stem + ".txt")).write_text(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
