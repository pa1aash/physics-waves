"""Mass, energy and potential enstrophy through a run — the solver's own honesty check.

Physics first. The rotating shallow-water system has three integral invariants,
and each of them fails in a different way when the numerics go wrong, which is
what makes the trio worth watching rather than any one of them alone.

**Mass** is conserved *exactly*. The continuity equation is a divergence, so on a
closed sphere the area integral of the column depth ``H + h`` cannot change at
all: there is nowhere for fluid to go. Nothing physical can move this number, and
hyperdiffusion cannot either, since it too enters as a divergence. Any drift is
therefore pure implementation error — a mis-signed flux, a broken quadrature, a
timestepper losing a term — and blueprint section 9.3 puts the tolerance at
``1e-10`` relative, which is to say "round-off, and nothing else".

**Energy** is conserved by the inviscid dynamics and is *drained* by
hyperdiffusion. With the momentum equation carrying ``+nu L^p u``, the energy
budget closes as ``dE/dt = -nu integral |L^(p/2) u|^2 dA <= 0``: the regulariser
can only remove energy, never supply it. So energy is allowed to fall and is not
allowed to rise, and how far it falls is a statement about how hard the
dissipation is working. Blueprint section 9.3 asks that the drift be small *and
decreasing with resolution* — the second half of which is a statement about a
ladder of runs and cannot be evaluated from one run, so :func:`verdicts` decides
only what a single run can decide and :func:`energy_ladder_verdict` does the rest.

**Potential enstrophy** — the area average of ``(zeta + f)^2 / (H + h)`` — is the
strictest of the three, and blueprint section 9.3 names it the early-warning
signal. Its physical content is the mechanism this whole project studies:
``q = (zeta + f)/h`` is materially conserved, so a flow can rearrange potential
vorticity but cannot manufacture it. A cascade to the grid scale lets
hyperdiffusion destroy the small-scale part, so **slow monotonic decay is
expected and acceptable**. Growth is not, in either sense — it means the
discretisation is creating potential vorticity out of nothing, which is precisely
what a nascent numerical instability looks like *before* it is visible in the
fields. It shows here first because the invariant is quadratic in vorticity and
so is dominated by exactly the smallest resolved scales where the trouble starts.

**What the `energy` diagnostic actually is.** The handler in
``src/solver/harness.py`` writes the area average of
``(H + h) |u|^2 / 2 + g h^2 / 2``. The textbook shallow-water energy density uses
``g (H + h)^2 / 2`` for the potential part, which exceeds this by
``g H^2 / 2 + g H h``; mass conservation makes the area average of that difference
an exact constant, so the two definitions differ by an additive constant. The
*change* in energy is therefore identical between them, and only the reference
value that the relative drift is normalised by differs. That is worth knowing
before comparing a drift here against a number computed with the other
convention.

The three series are written every ``spectra_cadence`` by the ``spectra`` handler
— already area-averaged, one scalar per output time — so this module reads rather
than recomputes them, and the quadrature that produced them is the solver's own.

**One numerical subtlety, which matters precisely because mass is exact.** The
drift is dimensionless, so it could be formed either from the stored working-unit
numbers or from their SI conversions. It is formed from the stored numbers. For a
quantity conserved to a single unit in the last place, dividing by the length
scaling re-rounds the mantissa and can erase the very signal being measured: on
run V-02 the stored mass series drifts by ``-1.46e-16`` and the same series
converted to metres first drifts by exactly zero. The conversion is not neutral at
round-off level, so the raw numbers are what get judged and the SI values are
carried alongside for legibility.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.diagnostics.slices import TASK_DIMENSIONS, read_handler

#: The three invariants, in the order blueprint section 9.3 lists them.
QUANTITIES = ("mass", "energy", "potential_enstrophy")

#: Blueprint section 9.3: mass relative drift must stay below this. It is a
#: round-off tolerance, not a physical one — mass is conserved exactly.
MASS_DRIFT_TOLERANCE = 1.0e-10

#: How much potential enstrophy may rise above its own running minimum, relative
#: to its initial value, before the run is called growing. The blueprint fixes no
#: number here, so this is the module's stated choice and every caller may
#: override it. The reasoning: unlike mass, potential enstrophy is not conserved
#: exactly by the discretisation even without dissipation, so its noise floor is
#: set by time-integration error rather than by round-off, and a strict
#: monotonicity test would fail a clean run on a wobble of a few parts in 1e9. A
#: genuine numerical instability, by contrast, grows exponentially and clears any
#: threshold of this order within a few e-foldings.
POTENTIAL_ENSTROPHY_RISE_TOLERANCE = 1.0e-6

#: Energy may not grow: the only non-conservative term in the equations is the
#: hyperdiffusion, and it is a sink. This is the round-off allowance on that
#: statement.
ENERGY_GROWTH_TOLERANCE = 1.0e-9

#: Optional magnitude bound on the energy drift of a *single* run. Left unset by
#: default and on purpose: the blueprint's energy criterion is "small, and
#: decreasing with resolution", and how small is small depends on what the flow is
#: doing. V-02 (a steady state) loses 4e-5 of its energy in five days while I-00
#: (a jet rolling up into vortices, with a real enstrophy cascade for the
#: hyperdiffusion to drain) loses 6.6e-2 in fifteen — and the second is physics,
#: not a defect. Any fixed threshold would either miss the first or condemn the
#: second, so the test that means something is the ladder.
ENERGY_DRIFT_TOLERANCE: float | None = None


@dataclass(frozen=True)
class ConservationSeries:
    """The three invariants of one run through time, and their drift from ``t = 0``.

    ``values`` holds the quantities in SI, one scalar per output time, for reading
    and plotting. ``values_working`` holds them exactly as the solver wrote them,
    and it is these that ``relative_drift`` is formed from — see the module
    docstring on why that distinction is not pedantry for mass.

    ``relative_drift`` holds ``(X(t) - X(0)) / X(0)`` for each: the dimensionless
    form every criterion is stated in, and the form in which runs at different
    depths and resolutions can be compared at all.
    """

    run_id: str
    time_s: np.ndarray
    values: dict[str, np.ndarray]
    values_working: dict[str, np.ndarray]
    relative_drift: dict[str, np.ndarray]
    initial: dict[str, float]

    @property
    def time_days(self) -> np.ndarray:
        return self.time_s / 86400.0

    @property
    def n_times(self) -> int:
        return int(self.time_s.size)

    def net_drift(self, quantity: str) -> float:
        """Relative drift accumulated over the whole integration."""
        return float(self.relative_drift[quantity][-1])

    def max_abs_drift(self, quantity: str) -> float:
        """Largest relative departure from the initial value at any output time."""
        return float(np.max(np.abs(self.relative_drift[quantity])))


@dataclass(frozen=True)
class Verdict:
    """One quantity judged against one blueprint criterion, with its reasoning.

    ``reason`` is written to be readable in a report without the code beside it:
    it names the number measured, the number required, and what a failure would
    physically mean.
    """

    quantity: str
    passed: bool
    criterion: str
    reason: str
    measured: dict

    def as_dict(self) -> dict:
        return {
            "quantity": self.quantity,
            "passed": self.passed,
            "criterion": self.criterion,
            "reason": self.reason,
            "measured": self.measured,
        }


def relative_drift(values: np.ndarray) -> np.ndarray:
    """``(X - X(0)) / X(0)``, the dimensionless drift every criterion is stated in."""
    values = np.asarray(values, dtype=float)
    initial = values.flat[0]
    if initial == 0.0:
        raise ValueError(
            "the initial value is zero, so a relative drift is undefined; this "
            "quantity has to be judged in absolute terms"
        )
    return (values - initial) / initial


def conservation_series(run, *, runs_root: Path | None = None) -> ConservationSeries:
    """Read one run's mass, energy and potential-enstrophy series, with their drift.

    The three are written by the ``spectra`` handler as pre-averaged scalars, one
    per output time, so what happens here is a read, a unit conversion and a
    normalisation — the area quadrature was the solver's, on the solver's own
    grid, which is the only place it can be done exactly.
    """
    output = read_handler(run, "spectra", tasks=list(QUANTITIES), to_si=False, runs_root=runs_root)
    working = {name: np.asarray(output.tasks[name]).reshape(-1) for name in QUANTITIES}
    si = {
        name: output.units.to_si(
            series, length=TASK_DIMENSIONS[name][0], time=TASK_DIMENSIONS[name][1]
        )
        for name, series in working.items()
    }
    return ConservationSeries(
        run_id=output.run_id,
        time_s=output.time_s,
        values=si,
        values_working=working,
        relative_drift={name: relative_drift(series) for name, series in working.items()},
        initial={name: float(series[0]) for name, series in si.items()},
    )


def _rise_above_running_minimum(values: np.ndarray) -> float:
    """Largest rise above the running minimum, relative to the initial value.

    This is the growth measure, and it is deliberately not "is the series
    monotonic". A quantity that falls, wobbles up by a part in a billion, and then
    resumes falling has not grown in any sense a physicist would defend; a quantity
    that turns around and climbs has, even if it never regains its starting value.
    Measuring the rise above the running minimum catches the second and forgives
    the first.
    """
    values = np.asarray(values, dtype=float)
    running_min = np.minimum.accumulate(values)
    return float(np.max((values - running_min) / abs(values[0])))


def verdicts(
    series: ConservationSeries,
    *,
    mass_tolerance: float = MASS_DRIFT_TOLERANCE,
    energy_drift_tolerance: float | None = ENERGY_DRIFT_TOLERANCE,
    enstrophy_rise_tolerance: float = POTENTIAL_ENSTROPHY_RISE_TOLERANCE,
) -> dict[str, Verdict]:
    """Apply the three blueprint section 9.3 criteria and say what each one decided.

    Returns one :class:`Verdict` per quantity. Only what a *single* run can decide
    is decided here: the resolution half of the energy criterion needs a ladder and
    belongs to :func:`energy_ladder_verdict`.
    """
    results: dict[str, Verdict] = {}

    # --- mass: exactly conserved, so any drift at all is implementation error ---
    mass_net = series.net_drift("mass")
    mass_max = series.max_abs_drift("mass")
    results["mass"] = Verdict(
        quantity="mass",
        passed=bool(mass_max < mass_tolerance),
        criterion=f"relative drift below {mass_tolerance:.0e}",
        reason=(
            f"net drift {mass_net:+.3e}, largest departure {mass_max:.3e}. "
            + (
                "Mass is conserved exactly by the continuity equation on a closed "
                "sphere, so this is round-off."
                if mass_max < mass_tolerance
                else "Mass cannot move physically; a drift this large is an "
                "implementation error and must be investigated before anything "
                "downstream is believed."
            )
        ),
        measured={"net_relative_drift": mass_net, "max_abs_relative_drift": mass_max},
    )

    # --- energy: may fall, may not rise; the magnitude test needs a ladder ------
    energy_net = series.net_drift("energy")
    energy_rise = _rise_above_running_minimum(series.values_working["energy"])
    grew = energy_net > ENERGY_GROWTH_TOLERANCE
    too_large = energy_drift_tolerance is not None and abs(energy_net) > energy_drift_tolerance
    if grew:
        energy_reason = (
            f"energy grew by {energy_net:+.3e}. The only non-conservative term in "
            "the equations is the hyperdiffusion and it is a sink, so a numerical "
            "source is being created."
        )
    elif too_large:
        energy_reason = (
            f"energy fell by {abs(energy_net):.3e}, above the requested bound of "
            f"{energy_drift_tolerance:.1e}: excess hyperdiffusion, or a timestep "
            "too large for the scheme."
        )
    else:
        energy_reason = (
            f"energy fell by {abs(energy_net):.3e} over {series.time_days[-1]:.2f} "
            "days and never rose, which is what a dissipative regulariser does. "
            "The other half of the criterion — that this shrinks with resolution — "
            "is a statement about a ladder of runs and is untested by this one; "
            "see energy_ladder_verdict."
        )
    results["energy"] = Verdict(
        quantity="energy",
        passed=bool(not grew and not too_large),
        criterion="small relative drift, decreasing with resolution; no growth",
        reason=energy_reason,
        measured={
            "net_relative_drift": energy_net,
            "max_relative_rise": energy_rise,
            "magnitude_bound": energy_drift_tolerance,
        },
    )

    # --- potential enstrophy: decay acceptable, growth is not ------------------
    pe_values = series.values_working["potential_enstrophy"]
    pe_net = series.net_drift("potential_enstrophy")
    pe_rise = _rise_above_running_minimum(pe_values)
    strictly_monotone = bool(np.all(np.diff(pe_values) <= 0.0))
    pe_grew = pe_net > enstrophy_rise_tolerance or pe_rise > enstrophy_rise_tolerance
    if pe_grew:
        pe_reason = (
            f"potential enstrophy rose by {pe_rise:.3e} above its running minimum "
            f"(net drift {pe_net:+.3e}), past the {enstrophy_rise_tolerance:.0e} "
            "allowance. Potential vorticity is materially conserved, so the "
            "discretisation is manufacturing it — the early-warning signature of a "
            "numerical instability."
        )
    elif strictly_monotone:
        pe_reason = (
            f"monotonic decay of {abs(pe_net):.3e} over {series.time_days[-1]:.2f} "
            "days: the enstrophy cascade reaches the grid scale and the "
            "hyperdiffusion drains it there, which is what the regulariser is for."
        )
    else:
        pe_reason = (
            f"net decay of {abs(pe_net):.3e}, not strictly monotone but with the "
            f"largest rise above its running minimum only {pe_rise:.3e}, inside the "
            f"{enstrophy_rise_tolerance:.0e} allowance for time-integration noise. "
            "No growth."
        )
    results["potential_enstrophy"] = Verdict(
        quantity="potential_enstrophy",
        passed=bool(not pe_grew),
        criterion="monotonic slow decay acceptable, growth is not",
        reason=pe_reason,
        measured={
            "net_relative_drift": pe_net,
            "max_relative_rise": pe_rise,
            "strictly_monotone_decay": strictly_monotone,
            "rise_tolerance": enstrophy_rise_tolerance,
        },
    )
    return results


def energy_ladder_verdict(drift_by_resolution: dict[str, float]) -> Verdict:
    """The half of the energy criterion that needs more than one run.

    Blueprint section 9.3 asks that the energy drift be small *and decreasing with
    resolution*. That second clause is the one with teeth: a drift that does not
    shrink as the grid is refined is not discretisation error being resolved away,
    it is a fixed dissipative loss the scheme will carry at any resolution.

    ``drift_by_resolution`` maps a resolution label from the ladder
    (``"L0"``, ``"L1"``, ``"L2"``, ``"L3"``) to that run's net relative energy
    drift. The labels are ordered by the ladder, not alphabetically by accident.
    """
    ladder = [key for key in ("L0", "L1", "L2", "L3") if key in drift_by_resolution]
    unknown = sorted(set(drift_by_resolution) - set(ladder))
    if unknown:
        raise ValueError(f"unknown resolution labels {unknown}; the ladder is L0, L1, L2, L3")
    if len(ladder) < 2:
        return Verdict(
            quantity="energy",
            passed=False,
            criterion="relative energy drift decreasing with resolution",
            reason=(
                "fewer than two rungs supplied, so the trend with resolution "
                "cannot be evaluated. This is undecided, not passed."
            ),
            measured={"rungs": ladder},
        )
    magnitudes = [abs(float(drift_by_resolution[key])) for key in ladder]
    decreasing = all(
        second < first for first, second in zip(magnitudes, magnitudes[1:], strict=False)
    )
    listing = ", ".join(f"{key} {value:.3e}" for key, value in zip(ladder, magnitudes, strict=True))
    return Verdict(
        quantity="energy",
        passed=bool(decreasing),
        criterion="relative energy drift decreasing with resolution",
        reason=(
            f"|drift| = {listing}"
            + (
                ". Refining the grid removes it, so it is discretisation error."
                if decreasing
                else ". It does not shrink with the grid, so it is a fixed "
                "dissipative loss rather than resolvable error."
            )
        ),
        measured=dict(zip(ladder, magnitudes, strict=True)),
    )


def summarise(run, *, runs_root: Path | None = None, **tolerances) -> dict:
    """One run's conservation record and verdicts, as a JSON-serialisable dict."""
    series = conservation_series(run, runs_root=runs_root)
    judged = verdicts(series, **tolerances)
    return {
        "run_id": series.run_id,
        "n_output_times": series.n_times,
        "integration_days": float(series.time_days[-1]),
        "initial_values_si": series.initial,
        "net_relative_drift": {name: series.net_drift(name) for name in QUANTITIES},
        "max_abs_relative_drift": {name: series.max_abs_drift(name) for name in QUANTITIES},
        "verdicts": {name: verdict.as_dict() for name, verdict in judged.items()},
        "all_passed": all(verdict.passed for verdict in judged.values()),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", nargs="+", help="run IDs or run directories")
    parser.add_argument("--runs-root", default=None, help="where run directories live")
    parser.add_argument("--json", action="store_true", help="emit the full record as JSON")
    args = parser.parse_args(argv)

    root = Path(args.runs_root) if args.runs_root else None
    records = [summarise(run, runs_root=root) for run in args.runs]

    if args.json:
        print(json.dumps(records, indent=2))
        return 0 if all(record["all_passed"] for record in records) else 1

    for record in records:
        print(
            f"[conservation] {record['run_id']}: {record['integration_days']:.2f} days, "
            f"{record['n_output_times']} output times"
        )
        for name in QUANTITIES:
            verdict = record["verdicts"][name]
            print(
                f"  {name:20s} drift {record['net_relative_drift'][name]:+.4e}  "
                f"{'PASS' if verdict['passed'] else 'FAIL'}  {verdict['reason']}"
            )
    return 0 if all(record["all_passed"] for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
