"""The rotation sweep's cadence must scale with Omega, and here is what happens if it does not.

This file exists because of a specific, recoverable-only-by-luck failure: a
phase-speed run whose output cadence was chosen at Earth rate and then reused at
four times Earth rate returns a confident, precisely-quoted phase speed that is
wrong by a factor of four **with the sign reversed**, while every check that can
be computed from the output series alone reports the sampling as comfortable.

The tests below are ordered as the argument runs:

1. the scaling factor is right in both directions (``4 Omega_0`` down, ``0.25
   Omega_0`` up), and holds sampling density exactly constant;
2. the failure is real — a synthetic wave sampled at the *unscaled* cadence is
   recovered as an alias, wrong sign and all;
3. the naive margin indicator does not catch it, which is why the fix has to live
   in the sweep generator rather than in the fitter;
4. the same wave sampled at the *scaled* cadence is recovered correctly, to
   better than the project's 0.1% fitter tolerance;
5. the real ``configs/phase_speed/`` rotation sweep is planned correctly.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import yaml

from src.analysis.fit_phase_speed import fit_phase_speed
from src.analysis.hough import nondivergent_angular_phase_speed
from src.solver.cadence import (
    EARTH_OMEGA,
    angular_phase_speed,
    phase_step_rad,
    plan_cadences,
    samples_per_period,
    scale_cadence,
)

#: The mode the rotation sweep holds fixed while it varies Omega (P-08 ... P-12).
DEGREE_N = 4
ORDER_M = 2

#: The cadence every P-* stub states, chosen at Earth rate.
BASELINE_SNAPSHOT_S = 86400.0

#: The project's fitter tolerance, from tests/test_analysis_pipeline.py. A fitter
#: that recovers a known input to worse than 0.1% is not fit for this campaign.
FITTER_TOLERANCE = 1e-3

REPO_CONFIGS = "configs/phase_speed"


def synthetic_hovmoller(
    c_angular: float,
    time_s: np.ndarray,
    order_m: int = ORDER_M,
    n_longitude: int = 128,
    amplitude: float = 1.0,
    phase0: float = 0.37,
) -> np.ndarray:
    """A single travelling harmonic on a latitude circle, exactly.

    ``h(lambda, t) = A cos(m lambda + psi(t))`` with ``psi = -m c_ang t``, which is
    the convention ``fit_phase_speed`` inverts: it recovers ``c_ang = -(dpsi/dt)/m``.
    No noise, no other modes — the point of these tests is that the *sampling*
    breaks the measurement, so everything else must be perfect.
    """
    lon = np.linspace(0.0, 2.0 * np.pi, n_longitude, endpoint=False)
    psi = -order_m * c_angular * np.asarray(time_s, dtype=float) + phase0
    return amplitude * np.cos(order_m * lon[None, :] + psi[:, None])


def config_at(omega_ratio: float, **overrides) -> dict:
    """A minimal phase-speed config at a given multiple of Earth's rotation rate."""
    config = {
        "run_id": f"P-TEST-{omega_ratio:g}",
        "campaign": "phase_speed",
        "resolution": "L1",
        "initial_condition": "single_harmonic",
        "physical": {
            "R": 6371220.0,
            "Omega": EARTH_OMEGA * omega_ratio,
            "g": 9.80616,
            "H": 10000.0,
        },
        "numerics": {"stop_sim_time": 1728000.0},
        "outputs": {
            "snapshot_cadence": BASELINE_SNAPSHOT_S,
            "slice_cadence": 3600.0,
            "spectra_cadence": 3600.0,
            "write_full_fields": False,
        },
        "initial_condition_params": {
            "degree_n": DEGREE_N,
            "order_m": ORDER_M,
            "omega_multiplier": omega_ratio,
        },
    }
    for key, value in overrides.items():
        config[key] = value
    return config


# --------------------------------------------------------------------------
# 0. The dispersion relation this module restates must equal the one the
#    analysis side predicts against. Two copies of eq. (rhdisp) exist; if they
#    ever disagree, every cadence in every plan is scaled against a different
#    wave from the one the fit is compared with.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("degree_n", [1, 2, 4, 8, 16])
@pytest.mark.parametrize("omega_ratio", [0.25, 1.0, 4.0])
def test_the_two_copies_of_the_dispersion_relation_agree(degree_n, omega_ratio):
    omega = EARTH_OMEGA * omega_ratio
    assert angular_phase_speed(degree_n, omega) == pytest.approx(
        nondivergent_angular_phase_speed(degree_n, omega), rel=1e-15
    )


# --------------------------------------------------------------------------
# 1. The scaling factor, in both directions.
# --------------------------------------------------------------------------


def test_cadence_scales_down_by_four_at_four_times_earth_rotation():
    """At 4 Omega_0 the wave is 4x faster, so the interval must be 4x shorter."""
    scaled = scale_cadence(BASELINE_SNAPSHOT_S, EARTH_OMEGA * 4.0)
    assert scaled == pytest.approx(BASELINE_SNAPSHOT_S / 4.0, rel=1e-12)
    assert scaled < BASELINE_SNAPSHOT_S


