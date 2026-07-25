"""Tests for the analysis pipeline.

The pattern throughout is **fabricate a signal whose answer is known exactly, then
demand the tool recover it**. That is a stronger test than comparing against a
previous run of the same code, because a fitter with a systematic bias reproduces
itself perfectly and still gets the physics wrong. Where a tolerance appears it is
0.1% relative, which is the blueprint's own exit criterion for this session's
fitters and is not to be loosened to make a test pass — a fitter that cannot
recover a clean synthetic signal to 0.1% must not be trusted on a real run.

Two tests here are **regression locks** rather than validations: they pin the two
results Session L5 found by hand, so that a later session touching the fitters or
the eigenvalue solvers cannot silently move them.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS = REPO_ROOT / "runs"

pytest.importorskip("dedalus.public", reason="analysis tests need the pinned Dedalus build")

from src.analysis import compute_error_norms as en  # noqa: E402
from src.analysis.fit_growth_rate import (  # noqa: E402
    fit_growth_rate,
    synthetic_growth_series,
    window_sensitivity,
)
from src.analysis.fit_phase_speed import (  # noqa: E402
    dominant_wavenumber,
    fit_phase_speed,
    synthetic_hovmoller,
)
from src.solver import harness  # noqa: E402

# The blueprint's exit criterion for this session's fitters. Not to be loosened.
FITTER_TOLERANCE = 1e-3

OMEGA_EARTH = 7.292e-5
RADIUS_EARTH = 6371220.0

# --------------------------------------------------------------------------- #
# error norms
# --------------------------------------------------------------------------- #


def test_area_integral_is_area_weighted():
    """``I(1) = 1`` and ``I(sin^2 lat) = 1/3`` — the check an unweighted mean fails.

    A plain mean over the Gauss-Legendre colatitude grid gives roughly 0.5 for the
    second one, because the grid clusters towards the poles. Getting this wrong
    would make every error norm in the project wrong by tens of per cent, in a way
    that looks entirely plausible.
    """
    cfg = harness.load_config(REPO_ROOT / "configs" / "verification" / "V-02.yaml")
    _, _, theta = en.analytic_reference(cfg, 0.0)
    lat = np.pi / 2 - theta
    ones = np.ones((64, theta.size))
    assert en.area_integral(ones, theta) == pytest.approx(1.0, abs=1e-13)
    assert en.area_integral(np.tile(np.sin(lat) ** 2, (64, 1)), theta) == pytest.approx(
        1 / 3, abs=1e-13
    )


def test_gauss_weights_reject_a_grid_they_do_not_belong_to():
    """Applying Gauss-Legendre weights to an equispaced grid must fail loudly.

    It would otherwise produce a number that is wrong by a few per cent and looks
    completely reasonable, which is the worst kind of wrong.
    """
    with pytest.raises(ValueError, match="Gauss-Legendre"):
        en.gauss_weights(np.linspace(0.05, np.pi - 0.05, 32))


def test_error_norms_vanish_against_the_reference_itself():
    """The exact solution compared with itself must give zero to round-off.

    This is what confirms ``analytic_reference`` rebuilds the case identically to
    the way the run was initialised, rather than approximately.
    """
    cfg = harness.load_config(REPO_ROOT / "configs" / "verification" / "V-02.yaml")
    h_ref, u_ref, theta = en.analytic_reference(cfg, 0.0)
    scalar = en.error_norms(h_ref, h_ref + 0.0, theta)
    assert scalar["l2"] < 1e-15 and scalar["linf"] < 1e-15
    vector = en.error_norms(u_ref, u_ref + 0.0, theta, vector=True)
    assert vector["l2"] < 1e-15


def test_l2_of_a_known_perturbation_is_its_known_size():
    """Add a perturbation whose relative norm can be written down, and recover it.

    Adding ``eps * f_ref`` must give ``l2 = eps`` exactly, whatever the field is,
    because both numerator and denominator carry the same weighting. If the
    weights were applied to only one of them, this identity would fail.
    """
    cfg = harness.load_config(REPO_ROOT / "configs" / "verification" / "V-02.yaml")
    h_ref, _, theta = en.analytic_reference(cfg, 0.0)
    for eps in (1e-2, 1e-5):
        assert en.l2(h_ref * (1 + eps), h_ref, theta) == pytest.approx(eps, rel=1e-12)


def test_analytic_reference_refuses_cases_that_have_none():
    """Williamson case 5 has no closed-form solution and must not pretend otherwise."""
    cfg = harness.load_config(REPO_ROOT / "configs" / "verification" / "V-03.yaml")
    with pytest.raises(ValueError, match="no analytic solution"):
        en.analytic_reference(cfg, 0.0)


# --------------------------------------------------------------------------- #
# phase-speed fitting — synthetic ground truth
# --------------------------------------------------------------------------- #

# (m, n): the zonal orders and total degrees the P-campaign actually runs. The
# angular frequency is the Rossby-Haurwitz prediction omega = m * c_ang with
# c_ang = -2 Omega / [n(n+1)], so each case is a wave this project will really
# have to measure, not an arbitrary sinusoid.
PHASE_SPEED_CASES = [(2, 2), (2, 4), (2, 8), (5, 6)]


def _rossby_haurwitz_omega(m: int, n: int) -> float:
    return m * (-2 * OMEGA_EARTH / (n * (n + 1)))


@pytest.mark.parametrize("m,n", PHASE_SPEED_CASES)
def test_phase_speed_fitter_recovers_known_input(m, n):
    """Fabricate a wave of known speed and demand it back to better than 0.1%.

    This is the blueprint's own exit criterion for the phase-speed pipeline. The
    synthetic field is sampled exactly as a real run samples it — uniform
    longitude grid, regular output cadence — and carries 2% Gaussian noise, so a
    fitter that only works on noiseless data fails here.
    """
    omega = _rossby_haurwitz_omega(m, n)
    field, time_s = synthetic_hovmoller(m, omega, noise_fraction=0.02, seed=3)
    fit = fit_phase_speed(field, time_s, wavenumber=m)
    expected = omega / m
    assert fit.c_angular_rad_s == pytest.approx(expected, rel=FITTER_TOLERANCE)
    assert fit.c_angular_rad_s < 0, "a Rossby wave must come out westward"
    assert fit.aliasing_risk == "none"


@pytest.mark.parametrize("m,n", PHASE_SPEED_CASES)
def test_dominant_wavenumber_finds_the_planted_mode(m, n):
    """The mode that was put in must be the mode that comes out."""
    field, _ = synthetic_hovmoller(m, _rossby_haurwitz_omega(m, n), noise_fraction=0.05, seed=11)
    assert dominant_wavenumber(field) == m


def test_phase_speed_fitter_survives_a_decaying_mode():
    """A mode that decays by two orders of magnitude must still give the right speed.

    Real runs damp: P-17's mode lost 6% of its amplitude over twenty days, and a
    hyperdiffusive run at higher wavenumber loses far more. Phase drift is
    independent of amplitude, which is the reason this method is used instead of
    crest tracking, and this test is what holds that claim to account.
    """
    m, omega = 2, _rossby_haurwitz_omega(2, 4)
    field, time_s = synthetic_hovmoller(m, omega, noise_fraction=0.01, seed=5)
    decay = np.exp(-time_s / (time_s[-1] / np.log(100)))[:, None]
    fit = fit_phase_speed(field * decay, time_s, wavenumber=m, amplitude_weighted=True)
    assert fit.c_angular_rad_s == pytest.approx(omega / m, rel=FITTER_TOLERANCE)


def test_phase_speed_fitter_flags_marginal_sampling():
    """Sample just inside Nyquist and check the fit says the margin is thin.

    Aliasing is the failure mode that produces a confident, precise, wrong number.
    It has to be announced from the *data*, and the announcement has to be
    calibrated: a comfortably sampled wave must not raise it, a marginal one must.
    """
    m = 4
    duration, n_time = 6 * 86400.0, 25
    dt = duration / (n_time - 1)
    # Choose omega so the phase advances 0.95 pi per sample: resolved, barely.
    omega = 0.95 * np.pi / dt
    field, time_s = synthetic_hovmoller(m, omega, n_time=n_time, duration_s=duration)
    fit = fit_phase_speed(field, time_s, wavenumber=m)
    assert fit.aliasing_risk == "severe"
    assert any("ALIASING RISK SEVERE" in note for note in fit.notes)

    comfortable, comfortable_t = synthetic_hovmoller(
        m, omega / 10, n_time=n_time, duration_s=duration
    )
    assert fit_phase_speed(comfortable, comfortable_t, wavenumber=m).aliasing_risk == "none"


def test_aliasing_is_invisible_in_the_data_and_visible_against_an_expectation():
    """The central honest limitation of phase fitting, pinned as a test.

    A wave sampled past Nyquist presents *small* phase steps — it looks like a
    well-resolved slow wave — so the series alone reports a comfortable margin
    while the fit is wrong by a large factor and often of the opposite sign. That
    is asserted here rather than papered over. Supplying an independent expected
    speed makes the same case detectable, because the expectation is not folded
    into ``(-pi, pi]``, and that is why the phase-speed campaign always passes one.
    """
    m = 4
    duration, n_time = 6 * 86400.0, 25
    dt = duration / (n_time - 1)
    omega = 1.9 * np.pi / dt  # well past Nyquist
    field, time_s = synthetic_hovmoller(m, omega, n_time=n_time, duration_s=duration)

    blind = fit_phase_speed(field, time_s, wavenumber=m)
    assert blind.aliasing_risk == "none", "the alias genuinely hides from the data"
    assert abs(blind.c_angular_rad_s - omega / m) / abs(omega / m) > 0.5

    warned = fit_phase_speed(field, time_s, wavenumber=m, expected_c_angular=omega / m)
    assert warned.aliasing_risk == "severe"
    assert warned.alias_order != 0
    assert any("ALIASING RISK SEVERE" in note for note in warned.notes)


def test_a_well_sampled_wave_is_not_flagged_when_an_expectation_is_supplied():
    """The external check must not cry wolf on a properly sampled run."""
    m, n = 2, 4
    omega = _rossby_haurwitz_omega(m, n)
    field, time_s = synthetic_hovmoller(m, omega, noise_fraction=0.02, seed=3)
    fit = fit_phase_speed(field, time_s, wavenumber=m, expected_c_angular=omega / m)
    assert fit.aliasing_risk == "none"
    assert fit.alias_order == 0


def test_phase_speed_linear_conversion_uses_the_latitude_circle():
    """``c = c_ang R cos(phi)`` — the linear speed depends on where you measure it."""
    m, omega = 2, _rossby_haurwitz_omega(2, 4)
    field, time_s = synthetic_hovmoller(m, omega, seed=1)
    fit = fit_phase_speed(
        field, time_s, wavenumber=m, latitude_rad=np.pi / 4, radius_m=RADIUS_EARTH
    )
    assert fit.c_linear_m_s == pytest.approx(
        fit.c_angular_rad_s * RADIUS_EARTH * np.cos(np.pi / 4), rel=1e-12
    )


# --------------------------------------------------------------------------- #
# growth-rate fitting — synthetic ground truth
# --------------------------------------------------------------------------- #

# Rates spanning what the instability campaign produces: the Galewsky anchor
# (2.07e-5), the weakest resolved rung of the shear ladder (3.52e-6), and a rate
# faster than anything measured so far.
GROWTH_RATE_CASES = [
    ("anchor", 2.07e-5, {"noise_fraction": 0.02}),
    ("weak rung", 3.52e-6, {"noise_fraction": 0.02, "duration_s": 20 * 86400.0}),
    ("fast", 3.0e-5, {"noise_fraction": 0.05}),
]


@pytest.mark.parametrize("name,sigma,kwargs", GROWTH_RATE_CASES)
def test_growth_rate_fitter_recovers_known_input(name, sigma, kwargs):
    """``E = E0 exp(2 sigma t)`` with noise, recovered to better than 0.1%."""
    time_s, series = synthetic_growth_series(sigma, seed=7, **kwargs)
    fit = fit_growth_rate(time_s, series, quantity="energy")
    assert fit.growth_rate_s == pytest.approx(sigma, rel=FITTER_TOLERANCE)
    assert fit.e_folding_days == pytest.approx(1 / sigma / 86400, rel=FITTER_TOLERANCE)


# Oscillation periods chosen to fit a NON-integer number of cycles into the
# window. That is the case the fitter has to handle: an integer number of cycles
# averages out on its own and would let a biased fitter pass.
OSCILLATION_CASES = [(2.3, 0.4, 1.41e-5), (1.7, 0.4, 1.41e-5), (3.4, 0.5, 2.07e-5)]


@pytest.mark.parametrize("cycles,amplitude,sigma", OSCILLATION_CASES)
def test_growth_rate_fitter_is_not_fooled_by_a_superimposed_oscillation(cycles, amplitude, sigma):
    """Real eddy energy wobbles as it grows; the fitted rate must not wobble with it.

    The test also asserts that the naive fit *is* biased on the same data, so this
    is demonstrably testing the correction rather than a case that would pass
    anyway.
    """
    duration = 6 * 86400.0
    time_s, series = synthetic_growth_series(
        sigma,
        seed=7,
        noise_fraction=0.02,
        duration_s=duration,
        oscillation_period_s=duration / cycles,
        oscillation_amplitude=amplitude,
    )
    fit = fit_growth_rate(time_s, series, quantity="energy")
    assert fit.growth_rate_s == pytest.approx(sigma, rel=FITTER_TOLERANCE)
    assert fit.oscillation_period_s == pytest.approx(duration / cycles, rel=0.02)

    naive = fit_growth_rate(time_s, series, quantity="energy", remove_oscillation=False)
    assert abs(naive.growth_rate_s - sigma) / sigma > FITTER_TOLERANCE


def test_energy_and_amplitude_conventions_differ_by_exactly_two():
    """A quadratic diagnostic grows twice as fast as the amplitude it is built from.

    Getting this factor wrong would put every growth rate in the project out by a
    factor of two while leaving every fit looking perfect.
    """
    sigma = 1.5e-5
    time_s, amplitude = synthetic_growth_series(sigma, quantity="amplitude", seed=1)
    from_amplitude = fit_growth_rate(time_s, amplitude, quantity="amplitude").growth_rate_s
    from_energy = fit_growth_rate(time_s, amplitude**2, quantity="energy").growth_rate_s
    assert from_amplitude == pytest.approx(sigma, rel=FITTER_TOLERANCE)
    assert from_energy == pytest.approx(sigma, rel=FITTER_TOLERANCE)


def test_automatic_window_rejects_the_saturated_plateau():
    """Saturation is straight in the log too — the window must not settle there.

    A saturated plateau is a horizontal line and is usually the *longest* straight
    stretch in an instability run, so a window search that maximises duration
    reliably selects the one part of the record where nothing is growing. The
    search maximises e-foldings spanned instead, and this is the test that pins
    that choice down.
    """
    time_s = np.linspace(0, 12 * 86400.0, 289)
    sigma = 2.07e-5
    raw = 1e-12 * np.exp(2 * sigma * time_s)
    saturating = raw / (1 + raw / 1e-4)
    noisy = saturating * (1 + np.random.default_rng(0).normal(0, 0.02, time_s.size))
    fit = fit_growth_rate(time_s, noisy, quantity="energy", auto_window=True)
    assert fit.growth_rate_s == pytest.approx(sigma, rel=FITTER_TOLERANCE)
    assert fit.window_end_s < 6 * 86400.0, "window must stop before saturation"


def test_window_sensitivity_dominates_on_a_realistic_record():
    """On a record with saturation in it, the window matters far more than the noise.

    ``docs/CONVENTIONS.md`` requires a named dominant uncertainty source. This test
    pins which one it is for a growth rate: across plausible windows of a
    saturating record the fitted rate moves by tens of per cent, while the standard
    error of any single fit is parts in a thousand. Quoting the standard error
    alone would understate the uncertainty by two orders of magnitude.
    """
    time_s = np.linspace(0, 12 * 86400.0, 289)
    raw = 1e-12 * np.exp(2 * 2.07e-5 * time_s)
    series = (raw / (1 + raw / 1e-4)) * (1 + np.random.default_rng(0).normal(0, 0.02, time_s.size))
    fit = fit_growth_rate(time_s, series, quantity="energy", auto_window=True)
    spread = window_sensitivity(time_s, series, quantity="energy")
    assert spread["n_windows"] > 4
    assert spread["relative_spread"] > 0.1
    assert spread["max_s"] - spread["min_s"] > 100 * fit.growth_rate_stderr_s


# --------------------------------------------------------------------------- #
# space-time (Hayashi) decomposition — the tool Session L8 inherits
# --------------------------------------------------------------------------- #


def test_hayashi_separates_two_branches_at_different_wavenumbers():
    """A superposition of one eastward and one westward wave must come apart cleanly."""
    from src.analysis.spectral_decompose import (
        hayashi_decompose,
        mode_amplitude,
        synthetic_two_branch_field,
    )

    omega_e = 2 * (2 * OMEGA_EARTH / (4 * 5))
    omega_w = 3 * (2 * OMEGA_EARTH / (5 * 6))
    field, time_s = synthetic_two_branch_field((2, omega_e, 1.0), (3, omega_w, 0.6))
    decomposition = hayashi_decompose(field, time_s)

    freq_e, amp_e = mode_amplitude(decomposition, "eastward", 2)
    freq_w, amp_w = mode_amplitude(decomposition, "westward", 3)
    assert freq_e == pytest.approx(omega_e, rel=0.02)
    assert freq_w == pytest.approx(omega_w, rel=0.02)
    assert amp_e == pytest.approx(1.0, rel=0.01)
    assert amp_w == pytest.approx(0.6, rel=0.01)

    # Almost nothing may leak into the counter-propagating branch: a spurious
    # counter-branch is exactly what would wreck the Doppler correction.
    assert decomposition["westward"][2].sum() / decomposition["eastward"][2].sum() < 1e-4
    assert decomposition["eastward"][3].sum() / decomposition["westward"][3].sum() < 1e-4


def test_hayashi_separates_two_branches_at_the_same_wavenumber():
    """The case Session L8 actually faces, and the one no snapshot spectrum can do.

    An observed 500 hPa field contains a pattern advected eastward by the jet and
    an intrinsic westward Rossby signal, and they can share a zonal scale. Only the
    joint wavenumber-frequency transform can tell them apart, which is why the
    Doppler-correction convention specifies this decomposition and not a time
    high-pass.
    """
    from src.analysis.spectral_decompose import (
        hayashi_decompose,
        mode_amplitude,
        synthetic_two_branch_field,
    )

    m = 4
    omega_e, omega_w = m * 3.0e-6, m * 7.0e-6
    field, time_s = synthetic_two_branch_field(
        (m, omega_e, 1.0), (m, omega_w, 0.5), noise_fraction=0.03, seed=2
    )
    decomposition = hayashi_decompose(field, time_s)

    freq_e, amp_e = mode_amplitude(decomposition, "eastward", m)
    freq_w, amp_w = mode_amplitude(decomposition, "westward", m)
    assert freq_e == pytest.approx(omega_e, rel=0.01)
    assert freq_w == pytest.approx(omega_w, rel=0.01)
    assert amp_e == pytest.approx(1.0, rel=0.02)
    assert amp_w == pytest.approx(0.5, rel=0.02)


def test_hayashi_direction_convention_matches_the_projects_sign():
    """Westward must come out as a negative angular phase speed, as in eq. (rhdisp).

    A sign error here would be invisible in every magnitude and would invert the
    project's central claim, so it is asserted directly.
    """
    from src.analysis.spectral_decompose import (
        dominant_propagating_modes,
        hayashi_decompose,
        synthetic_two_branch_field,
    )

    field, time_s = synthetic_two_branch_field((3, 1e-6, 0.01), (3, 3 * 2.4e-6, 1.0))
    top = dominant_propagating_modes(hayashi_decompose(field, time_s), n_modes=1)[0]
    assert top["direction"] == "westward"
    assert top["c_angular_rad_s"] < 0
    assert top["c_angular_rad_s"] == pytest.approx(-2.4e-6, rel=0.02)


def test_windowing_suppresses_the_spurious_counter_branch():
    """Leakage across the sign of the frequency invents a wave that is not there.

    A one-way wave whose record contains a non-integer number of cycles leaks power
    into the opposite branch when no window is applied. This test shows the window
    earning its place rather than being applied out of habit.
    """
    from src.analysis.spectral_decompose import hayashi_decompose, synthetic_two_branch_field

    m = 4
    duration = 20 * 86400.0
    omega = 2 * np.pi * 5.35 / duration  # a deliberately non-integer 5.35 cycles
    field, time_s = synthetic_two_branch_field(
        (m, omega, 1.0), (m, omega, 0.0), duration_s=duration
    )
    with_window = hayashi_decompose(field, time_s, window="hann")
    without = hayashi_decompose(field, time_s, window="none")
    leak_with = with_window["westward"][m].sum() / with_window["eastward"][m].sum()
    leak_without = without["westward"][m].sum() / without["eastward"][m].sum()
    assert leak_with < leak_without / 10


def test_hayashi_rejects_uneven_sampling():
    """Irregular output times make the frequency axis meaningless; say so."""
    from src.analysis.spectral_decompose import hayashi_decompose

    field = np.zeros((16, 32))
    time_s = np.sort(np.random.default_rng(0).uniform(0, 1e5, 16))
    with pytest.raises(ValueError, match="uniform time sampling"):
        hayashi_decompose(field, time_s)


# --------------------------------------------------------------------------- #
# meridional structure
# --------------------------------------------------------------------------- #


def test_mode_profile_recovers_a_planted_envelope_and_tilt():
    """Plant a Gaussian envelope with a known phase tilt and read both back."""
    from src.analysis.extract_structure import (
        normalise_profile,
        pattern_correlation,
        structure_diagnostics,
        zonal_mode_profile,
    )

    lat = np.linspace(-np.pi / 2 + 0.01, np.pi / 2 - 0.01, 64)
    lon = np.linspace(0, 2 * np.pi, 96, endpoint=False)
    envelope = np.exp(-(((lat - np.pi / 4) / 0.20) ** 2))
    tilt_rate = 1.3
    complex_profile = envelope * np.exp(1j * tilt_rate * (lat - np.pi / 4))
    field = np.real(complex_profile[None, :] * np.exp(1j * 4 * lon[:, None]))

    recovered = normalise_profile(zonal_mode_profile(field, 4))
    assert np.max(np.abs(np.abs(recovered) - envelope / envelope.max())) < 1e-12
    assert pattern_correlation(recovered, recovered, lat) == pytest.approx(1.0, abs=1e-12)

    diagnostics = structure_diagnostics(recovered, lat)
    assert diagnostics["peak_lat_deg"] == pytest.approx(45.0, abs=1.0)
    assert diagnostics["phase_tilt_rad"] > 0.4


def test_pattern_correlation_discriminates_a_displaced_mode():
    """Two modes centred fifteen degrees apart must not look like the same mode."""
    from src.analysis.extract_structure import pattern_correlation

    lat = np.linspace(-np.pi / 2 + 0.01, np.pi / 2 - 0.01, 64)
    here = np.exp(-(((lat - np.pi / 4) / 0.20) ** 2)).astype(complex)
    there = np.exp(-(((lat - np.pi / 3) / 0.20) ** 2)).astype(complex)
    assert pattern_correlation(here, here, lat) == pytest.approx(1.0, abs=1e-12)
    assert pattern_correlation(here, there, lat) < 0.6


def test_eigenfunction_evaluation_is_finite_and_regular_at_the_poles():
    """A spectral eigenvector must evaluate to a finite profile that vanishes at the poles.

    Regularity at the poles is what the spherical-harmonic basis buys in place of
    boundary conditions, so a profile that blew up there would mean the basis
    normalisation had been mistranscribed.
    """
    from src.solver import evp_stability as es

    lat = np.linspace(-np.pi / 2, np.pi / 2, 128)
    _, vectors, degrees = es.stability_evp(
        6, 60, es.solid_body_profile(40.0), RADIUS_EARTH, OMEGA_EARTH, return_vectors=True
    )
    profile = es.eigenfunction_on_latitudes(vectors[:, 0], degrees, 6, lat)
    assert np.all(np.isfinite(profile))
    assert abs(profile[0]) < 1e-8 * np.max(np.abs(profile))
    assert abs(profile[-1]) < 1e-8 * np.max(np.abs(profile))


# --------------------------------------------------------------------------- #
# core diagnostics, read from the real proof runs
# --------------------------------------------------------------------------- #

pytestmark_runs = pytest.mark.skipif(
    not (RUNS / "V-02" / "provenance.json").exists(),
    reason="Session L5 proof runs are not present",
)


@pytestmark_runs
def test_conservation_reproduces_the_documented_v02_drift():
    """The number `docs/SOLVER_CORE_RESULTS.md` quotes must come out of the module.

    Session L5 computed that mass drift by hand. This makes it a pipeline output,
    so that a later change to the reader or the diagnostics cannot move it quietly.
    """
    from src.diagnostics import conservation

    series = conservation.conservation_series("V-02")
    assert float(series.relative_drift["mass"][-1]) == pytest.approx(-1.5e-16, abs=2e-17)
    assert float(series.relative_drift["energy"][-1]) == pytest.approx(-4.3e-5, rel=0.05)
    assert float(series.relative_drift["potential_enstrophy"][-1]) == pytest.approx(
        -1.8e-5, rel=0.05
    )


@pytestmark_runs
@pytest.mark.parametrize("run", ["V-02", "P-17", "I-00"])
def test_conservation_verdicts_pass_on_every_proof_run(run):
    """Blueprint §9.3: mass at round-off, energy not growing, enstrophy not growing."""
    from src.diagnostics import conservation

    results = conservation.verdicts(conservation.conservation_series(run))
    failed = {name: v.reason for name, v in results.items() if not v.passed}
    assert not failed, failed


@pytestmark_runs
def test_reader_concatenates_a_split_handler_in_time_order():
    """I-00's snapshots span two files; sorting by filename would misorder ``_s10``."""
    from src.diagnostics import slices

    handler = slices.read_handler("I-00", "snapshots")
    assert len(handler.files) == 2
    assert np.all(np.diff(handler.time_s) > 0)
    assert handler.tasks["height"].shape[0] == handler.time_s.size


