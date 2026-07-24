"""Pre-run Rayleigh-Kuo prediction for the Phase-0 gate jet.

Physics. Barotropic instability of a zonal jet ``u_bar(phi)`` requires the
background gradient of absolute vorticity,

    dQ/dy = beta - d^2 u_bar / dy^2 ,

to change sign somewhere across the jet (Rayleigh 1880; Kuo 1949). This is a
NECESSARY condition, not a sufficient one: a sign change means instability *can*
grow there, not that it *will* at the reference script's particular perturbation
amplitude and 15-day integration.

We evaluate this analytically from the exact jet profile that the unmodified
reference ``dedalus_reference/shallow_water.py`` imposes (the Galewsky et al.
2004 mid-latitude jet), BEFORE running any simulation, so the Phase-0 gate has a
falsifiable prediction to close the loop against (acceptance criterion 4).

The jet is a compactly-supported C-infinity bump on ``[phi0, phi1]``:

    u_bar(phi) = (umax / en) * exp( 1 / ((phi - phi0) (phi - phi1)) ),  phi0 < phi < phi1
               = 0                                                       otherwise

with ``en = exp(-4 / (phi1 - phi0)^2)`` chosen so ``u_bar`` peaks at ``umax``.

Spherical metric. The meridional coordinate is arc length ``y = R * phi`` (phi is
latitude), so ``d/dy = (1/R) d/dphi`` and ``d^2 u_bar / dy^2 = (1/R^2)
d^2 u_bar / dphi^2`` — the ``1/R^2`` is the metric factor, not a flat-plane
derivative. The planetary vorticity gradient is ``beta = df/dy = (2*Omega/R)
cos(phi)`` with ``f = 2*Omega*sin(phi)``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# --- parameters, read verbatim from dedalus_reference/shallow_water.py ---------
R = 6.37122e6  # sphere radius, m
OMEGA = 7.292e-5  # rotation rate, 1/s
UMAX = 80.0  # jet peak speed, m/s
PHI0 = np.pi / 7  # equatorward edge (latitude, rad) ~ 25.71 deg
PHI1 = np.pi / 2 - PHI0  # poleward edge (latitude, rad) ~ 64.29 deg
EN = np.exp(-4.0 / (PHI1 - PHI0) ** 2)

HERE = Path(__file__).resolve().parent
FIG = HERE / "diagnostics" / "rayleigh_kuo_prediction.png"


def u_bar(phi: np.ndarray) -> np.ndarray:
    """The Galewsky jet zonal velocity u_bar(phi), phi = latitude in radians."""
    u = np.zeros_like(phi)
    inside = (phi > PHI0) & (phi < PHI1)
    p = phi[inside]
    u[inside] = UMAX / EN * np.exp(1.0 / ((p - PHI0) * (p - PHI1)))
    return u


def compute() -> dict:
    """Return the Rayleigh-Kuo diagnostic sampled on a fine latitude grid."""
    phi = np.linspace(-np.pi / 2, np.pi / 2, 200_001)
    dphi = phi[1] - phi[0]
    u = u_bar(phi)

    # d^2 u / dphi^2 numerically (2nd-order central via np.gradient twice); the
    # bump -> 0 with all derivatives at the edges, so no spurious edge spike.
    d2u_dphi2 = np.gradient(np.gradient(u, dphi), dphi)

    u_yy = d2u_dphi2 / R**2  # meridional curvature in arc length y = R*phi
    beta = (2 * OMEGA / R) * np.cos(phi)  # planetary vorticity gradient
    dQdy = beta - u_yy  # background absolute-vorticity gradient

    return {
        "phi": phi,
        "u": u,
        "u_yy": u_yy,
        "beta": beta,
        "dQdy": dQdy,
    }


def sign_change_latitudes(phi: np.ndarray, dQdy: np.ndarray) -> list[float]:
    """Latitudes (degrees) where dQ/dy crosses zero, restricted to the jet band."""
    band = (phi > PHI0 - 0.02) & (phi < PHI1 + 0.02)
    s = np.sign(dQdy)
    crossings = np.where((np.diff(s) != 0) & band[:-1])[0]
    lats = []
    for i in crossings:
        # linear interpolation of the zero crossing
        x0, x1 = phi[i], phi[i + 1]
        y0, y1 = dQdy[i], dQdy[i + 1]
        xc = x0 - y0 * (x1 - x0) / (y1 - y0)
        lats.append(np.degrees(xc))
    # dedupe near-identical crossings
    out: list[float] = []
    for la in lats:
        if not out or abs(la - out[-1]) > 0.05:
            out.append(la)
    return out


def _plot(data: dict, crossings: list[float]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    phi_deg = np.degrees(data["phi"])
    m = (phi_deg > 10) & (phi_deg < 80)  # zoom on the jet band
    fig, ax = plt.subplots(2, 1, figsize=(7, 7), sharex=True)
    ax[0].plot(phi_deg[m], u_bar(data["phi"])[m], "k")
    ax[0].set_ylabel("u_bar  [m/s]")
    ax[0].set_title("Phase-0 jet (Galewsky 2004) and Rayleigh-Kuo diagnostic")
    ax[1].plot(phi_deg[m], data["beta"][m] * 1e11, label=r"$\beta$")
    ax[1].plot(phi_deg[m], data["u_yy"][m] * 1e11, label=r"$d^2\bar u/dy^2$")
    ax[1].plot(phi_deg[m], data["dQdy"][m] * 1e11, "r", lw=2, label=r"$\beta - d^2\bar u/dy^2$")
    ax[1].axhline(0, color="gray", lw=0.8)
    for xc in crossings:
        ax[1].axvline(xc, color="purple", ls="--", lw=0.8)
    ax[1].set_ylabel(r"[$10^{-11}\,\mathrm{m^{-1}s^{-1}}$]")
    ax[1].set_xlabel("latitude [deg]")
    ax[1].legend(loc="best", fontsize=8)
    FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(FIG, dpi=120)
    plt.close(fig)


def main() -> int:
    data = compute()
    phi, dQdy = data["phi"], data["dQdy"]
    jet_core = np.degrees(phi[np.argmax(data["u"])])
    crossings = sign_change_latitudes(phi, dQdy)
    _plot(data, crossings)

    print("=== Phase-0 Rayleigh-Kuo PREDICTION (pre-run) ===")
    print(f"jet band:            {np.degrees(PHI0):.2f} to {np.degrees(PHI1):.2f} deg N")
    print(f"jet core (u max):    {jet_core:.2f} deg N,  u_max = {UMAX:.1f} m/s")
    print(
        f"beta - d2u/dy2 sign changes at latitudes: "
        f"{', '.join(f'{c:.2f}' for c in crossings)} deg N"
    )
    if crossings:
        print(
            "PREDICTION: the background PV gradient reverses on the jet flank(s) "
            "above -> barotropic instability is POSSIBLE there (necessary, not "
            "sufficient). Expect filamentary instability to develop near these "
            "latitudes within the run."
        )
        print(f"figure: {FIG.relative_to(HERE.parents[1])}")
        return 0
    print(
        "PREDICTION: NO sign change found -> the configuration would NOT be a "
        "valid barotropic-instability test. Investigate before running (see §16)."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
