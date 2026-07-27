"""How often a run must be written out, given how fast its wave travels.

Physics first. A Rossby-Haurwitz mode of total spherical-harmonic degree ``n``
travels westward with angular phase speed

    c_ang = -2 Omega / [n(n+1)]                                    eq. (rhdisp)

— the same relation ``src/analysis/hough.py`` predicts against, restated here so
that the solver side does not have to import the analysis side to know how fast
the thing it is integrating moves. The two are asserted equal in
``tests/test_sweep_cadence.py``; if one is ever edited without the other, that
test fails.

**The consequence for output.** ``c_ang`` is *linear in* ``Omega``. Double the
rotation rate and the pattern crosses the sphere twice as fast, so a fixed output
interval buys half as many samples per wave period. The rotation sweep
(``P-08`` … ``P-12``) spans ``0.25 Omega_0`` to ``4 Omega_0``, a factor of sixteen
in phase speed, while every one of those configs states the same
``snapshot_cadence: 86400``. At Earth rate that cadence advances the order-``m=2``
phase by ``0.40 pi`` per sample — comfortable. At ``4 Omega_0`` it advances it by
``1.60 pi``, past Nyquist, and the measurement is destroyed.

**Destroyed silently, which is the whole point.** Phase unwrapping folds every
increment into ``(-pi, pi]``, so a true step of ``1.60 pi`` is observed as
``-0.40 pi``: a *slower* wave going the *other way*. The fit returns
``c_ang = +7.19e-6`` where the truth is ``-2.92e-5`` — wrong by a factor of four,
with the sign reversed, which for this project is the difference between
confirming Rossby-Haurwitz and refuting it. Worse, the margin indicator that can
be computed from the series alone reads ``0.40 pi``, i.e. "comfortably resolved".
``src/analysis/fit_phase_speed.py`` documents why that indicator can never catch
this: measured on the output, aliasing hides itself.

So the safeguard has to be applied **before the run**, not diagnosed after it,
and it has to be applied by the thing that plans the sweep rather than by whoever
happens to read the config. That is what this module is for.

**The rule.** Hold the number of samples per wave period constant across the
sweep by scaling the interval inversely with rotation rate:

    dt(Omega) = dt_0 * Omega_0 / Omega                             eq. (cadscale)

Since the phase step is ``m |c_ang| dt = 2 m Omega dt / [n(n+1)]`` and ``Omega``
appears once in each factor, the product is invariant. Every member of the
rotation sweep is then sampled at the same phase density, so a residual trend of
measured speed against ``Omega`` is physics rather than a sampling artefact —
which matters, because that trend *is* the campaign's result.

**Rotation is not the only thing that makes a wave fast, so there are two
bounds.** Eq. (cadscale) is a *relative* statement — it holds sampling constant
against the Earth-rate member of the same sweep — and it therefore says nothing
about the wavenumber sweep, where ``Omega`` is fixed and ``n`` varies instead.
There it is ``1/[n(n+1)]`` that does the work: ``P-01`` at ``n = 2`` travels five
times faster than ``P-07`` at ``n = 8``, and the shared Earth-rate snapshot
cadence advances its phase by ``1.34 pi`` per sample. Aliased, at Earth rate,
with no rotation factor available to rescue it. So :func:`nyquist_safe_cadence`
supplies an absolute floor from the mode itself, eq. (cadsafe), and a plan
applies whichever bound is tighter, recording which one bound it in
``CadenceDecision.bound_by``.

**Overridden is not the same as rescued.** Scaling to constant density will
sometimes tighten a cadence that was never in danger: ``slice_cadence: 3600`` at
``4 Omega_0`` sits at ``0.067 pi`` per sample, perfectly safe, and is still
tightened to ``900`` so its sampling density matches the rest of the sweep. That
is a methodological override. :class:`CadenceDecision` records
``aliased_as_stated`` separately from ``overridden`` so a plan file never makes
the two look alike.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.solver.equations import EARTH

#: Earth's rotation rate, the reference against which a sweep's cadences scale.
#: Taken from the same table the solver builds its Coriolis parameter from, so a
#: config at ``omega_multiplier: 1.0`` scales by exactly one.
EARTH_OMEGA: float = float(EARTH["Omega"])

#: The three output streams a run config declares. All three scale together:
#: they sample the same moving wave, and a Hovmoller diagram is assembled from
#: whichever of them is available (see ``src/analysis/extract_hovmoller.py``), so
#: leaving one unscaled leaves one route to a wrong answer open.
CADENCE_KEYS: tuple[str, ...] = ("snapshot_cadence", "slice_cadence", "spectra_cadence")

#: Phase advance per sample, as a fraction of ``pi``, above which the sampling is
#: aliased outright. Exactly 1.0 is the Nyquist limit; there is no tolerance to
#: choose here, it is where unwrapping stops being invertible.
NYQUIST_LIMIT_PI: float = 1.0

#: The phase step the safety floor targets, as a fraction of ``pi``. Set at the
#: boundary ``src/analysis/fit_phase_speed.py`` uses to stop calling a fit's
#: aliasing risk "none", so a cadence this module applies is one that fitter will
#: not complain about. Sitting just under the Nyquist limit would be resolved in
#: principle and worthless in practice: a wave sampled twice per period has no
#: margin for a mode whose speed differs from the prediction, which is precisely
#: the departure this campaign is trying to measure.
SAFE_PHASE_STEP_PI: float = 0.5

#: Below this many samples across the whole integration a fit is reported as
#: thin. Scaling *up* at low rotation rates is correct — the wave really is
#: slower — but a 20-day run at ``0.25 Omega_0`` yields five snapshots, and that
#: is worth saying out loud in the plan rather than discovering in the fit.
THIN_SAMPLE_COUNT: int = 12


def angular_phase_speed(degree_n: int, omega: float) -> float:
    """``c_ang = -2 Omega / [n(n+1)]``, eq. (rhdisp). Negative is westward."""
    if degree_n < 1:
        raise ValueError(f"degree n must be at least 1, got {degree_n}")
    return -2.0 * omega / (degree_n * (degree_n + 1))


def scale_cadence(
    baseline_cadence_s: float,
    omega: float,
    omega_reference: float = EARTH_OMEGA,
) -> float:
    """``dt(Omega) = dt_0 Omega_0 / Omega``, eq. (cadscale).

    ``baseline_cadence_s`` is the interval that samples the mode acceptably at
    ``omega_reference`` — in this project, the Earth-rate member of the sweep.
    The returned interval samples it at the same phase density at ``omega``.

    Note this needs neither ``n`` nor ``m``: both cancel out of the ratio, which
    is why one scaling serves every mode in the campaign. They are needed only to
    say *how* dense that density is, which :func:`phase_step_rad` reports.
    """
    if baseline_cadence_s <= 0:
        raise ValueError(f"baseline cadence must be positive, got {baseline_cadence_s}")
    if omega <= 0:
        raise ValueError(
            f"rotation rate must be positive to scale a cadence, got {omega}. "
            "A non-rotating sphere has no Rossby wave to sample."
        )
    return baseline_cadence_s * omega_reference / omega


def phase_step_rad(cadence_s: float, degree_n: int, order_m: int, omega: float) -> float:
    """Phase advance of the order-``m`` component between consecutive samples.

    ``m |c_ang| dt``. Compare against ``pi``: at or above it, unwrapping picks the
    wrong branch and the fitted speed is an alias of the true one.
    """
    if order_m < 1:
        raise ValueError(f"zonal order m must be at least 1, got {order_m}")
    return order_m * abs(angular_phase_speed(degree_n, omega)) * cadence_s


def samples_per_period(cadence_s: float, degree_n: int, order_m: int, omega: float) -> float:
    """How many samples fall in one full period of the order-``m`` component."""
    step = phase_step_rad(cadence_s, degree_n, order_m, omega)
    return math.inf if step == 0 else 2.0 * math.pi / step


def nyquist_safe_cadence(
    degree_n: int,
    order_m: int,
    omega: float,
    target_phase_step_pi: float = SAFE_PHASE_STEP_PI,
) -> float:
    """The longest interval that still resolves this mode, with margin.

    Inverting ``m |c_ang| dt = target * pi`` gives

        dt_safe = target * pi * n(n+1) / (2 m Omega)                eq. (cadsafe)

    **This is a different constraint from eq. (cadscale), and it is needed because
    rotation rate is not the only thing that sets how fast the wave moves.** The
    density rule holds sampling constant *relative to the Earth-rate member of the
    same sweep*, which is exactly right for the rotation sweep and says nothing at
    all about the wavenumber sweep, where ``Omega`` is fixed and ``n`` varies.
    Since ``c_ang`` goes as ``1/[n(n+1)]``, the low-degree end is the fast end:
    ``P-01`` at ``n = 2`` travels five times faster than ``P-07`` at ``n = 8``, and
    the single Earth-rate cadence every stub shares advances its phase by
    ``1.34 pi`` per snapshot — past Nyquist, at Earth rate, with no rotation
    scaling available to rescue it.

    So a plan applies whichever of the two bounds is tighter. The density rule
    makes the rotation sweep comparable; this floor makes every run measurable.
    """
    if omega <= 0:
        raise ValueError(f"rotation rate must be positive, got {omega}")
    speed = abs(angular_phase_speed(degree_n, omega))
    if speed == 0:
        return math.inf
    return target_phase_step_pi * math.pi / (order_m * speed)


@dataclass(frozen=True)
class CadenceDecision:
    """What the plan does to one output cadence of one config, and why.

    ``overridden`` and ``aliased_as_stated`` are deliberately separate. The first
    says the plan changed the number; the second says the config as written would
    have produced a wrong answer. A cadence can be overridden for sampling-density
    parity without ever having been in danger, and a plan that conflated the two
    would make every override look like a near miss.
    """

    key: str
    stated_s: float | None
    required_s: float
    applied_s: float
    overridden: bool
    reason: str
    omega: float
    omega_ratio: float
    #: Which constraint set ``applied_s``: ``"stated"`` (the config was already
    #: fine), ``"density"`` (eq. cadscale, sweep comparability) or ``"nyquist"``
    #: (eq. cadsafe, the mode is simply too fast for the stated interval).
    bound_by: str = "stated"
    safe_s: float | None = None
    phase_step_stated_pi: float | None = None
    phase_step_applied_pi: float | None = None
    aliased_as_stated: bool = False
    samples_over_run: float | None = None
    thin: bool = False

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class CadencePlan:
    """Every cadence decision for one config, plus the mode it was judged against."""

    run_id: str
    omega: float
    omega_ratio: float
    degree_n: int | None
    order_m: int | None
    decisions: dict[str, CadenceDecision] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def overrides(self) -> dict[str, float]:
        """Just the cadences that changed, ready to merge into a run's outputs."""
        return {k: d.applied_s for k, d in self.decisions.items() if d.overridden}

    @property
    def would_have_aliased(self) -> list[str]:
        return [k for k, d in self.decisions.items() if d.aliased_as_stated]

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "omega": self.omega,
            "omega_ratio": self.omega_ratio,
            "degree_n": self.degree_n,
            "order_m": self.order_m,
            "decisions": {k: d.as_dict() for k, d in self.decisions.items()},
            "overrides": self.overrides,
            "would_have_aliased": self.would_have_aliased,
            "notes": list(self.notes),
        }