@pytestmark_runs
def test_slice_latitudes_come_from_the_task_name_not_the_stored_grid():
    """The stored colatitude for an interpolated slice is a degenerate decoy.

    Dedalus writes the two Gauss-Legendre nodes of the degenerate basis — plus and
    minus 35.26 degrees — identically in every run whatever its resolution and
    whatever latitude was actually requested. Reading the slice latitude from there
    would put every phase speed on the wrong circle.
    """
    import h5py

    from src.diagnostics import slices

    assert slices.slice_latitude_rad("height_45N") == pytest.approx(np.pi / 4)
    assert slices.slice_latitude_rad("height_equator") == pytest.approx(0.0, abs=1e-12)

    path = slices.handler_files("V-02", "slices")[0]
    with h5py.File(path) as handle:
        name = next(k for k in handle["scales"] if k.startswith("theta_hash_"))
        stored = np.degrees(handle["scales"][name][:])
    assert np.allclose(np.sort(stored), np.sort([54.7356, 125.2644]), atol=1e-3)


@pytestmark_runs
def test_spherical_harmonic_transform_concentrates_a_planted_mode():
    """An exact ``Y_n^m`` on a run's own grid must put all its power in that cell."""
    from src.diagnostics import slices, spectra

    grid = slices.snapshot_map("V-02", "height", index=0)
    for n, m in ((5, 3), (10, 7)):
        field = spectra.real_harmonic_field(grid.lon_rad, grid.colatitude_rad, n, m)
        degrees, power = spectra.power_spectrum(field, grid.colatitude_rad)
        orders, zonal = spectra.zonal_power_spectrum(field, grid.colatitude_rad)
        assert power[n] / power.sum() == pytest.approx(1.0, abs=1e-12)
        assert zonal[m] / zonal.sum() == pytest.approx(1.0, abs=1e-12)