def test_cadence_scales_up_by_four_at_a_quarter_of_earth_rotation():
    """At 0.25 Omega_0 the wave is 4x slower, so sampling that fast is waste."""
    scaled = scale_cadence(BASELINE_SNAPSHOT_S, EARTH_OMEGA * 0.25)
    assert scaled == pytest.approx(BASELINE_SNAPSHOT_S * 4.0, rel=1e-12)
    assert scaled > BASELINE_SNAPSHOT_S


@pytest.mark.parametrize("omega_ratio", [0.25, 0.5, 1.0, 2.0, 4.0])
def test_scaling_holds_samples_per_period_exactly_constant(omega_ratio):
    """The invariant the scaling exists to enforce, checked across the sweep.

    ``m |c_ang| dt`` carries one factor of Omega in ``|c_ang|`` and one inverse
    factor in ``dt``, so the phase step per sample is the same at every rotation
    rate in the sweep. This is what makes a residual trend against Omega physics
    rather than a sampling artefact.
    """
    omega = EARTH_OMEGA * omega_ratio
    scaled = scale_cadence(BASELINE_SNAPSHOT_S, omega)
    reference = samples_per_period(BASELINE_SNAPSHOT_S, DEGREE_N, ORDER_M, EARTH_OMEGA)
    assert samples_per_period(scaled, DEGREE_N, ORDER_M, omega) == pytest.approx(
        reference, rel=1e-12
    )


def test_scaling_refuses_a_non_rotating_sphere():
    """There is no Rossby wave at Omega = 0, so there is no cadence to derive."""
    with pytest.raises(ValueError, match="rotation rate must be positive"):
        scale_cadence(BASELINE_SNAPSHOT_S, 0.0)


# --------------------------------------------------------------------------
# 2-4. The aliasing failure itself, reproduced and then fixed.
# --------------------------------------------------------------------------


def test_the_unscaled_cadence_aliases_at_four_times_earth_rotation():
    """The Session L6 failure, reproduced exactly.

    At 4 Omega_0 the true phase step at the stub's 86400 s cadence is 1.60 x pi.
    Unwrapping folds it to -0.40 x pi, so the fit reports a *slower* wave going
    the *wrong way*.
    """
    omega = EARTH_OMEGA * 4.0
    truth = angular_phase_speed(DEGREE_N, omega)

    step_pi = phase_step_rad(BASELINE_SNAPSHOT_S, DEGREE_N, ORDER_M, omega) / math.pi
    assert step_pi > 1.0, "this test is meaningless unless the stated cadence really aliases"
    assert step_pi == pytest.approx(1.604, abs=1e-3)

    time_s = np.arange(0.0, 40.0 * BASELINE_SNAPSHOT_S, BASELINE_SNAPSHOT_S)
    fit = fit_phase_speed(synthetic_hovmoller(truth, time_s), time_s, wavenumber=ORDER_M)

    # Westward truth, eastward answer: the sign is reversed.
    assert truth < 0.0
    assert fit.c_angular_rad_s > 0.0

    # And the magnitude is wrong by the factor the alias implies, ~4.
    assert abs(fit.c_angular_rad_s / truth) == pytest.approx(0.2468, abs=1e-3)

    # It is not a noisy answer. It is a precise, confident, wrong one: the
    # residual of the straight-line phase fit is at round-off.
    assert fit.residual_rms_rad < 1e-9


def test_the_naive_margin_indicator_does_not_catch_the_alias():
    """Why the fix cannot live in the fitter.

    The only quantity computable from the output series alone -- the largest
    wrapped phase step -- reads 0.40 x pi for the aliased run, which is the same
    comfortable number the correctly-sampled run reports. Measured on the series,
    aliasing hides itself.
    """
    omega = EARTH_OMEGA * 4.0
    truth = angular_phase_speed(DEGREE_N, omega)
    time_s = np.arange(0.0, 40.0 * BASELINE_SNAPSHOT_S, BASELINE_SNAPSHOT_S)

    fit = fit_phase_speed(synthetic_hovmoller(truth, time_s), time_s, wavenumber=ORDER_M)

    assert fit.nyquist_ratio < 0.5
    assert fit.aliasing_risk == "none"

    # Supplying the external expectation is the only thing that exposes it --
    # and that is a check the *analysis* can make afterwards, long after the
    # compute has been spent. The sweep generator is what prevents it.
    checked = fit_phase_speed(
        synthetic_hovmoller(truth, time_s),
        time_s,
        wavenumber=ORDER_M,
        expected_c_angular=truth,
    )
    assert checked.aliasing_risk == "severe"
    assert checked.alias_order is not None and checked.alias_order != 0


