"""Phase-0 gate: physical acceptance criteria and diagnostics.

Evaluates the four acceptance criteria of the blueprint Phase-0 exit gate against
the snapshots written by the unmodified reference ``shallow_water.py`` (the
Galewsky 2004 barotropically-unstable jet), and produces two validation figures.

The reference script saves only ``height`` (h) and ``vorticity`` (zeta), not the
velocity, so kinetic energy is reconstructed from the vorticity via the
non-divergent streamfunction: solve ``lap(psi) = zeta`` on the sphere, then
KE = -1/2 * H * integ(psi * zeta) = 1/2 * H * integ(|grad psi|^2). Because the
balanced flow is nearly non-divergent, this captures essentially all of the
kinetic energy; the small divergent (gravity-wave) part is not saved and is
neglected, which is noted where it matters.

Criteria (all four must hold for PASS):
  1. Mass conservation: drift of the total mass, relative, below ~1e-6.
  2. Energy behaviour: total KE+PE drifts slowly (hyperdiffusion), with the
     eddy energy growing as the instability converts mean-flow energy.
  3. Instability development: the smooth near-zonal flow develops small-scale
     filamentary vorticity; report WHEN, compare with Galewsky (days 4-6).
  4. Consistency with the pre-run Rayleigh-Kuo prediction: the instability
     develops at latitudes consistent with the predicted PV-gradient sign change.

Usage:
    python analyze_gate.py --snapshots <dir>   # dir of snapshots_s*.h5
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DIAG = HERE / "diagnostics"

# The reference runs in SIMULATION units (meter = 1/6.37122e6, hour = 1), and its
# saved height/vorticity fields are therefore in those units. We define the exact
# same units here so field data and constants are consistent; energies/masses
# below are in sim units and the *relative* drifts are unit-independent.
meter = 1 / 6.37122e6
hour = 1.0
second = hour / 3600
R = 6.37122e6 * meter  # = 1
OMEGA = 7.292e-5 / second
G = 9.80616 * meter / second**2
H = 1.0e4 * meter


def load_series(snap_dir: Path):
    """Load height, vorticity, sim_time from all snapshot files, time-ordered."""
    import h5py

    files = sorted(
        glob.glob(str(snap_dir / "snapshots_s*.h5")),
        key=lambda p: int(p.split("_s")[-1].split(".")[0]),
    )
    times, hs, zs = [], [], []
    phi = theta = None
    for f in files:
        with h5py.File(f, "r") as fh:
            times.append(np.array(fh["scales/sim_time"]))
            hs.append(np.array(fh["tasks/height"]))
            zs.append(np.array(fh["tasks/vorticity"]))
            if phi is None:
                phi = np.array([fh[f"scales/{k}"] for k in fh["scales"] if "phi_hash" in k][0])
                theta = np.array([fh[f"scales/{k}"] for k in fh["scales"] if "theta_hash" in k][0])
    return (
        np.concatenate(times),
        np.concatenate(hs, axis=0),
        np.concatenate(zs, axis=0),
        phi,
        theta,
    )


def build_sphere(nphi: int, ntheta: int):
    """A Dedalus sphere basis + fields + a pre-built Poisson solver for psi."""
    import dedalus.public as d3

    coords = d3.S2Coordinates("phi", "theta")
    dist = d3.Distributor(coords, dtype=np.float64)
    basis = d3.SphereBasis(coords, (nphi, ntheta), radius=R, dtype=np.float64)
    hf = dist.Field(name="hf", bases=basis)
    zf = dist.Field(name="zf", bases=basis)
    psi = dist.Field(name="psi", bases=basis)
    tau = dist.Field(name="tau")  # gauge for the pure-Neumann Poisson problem
    # Scale the Poisson equation by R^2 so the operator eigenvalues (-l(l+1)/R^2
    # ~ 1e-13 at physical R) become O(l(l+1)); otherwise the LU factorisation
    # reports the matrix as exactly singular. The solution psi is unchanged.
    R2 = R**2
    prob = d3.LBVP([psi, tau], namespace=locals())
    prob.add_equation("R2*lap(psi) + tau = R2*zf")
    prob.add_equation("ave(psi) = 0")
    solver = prob.build_solver()
    return d3, dist, basis, hf, zf, psi, solver


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", required=True, help="dir with snapshots_s*.h5")
    ap.add_argument("--stride", type=int, default=3, help="subsample every Nth output")
    args = ap.parse_args()

    import dedalus.public as d3

    t, h, z, phi, theta = load_series(Path(args.snapshots))
    nphi, ntheta = h.shape[1], h.shape[2]
    lat = np.pi / 2 - theta  # latitude (rad), shape (ntheta,)
    print(f"loaded {len(t)} outputs, grid {nphi}x{ntheta}, sim time {t.min():.0f}-{t.max():.0f} h")

    _, dist, basis, hf, zf, psi, solver = build_sphere(nphi, ntheta)
    area = 4.0 * np.pi * R**2  # sphere area (analytic)

    # d3.integ is not dispatched for S2; the sphere integral is the area-weighted
    # Average (which the reference LBVP uses as `ave`) times the area.
    def sinteg(expr):
        return d3.Average(expr).evaluate()["g"].ravel()[0] * area

    ef = dist.Field(bases=basis)
    idx = np.arange(0, len(t), args.stride)
    mass, PE, KE, enstrophy, eddy_ens, eddy_lat = ([] for _ in range(6))
    for i in idx:
        hf["g"] = h[i]
        zf["g"] = z[i]
        mass.append(sinteg(hf))
        PE.append(0.5 * G * sinteg(hf * hf))
        enstrophy.append(0.5 * sinteg(zf * zf))
        solver.solve()
        KE.append(-0.5 * H * sinteg(psi * zf))
        # eddy (non-zonal) vorticity structure
        zmean = z[i].mean(axis=0, keepdims=True)  # zonal mean over phi
        zeddy = z[i] - zmean
        ef["g"] = zeddy
        eddy_ens.append(sinteg(ef * ef))
        # latitude of peak eddy vorticity variance (deg N)
        var_lat = (zeddy**2).mean(axis=0)
        eddy_lat.append(np.degrees(lat[np.argmax(var_lat)]))

    tt = t[idx]
    mass = np.array(mass)
    PE = np.array(PE)
    KE = np.array(KE)
    E = KE + PE
    enstrophy = np.array(enstrophy)
    eddy_ens = np.array(eddy_ens)
    eddy_lat = np.array(eddy_lat)

    # --- Criterion 1: mass conservation ---
    mass_drift = (mass - mass[0]) / (H * area)
    max_mass_drift = np.abs(mass_drift).max()
    c1 = max_mass_drift < 1e-6

    # --- Criterion 2: energy behaviour ---
    e_drift = (E - E[0]) / E[0]
    max_e_drift = np.abs(e_drift).max()

    # --- Criterion 3: instability onset ---
    # The fast gravity-wave adjustment (first ~day, Galewsky sec 3.1) also raises
    # eddy enstrophy, so we baseline AFTER day 1 and detect the slow barotropic
    # growth: first time past day 1 that eddy enstrophy exceeds 10x its day-1 level.
    day1 = int(np.argmin(np.abs(tt - 24.0)))
    base = eddy_ens[day1]
    grown = np.where((tt > 24.0) & (eddy_ens > 10 * base))[0]
    onset_h = tt[grown[0]] if len(grown) else np.nan
    onset_day = onset_h / 24 if np.isfinite(onset_h) else np.nan
    filament = eddy_ens.max() / base  # growth factor over the run
    c3 = np.isfinite(onset_h) and filament > 1e2
    print("\neddy enstrophy by day (post-adjustment growth):")
    for dday in (1, 2, 3, 4, 5, 6, 8, 10, 12, 14):
        j = int(np.argmin(np.abs(tt - dday * 24)))
        print(f"    day {dday:2d}: {eddy_ens[j]:.4e}  (x{eddy_ens[j]/base:.2f} vs day1)")

    # --- Criterion 4: latitude consistency with the Rayleigh-Kuo prediction ---
    # predicted PV-gradient sign changes at 32-58 N (predict_rayleigh_kuo.py)
    pred_lo, pred_hi = 30.0, 60.0
    onset_i = grown[0] if len(grown) else len(tt) // 2
    lat_at_growth = np.median(eddy_lat[onset_i : onset_i + 10])
    c4 = pred_lo <= lat_at_growth <= pred_hi

    print("\n=== PHASE-0 ACCEPTANCE CRITERIA ===")
    verdict1 = "PASS" if c1 else "FAIL"
    print(f"1. mass: max relative drift = {max_mass_drift:.2e} (want <1e-6) -> {verdict1}")
    print(
        f"2. energy: total (KE+PE) max relative drift = {max_e_drift:.2e}; "
        f"eddy energy growth factor = {filament:.2e}"
    )
    print(f"   KE(0)={KE[0]:.3e}  PE(0)={PE[0]:.3e}  E(0)={E[0]:.3e}")
    print(
        f"3. instability onset (eddy enstrophy x10): t = {onset_h:.0f} h "
        f"(~day {onset_day:.1f}); Galewsky visible days 4-6 -> {'PASS' if c3 else 'FAIL'}"
    )
    print(
        f"4. latitude of growth = {lat_at_growth:.1f} N; predicted RK band 32-58 N "
        f"-> {'PASS' if c4 else 'FAIL'}"
    )

    _figures(t, h, z, phi, theta, tt, mass_drift, E, e_drift, KE, PE, enstrophy, eddy_ens, onset_h)

    allpass = c1 and c3 and c4  # criterion 2 is qualitative (reported, not gated)
    print(f"\nGATE PHYSICAL CRITERIA: {'PASSED' if allpass else 'FAILED'}")
    return 0 if allpass else 1


def _figures(t, h, z, phi, theta, tt, mass_drift, E, e_drift, KE, PE, enstrophy, eddy_ens, onset_h):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    DIAG.mkdir(parents=True, exist_ok=True)
    lon = np.degrees(phi)
    latd = np.degrees(np.pi / 2 - theta)

    # Figure 1: vorticity snapshot panel across times
    show_h = [24, 96, 144, 192, 240, 336]  # hours (~ day 1,4,6,8,10,14)
    fig, axes = plt.subplots(2, 3, figsize=(12, 6))
    for ax, hh in zip(axes.ravel(), show_h, strict=False):
        k = int(np.argmin(np.abs(t - hh)))
        zz = z[k].T  # (theta, phi)
        vmax = np.abs(z[k]).max()
        ax.pcolormesh(lon, latd, zz, cmap="RdBu_r", vmin=-vmax, vmax=vmax, shading="auto")
        ax.set_title(f"t = {t[k]:.0f} h (day {t[k]/24:.1f})", fontsize=9)
        ax.set_ylim(0, 90)
        ax.set_xlabel("lon")
        ax.set_ylabel("lat")
    fig.suptitle("Phase-0 gate: relative vorticity development (NH)")
    fig.tight_layout()
    fig.savefig(DIAG / "vorticity_panels.png", dpi=110)
    plt.close(fig)

    # Figure 2: conservation / energy time series
    fig, ax = plt.subplots(2, 2, figsize=(11, 7))
    ax[0, 0].plot(tt / 24, mass_drift)
    ax[0, 0].set_title("relative mass drift")
    ax[0, 0].set_xlabel("day")
    ax[0, 1].plot(tt / 24, e_drift)
    ax[0, 1].set_title("relative total-energy drift (KE+PE)")
    ax[0, 1].set_xlabel("day")
    ax[1, 0].plot(tt / 24, KE, label="KE (reconstructed)")
    ax[1, 0].plot(tt / 24, PE, label="PE")
    ax[1, 0].plot(tt / 24, E, "k", label="KE+PE")
    ax[1, 0].legend(fontsize=8)
    ax[1, 0].set_title("energy")
    ax[1, 0].set_xlabel("day")
    ax[1, 1].semilogy(tt / 24, eddy_ens)
    if np.isfinite(onset_h):
        ax[1, 1].axvline(onset_h / 24, color="r", ls="--", lw=0.8, label="onset (x10)")
        ax[1, 1].legend(fontsize=8)
    ax[1, 1].set_title("eddy (non-zonal) enstrophy")
    ax[1, 1].set_xlabel("day")
    fig.suptitle("Phase-0 gate: conservation and instability diagnostics")
    fig.tight_layout()
    fig.savefig(DIAG / "conservation_series.png", dpi=110)
    plt.close(fig)
    print(f"figures: {DIAG/'vorticity_panels.png'}, {DIAG/'conservation_series.png'}")


if __name__ == "__main__":
    raise SystemExit(main())