@pytestmark_runs
def test_williamson_case2_is_a_single_zonal_harmonic():
    """A physical check the transform was not tuned for.

    Case 2 at ``alpha = 0`` is solid-body rotation, whose balanced height field is
    exactly a zonal spherical harmonic of degree 2. If the transform put its power
    anywhere else, the transform would be wrong — and this is real run output, not
    a planted test signal.
    """
    from src.diagnostics import slices, spectra

    grid = slices.snapshot_map("V-02", "height", index=0)
    degrees, power = spectra.power_spectrum(grid.values, grid.colatitude_rad)
    orders, zonal = spectra.zonal_power_spectrum(grid.values, grid.colatitude_rad)
    assert power[2] / power.sum() == pytest.approx(1.0, abs=1e-9)
    assert zonal[0] / zonal.sum() == pytest.approx(1.0, abs=1e-9)


# --------------------------------------------------------------------------- #
# Hovmöller extraction
# --------------------------------------------------------------------------- #


@pytestmark_runs
def test_hovmoller_prefers_the_high_cadence_slice_and_reports_its_latitude():
    """45 degrees is the fixed point of the colatitude flip, so test the equator too.

    A latitude/colatitude double conversion is invisible at 45 degrees and wrong
    everywhere else; asking for the equator is what exposes it.
    """
    from src.analysis.extract_hovmoller import available_slice_latitudes, extract_hovmoller

    latitudes = available_slice_latitudes("P-17")
    assert np.degrees(latitudes["height_45N"]) == pytest.approx(45.0)
    assert np.degrees(latitudes["height_equator"]) == pytest.approx(0.0, abs=1e-9)

    for requested in (45.0, 0.0):
        diagram = extract_hovmoller("P-17", requested)
        assert diagram.latitude_deg == pytest.approx(requested, abs=1e-6)
        assert diagram.source.startswith("slice task")
        assert diagram.cadence_s < 3600.0


