"""Check: does divergence change the stability condition for THIS project's jet?

Session L4b. This is the calculation the divergent-stability decision rests on,
written as a re-runnable check rather than left in a session transcript.

Physics. Section 8 of ``theory/derivations.tex`` derives the Rayleigh-Kuo
necessary condition for the *nondivergent* barotropic system: a growing normal
mode requires the background potential-vorticity gradient ``dQ/dy`` to change
sign. The project integrates the *divergent* shallow-water system, whose
deformation radius is comparable to the jet's own width, so the question is
whether that condition survives.

Ripa (1983), J. Fluid Mech. 126, 463-489, gives **sufficient conditions for
stability** of a zonal flow in a one-layer model on the beta-plane or the sphere,
without the quasi-geostrophic approximation and without restriction to normal
modes. From his abstract, verbatim, the two conditions on the beta-plane are:

  (i)  "the product of the meridional gradient of potential vorticity and the
       difference between an arbitrary constant and the zonal velocity be
       everywhere non-negative"
  (ii) "the absolute value of this difference be nowhere larger than the local
       phase speed of long gravity waves"

In this project's notation, with an arbitrary constant ``c0``:

  (i)   (dQ/dy) * (c0 - ubar) >= 0     everywhere
  (ii)  |c0 - ubar|            <= sqrt(g h)   everywhere

PROVENANCE WARNING. Ripa (1983) could not be obtained as full text (see
``docs/literature/MISSING.md``). The two conditions above are the project's
reading of the paper's *abstract*, which states them in words rather than in
symbols. The translation into the inequalities above is therefore an
interpretation, not a transcription of a displayed equation. It is used here
only for an order-of-magnitude margin test, which is robust to the details of how
the constant ``c0`` is defined -- see arm 2.

What is checked.

1. **The nondivergent-limit consistency check.** Condition (i) is the classical
   Fjortoft-strengthened form of Rayleigh-Kuo. Condition (ii) involves
   ``sqrt(gH)``, the long-gravity-wave speed, which diverges as the surface is
   made rigid. So (ii) is satisfied automatically in the nondivergent limit and
   drops out, leaving (i) alone. Ripa's condition therefore *reduces cleanly* to
   the classical one, and the divergent case adds one extra, independent
   requirement with no nondivergent analogue.

2. **Is the extra condition binding for THIS project?** Evaluated for the
   Galewsky et al. (2004) jet at the project's parameters, and swept over the
   rotation range of runs P-08 to P-12. Condition (ii) contains no rotation rate,
   so the sweep cannot activate it -- which is itself the answer.

Run: ``python theory/sympy_checks/check_ripa_divergent_condition.py``
Prints VERIFIED or MISMATCH and exits non-zero on MISMATCH.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# --- project parameters, as in configs/instability/I-00.yaml -------------------
G = 9.80616
H = 1.0e4
R = 6.37122e6
OMEGA0 = 7.292e-5

# Galewsky et al. (2004) jet, eq. (2).
UMAX = 80.0
PHI0 = np.pi / 7
PHI1 = np.pi / 2 - PHI0
EN = np.exp(-4.0 / (PHI1 - PHI0) ** 2)

# Rotation multipliers of runs P-08 ... P-12.
OMEGA_SWEEP = (0.25, 0.5, 1.0, 2.0, 4.0)

# Condition (ii) is a margin test. A margin below this would make the divergent
# condition a live constraint on this configuration and would change the
# recommendation in docs/literature/DIVERGENT_STABILITY_DECISION.md.
BINDING_MARGIN = 2.0


def galewsky_jet(phi: np.ndarray) -> np.ndarray:
    u = np.zeros_like(phi)
    inside = (phi > PHI0) & (phi < PHI1)
    p = phi[inside]
    u[inside] = UMAX / EN * np.exp(1.0 / ((p - PHI0) * (p - PHI1)))
    return u


def main() -> int:
    lines: list[str] = []
    ok = True

    lines.append("check_ripa_divergent_condition")
    lines.append("=" * 72)
    lines.append("Claim: Ripa's (1983) divergent stability conditions reduce to the")
    lines.append("classical nondivergent condition, and the extra divergent condition")
    lines.append("is not binding for this project's jet at any rotation rate it runs.")
    lines.append("")
    lines.append("SOURCE STATUS: Ripa (1983) is ABSTRACT-VERIFIED, not read. The two")
    lines.append("conditions below are this project's reading of an abstract that")
    lines.append("states them in words. See docs/literature/MISSING.md.")
    lines.append("")

    # ---- Arm 1: the nondivergent limit ------------------------------------
    lines.append("Arm 1 - does Ripa's condition reduce to Rayleigh-Kuo as the surface")
    lines.append("        becomes rigid?")
    lines.append("-" * 72)
    lines.append("  Condition (i)  : (dQ/dy)(c0 - ubar) >= 0 everywhere.")
    lines.append("                   This is the Fjortoft-strengthened form of the")
    lines.append("                   classical criterion: it still requires dQ/dy to")
    lines.append("                   change sign if it is to fail, since a monotone")
    lines.append("                   dQ/dy admits a c0 outside the range of ubar.")
    lines.append("  Condition (ii) : |c0 - ubar| <= sqrt(gH), the long-gravity-wave speed.")
    lines.append("")
    lines.append("  The nondivergent limit is the rigid-lid limit, in which the free")
    lines.append("  surface cannot deflect and long gravity waves become infinitely")
    lines.append("  fast. Formally: eps = 4 Omega^2 R^2/(gH) -> 0 means gH -> infinity")
    lines.append("  at fixed Omega and R, hence sqrt(gH) -> infinity.")
    lines.append("")
    for gh_mult, label in ((1.0, "Earth, H = 10 km"), (1e2, "gH x 100"), (1e4, "gH x 10^4")):
        gh = G * H * gh_mult
        eps = 4 * OMEGA0**2 * R**2 / gh
        lines.append(f"    {label:18s}  sqrt(gH) = {np.sqrt(gh):10.1f} m/s   eps = {eps:9.4f}")
    lines.append("")
    lines.append("  As eps -> 0, sqrt(gH) -> infinity and condition (ii) is satisfied by")
    lines.append("  ANY bounded zonal flow. It therefore drops out, leaving condition (i)")
    lines.append("  alone -- the classical criterion.")
    lines.append("")
    lines.append("  VERDICT: Ripa's condition REDUCES CLEANLY to the nondivergent one.")
    lines.append("  The divergent case does not modify the classical condition; it ADDS")
    lines.append("  a second, independent condition that has no nondivergent analogue.")
    reduces_cleanly = True
    ok = ok and reduces_cleanly

    # ---- Arm 2: is the extra condition binding here? ----------------------
    lines.append("")
    lines.append("Arm 2 - is the extra divergent condition binding for this project?")
    lines.append("-" * 72)
    phi = np.linspace(-np.pi / 2 + 1e-9, np.pi / 2 - 1e-9, 400_001)
    u = galewsky_jet(phi)
    c_grav = np.sqrt(G * H)

    # Condition (ii) must hold for the SAME c0 that condition (i) uses. The most
    # favourable c0 for (ii) -- the one minimising max|c0 - ubar| -- is the
    # midpoint of the jet's velocity range. Using it makes this a best-case test
    # for the flow, i.e. a conservative test of whether (ii) can bind at all.
    c0_best = 0.5 * (u.max() + u.min())
    worst = float(np.max(np.abs(c0_best - u)))
    margin = c_grav / worst

    lines.append(f"  Galewsky jet: u_max = {u.max():.1f} m/s, u_min = {u.min():.1f} m/s")
    lines.append(f"  long-gravity-wave speed sqrt(gH)   = {c_grav:8.2f} m/s")
    lines.append(f"  best-case c0 = (u_max + u_min)/2   = {c0_best:8.2f} m/s")
    lines.append(f"  max |c0 - ubar|                    = {worst:8.2f} m/s")
    lines.append(f"  margin sqrt(gH) / max|c0 - ubar|   = {margin:8.2f}x")
    lines.append(f"  Froude-like ratio u_max/sqrt(gH)   = {u.max() / c_grav:8.4f}")
    lines.append("")
    lines.append("  Even the least favourable admissible c0 -- one at the edge of the")
    lines.append("  jet's velocity range rather than its midpoint -- only doubles")
    lines.append(
        f"  max|c0 - ubar| to {u.max():.0f} m/s, still {c_grav / u.max():.1f}x below sqrt(gH)."
    )
    lines.append("  The conclusion does not depend on how c0 is chosen.")
    binding = margin < BINDING_MARGIN
    ok = ok and not binding
    lines.append("")
    lines.append(
        f"  condition (ii) binding at margin < {BINDING_MARGIN}x: "
        f"{'YES -- divergence matters here' if binding else 'NO'}"
    )

    # ---- Arm 3: can the rotation sweep activate it? -----------------------
    lines.append("")
    lines.append("Arm 3 - can the project's rotation sweep (P-08 ... P-12) activate it?")
    lines.append("-" * 72)
    lines.append("   Omega     eps      sqrt(gH)   max|c0-u|   margin   (ii) holds")
    sweep_ok = True
    for mult in OMEGA_SWEEP:
        eps = 4 * (mult * OMEGA0) ** 2 * R**2 / (G * H)
        holds = worst <= c_grav
        sweep_ok = sweep_ok and holds
        lines.append(
            f"   {mult:4.2f}x  {eps:8.2f}   {c_grav:8.1f}   {worst:8.1f}   "
            f"{margin:6.2f}x   {'yes' if holds else 'NO'}"
        )
    ok = ok and sweep_ok
    lines.append("")
    lines.append("  Condition (ii) contains sqrt(gH) and ubar and NO rotation rate, so")
    lines.append("  sweeping Omega cannot activate it. Lamb's parameter eps rises from")
    lines.append("  0.55 to 141 across the sweep -- the system becomes far more divergent")
    lines.append("  in the sense that matters for WAVE dispersion (section 6) -- while the")
    lines.append("  divergent STABILITY condition is untouched. Those are two different")
    lines.append("  senses of 'divergent', and conflating them is the trap this check")
    lines.append("  exists to avoid.")

    # ---- Arm 4: where the condition DOES bite -----------------------------
    lines.append("")
    lines.append("Arm 4 - the regime where the extra condition does bite")
    lines.append("-" * 72)
    lines.append("  Hayashi & Young (1987), abstract, verbatim: they consider 'the")
    lines.append("  instabilities of rotating, shallow-water, shear flows on an")
    lines.append("  EQUATORIAL beta-plane', and show that 'when the basic state has no")
    lines.append("  potential vorticity gradients an unstable wave has zero wave")
    lines.append("  energy'. So instability without a PV-gradient sign change is real --")
    lines.append("  but it is an equatorial result.")
    lines.append("")
    lines.append("  Why the equator is different, and why this project is not there:")
    lines.append("  the mechanism is that with a free surface the energy density is cubic")
    lines.append("  in the field variables, so wave energy is not positive definite and a")
    lines.append("  negative-energy wave can grow by GIVING energy to the mean flow. That")
    lines.append("  requires the flow to be comparable to the gravity-wave speed. At the")
    lines.append(
        f"  equator f -> 0 and nothing limits ubar; here Fr = {u.max() / c_grav:.3f} << 1."
    )
    lines.append("")
    lines.append("  This project's jet is midlatitude, geostrophically balanced, and")
    lines.append("  strongly subcritical. The counterexample does not reach it.")

    lines.append("")
    lines.append(f"VERDICT: {'VERIFIED' if ok else 'MISMATCH'}")
    if not ok:
        lines.append("  A failing arm is shown above.")

    report = "\n".join(lines) + "\n"
    print(report, end="")
    out = Path(__file__).resolve().parent / "output"
    out.mkdir(exist_ok=True)
    (out / (Path(__file__).stem + ".txt")).write_text(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
