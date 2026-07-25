"""Check: the Rossby-Haurwitz angular phase speed c_ang = -2 Omega / [n(n+1)].

Physics. Section 5 linearises the nondivergent barotropic vorticity equation
about a state of rest and finds that every free mode travels westward at an
angular rate set by the mode's total degree alone. The physical mechanism is
narrow and worth stating precisely: a column pushed poleward finds itself in a
larger planetary vorticity ``f``, and with the column depth fixed, conservation
of ``q`` forces its relative vorticity to fall by the same amount. The resulting
chain of alternating vorticity anomalies induces a meridional velocity field a
quarter wavelength out of phase with the displacement, and that quadrature is
what makes the pattern translate rather than merely oscillate in place. The sign
comes out negative -- westward -- and it is not a convention.

What is checked.

1. That the linearisation about rest of the spherical nondivergent vorticity
   equation is exactly

       d_t (nabla^2 psi) + (2 Omega / R^2) d_lambda psi = 0

   In particular that the beta term ``v df/dy`` collapses to ``(2 Omega/R^2)
   d_lambda psi`` with the ``cos(phi)`` from ``beta = 2 Omega cos(phi)/R``
   cancelling against the ``1/cos(phi)`` in the metric expression for ``v``.
   That cancellation is why the spherical result depends on ``n`` alone.

2. That substituting ``psi = P_n^m(sin phi) exp[i(m lambda - omega t)]`` returns
   ``omega = -2 Omega m / [n(n+1)]``, hence ``c_ang = omega/m =
   -2 Omega/[n(n+1)]``, symbolically and exactly, for a range of (n, m).

3. The sign, derived rather than asserted: the beta-plane companion calculation
   ``zeta' = -beta * eta`` followed by inversion and the kinematic condition
   ``d_t eta = v'`` returns ``c = -beta/k^2 < 0``, and the spherical result is
   shown to be that same expression under the exact identifications
   ``beta = 2 Omega cos(phi)/R`` and ``K^2 = n(n+1)/R^2``.

Run: ``python theory/sympy_checks/check_rh_dispersion.py``
Prints VERIFIED or MISMATCH and exits non-zero on MISMATCH.
"""

from __future__ import annotations

import sys
from pathlib import Path

import sympy as sp

lam, phi, t, x = sp.symbols("lambda phi t x", real=True)
R, Omega = sp.symbols("R Omega", positive=True)
beta, k, eta0 = sp.symbols("beta k eta_0", positive=True)

CASES = [(1, 1), (2, 1), (2, 2), (3, 1), (3, 2), (3, 3), (4, 2), (5, 4), (6, 1)]


def spherical_laplacian(expr):
    cos = sp.cos(phi)
    return sp.diff(expr, lam, 2) / (R**2 * cos**2) + sp.diff(cos * sp.diff(expr, phi), phi) / (
        R**2 * cos
    )


def arm_linearisation(lines):
    """The beta term collapses to (2 Omega/R^2) d_lambda psi."""
    psi = sp.Function("psi")(lam, phi, t)
    cos = sp.cos(phi)

    # Nondivergent flow from a streamfunction, in physical components.
    u = -sp.diff(psi, phi) / R
    v = sp.diff(psi, lam) / (R * cos)
    zeta = (sp.diff(v, lam) - sp.diff(u * cos, phi)) / (R * cos)
    f = 2 * Omega * sp.sin(phi)

    # Full nonlinear barotropic vorticity equation, then drop terms quadratic in
    # the perturbation (u d_lambda zeta and v d_phi zeta). The term
    # u d_lambda f vanishes identically because f has no longitude dependence.
    beta_term = v * sp.diff(f, phi) / R

    # Consistency: zeta from the streamfunction is the spherical Laplacian.
    d_zeta = sp.simplify(zeta - spherical_laplacian(psi))
    ok_zeta = d_zeta == 0
    lines.append(
        "  zeta = nabla^2 psi for the metric streamfunction: "
        f"{'exact zero' if ok_zeta else f'NONZERO {d_zeta}'}"
    )

    d_beta = sp.simplify(beta_term - 2 * Omega * sp.diff(psi, lam) / R**2)
    ok_beta = d_beta == 0
    lines.append(
        "  v df/dy - (2 Omega/R^2) d_lambda psi: "
        f"{'exact zero' if ok_beta else f'NONZERO {d_beta}'}"
    )
    lines.append("  (the cos(phi) of beta cancels the 1/cos(phi) of v -- this is why the")
    lines.append("   spherical phase speed depends on n alone, not on latitude)")
    return ok_zeta and ok_beta