@pytestmark_runs
def test_hovmoller_falls_back_to_interpolated_snapshots_and_says_so():
    """A latitude the harness did not record is interpolated, and labelled as such."""
    from src.analysis.extract_hovmoller import extract_hovmoller

    diagram = extract_hovmoller("P-17", 30.0)
    assert diagram.source == "interpolated snapshots"
    assert diagram.latitude_deg == pytest.approx(30.0)
    assert diagram.cadence_s > 3600.0


@pytestmark_runs
def test_the_same_mode_gives_the_same_angular_speed_on_two_different_circles():
    """On a sphere the *angular* speed belongs to the mode, not to the latitude.

    Measuring the same wave at 45 degrees and at 30 degrees must give the same
    ``c_ang`` even though the linear speeds differ by ``cos(45)/cos(30)``. This is
    a physical consistency check on the whole extraction-plus-fitting chain, using
    real run output.
    """
    from src.analysis.extract_hovmoller import extract_hovmoller

    speeds = []
    for latitude in (45.0, 30.0):
        diagram = extract_hovmoller("P-17", latitude)
        fit = fit_phase_speed(diagram.values, diagram.time_s, wavenumber=2)
        speeds.append(fit.c_angular_rad_s)
    assert speeds[0] == pytest.approx(speeds[1], rel=0.005)


