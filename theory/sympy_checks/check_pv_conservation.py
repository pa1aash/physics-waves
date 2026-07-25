"""Check: the spherical shallow-water equations reduce exactly to Dq/Dt = 0.

Physics. This is the spine of the whole project. A column of fluid carries a
label, its potential vorticity ``q = (zeta + f)/h``, and nothing in the inviscid,
unforced shallow-water system can change that label. Section 1 argues this
physically from Kelvin's circulation theorem plus mass conservation in a column;
section 3 does it again as algebra on the sphere. This script is the audit of the
algebra: if a stray metric term survived anywhere in the vector-invariant
momentum equations or in the flux-form continuity equation, the reduction would
leave a residue, and every downstream result -- the westward propagation of
section 5, the Rayleigh-Kuo criterion of section 8 -- would inherit it.

What is checked. For *arbitrary* fields ``u, v, h`` on the sphere (no wave
ansatz, no linearisation, no assumed symmetry), the exact algebraic identity

    h * Dq/Dt  =  curl(M)  -  q * C

where

    M  = the residual of the vector-invariant momentum equations,
    C  = the residual of the continuity equation,
    curl(M) = 1/(R cos phi) [ d_lambda M_v - d_phi (cos phi * M_u) ] ,

with all operators written in spherical coordinates using the section-2 metric.
The identity is proved by symbolic cancellation, not by assuming the equations
hold: only *after* it is established do we set ``M = 0`` and ``C = 0`` and read
off ``Dq/Dt = 0``. The physical content of the identity is that potential
vorticity is not an extra assumption bolted onto the system -- it is what the
curl of the momentum equation and the continuity equation say jointly.

Three arms:

1. The vorticity equation ``d_t zeta + div[(zeta + f) u] = curl(M)`` follows from
   the momentum equations alone, with no use of continuity.
2. The full identity ``h Dq/Dt = curl(M) - q C`` holds identically.
3. A numerical spot-check on concrete analytic fields, evaluated at pseudo-random
   points, as an independent guard against a simplification that only *appears*
   to vanish.

Run: ``python theory/sympy_checks/check_pv_conservation.py``
Prints VERIFIED or MISMATCH and exits non-zero on MISMATCH.
"""

from __future__ import annotations

import sys
from pathlib import Path

import sympy as sp

lam, phi, t = sp.symbols("lambda phi t", real=True)
R, Omega, g = sp.symbols("R Omega g", positive=True)

NUMERIC_ATOL = 1e-9


def operators(u, v, h):
    """Return the pieces of the spherical shallow-water system."""
    cos = sp.cos(phi)

    def material(A):
        return sp.diff(A, t) + u * sp.diff(A, lam) / (R * cos) + v * sp.diff(A, phi) / R

    def divergence(A_east, A_north):
        return (sp.diff(A_east, lam) + sp.diff(A_north * cos, phi)) / (R * cos)

    def curl(A_east, A_north):
        return (sp.diff(A_north, lam) - sp.diff(A_east * cos, phi)) / (R * cos)

    zeta = curl(u, v)
    f = 2 * Omega * sp.sin(phi)
    K = (u**2 + v**2) / 2
    bernoulli = g * h + K

    # Vector-invariant momentum residuals.
    M_u = sp.diff(u, t) - (zeta + f) * v + sp.diff(bernoulli, lam) / (R * cos)
    M_v = sp.diff(v, t) + (zeta + f) * u + sp.diff(bernoulli, phi) / R

    # Flux-form continuity residual.
    C = sp.diff(h, t) + divergence(h * u, h * v)

    return {
        "material": material,
        "divergence": divergence,
        "curl": curl,
        "zeta": zeta,
        "f": f,
        "M_u": M_u,
        "M_v": M_v,
        "C": C,
    }