def plan_cadences(
    config: dict,
    baseline: dict[str, float] | None = None,
    omega_reference: float = EARTH_OMEGA,
) -> CadencePlan:
    """Decide every output cadence for one config, scaled to its rotation rate.

    ``baseline`` is the Earth-rate cadence for each key. It defaults to the
    config's own stated cadences, which is the right default for this project:
    every ``P-*`` stub was written with the same Earth-rate numbers, so reading
    the baseline off the config and scaling it reproduces exactly the intent the
    stub had before the rotation sweep broke it.

    A config whose stated cadence is already at least as fine as the requirement
    is left alone — the plan tightens sampling, it never loosens it.
    """
    run_id = str(config.get("run_id", "<unnamed>"))
    physical = config.get("physical") or {}
    outputs = config.get("outputs") or {}
    numerics = config.get("numerics") or {}
    params = config.get("initial_condition_params") or {}

    omega = float(physical["Omega"])
    omega_ratio = omega / omega_reference

    degree_n = params.get("degree_n")
    order_m = params.get("order_m")
    degree_n = int(degree_n) if degree_n is not None else None
    order_m = int(order_m) if order_m is not None else None

    plan = CadencePlan(
        run_id=run_id,
        omega=omega,
        omega_ratio=omega_ratio,
        degree_n=degree_n,
        order_m=order_m,
    )

    # The rotation configs declare their multiplier as well as their absolute
    # rate. The harness already warns when the two disagree; the plan refuses,
    # because a plan built on the stale one of the pair would scale every cadence
    # in the run by the wrong factor.
    multiplier = params.get("omega_multiplier")
    if multiplier is not None and not math.isclose(float(multiplier), omega_ratio, rel_tol=1e-6):
        raise ValueError(
            f"{run_id}: initial_condition_params.omega_multiplier is {multiplier} but "
            f"physical.Omega / Omega_0 is {omega_ratio:.6g}. One of the two is stale, "
            "and a cadence scaled by the wrong one is worse than an unscaled cadence."
        )

    if degree_n is None or order_m is None:
        plan.notes.append(
            "the config does not declare degree_n / order_m, so cadences are scaled by "
            "rotation rate but their phase step cannot be reported; this is expected for "
            "the jet and benchmark cases, which are not single-mode"
        )

    stop_sim_time = numerics.get("stop_sim_time")
    stop_sim_time = float(stop_sim_time) if isinstance(stop_sim_time, int | float) else None

    for key in CADENCE_KEYS:
        stated = outputs.get(key)
        if not isinstance(stated, int | float) or stated <= 0:
            continue  # a disabled stream (0 / false) has no cadence to scale
        stated = float(stated)
        base = float((baseline or {}).get(key, stated))
        required = scale_cadence(base, omega, omega_reference)

        # The Nyquist floor, where the mode is known. This is independent of the
        # density rule and binds where that rule cannot reach -- most visibly at
        # the fast, low-degree end of the wavenumber sweep, where Omega is fixed
        # at Earth rate and there is no scaling factor to apply.
        safe = None
        if degree_n is not None and order_m is not None:
            safe = nyquist_safe_cadence(degree_n, order_m, omega)

        # Tighten, never loosen: apply whichever bound is tightest, and record
        # which one it was. A config that already samples finer than both is
        # respected exactly as written.
        target = required if safe is None else min(required, safe)
        if stated <= target * (1.0 + 1e-9):
            applied, overridden, bound_by = stated, False, "stated"
            reason = (
                f"stated {stated:g} s already samples at least as finely as the "
                f"{target:g} s required at Omega = {omega_ratio:g} Omega_0"
            )
        elif safe is not None and safe < required:
            applied, overridden, bound_by = safe, True, "nyquist"
            reason = (
                f"stated {stated:g} s advances the phase of the (n={degree_n}, m={order_m}) "
                f"mode too far per sample; overridden to {safe:g} s, the longest interval "
                f"that keeps the step at {SAFE_PHASE_STEP_PI:g} x pi, eq. (cadsafe)"
            )
        else:
            applied, overridden, bound_by = required, True, "density"
            reason = (
                f"stated {stated:g} s is coarser than the {required:g} s required to hold "
                f"sampling density constant at Omega = {omega_ratio:g} Omega_0 "
                f"(baseline {base:g} s at Earth rate); overridden by the plan"
            )

        step_stated = step_applied = None
        aliased = False
        if degree_n is not None and order_m is not None:
            step_stated = phase_step_rad(stated, degree_n, order_m, omega) / math.pi
            step_applied = phase_step_rad(applied, degree_n, order_m, omega) / math.pi
            aliased = step_stated >= NYQUIST_LIMIT_PI

        n_samples = stop_sim_time / applied if stop_sim_time else None
        thin = bool(n_samples is not None and n_samples < THIN_SAMPLE_COUNT)

        decision = CadenceDecision(
            key=key,
            stated_s=stated,
            required_s=required,
            applied_s=applied,
            overridden=overridden,
            reason=reason,
            omega=omega,
            omega_ratio=omega_ratio,
            bound_by=bound_by,
            safe_s=safe,
            phase_step_stated_pi=step_stated,
            phase_step_applied_pi=step_applied,
            aliased_as_stated=aliased,
            samples_over_run=n_samples,
            thin=thin,
        )
        plan.decisions[key] = decision

        if aliased:
            plan.notes.append(
                f"{key}: as stated, the phase advances {step_stated:.2f} x pi per sample — "
                f"past Nyquist. Unwrapping would have returned an alias, most likely of the "
                f"wrong sign. Overridden to {applied:g} s ({step_applied:.2f} x pi)."
            )
        if thin:
            plan.notes.append(
                f"{key}: the scaled cadence yields only {n_samples:.0f} samples across the "
                f"integration. Correct — the wave is genuinely slower at "
                f"{omega_ratio:g} Omega_0 — but the fit will be correspondingly noisier, and "
                "lengthening stop_sim_time is the honest remedy, not re-coarsening the fit."
            )

    return plan