# --------------------------------------------------------------------------- #
# Part 6 — measured vs nondivergent vs Hough
# --------------------------------------------------------------------------- #

# Session L5's by-hand result for the (m, n) = (2, 4) mode of run P-17, and the
# tolerances this session locks it in at. The measured and Hough slowings are
# pinned to a tenth of a percentage point each, and their agreement — the headline
# number — to a tenth of a percentage point.
L5_MEASURED_SLOWING = -0.1572
L5_HOUGH_SLOWING = -0.1577
L5_AGREEMENT_PP = 0.05
SLOWING_TOLERANCE = 0.001


@pytestmark_runs
def test_hough_comparison_reproduces_session_l5_by_hand_result():
    """**Regression lock.** The unplanned finding of Session L5, made routine.

    Session L5 measured the ``(m, n) = (2, 4)`` mode of P-17 at 15.72% slower than
    the nondivergent Rossby-Haurwitz prediction, and solved the divergent Hough
    eigenvalue independently at 15.77%. Those two numbers come from a nonlinear
    time integration and from a linear eigenvalue problem respectively, so their
    agreement is evidence about the physics rather than about the code — and it is
    precisely the kind of result that a later refactor of a fitter could move
    without anyone noticing. This test is what stops that.
    """
    from src.analysis.hough import compare_run

    result = compare_run("P-17")
    assert (result.wavenumber_m, result.degree_n) == (2, 4)
    assert result.lambs_parameter == pytest.approx(8.8044, rel=1e-3)
    assert result.measured_vs_nondivergent == pytest.approx(
        L5_MEASURED_SLOWING, abs=SLOWING_TOLERANCE
    )
    assert result.hough_vs_nondivergent == pytest.approx(L5_HOUGH_SLOWING, abs=SLOWING_TOLERANCE)
    assert result.agreement_percentage_points == pytest.approx(L5_AGREEMENT_PP, abs=0.1)
    assert result.aliasing_risk == "none"