def arm_dispersion(lines):
    ok = True
    omega = sp.Symbol("omega")
    for n, m in CASES:
        psi = sp.assoc_legendre(n, m, sp.sin(phi)) * sp.exp(sp.I * (m * lam - omega * t))
        eq = sp.expand(sp.diff(spherical_laplacian(psi), t) + 2 * Omega * sp.diff(psi, lam) / R**2)
        # Divide out the common non-zero factor psi to leave the algebraic
        # dispersion relation.
        reduced = sp.simplify(sp.cancel(eq / psi))
        sols = sp.solve(sp.Eq(reduced, 0), omega)
        expected = -2 * Omega * m / sp.Integer(n * (n + 1))
        got = sp.simplify(sols[0]) if len(sols) == 1 else None
        passed = got is not None and sp.simplify(got - expected) == 0
        ok = ok and passed
        c_ang = sp.simplify(expected / m)
        lines.append(
            f"  (n, m) = ({n}, {m}): omega = {sp.nsimplify(got)}  "
            f"expected {expected}  -> {'agrees' if passed else 'DISAGREES'}"
        )
        if n == m == 1 or (n, m) == (6, 1):
            lines.append(f"      c_ang = omega/m = {c_ang}   (negative: westward)")
    return ok


def arm_sign(lines):
    """The sign, from the beta-plane displacement argument, and its spherical map."""
    # A chain of meridional displacements eta(x) = eta0 sin(k x). Conservation of
    # q with fixed depth gives zeta' = -beta eta.
    eta = eta0 * sp.sin(k * x)
    zeta_p = -beta * eta

    # Invert: for a purely zonal structure, d^2 psi/dx^2 = zeta', so psi is
    # zeta' divided by -k^2 for this sinusoid.
    psi = sp.simplify(-zeta_p / k**2)
    v_p = sp.diff(psi, x)

    # Kinematic condition d_t eta = v'. For eta = eta0 sin(k(x - c t)) the left
    # side at t = 0 is -c k eta0 cos(k x).
    c = sp.Symbol("c", real=True)
    lhs = -c * k * eta0 * sp.cos(k * x)
    sol = sp.solve(sp.Eq(sp.simplify(lhs - v_p), 0), c)
    c_plane = sp.simplify(sol[0]) if len(sol) == 1 else None
    ok_plane = c_plane is not None and sp.simplify(c_plane + beta / k**2) == 0
    lines.append(
        f"  beta-plane: c = {c_plane}  expected -beta/k^2  -> "
        f"{'agrees' if ok_plane else 'DISAGREES'}"
    )
    lines.append("  beta > 0 and k^2 > 0, so c < 0 unconditionally: westward, not by choice.")

    # Map to the sphere: beta = 2 Omega cos(phi)/R, K^2 = n(n+1)/R^2, and the
    # zonal phase speed of the spherical mode is c_ang * R cos(phi).
    n = sp.Symbol("n", positive=True, integer=True)
    beta_sph = 2 * Omega * sp.cos(phi) / R
    K2 = n * (n + 1) / R**2
    c_from_plane = sp.simplify(-beta_sph / K2)
    c_ang = -2 * Omega / (n * (n + 1))
    c_zonal = sp.simplify(c_ang * R * sp.cos(phi))
    ok_map = sp.simplify(c_from_plane - c_zonal) == 0
    lines.append(f"  spherical: -beta/K^2 = {c_from_plane}, c_ang R cos(phi) = {c_zonal}")
    lines.append(f"  the two agree identically: {'yes' if ok_map else 'NO -- DISAGREEMENT'}")
    return ok_plane and ok_map


def main() -> int:
    lines: list[str] = []
    lines.append("check_rh_dispersion")
    lines.append("=" * 60)
    lines.append("Claim: c_ang = -2 Omega / [n(n+1)] for the nondivergent")
    lines.append("barotropic vorticity equation linearised about rest.")
    lines.append("")
    lines.append("Arm 1 - the linearised equation")
    lines.append("-" * 60)
    ok1 = arm_linearisation(lines)

    lines.append("")
    lines.append("Arm 2 - spherical-harmonic ansatz, solved for omega")
    lines.append("-" * 60)
    ok2 = arm_dispersion(lines)

    lines.append("")
    lines.append("Arm 3 - the sign, derived from the displacement argument")
    lines.append("-" * 60)
    ok3 = arm_sign(lines)

    ok = ok1 and ok2 and ok3
    lines.append("")
    lines.append(f"VERDICT: {'VERIFIED' if ok else 'MISMATCH'}")

    report = "\n".join(lines) + "\n"
    print(report, end="")

    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    (out / (Path(__file__).stem + ".txt")).write_text(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