@pytest.mark.parametrize("omega_ratio", [0.25, 0.5, 1.0, 2.0, 4.0])
def test_the_scaled_cadence_recovers_the_true_phase_speed(omega_ratio):
    """The fix, across the whole rotation sweep.

    Same synthetic wave, same fitter, cadence scaled by eq. (cadscale): phase
    unwrapping now picks the right branch and the fit recovers the truth to
    better than the project's 0.1% tolerance -- including the sign.
    """
    omega = EARTH_OMEGA * omega_ratio
    truth = angular_phase_speed(DEGREE_N, omega)
    cadence = scale_cadence(BASELINE_SNAPSHOT_S, omega)

    time_s = np.arange(0.0, 40.0 * cadence, cadence)
    fit = fit_phase_speed(
        synthetic_hovmoller(truth, time_s),
        time_s,
        wavenumber=ORDER_M,
        expected_c_angular=truth,
    )

    assert fit.c_angular_rad_s < 0.0, "the recovered wave must still travel westward"
    assert fit.c_angular_rad_s == pytest.approx(truth, rel=FITTER_TOLERANCE)
    assert fit.aliasing_risk == "none"
    assert fit.alias_order in (0, None)


# --------------------------------------------------------------------------
# 5. The planner, and the real configs it will be pointed at.
# --------------------------------------------------------------------------


def test_the_plan_overrides_an_aliasing_cadence_and_says_so():
    plan = plan_cadences(config_at(4.0))
    snapshot = plan.decisions["snapshot_cadence"]

    assert snapshot.overridden is True
    assert snapshot.aliased_as_stated is True
    assert snapshot.applied_s == pytest.approx(BASELINE_SNAPSHOT_S / 4.0)
    assert snapshot.phase_step_applied_pi < 1.0
    assert "snapshot_cadence" in plan.would_have_aliased
    assert any("past Nyquist" in note for note in plan.notes)


def test_the_plan_separates_a_density_override_from_a_rescue():
    """slice_cadence at 4 Omega_0 is tightened, but was never aliased."""
    plan = plan_cadences(config_at(4.0))
    sliced = plan.decisions["slice_cadence"]

    assert sliced.overridden is True
    assert sliced.aliased_as_stated is False
    assert sliced.phase_step_stated_pi < 1.0
    assert sliced.applied_s == pytest.approx(900.0)


def test_the_plan_leaves_earth_rate_configs_untouched():
    plan = plan_cadences(config_at(1.0))
    assert plan.overrides == {}
    assert plan.would_have_aliased == []


def test_the_plan_scales_up_and_flags_the_thin_sample_count():
    """At 0.25 Omega_0 the cadence lengthens, and the plan says what that costs."""
    plan = plan_cadences(config_at(0.25))
    snapshot = plan.decisions["snapshot_cadence"]

    # The requirement really does scale up by four: at a quarter of Earth's
    # rotation the wave takes four times as long to travel a wavelength.
    assert snapshot.required_s == pytest.approx(BASELINE_SNAPSHOT_S * 4.0)

    # But sampling four times faster than required is merely wasteful, never
    # wrong, so the "tighten, never loosen" rule keeps the stated value and
    # records that it is finer than it needs to be.
    assert snapshot.applied_s == pytest.approx(BASELINE_SNAPSHOT_S)
    assert snapshot.overridden is False
    assert snapshot.required_s > snapshot.stated_s

    # But a stream that *was* already at the scaled value would be thin, and the
    # planner has to say so rather than let a five-sample fit look healthy.
    lean = config_at(0.25)
    lean["outputs"]["snapshot_cadence"] = BASELINE_SNAPSHOT_S * 4.0
    assert plan_cadences(lean).decisions["snapshot_cadence"].thin is True


def test_the_plan_refuses_a_config_whose_two_rotation_statements_disagree():
    config = config_at(4.0)
    config["initial_condition_params"]["omega_multiplier"] = 2.0
    with pytest.raises(ValueError, match="stale"):
        plan_cadences(config)


@pytest.mark.parametrize(
    "run_id,omega_ratio",
    [("P-08", 0.25), ("P-09", 0.5), ("P-10", 1.0), ("P-11", 2.0), ("P-12", 4.0)],
)
def test_the_real_rotation_sweep_is_planned_correctly(run_id, omega_ratio):
    """The tracked configs, not a fabrication: P-08 ... P-12 as they stand today."""
    with open(f"{REPO_CONFIGS}/{run_id}.yaml", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    plan = plan_cadences(config, baseline={"snapshot_cadence": BASELINE_SNAPSHOT_S})
    assert plan.omega_ratio == pytest.approx(omega_ratio, rel=1e-4)

    snapshot = plan.decisions["snapshot_cadence"]
    assert (
        snapshot.applied_s == pytest.approx(BASELINE_SNAPSHOT_S / plan.omega_ratio, rel=1e-4)
        or not snapshot.overridden
    )

    # Every applied cadence in the sweep must resolve the wave, whatever the
    # config said. This is the property the whole session turns on.
    assert snapshot.phase_step_applied_pi < 1.0


def test_the_committed_rotation_sweep_contains_a_real_aliasing_bug():
    """Guard against this test file quietly becoming vacuous.

    If someone edits the P-* configs so nothing aliases any more, the fix is to
    delete this test deliberately -- not to let the suite keep passing while the
    thing it was written to catch has silently gone away.
    """
    with open(f"{REPO_CONFIGS}/P-12.yaml", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    plan = plan_cadences(config, baseline={"snapshot_cadence": BASELINE_SNAPSHOT_S})
    assert "snapshot_cadence" in plan.would_have_aliased