@pytestmark_runs
def test_the_wave_is_westward_and_slowed_not_speeded():
    """Both the measurement and the eigenvalue must be westward, and both slower.

    The free surface can only dilute the restoring mechanism, so a divergent wave
    is *always* slower than its nondivergent counterpart. A positive slowing would
    be unphysical rather than merely surprising, and would point at a sign error
    somewhere in the chain.
    """
    from src.analysis.hough import compare_run

    result = compare_run("P-17")
    assert result.measured_c_angular_rad_s < 0
    assert result.hough_c_angular_rad_s < 0
    assert result.nondivergent_c_angular_rad_s < 0
    assert abs(result.measured_c_angular_rad_s) < abs(result.nondivergent_c_angular_rad_s)
    assert abs(result.hough_c_angular_rad_s) < abs(result.nondivergent_c_angular_rad_s)


@pytestmark_runs
def test_degree_is_read_from_vorticity_because_height_gives_the_wrong_answer():
    """The mode's degree is a property of the streamfunction, not of the height.

    A single-harmonic run seeds one spherical harmonic in the streamfunction, so
    its vorticity is exactly that degree. Its *balanced height* is not: the balance
    multiplies by ``sin(latitude)`` and ``mu P_n^m`` couples only to ``n +/- 1``, so
    the height of a clean ``n = 4`` mode sits in degrees 3 and 5. Reading the degree
    off the height field returns 3 — a plausible, wrong answer — and this test
    documents that trap as much as it checks the code.
    """
    from src.analysis.hough import dominant_degree

    assert dominant_degree("P-17", 2, "vorticity") == 4
    assert dominant_degree("P-17", 2, "height") == 3


