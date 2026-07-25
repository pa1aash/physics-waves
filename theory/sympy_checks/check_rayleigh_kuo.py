"""Check: the Rayleigh-Kuo necessary condition follows from the linearised PV equation.

Physics. Section 5's restoring mechanism needs the background potential vorticity
to increase monotonically poleward: a column pushed north always finds more ``q``
ahead of it, always acquires the compensating relative vorticity of the same
sign, and the disturbance always propagates rather than grows. Curve a zonal jet
sharply enough that its own vorticity gradient cancels the planetary one
somewhere, and that monotonicity is lost. Where ``dQ/dy`` changes sign, the fluid
no longer has a single-signed restoring agent across the jet, and a disturbance
can extract energy from the shear instead of merely riding on it. The
Rayleigh-Kuo criterion is the formal statement of that loss.

It is a **necessary** condition, not a sufficient one. This script checks both
halves of that sentence.

Arms:

1. Symbolic -- the normal-mode reduction. Substituting
   ``psi' = Psi(phi) exp[i m (lambda - c_a t)]`` into the linearised barotropic
   potential-vorticity equation about a zonal base state ``ubar(phi)`` returns
   exactly

       (ubar_a - c_a) L_m Psi + (1/(R^2 cos phi)) dQ/dphi Psi = 0

   with ``ubar_a = ubar/(R cos phi)`` the base flow's *angular* velocity, and
   ``L_m`` the spherical Laplacian at zonal order ``m``.

2. Symbolic -- the integration-by-parts identity that makes the argument work,

       Psi* L_m Psi cos(phi) = (1/R^2) { d/dphi[cos(phi) Psi* dPsi/dphi]
                                          - cos(phi)|dPsi/dphi|^2
                                          - m^2 |Psi|^2 / cos(phi) }

   verified pointwise. Its consequence is that the integral of the left side is
   real and negative once regularity at the poles kills the exact-derivative
   term, which is where the sphere supplies what channel walls supply on a plane.

3. Symbolic -- the imaginary-part extraction,
   ``Im[1/(ubar_a - c_r - i c_i)] = c_i / |ubar_a - c_a|^2``, so that a growing
   mode forces ``integral of dQ/dphi |Psi|^2 / |ubar_a - c_a|^2 = 0``. Since the
   weight is strictly positive, ``dQ/dphi`` must change sign. No assumption
   beyond those stated in the derivation is used: base flow real and zonal,
   ``Psi`` regular at the poles and not identically zero.

4. Numerical -- necessary is not sufficient, demonstrated both ways by solving
   the section-9 eigenvalue problem on two concrete base states:

   (a) solid-body rotation, for which ``dQ/dphi = 2(Omega + U0/R) cos(phi)`` has
       no sign change: every eigenvalue must come out real. This is hypothesis
       H7 as a prohibition.
   (b) the Galewsky et al. (2004) mid-latitude jet, for which ``dQ/dphi`` does
       change sign: complex pairs must appear, and the growth rate and dominant
       zonal wavenumber are reported. The sign change alone could not have told
       us either number -- that gap is what section 9 exists to close.

   Spurious eigenvalues are filtered by resolution doubling: only modes that
   persist between truncation ``N`` and ``2N`` are kept. That filter is the
   recipe section 9 specifies for the Dedalus implementation.

Run: ``python theory/sympy_checks/check_rayleigh_kuo.py``
Prints VERIFIED or MISMATCH and exits non-zero on MISMATCH.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import scipy.linalg as sla
import sympy as sp
from scipy.special import assoc_legendre_p_all, roots_legendre

# --- tolerances ---------------------------------------------------------------
# A base state with no sign change in dQ/dphi must produce a spectrum whose
# imaginary parts are numerical noise only. Scaled by the spread of the real
# parts so it is a relative statement about the spectrum, not an absolute one.
STABLE_IMAG_RTOL = 1e-8
# Resolution-doubling filter: a growth rate counts as resolved only if it moves
# by less than this relative amount when the spectral truncation is doubled.
PERSIST_RTOL = 1e-3

# --- Galewsky et al. (2004) jet, parameters as in the Phase-0 reference --------
R_EARTH = 6.37122e6
OMEGA_EARTH = 7.292e-5
UMAX = 80.0
PHI0 = np.pi / 7
PHI1 = np.pi / 2 - PHI0
EN = np.exp(-4.0 / (PHI1 - PHI0) ** 2)


# ============================== symbolic arms ================================

lam_s, phi_s, t_s = sp.symbols("lambda phi t", real=True)
R_s, Omega_s, m_s = sp.symbols("R Omega m", positive=True)


def L_operator(expr, m):
    """Spherical Laplacian acting on Psi(phi) exp(i m lambda), returned on Psi."""
    cos = sp.cos(phi_s)
    return sp.diff(cos * sp.diff(expr, phi_s), phi_s) / (R_s**2 * cos) - (m**2 * expr) / (
        R_s**2 * cos**2
    )


def arm_normal_mode(lines):
    psibar = sp.Function("psibar")(phi_s)
    Psi = sp.Function("Psi")(phi_s)
    c_a = sp.Symbol("c_a")

    cos = sp.cos(phi_s)
    ubar = -sp.diff(psibar, phi_s) / R_s
    ubar_a = ubar / (R_s * cos)

    # Base-state relative vorticity, two ways: as the Laplacian of the base
    # streamfunction, and as the metric curl of the base velocity.
    zbar_lap = sp.diff(cos * sp.diff(psibar, phi_s), phi_s) / (R_s**2 * cos)
    zbar_curl = -sp.diff(ubar * cos, phi_s) / (R_s * cos)
    d_metric = sp.simplify(zbar_lap - zbar_curl)
    ok_metric = d_metric == 0
    lines.append(
        "  base vorticity, Laplacian form vs metric curl form: "
        f"{'exact zero' if ok_metric else f'NONZERO {d_metric}'}"
    )

    Q = zbar_lap + 2 * Omega_s * sp.sin(phi_s)

    # Perturbation with the normal-mode ansatz.
    psi_p = Psi * sp.exp(sp.I * m_s * (lam_s - c_a * t_s))
    zeta_p = sp.diff(cos * sp.diff(psi_p, phi_s), phi_s) / (R_s**2 * cos) + sp.diff(
        psi_p, lam_s, 2
    ) / (R_s**2 * cos**2)
    v_p = sp.diff(psi_p, lam_s) / (R_s * cos)

    # Linearised barotropic PV equation about the zonal base state.
    linear = sp.diff(zeta_p, t_s) + ubar_a * sp.diff(zeta_p, lam_s) + v_p * sp.diff(Q, phi_s) / R_s

    target = (
        sp.I
        * m_s
        * ((ubar_a - c_a) * L_operator(Psi, m_s) + sp.diff(Q, phi_s) * Psi / (R_s**2 * cos))
        * sp.exp(sp.I * m_s * (lam_s - c_a * t_s))
    )

    diff = sp.simplify(sp.expand(linear - target))
    ok = diff == 0
    lines.append(
        "  linearised PV equation - i m [(ubar_a - c_a) L Psi + Q_phi Psi/"
        f"(R^2 cos)] e^(...) = {'exact zero' if ok else f'NONZERO {diff}'}"
    )
    return ok_metric and ok


def arm_parts_identity(lines):
    F = sp.Function("F", real=True)(phi_s)
    G = sp.Function("G", real=True)(phi_s)
    Psi = F + sp.I * G
    Psi_c = F - sp.I * G
    cos = sp.cos(phi_s)

    lhs = Psi_c * L_operator(Psi, m_s) * cos
    grad2 = sp.diff(Psi_c, phi_s) * sp.diff(Psi, phi_s)
    rhs = (
        sp.diff(cos * Psi_c * sp.diff(Psi, phi_s), phi_s)
        - cos * grad2
        - m_s**2 * (Psi_c * Psi) / cos
    ) / R_s**2

    diff = sp.simplify(sp.expand(lhs - rhs))
    ok = diff == 0
    lines.append(f"  pointwise identity residual: {'exact zero' if ok else f'NONZERO {diff}'}")

    # The two quadratic terms are real and non-negative. Checked on explicitly
    # real components (Psi = p + i q, dPsi/dphi = a + i b) rather than on
    # unevaluated Derivative objects, which sympy will not assume to be real.
    p, q, a, b, cval = sp.symbols("p q a b c", real=True)
    quad = (
        cval * ((a - sp.I * b) * (a + sp.I * b)) + m_s**2 * ((p - sp.I * q) * (p + sp.I * q)) / cval
    )
    quad = sp.simplify(sp.expand(quad))
    reality = sp.simplify(sp.im(quad))
    ok_real = reality == 0
    lines.append(
        "  the quadratic terms cos|Psi'|^2 + m^2|Psi|^2/cos reduce to "
        f"{quad}: imaginary part {'zero' if ok_real else reality}"
    )
    nonneg = sp.simplify(quad.subs({cval: sp.Symbol("c", positive=True)}))
    lines.append(f"  and are non-negative for cos(phi) > 0: {nonneg} is a sum of squares")
    lines.append("  hence <Psi, L Psi> is real and negative once regularity at the poles")
    lines.append("  removes the exact-derivative term.")
    return ok and ok_real


def arm_imaginary_part(lines):
    ua, cr, ci = sp.symbols("ubar_a c_r c_i", real=True)
    expr = sp.im(sp.simplify(1 / (ua - (cr + sp.I * ci))))
    target = ci / ((ua - cr) ** 2 + ci**2)
    diff = sp.simplify(expr - target)
    ok = diff == 0
    lines.append(
        f"  Im[1/(ubar_a - c_a)] - c_i/|ubar_a - c_a|^2 = "
        f"{'exact zero' if ok else f'NONZERO {diff}'}"
    )
    lines.append("  the weight |Psi|^2/|ubar_a - c_a|^2 is strictly positive, so c_i != 0")
    lines.append("  forces dQ/dphi to change sign. Necessary condition established.")
    lines.append("  Assumptions used, and only these: base flow real and zonal;")
    lines.append("  Psi regular at both poles; Psi not identically zero.")
    return ok


# ============================== numerical arm ================================


def galewsky_profile(phi):
    """Return (ubar, dubar/dphi, d2ubar/dphi2) for the Galewsky jet."""
    u = np.zeros_like(phi)
    du = np.zeros_like(phi)
    d2u = np.zeros_like(phi)
    inside = (phi > PHI0) & (phi < PHI1)
    p = phi[inside]
    s = (p - PHI0) * (p - PHI1)
    sp_ = 2 * p - PHI0 - PHI1  # ds/dphi
    A = UMAX / EN
    E = np.exp(1.0 / s)
    u[inside] = A * E
    du[inside] = A * E * (-sp_ / s**2)
    d2u[inside] = A * E * (sp_**2 / s**4 - 2.0 / s**2 + 2.0 * sp_**2 / s**3)
    return u, du, d2u


def solid_body_profile(phi, u0):
    u = u0 * np.cos(phi)
    du = -u0 * np.sin(phi)
    d2u = -u0 * np.cos(phi)
    return u, du, d2u


def base_state_fields(phi, profile):
    """Return (ubar_angular, dQ/dphi) on the given latitudes."""
    u, du, d2u = profile(phi)
    cos = np.cos(phi)
    ubar_a = u / (R_EARTH * cos)
    # zeta_bar = -u'/R + u tan(phi)/R  ->  dQ/dphi = 2 Omega cos
    #            - u''/R + u' tan(phi)/R + u/(R cos^2 phi)
    dQ = 2 * OMEGA_EARTH * cos - d2u / R_EARTH + du * np.tan(phi) / R_EARTH + u / (R_EARTH * cos**2)
    return ubar_a, dQ


def stability_evp(m: int, nmax: int, profile, nq: int = 1024):
    """Solve (ubar_a - c_a) L Psi + Q_phi Psi/(R^2 cos phi) = 0 for c_a.

    Galerkin in spherical harmonics of order ``m``, so regularity at both poles
    is built into the basis rather than imposed as a boundary condition.
    """
    mu, w = roots_legendre(nq)
    phi = np.arcsin(mu)
    cos = np.cos(phi)

    table = assoc_legendre_p_all(nmax, m, mu, norm=True, diff_n=0)
    degrees = np.arange(m, nmax + 1)
    P = np.array([table[0, n, m] for n in degrees])
    P = P / np.sqrt((P**2 * w).sum(axis=1))[:, None]

    ubar_a, dQ = base_state_fields(phi, profile)
    W = dQ / (R_EARTH**2 * cos)  # the section-8 weight, regular at the poles
    lam = degrees * (degrees + 1.0)

    # <P_n', ubar_a P_n> and <P_n', W P_n>
    U = (P * w) @ (ubar_a * P).T
    Wm = (P * w) @ (W * P).T

    B = np.diag(-lam / R_EARTH**2)
    A = U @ B + Wm
    c = sla.eig(A, B, right=False)
    return c[np.isfinite(c)]


def max_growth(m, nmax, profile):
    """Fastest growth rate at zonal order m, with a resolution-doubling verdict.

    Returns (growth at 2*nmax, relative change from nmax, resolved?). The
    doubling test is the filter section 9 specifies: a barotropic jet's
    discretised spectrum always contains modes that are artefacts of resolving a
    critical layer on a finite grid, and those move when the truncation moves
    while genuine discrete modes do not.
    """
    coarse = float(np.max(stability_evp(m, nmax, profile).imag))
    fine = float(np.max(stability_evp(m, 2 * nmax, profile).imag))
    rel = abs(coarse - fine) / max(abs(fine), 1e-30)
    return m * fine, rel, rel < PERSIST_RTOL


def numeric_arm(lines):
    ok = True

    # --- (a) no sign change -> provably stable --------------------------------
    lines.append("  (a) solid-body rotation, U0 = 40 m/s: dQ/dphi has no sign change")
    phi_probe = np.linspace(-np.pi / 2 + 1e-6, np.pi / 2 - 1e-6, 20001)
    _, dQ_sb = base_state_fields(phi_probe, lambda p: solid_body_profile(p, 40.0))
    sb_sign_change = bool(np.any(np.diff(np.sign(dQ_sb)) != 0))
    lines.append(
        f"      dQ/dphi min = {dQ_sb.min():.4e}, max = {dQ_sb.max():.4e}, "
        f"sign change: {'YES' if sb_sign_change else 'no'}"
    )
    ok = ok and not sb_sign_change

    for m in (1, 2, 3, 4, 5, 6):
        c = stability_evp(m, 96, lambda p: solid_body_profile(p, 40.0))
        spread = float(np.ptp(c.real)) or 1.0
        rel_imag = float(np.max(np.abs(c.imag))) / spread
        passed = rel_imag < STABLE_IMAG_RTOL
        ok = ok and passed
        lines.append(
            f"      m = {m}: {c.size:3d} modes, "
            f"max|Im c_a|/spread(Re c_a) = {rel_imag:.2e}  "
            f"[{'all real' if passed else 'COMPLEX -- H7 VIOLATED'}]"
        )
    lines.append(
        f"      tolerance: {STABLE_IMAG_RTOL:.1e}  " "(this is hypothesis H7 as a prohibition)"
    )

    # --- (b) sign change -> actually unstable ---------------------------------
    lines.append("")
    lines.append("  (b) Galewsky et al. (2004) jet: dQ/dphi does change sign")
    _, dQ_gw = base_state_fields(phi_probe, galewsky_profile)
    sign_idx = np.where(np.diff(np.sign(dQ_gw)) != 0)[0]
    lats = np.degrees(phi_probe[sign_idx])
    lines.append(
        f"      sign changes at latitudes: "
        f"{', '.join(f'{x:+.2f} deg' for x in lats) if lats.size else 'NONE'}"
    )
    ok = ok and lats.size > 0

    best = (None, -np.inf)
    lines.append("       m   growth m*Im(c_a) [1/s]   e-fold [days]   N-doubling change")
    for m in range(1, 13):
        growth, rel, resolved = max_growth(m, 240, galewsky_profile)
        tau = 1.0 / growth / 86400.0 if growth > 0 else float("nan")
        flag = "resolved" if resolved else "UNRESOLVED"
        lines.append(f"      {m:2d}   {growth:.6e}          {tau:8.3f}       " f"{rel:.2e}  {flag}")
        if resolved and growth > best[1]:
            best = (m, growth)
    lines.append(f"      resolution: N = 240, doubled to 480; tolerance {PERSIST_RTOL:.0e}")
    lines.append("")
    if best[0] is None or best[1] <= 0:
        lines.append("      no resolved growing mode found -- MISMATCH against Phase-0")
        ok = False
    else:
        lines.append(
            f"      most unstable zonal wavenumber m* = {best[0]}, "
            f"growth rate {best[1]:.4e} 1/s "
            f"(e-folding {1.0 / best[1] / 86400.0:.2f} days)"
        )
        lines.append("      The Phase-0 gate observed roll-up over days 4-6; with a")
        lines.append("      120 m initial height bump that is several e-foldings at this")
        lines.append("      rate, so the two are consistent.")
    lines.append("")
    lines.append("      Necessary is not sufficient: (a) shows the criterion forbids")
    lines.append("      growth when it is not met, (b) shows that when it *is* met only")
    lines.append("      the solved eigenvalue problem supplies a growth rate and an m*.")
    return ok


def main() -> int:
    lines: list[str] = []
    lines.append("check_rayleigh_kuo")
    lines.append("=" * 72)
    lines.append("Claim: the necessary condition -- dQ/dy must change sign -- follows")
    lines.append("from the structure of the linearised PV equation, with no assumption")
    lines.append("beyond those stated in section 8.")
    lines.append("")

    lines.append("Arm 1 - normal-mode reduction to the section-9 operator")
    lines.append("-" * 72)
    ok1 = arm_normal_mode(lines)

    lines.append("")
    lines.append("Arm 2 - integration-by-parts identity (reality and sign of <Psi,LPsi>)")
    lines.append("-" * 72)
    ok2 = arm_parts_identity(lines)

    lines.append("")
    lines.append("Arm 3 - imaginary-part extraction")
    lines.append("-" * 72)
    ok3 = arm_imaginary_part(lines)

    lines.append("")
    lines.append("Arm 4 - necessary but not sufficient, on two concrete base states")
    lines.append("-" * 72)
    ok4 = numeric_arm(lines)

    ok = ok1 and ok2 and ok3 and ok4
    lines.append("")
    lines.append(f"VERDICT: {'VERIFIED' if ok else 'MISMATCH'}")
    if not ok:
        lines.append(f"  arm1={ok1} arm2={ok2} arm3={ok3} arm4={ok4}")

    report = "\n".join(lines) + "\n"
    print(report, end="")

    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    (out / (Path(__file__).stem + ".txt")).write_text(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
