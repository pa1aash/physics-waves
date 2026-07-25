"""Necessary, sufficient, and actual: where a jet family really goes unstable.

Physics first. There are three different statements one can make about whether a
zonal jet is barotropically unstable, and this project can now make all three. They
do not coincide, and the gaps between them are the point.

**Necessary — Rayleigh and Kuo.** If the background absolute-vorticity gradient
``dQ/dy = beta - d^2 ubar/dy^2`` never changes sign, no normal mode can grow. This
*forbids* instability below a threshold and says nothing whatever above it. It is
cheap, exact, and weak.

**Sufficient — Ripa.** If a constant ``c0`` exists with ``(dQ/dy)(c0 - ubar) >= 0``
everywhere *and* ``|c0 - ubar| <= sqrt(gH)`` everywhere, the flow is stable — and
stable against arbitrary disturbances, not merely against normal modes. This
*certifies* stability below a threshold and says nothing above it. It is the only
statement in this project that can prove a flow safe.

**Actual — the eigenvalue problem.** Solve for the spectrum and read off the
fastest growing mode. This says what happens, at the cost of being a normal-mode
statement about a non-normal operator: an all-real spectrum forbids a growing mode
and does not exclude finite-time transient amplification.

Between the necessary threshold and the point where a mode actually grows lies a
band where **instability is permitted but does not occur**. That band is not a
technicality; it is the quantitative content of the phrase "necessary but not
sufficient", and locating it is something a criterion alone can never do. Session
L5 found it by hand on a five-rung ladder. This module makes it a sweep.

**One correction to Session L5's phrasing, which this module's finer sweep
exposes.** That session reported Ripa certifying stability "to S = 0.05" and
Rayleigh-Kuo triggering at ``S = 0.0728``, which reads as two different
thresholds. They are not: 0.05 was simply the largest rung of the ladder that
happened to be tested. For this jet family Ripa's condition (ii) — gravity-wave
criticality — is satisfied with a margin of order fifty, so it is never binding,
and Ripa's condition (i) fails exactly when ``dQ/dy`` first changes sign. **The
sufficient and necessary thresholds coincide here**, and the whole gap is between
that shared threshold and the onset of actual growth. Saying so is worth more than
the extra threshold, because it identifies *why* they coincide and when they would
not: raise ``eps`` far enough, or shrink ``gH``, and condition (ii) would start to
bite first.

**SCOPE, inherited from Session L4b and not re-litigated here.** The eigenvalue
problem is nondivergent. Growth rates below are therefore modal growth rates of the
nondivergent operator, and they carry a known one-signed bias — nondivergent
overestimates. See ``docs/literature/DIVERGENT_STABILITY_DECISION.md``.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import numpy as np

from src.solver.evp_stability import (
    PERSIST_RTOL,
    resolved_growth_rate,
    ripa_diagnostics,
)
from src.solver.initial_conditions.galewsky import PHI0, PHI1, UMAX, jet_profile_derivatives
from src.solver.initial_conditions.jet_family import critical_shear_parameter

# A rate below this is numerical dust, not growth: it corresponds to an e-folding
# time of more than three years, on a jet whose own advective timescale is days.
GROWTH_FLOOR_S = 1.0e-8

# Truncation pair for the sweep. The (240, 480) pair derivations.tex §9.2 specifies
# is used for reported numbers; a coarser pair is available for threshold searches,
# where many evaluations are needed and only a bracket is being narrowed.
REPORTING_TRUNCATION = (240, 480)
SEARCH_TRUNCATION = (120, 240)

EARTH = {"R": 6371220.0, "Omega": 7.292e-05, "g": 9.80616, "H": 10000.0}

# Zonal orders swept by default. Session L5's EVP-jet-stability config sweeps
# m = 1..12, and the fastest-growing mode of every jet in this family lies well
# inside that range, so widening it costs time and finds nothing.
DEFAULT_ORDERS = tuple(range(1, 13))


@dataclass
class StabilityLadderRow:
    """One base state, judged by all three criteria."""

    shear_parameter_S: float
    umax_m_s: float
    rayleigh_kuo_permits: bool
    min_dQdy: float
    ripa_certifies_stable: bool
    ripa_condition_i: bool
    ripa_condition_ii: bool
    ripa_criticality_margin: float
    m_star: int | None
    sigma_max_s: float | None
    e_folding_days: float | None
    n_resolved_growing: int

    @property
    def actually_grows(self) -> bool:
        return self.sigma_max_s is not None and self.sigma_max_s > GROWTH_FLOOR_S

    @property
    def verdict(self) -> str:
        """A one-word summary of which of the three regimes this rung is in."""
        if self.ripa_certifies_stable:
            return "certified stable"
        if not self.actually_grows:
            return "permitted, not growing"
        return "growing"

    def as_dict(self) -> dict:
        out = dict(self.__dict__)
        out["actually_grows"] = self.actually_grows
        out["verdict"] = self.verdict
        return out


@dataclass
class ThresholdSet:
    """The three thresholds, and the gap between the outer two."""

    rayleigh_kuo_S: float
    ripa_S: float
    growth_onset_S: float
    growth_onset_bracket: tuple[float, float]
    truncation: tuple[int, int]
    notes: list[str] = dataclass_field(default_factory=list)

    @property
    def permitted_but_stable_width(self) -> float:
        """How wide, in ``S``, the band is where instability is allowed but absent."""
        return self.growth_onset_S - self.rayleigh_kuo_S

    def as_dict(self) -> dict:
        out = dict(self.__dict__)
        out["permitted_but_stable_width"] = self.permitted_but_stable_width
        out["notes"] = list(self.notes)
        return out


def _profile_for(shear: float, phi0: float = PHI0, phi1: float = PHI1, umax_ref: float = UMAX):
    def profile(lat):
        return jet_profile_derivatives(lat, shear * umax_ref, phi0, phi1)

    return profile


def rayleigh_kuo_verdict(shear: float, physical: dict | None = None) -> tuple[bool, float]:
    """Does ``dQ/dy`` change sign for this jet? Returns ``(permits_instability, min dQ/dy)``.

    Evaluated on a fine latitude grid from the *analytic* derivatives of the jet,
    not from finite differences of a sampled profile: near its compactly supported
    edges this jet behaves like ``exp(-1/x)``, whose curvature has structure on a
    scale that shrinks without bound, and a fixed grid would either smear it or
    amplify round-off into a spurious sign change.
    """
    physical = physical or EARTH
    lat = np.linspace(-np.pi / 2 + 1e-9, np.pi / 2 - 1e-9, 200_001)
    _, d2u = _second_derivative(shear, lat)
    beta = (2 * physical["Omega"] / physical["R"]) * np.cos(lat)
    dQdy = beta - d2u / physical["R"] ** 2
    return bool(np.any(dQdy < 0)), float(np.min(dQdy))


def _second_derivative(shear: float, lat: np.ndarray):
    u, _, d2u = _profile_for(shear)(lat)
    return u, d2u


def evaluate_shear(
    shear: float,
    orders=DEFAULT_ORDERS,
    physical: dict | None = None,
    truncation: tuple[int, int] = REPORTING_TRUNCATION,
) -> StabilityLadderRow:
    """Judge one member of the jet family by all three criteria."""
    physical = dict(physical or EARTH)
    profile = _profile_for(shear)

    permits, min_dQdy = rayleigh_kuo_verdict(shear, physical)
    ripa = ripa_diagnostics(profile, physical)

    rows = [
        resolved_growth_rate(m, profile, physical["R"], physical["Omega"], truncation)
        for m in orders
    ]
    growing = [
        r
        for r in rows
        if r["resolved"] and r["growth_rate_s"] is not None and r["growth_rate_s"] > GROWTH_FLOOR_S
    ]
    peak = max(growing, key=lambda r: r["growth_rate_s"]) if growing else None

    return StabilityLadderRow(
        shear_parameter_S=float(shear),
        umax_m_s=float(shear * UMAX),
        rayleigh_kuo_permits=permits,
        min_dQdy=min_dQdy,
        ripa_certifies_stable=bool(ripa["certifies_stable"]),
        ripa_condition_i=bool(ripa["condition_i_pv_gradient"]),
        ripa_condition_ii=bool(ripa["condition_ii_criticality"]),
        ripa_criticality_margin=float(ripa["criticality_margin"]),
        m_star=int(peak["m"]) if peak else None,
        sigma_max_s=float(peak["growth_rate_s"]) if peak else None,
        e_folding_days=float(peak["e_folding_days"]) if peak else None,
        n_resolved_growing=len(growing),
    )


def sweep_shear_ladder(
    shear_values=(0.05, 0.1, 0.25, 0.5, 1.0),
    orders=DEFAULT_ORDERS,
    physical: dict | None = None,
    truncation: tuple[int, int] = REPORTING_TRUNCATION,
) -> list[StabilityLadderRow]:
    """The full table: parameter, necessary verdict, sufficient verdict, actual rate.

    This is exactly the structure needed to locate the three thresholds, and it is
    the table the manuscript's stability figure is drawn from.
    """
    return [evaluate_shear(s, orders, physical, truncation) for s in shear_values]


def locate_thresholds(
    orders=DEFAULT_ORDERS,
    physical: dict | None = None,
    bracket: tuple[float, float] = (0.05, 1.0),
    truncation: tuple[int, int] = REPORTING_TRUNCATION,
    tolerance: float = 0.01,
) -> ThresholdSet:
    """Find all three thresholds: where each criterion switches, and where growth starts.

    The Rayleigh-Kuo threshold is closed form — the curvature term is exactly
    linear in ``S`` while ``beta`` does not depend on the jet at all, so the
    critical value is a minimum of a ratio rather than a search. Ripa's is found by
    checking its two conditions on either side of that value. The onset of actual
    growth has no closed form and is bisected.

    **The onset is bisected at the reporting truncation, and it has to be.** The
    obvious economy — narrow the bracket cheaply at a coarser truncation, since
    only the existence of a growing mode is in question — gives a different answer,
    and measurably so: at ``N = 120/240`` the ``S = 0.25`` jet's fastest mode has a
    growth rate of ``3.5225e-6`` while the resolution-doubling filter rejects it as
    unresolved (it moves by 7.3e-3 between truncations), so a coarse search places
    the onset near ``S = 0.33``. At ``N = 240/480`` the same mode moves by only
    1.1e-4, is accepted, and the onset drops below 0.25. The rate is the same to
    four figures either way — what changes is whether the discretisation can
    *certify* it. Near a threshold, "does a growing mode exist" is therefore partly
    a statement about resolution, and the truncation used is reported alongside the
    answer rather than left implicit.
    """
    physical = dict(physical or EARTH)
    notes: list[str] = []

    rk = critical_shear_parameter(physical["R"], physical["Omega"])

    # Ripa: condition (i) is the same sign statement as Rayleigh-Kuo's, so unless
    # condition (ii) bites the two thresholds are identical. Check rather than
    # assume, on either side of the Rayleigh-Kuo value.
    #
    # The bracket is +/-10%, not a couple of per cent, and the same fine latitude
    # grid is handed to both. Near its compactly supported edges this jet's
    # curvature has structure on a shrinking scale, so *where* a grid happens to
    # place its points changes the sampled peak by a per cent or two — and a
    # bracket narrower than that grid sensitivity would compare the two criteria
    # on different effective thresholds and conclude, wrongly, that they differ.
    fine_lat = np.linspace(-np.pi / 2 + 1e-9, np.pi / 2 - 1e-9, 200_001)
    below = ripa_diagnostics(_profile_for(0.90 * rk), physical, lat=fine_lat)
    above = ripa_diagnostics(_profile_for(1.10 * rk), physical, lat=fine_lat)
    ripa_threshold = rk
    if below["certifies_stable"] and not above["certifies_stable"]:
        notes.append(
            "Ripa's sufficient threshold coincides with Rayleigh-Kuo's necessary one for "
            f"this family: condition (ii) is satisfied with a margin of "
            f"{below['criticality_margin']:.0f}, so it never binds and condition (i) fails "
            "exactly where dQ/dy first reverses"
        )
    else:
        ripa_threshold = float("nan")
        notes.append(
            "Ripa's threshold does NOT coincide with Rayleigh-Kuo's here; condition (ii) "
            "is binding, which changes the interpretation of the whole ladder"
        )

    lo, hi = bracket
    if evaluate_shear(hi, orders, physical, truncation).actually_grows is False:
        notes.append(f"no growing mode even at S = {hi}; the bracket does not contain the onset")
        return ThresholdSet(rk, ripa_threshold, float("nan"), (lo, hi), truncation, notes)
    if evaluate_shear(lo, orders, physical, truncation).actually_grows:
        notes.append(f"already growing at S = {lo}; the onset is below the bracket")
        return ThresholdSet(rk, ripa_threshold, float("nan"), (lo, hi), truncation, notes)

    while hi - lo > tolerance:
        mid = 0.5 * (lo + hi)
        if evaluate_shear(mid, orders, physical, truncation).actually_grows:
            hi = mid
        else:
            lo = mid

    return ThresholdSet(rk, ripa_threshold, 0.5 * (lo + hi), (lo, hi), truncation, notes)


def main(argv=None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--shear", type=float, nargs="*", default=[0.05, 0.1, 0.25, 0.5, 1.0])
    parser.add_argument("--thresholds", action="store_true", help="also bisect the growth onset")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    rows = sweep_shear_ladder(args.shear)
    payload = {"ladder": [r.as_dict() for r in rows]}
    if not args.json:
        print("[stability]     S  umax   RK permits  Ripa certifies   m*   sigma (1/s)   verdict")
        for r in rows:
            sigma = f"{r.sigma_max_s:.4e}" if r.sigma_max_s else "        --"
            print(
                f"[stability] {r.shear_parameter_S:5.3f} {r.umax_m_s:5.1f}   "
                f"{str(r.rayleigh_kuo_permits):>10s}   {str(r.ripa_certifies_stable):>13s}  "
                f"{str(r.m_star):>3s}   {sigma}   {r.verdict}"
            )
    if args.thresholds:
        thresholds = locate_thresholds()
        payload["thresholds"] = thresholds.as_dict()
        if not args.json:
            rk = thresholds.rayleigh_kuo_S
            print(f"[stability] Rayleigh-Kuo (necessary) threshold S = {rk:.4f}")
            print(f"[stability] Ripa (sufficient) threshold      S = {thresholds.ripa_S:.4f}")
            print(
                f"[stability] growth actually begins at        S = {thresholds.growth_onset_S:.4f} "
                f"(bracket {thresholds.growth_onset_bracket[0]:.4f}-"
                f"{thresholds.growth_onset_bracket[1]:.4f})"
            )
            for note in thresholds.notes:
                print(f"[stability]   note: {note}")
    if args.json:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "GROWTH_FLOOR_S",
    "PERSIST_RTOL",
    "StabilityLadderRow",
    "ThresholdSet",
    "evaluate_shear",
    "locate_thresholds",
    "rayleigh_kuo_verdict",
    "sweep_shear_ladder",
]