def symbolic_arms(lines):
    u = sp.Function("u")(lam, phi, t)
    v = sp.Function("v")(lam, phi, t)
    h = sp.Function("h")(lam, phi, t)

    op = operators(u, v, h)
    zeta, f = op["zeta"], op["f"]
    M_u, M_v, C = op["M_u"], op["M_v"], op["C"]
    curl, divergence, material = op["curl"], op["divergence"], op["material"]

    curl_M = curl(M_u, M_v)

    # Arm 1: the vorticity equation, from the momentum equations alone.
    vort_residual = sp.simplify(
        sp.expand(sp.diff(zeta, t) + divergence((zeta + f) * u, (zeta + f) * v) - curl_M)
    )
    ok1 = vort_residual == 0
    lines.append(
        "  d_t zeta + div[(zeta+f) u] - curl(M) = "
        f"{'0 exactly' if ok1 else f'NONZERO: {vort_residual}'}"
    )

    # Arm 2: the full potential-vorticity identity.
    q = (zeta + f) / h
    identity = sp.simplify(sp.expand(h * material(q) - curl_M + q * C))
    ok2 = identity == 0
    lines.append("  h Dq/Dt - curl(M) + q C = " f"{'0 exactly' if ok2 else f'NONZERO: {identity}'}")

    return ok1 and ok2


def numeric_arm(lines):
    """Independent spot-check with concrete analytic fields."""
    # Smooth, fully three-dimensional test fields with no symmetry to exploit,
    # regular at the poles because every latitude dependence is built from
    # cos(phi) and sin(phi).
    u = 3 * sp.cos(phi) * sp.sin(2 * lam - sp.Rational(1, 3) * t) + sp.cos(phi) ** 2 * sp.cos(
        lam + t
    )
    v = sp.cos(phi) * sp.sin(phi) * sp.cos(3 * lam + sp.Rational(1, 5) * t) + sp.cos(phi) * sp.sin(
        lam
    )
    h = 4 + sp.sin(phi) * sp.cos(lam - t) / 2 + sp.cos(phi) ** 2 / 3

    op = operators(u, v, h)
    zeta, f = op["zeta"], op["f"]
    q = (zeta + f) / h
    expr = h * op["material"](q) - op["curl"](op["M_u"], op["M_v"]) + q * op["C"]

    subs_const = {
        R: sp.Rational(6371220, 1),
        Omega: sp.Rational(7292, 10**8),
        g: sp.Rational(980616, 100000),
    }
    expr = expr.subs(subs_const)

    samples = [
        (sp.Rational(1, 7), sp.Rational(2, 5), sp.Rational(3, 11)),
        (sp.Rational(-9, 4), sp.Rational(-7, 10), sp.Rational(5, 3)),
        (sp.Rational(13, 6), sp.Rational(11, 13), sp.Rational(-2, 7)),
        (sp.Rational(0), sp.Rational(0), sp.Rational(1)),
    ]
    worst = 0.0
    for L, P, T in samples:
        val = complex(expr.subs({lam: L, phi: P, t: T}).evalf(40))
        worst = max(worst, abs(val))
    ok = worst < NUMERIC_ATOL
    lines.append(f"  worst |residual| over 4 sample points: {worst:.3e}")
    lines.append(f"  tolerance: {NUMERIC_ATOL:.1e}")
    return ok


def main() -> int:
    lines: list[str] = []
    lines.append("check_pv_conservation")
    lines.append("=" * 60)
    lines.append("Claim: the spherical shallow-water momentum and continuity equations")
    lines.append("combine algebraically into Dq/Dt = 0 with q = (zeta + f)/h,")
    lines.append("with no unaccounted residual term.")
    lines.append("")
    lines.append("Arms 1-2 - symbolic, arbitrary fields u(lam,phi,t), v(...), h(...)")
    lines.append("-" * 60)
    ok_sym = symbolic_arms(lines)

    lines.append("")
    lines.append("Arm 3 - numeric spot-check on concrete analytic fields")
    lines.append("-" * 60)
    ok_num = numeric_arm(lines)

    ok = ok_sym and ok_num
    lines.append("")
    if ok:
        lines.append("Consequence: setting M = 0 and C = 0 (the equations of motion)")
        lines.append("leaves h Dq/Dt = 0, hence Dq/Dt = 0 for h > 0.")
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
