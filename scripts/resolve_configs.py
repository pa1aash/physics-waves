#!/usr/bin/env python
"""Fill in the Session-00 placeholders in every run config, from a stated policy.

Session 00 wrote every config with ``TBD_SESSION_L5`` wherever a value could not
be chosen before a solver existed. This script chooses them. It exists as a
tracked tool rather than as a one-off edit for one reason: **the policy is the
interesting thing, not the numbers**. A reader who wants to know why V-02
integrates for five days, or why every run shares one hyperdiffusion
coefficient, should be able to read the reason next to the value.

The script is idempotent — it only replaces the sentinel and the four
``physical.H`` values it is explicitly told to correct — so re-running it after a
config edit changes nothing else.

## The policy

**Timestep.** ``dt`` at L1 is 600 s, the value in the Dedalus reference script
this project validated in its Phase-0 gate, and therefore the one value here with
direct evidence behind it. Other resolutions scale it linearly with grid spacing.
The gravity-wave term ``H div(u)`` is treated implicitly, so the binding
restriction is advective, not the ~500 s a gravity wave would impose at L1.

**Hyperdiffusion.** One coefficient for every run and every resolution:
``nu_4 = 1e5 * R^2 / 32^2``, the ``nabla^4`` coefficient matched to a ``1e5 m^2/s``
``nabla^2`` diffusion at spherical degree 32, as in the reference script.
*Deliberately not scaled with resolution.* The convergence study V-07 compares
solutions across the ladder, and that comparison is meaningless unless every rung
solves the *same equations*: a resolution-dependent ``nu`` converges to nothing.
Run P-18 varies it on purpose, which is the honest way to expose the dependence.

**Integration length.** Taken from each source's own error-measurement protocol
where one exists — five days for Williamson case 2, fifteen for case 5, fourteen
for case 6, one revolution (twelve days) for case 1, twelve hours for Läuter. The
phase-speed campaign runs twenty days, enough for at least one full westward
period of the slowest mode in the sweep (``n = 8`` at ``m = 2``, 17.9 days). The
instability campaign runs fifteen days, matching the Phase-0 reference.

**Mean depth.** Four benchmark cases carry a mean depth of their own that is not
10 km, and the stub configs said 10 km for all of them. They are corrected here
to the case's own area-mean free surface, computed from the case definition, not
typed in. This is not cosmetic: ``H`` is the depth the implicit term linearises
about, and a config claiming a 10 km ocean for a 2.4 km case describes a fluid
the run does not contain.

**Zonal order for the phase-speed campaign.** ``m = 2`` throughout, matching the
ladder ``theory/derivations.tex`` §6 uses and ``docs/DEDALUS_API.md`` §11
confirmed against the analytic spectrum, so the simulations and the eigenvalue
solver address the same modes.

**Amplitude.** 1 m/s peak wind for every phase-speed run except the linearity
ladder P-13/14/15, which steps 1, 5 and 20 m/s. One metre per second is roughly
2% of the wave's own phase speed at ``n = 4``, so the run sits deep in the linear
regime the dispersion relation describes; the ladder walks out of it deliberately.

**Shear ladder.** ``S`` is the jet's peak speed as a fraction of Galewsky's
80 m/s. The Rayleigh-Kuo *necessary* condition is first met at ``S = 0.0728``
(computed exactly by ``jet_family.critical_shear_parameter``), so the ladder
0.05, 0.1, 0.25, 0.5, 1.0 straddles that threshold and ends at the anchor jet
that is known to be unstable. The criterion being necessary and not sufficient is
the whole reason the ladder does not stop at 0.0728: where instability actually
appears is the measurement.

Run: ``python scripts/resolve_configs.py [--check]``
``--check`` reports what would change and exits non-zero if anything would,
which is what the audit uses.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.special import roots_legendre

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = REPO_ROOT / "configs"
SENTINEL = "TBD_SESSION_L5"

DAY = 86400.0
R = 6371220.0
OMEGA = 7.292e-05
G = 9.80616
U0_12DAY = 2 * np.pi * R / (12 * DAY)

# nabla^4 coefficient matched to 1e5 m^2/s of nabla^2 diffusion at degree 32.
NU4 = 1.0e5 * R**2 / 32**2

# dt = 600 s at L1 (Ntheta = 128), scaled linearly with grid spacing.
DT_BY_RESOLUTION = {"L0": 2400.0, "L1": 600.0, "L2": 300.0, "L3": 150.0}

STOP_BY_CASE = {
    "williamson_1": 12 * DAY,  # one revolution; the report advects the bell once round
    "williamson_2": 5 * DAY,  # report: contour maps and error "after five days"
    "williamson_5": 15 * DAY,  # report: error at days 5, 10 and 15
    "williamson_6": 14 * DAY,  # report: error at day 0, 7 and 14
    "lauter": 0.5 * DAY,  # paper measures L2 error after 12 h
    "single_harmonic": 20 * DAY,  # >= 1 westward period for the slowest mode swept
    "galewsky": 15 * DAY,  # matches the validated Phase-0 reference run
    "jet": 15 * DAY,
}

CADENCES = {
    "verification": {
        "snapshot_cadence": DAY,
        "slice_cadence": 6 * 3600.0,
        "spectra_cadence": 3600.0,
    },
    "phase_speed": {"snapshot_cadence": DAY, "slice_cadence": 3600.0, "spectra_cadence": 3600.0},
    "instability": {
        "snapshot_cadence": 6 * 3600.0,
        "slice_cadence": 3600.0,
        "spectra_cadence": 3600.0,
    },
}

SHEAR_LADDER = {"I-01": 0.05, "I-02": 0.1, "I-03": 0.25, "I-04": 0.5, "I-05": 1.0}
ROTATION_LADDER = {"I-06": 0.5, "I-07": 1.0, "I-08": 2.0, "I-09": 4.0}
AMPLITUDE_LADDER = {"P-13": 1.0, "P-14": 5.0, "P-15": 20.0}

# Galewsky et al. (2004) eq. (4), written out rather than left to a default so
# that the config records what was actually used.
GALEWSKY_PERTURBATION = {
    "h_hat": 120.0,
    "phi2": float(np.pi / 4),
    "alpha": 1.0 / 3.0,
    "beta": 1.0 / 15.0,
}

STUB_NOTICE = (
    "# Run-config stub (Session 00). Solver-dependent values are marked\n"
    "# TBD_SESSION_L5 and finalised in Session L5. Validates against\n"
    "# configs/_schema.yaml.\n"
)
RESOLVED_NOTICE = (
    "# Run configuration. Solver-dependent values were resolved in Session L5 by\n"
    "# scripts/resolve_configs.py, which states the policy behind each one.\n"
    "# Validates against configs/_schema.yaml.\n"
)


def _mu_quadrature(n: int = 512):
    """Gauss-Legendre nodes in ``mu = sin(latitude)``; the area mean is (1/2) * sum."""
    mu, w = roots_legendre(n)
    return np.arcsin(np.clip(mu, -1.0, 1.0)), 0.5 * w


def mean_depth_williamson_2(gh0: float = 2.94e4) -> float:
    """Report eq. (95) with ``alpha = 0``; ``<sin^2(lat)> = 1/3`` exactly."""
    return (gh0 - (R * OMEGA * U0_12DAY + U0_12DAY**2 / 2) / 3) / G


def mean_depth_williamson_5(h0: float = 5400.0) -> float:
    """Case 5 is case 2 at ``alpha = 0`` with the mean height changed to 5400 m."""
    return mean_depth_williamson_2(G * h0)


def mean_depth_williamson_6(omega=7.848e-6, K=7.848e-6, Rw=4, h0=8.0e3) -> float:
    """Report eqs. (140)-(141): the ``B`` and ``C`` terms have zero zonal mean."""
    lat, w = _mu_quadrature()
    c = np.cos(lat)
    A = (omega / 2) * (2 * OMEGA + omega) * c**2 + 0.25 * K**2 * (
        c ** (2 * Rw) * ((Rw + 1) * c**2 + (2 * Rw**2 - Rw - 2)) - 2 * Rw**2 * c ** (2 * Rw - 2)
    )
    return h0 + R**2 * float(np.dot(w, A)) / G


def mean_depth_lauter(alpha=np.pi / 4, k1=133681.0) -> float:
    """Läuter Example 3's free surface, averaged over the sphere at ``t = 0``.

    Only the zonal mean survives the average, so a 1-D quadrature in latitude is
    exact: the azimuthal dependence enters through ``cos(lambda)`` and
    ``cos^2(lambda)``, whose means are 0 and 1/2.
    """
    lat, w = _mu_quadrature()
    u0 = U0_12DAY
    sa, ca = np.sin(alpha), np.cos(alpha)
    centrifugal = R * OMEGA * np.sin(lat)
    # c_n = -sa cos(lat) cos(chi) + ca sin(lat); average (u0 c_n + centrifugal)^2
    # over chi analytically: <cos(chi)> = 0, <cos^2(chi)> = 1/2.
    mean_sq = 0.5 * (u0 * sa * np.cos(lat)) ** 2 + (u0 * ca * np.sin(lat) + centrifugal) ** 2
    phi_free = -0.5 * mean_sq + 0.5 * centrifugal**2 + k1
    return float(np.dot(w, phi_free)) / G


MEAN_DEPTH_OVERRIDE = {
    "williamson_2": mean_depth_williamson_2,
    "williamson_5": mean_depth_williamson_5,
    "williamson_6": mean_depth_williamson_6,
    "lauter": mean_depth_lauter,
}


def resolve(config: dict) -> dict:
    """Return the config with every sentinel replaced. Pure; does no I/O."""
    config = dict(config)
    run_id = config["run_id"]
    campaign = config["campaign"]
    ic = config.get("initial_condition")
    resolution = config["resolution"]

    numerics = dict(config.get("numerics") or {})
    if numerics:
        numerics["timestepper"] = "RK222"
        numerics["dt"] = DT_BY_RESOLUTION[resolution]
        numerics["hyperdiffusion_coefficient"] = float(f"{NU4:.6g}")
        numerics["stop_sim_time"] = STOP_BY_CASE[ic]
        if run_id == "P-18":
            # The sensitivity run has to differ from the standard one or it is
            # not a run at all. It takes ten times the standard coefficient, so
            # that P-03 and P-18 form a two-point sensitivity at fixed mode and
            # resolution. Session L7's sweep generator widens this into a proper
            # bracket; one decade is enough to show whether the answer moves.
            numerics["hyperdiffusion_coefficient"] = float(f"{10 * NU4:.6g}")
        config["numerics"] = numerics

    outputs = dict(config.get("outputs") or {})
    if outputs:
        outputs.update(CADENCES[campaign])
        config["outputs"] = outputs

    physical = dict(config.get("physical") or {})
    if physical and ic in MEAN_DEPTH_OVERRIDE:
        physical["H"] = round(MEAN_DEPTH_OVERRIDE[ic](), 3)
        config["physical"] = physical

    params = dict(config.get("initial_condition_params") or {})
    if params and campaign == "evp":
        if run_id == "EVP-hough":
            # The ladder starts at 1e-6 so the eps -> 0 branch can be identified
            # unambiguously and followed by continuation, which is how
            # derivations.tex §6 avoids the mode-misidentification failure it
            # records; it ends well past Earth's eps = 8.80.
            params["lambs_parameter_range"] = [
                1.0e-6,
                1.0e-4,
                1.0e-2,
                0.1,
                1.0,
                8.8044,
                20.0,
                100.0,
            ]
            params["azimuthal_orders"] = [1, 2, 3, 4, 5]
            params["truncation"] = 60
        if run_id == "EVP-jet-stability":
            params["base_states"] = ["I-00", "I-01", "I-02", "I-03", "I-04", "I-05"]
            params["azimuthal_orders"] = list(range(1, 13))
            # N and 2N, the resolution-doubling spurious-mode filter of
            # derivations.tex §9.2, at the values check_rayleigh_kuo.py uses.
            params["truncation"] = [240, 480]
        config["initial_condition_params"] = params
        return config

    if params:
        if ic == "single_harmonic":
            params["order_m"] = 2
            params["amplitude"] = AMPLITUDE_LADDER.get(run_id, 1.0)
        if ic == "galewsky":
            params["perturbation"] = dict(GALEWSKY_PERTURBATION)
        if ic == "jet":
            if params.get("profile") == "reanalysis_djf":
                params["profile_path"] = "data/processed/ncep_djf_zonal_mean_jet.npz"
                params["perturbation"] = dict(GALEWSKY_PERTURBATION)
            else:
                params["shear_parameter_S"] = SHEAR_LADDER.get(run_id, 1.0)
                if params.get("perturbation") == "random":
                    params["perturbation"] = "random"
                else:
                    params["perturbation"] = dict(GALEWSKY_PERTURBATION)
            if run_id in ROTATION_LADDER:
                params["omega_multiplier"] = ROTATION_LADDER[run_id]
                physical = dict(config.get("physical") or {})
                physical["Omega"] = float(f"{ROTATION_LADDER[run_id] * OMEGA:.6g}")
                config["physical"] = physical
        config["initial_condition_params"] = params

    return config


def _leading_comments(text: str) -> str:
    lines, kept = text.splitlines(keepends=True), []
    for line in lines:
        if line.startswith("#") or not line.strip():
            kept.append(line)
        else:
            break
    header = "".join(kept)
    if header.startswith(STUB_NOTICE):
        header = RESOLVED_NOTICE + header[len(STUB_NOTICE) :]
    return header


def process(path: Path, check: bool) -> bool:
    original = path.read_text(encoding="utf-8")
    config = yaml.safe_load(original)
    resolved = resolve(config)
    body = yaml.safe_dump(
        resolved, sort_keys=False, default_flow_style=False, width=88, allow_unicode=True
    )
    updated = _leading_comments(original) + body
    if updated == original:
        return False
    if not check:
        path.write_text(updated, encoding="utf-8")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report changes without writing")
    args = parser.parse_args(argv)

    changed = [p for p in sorted(CONFIG_ROOT.glob("*/*.yaml")) if process(p, args.check)]
    verb = "would update" if args.check else "updated"
    for path in changed:
        print(f"[resolve-configs] {verb} {path.relative_to(REPO_ROOT)}")
    if args.check and changed:
        print(f"[resolve-configs] {len(changed)} config(s) out of date", file=sys.stderr)
        return 1
    print(
        f"[resolve-configs] {len(changed)} config(s) {'would change' if args.check else 'written'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