@pytestmark_runs
def test_the_comparison_is_reproducible_from_a_second_latitude_circle():
    """The slowing belongs to the mode, so a different circle must give the same number.

    An angular phase speed does not depend on which latitude circle it is measured
    on. Recovering the same slowing from a different circle of the same run is a
    check on the whole extraction chain that no synthetic test can provide.
    """
    from src.analysis.hough import compare_run

    at_45 = compare_run("P-17", latitude_deg=45.0)
    at_30 = compare_run("P-17", latitude_deg=30.0)
    assert at_30.measured_vs_nondivergent == pytest.approx(
        at_45.measured_vs_nondivergent, abs=0.005
    )
    assert at_45.mode_present and at_30.mode_present


@pytestmark_runs
def test_a_circle_where_the_mode_is_absent_is_refused_not_fitted():
    """P-17's height signal vanishes at the equator, and the fit must say so.

    This is physics, not a numerical accident: the balanced height of an
    ``(m, n) = (2, 4)`` mode sits in degrees 3 and 5, both of which are
    antisymmetric about the equator, so its ``m = 2`` component is identically zero
    there. Phase is defined for any nonzero complex number however tiny, so the
    fitter will happily return a confident slope through round-off — here a
    "measured" speed 24 times too large and of the wrong sign. Detecting the
    absence is the only defence.
    """
    from src.analysis.hough import compare_run

    at_equator = compare_run("P-17", latitude_deg=0.0)
    assert not at_equator.mode_present
    assert any("MODE ABSENT" in note for note in at_equator.notes)
