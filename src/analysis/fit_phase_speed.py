"""Fit the zonal phase speed of a wave from a longitude-time (Hovmöller) field.

Physics first. This module measures the single number the whole phase-speed
campaign exists to test: **how fast a Rossby wave travels, and in which
direction.** The prediction it is measured against is
``theory/derivations.tex`` eq. (rhdisp),

    c_ang = -2 Omega / [n(n+1)] ,

whose sign is not a convention — a Rossby wave goes *west*, always, because the
restoring mechanism is a poleward-increasing background potential vorticity and
the induced velocity field of the resulting vorticity anomalies transports the
pattern in one direction only. A measured eastward drift at low amplitude would
falsify the mechanism, not merely the number, which is why the sign is reported
rather than assumed.

**How the fit works, and why it is done in phase rather than by tracking a crest.**
Write the field at one latitude as a Fourier series in longitude. A single zonal
wavenumber ``m`` contributes

    h'(lambda, t) = |C_m(t)| cos( m lambda + psi(t) ) ,   psi = arg C_m ,

so the crest sits at ``lambda_peak = -psi/m`` and the pattern's angular velocity
is ``c_ang = -(d psi/dt)/m``. Fitting a straight line to the unwrapped ``psi(t)``
uses **every** sample, and is insensitive to amplitude changes — the wave may grow
or decay by a large factor while its phase drift stays perfectly linear, and a
crest-tracking method would be thrown by exactly that. It also degrades gracefully
under noise, because noise perturbs each sample's phase independently while the
signal accumulates linearly in time.

**The one thing that can silently break it is aliasing, and it cannot be detected
after the fact.** If the pattern advances by more than half a wavelength between
output samples, phase unwrapping picks the wrong branch and returns a confident,
precise, wrong answer — often of the wrong sign, which for this project would be a
spectacular false result. It is worth being exact about why this cannot simply be
checked: unwrapping folds every phase increment into ``(-pi, pi]``, so the
*fitted* speed always satisfies the Nyquist condition by construction, whether or
not the true one does. Testing the fitted speed against Nyquist would therefore be
a check that can never fail — vacuous, and worse than none, because it would look
like protection.

What can honestly be reported from the series alone is **how close to Nyquist the
data itself sits**: the largest wrapped phase increment between consecutive
samples, as a fraction of ``pi``. That number is useful but it is *not* an alias
detector, and it is important to see why. A wave whose true phase step is
``1.9 pi`` per sample presents an observed step of ``0.1 pi`` — it looks like a
beautifully resolved slow wave, and the fit returns a speed wrong by a factor of
nineteen with the opposite sign, with the margin indicator reading comfortable.
Measured on the series, aliasing hides itself.

**The only real safeguard is an external expectation**, so this module accepts
one. Pass ``expected_c_angular`` — for the phase-speed campaign the
Rossby-Haurwitz prediction is always available — and the fit checks the Nyquist
condition against *that* speed, which is a genuine test because the expectation is
not folded into ``(-pi, pi]``. When the fitted and expected speeds disagree, the
fit also reports which alias would reconcile them, so the difference between "this
wave is slower than theory says" and "this output cadence was too coarse" is
visible instead of being a matter of opinion.

**Units.** ``c_ang`` is an angular speed in rad/s: on a sphere it is angular speed,
not linear speed, that is the property of the mode — the linear speed
``c = c_ang R cos(phi)`` depends on which latitude circle you measure it on.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import numpy as np


@dataclass
class PhaseSpeedFit:
    """The result of one phase-speed fit, with everything needed to judge it."""

    wavenumber: int
    c_angular_rad_s: float
    c_angular_stderr_rad_s: float
    c_linear_m_s: float | None
    latitude_rad: float | None
    n_samples: int
    span_s: float
    phase_range_rad: float
    amplitude_first: float
    amplitude_last: float
    residual_rms_rad: float
    nyquist_ratio: float
    aliasing_risk: str
    variance_fraction: float = 1.0
    mode_present: bool = True
    expected_c_angular_rad_s: float | None = None
    expected_nyquist_ratio: float | None = None
    alias_order: int | None = None
    notes: list[str] = dataclass_field(default_factory=list)

    def as_dict(self) -> dict:
        out = dict(self.__dict__)
        out["notes"] = list(self.notes)
        return out


def zonal_coefficients(hovmoller: np.ndarray) -> np.ndarray:
    """Complex Fourier coefficients in longitude, shape ``(n_time, n_wavenumber)``.

    ``hovmoller`` is ``(n_time, n_longitude)`` on a uniform longitude grid covering
    the full circle exactly once. The normalisation is ``2/N`` for ``m >= 1`` so
    that a field ``A cos(m lambda + psi)`` returns ``|C_m| = A``, which makes the
    amplitude column of a fit directly comparable with the physical amplitude of
    the wave rather than with a transform convention.
    """
    data = np.asarray(hovmoller, dtype=float)
    if data.ndim != 2:
        raise ValueError(f"expected a (time, longitude) array, got shape {data.shape}")
    n_lon = data.shape[1]
    coef = np.fft.rfft(data, axis=1) * (2.0 / n_lon)
    coef[:, 0] /= 2.0  # the mean has no conjugate partner to double
    return coef


def dominant_wavenumber(hovmoller: np.ndarray, exclude_zonal_mean: bool = True) -> int:
    """The zonal wavenumber carrying the most variance, time-averaged.

    ``m = 0`` is excluded by default: it is the zonal mean, which is not a wave and
    would win outright in any run with a jet in it.
    """
    power = (np.abs(zonal_coefficients(hovmoller)) ** 2).mean(axis=0)
    start = 1 if exclude_zonal_mean else 0
    return int(start + np.argmax(power[start:]))


def fit_phase_speed(
    hovmoller: np.ndarray,
    time_s: np.ndarray,
    wavenumber: int | None = None,
    latitude_rad: float | None = None,
    radius_m: float | None = None,
    amplitude_weighted: bool = False,
    expected_c_angular: float | None = None,
) -> PhaseSpeedFit:
    """Fit ``c_ang`` for one zonal wavenumber from a longitude-time field.

    Parameters
    ----------
    hovmoller
        ``(n_time, n_longitude)`` samples of a field on one latitude circle.
    time_s
        Sample times in **seconds**. Need not be uniform; the least-squares fit
        does not assume it, though the Nyquist check uses the largest gap.
    wavenumber
        Which ``m`` to fit. Defaults to the dominant one.
    latitude_rad, radius_m
        Supply both to also get the linear phase speed at that latitude.
    amplitude_weighted
        Weight each sample by ``|C_m|``. Worth using when the mode grows or decays
        by orders of magnitude across the window, since the phase of a sample where
        the mode is a thousand times weaker is a thousand times noisier. Off by
        default, because for a clean single mode it changes nothing and an
        unweighted fit is easier to reason about.
    expected_c_angular
        An independent prediction of the angular phase speed, in rad/s. Supplying
        it turns the aliasing check from a margin indicator into a real test — see
        the module docstring. Nothing about the fit itself changes.

    Returns
    -------
    PhaseSpeedFit
        Negative ``c_angular_rad_s`` means **westward**.
    """
    time_s = np.asarray(time_s, dtype=float)
    coef = zonal_coefficients(hovmoller)
    if wavenumber is None:
        wavenumber = dominant_wavenumber(hovmoller)
    if not 1 <= wavenumber < coef.shape[1]:
        raise ValueError(
            f"wavenumber {wavenumber} is outside the resolvable range "
            f"1..{coef.shape[1] - 1} for this longitude grid"
        )

    series = coef[:, wavenumber]
    amplitude = np.abs(series)
    phase = np.unwrap(np.angle(series))

    weights = amplitude if amplitude_weighted else np.ones_like(amplitude)
    design = np.vstack([time_s, np.ones_like(time_s)]).T
    sqrt_w = np.sqrt(weights)[:, None]
    solution, *_ = np.linalg.lstsq(design * sqrt_w, phase * sqrt_w[:, 0], rcond=None)
    slope, intercept = float(solution[0]), float(solution[1])

    residual = phase - (slope * time_s + intercept)
    dof = max(time_s.size - 2, 1)
    residual_var = float(np.dot(weights, residual**2) / dof)
    # Standard error of the slope from the weighted normal equations.
    sw = weights.sum()
    stt = float(np.dot(weights, (time_s - np.dot(weights, time_s) / sw) ** 2))
    slope_stderr = float(np.sqrt(residual_var / stt)) if stt > 0 else float("nan")

    c_ang = -slope / wavenumber
    c_ang_err = abs(slope_stderr / wavenumber)

    notes: list[str] = []
    # How close the sampling sits to Nyquist, measured from the data rather than
    # from the answer: the largest wrapped phase step between consecutive samples.
    # This is bounded by pi by construction, which is exactly why it must be read
    # as "how much margin is there", never as "was this aliased".
    raw = np.angle(series)
    steps = np.abs((np.diff(raw) + np.pi) % (2 * np.pi) - np.pi)
    nyquist_ratio = float(np.max(steps) / np.pi) if steps.size else 0.0
    if nyquist_ratio > 0.9:
        risk = "severe"
        notes.append(
            f"ALIASING RISK SEVERE: the phase advances up to {nyquist_ratio:.2f} x pi between "
            "samples. The fitted speed may be an alias of the true one — possibly of the "
            "opposite sign — and no test on this series can decide. Re-run with a shorter "
            "output cadence before using this number."
        )
    elif nyquist_ratio > 0.5:
        risk = "marginal"
        notes.append(
            f"aliasing risk marginal: phase advances up to {nyquist_ratio:.2f} x pi per "
            "sample, so the sampling resolves the wave but with little margin"
        )
    else:
        risk = "none"

    # The external check. Unlike the observed step, the expected one is not folded
    # into (-pi, pi], so exceeding Nyquist here is detectable.
    expected_ratio = None
    alias_order = None
    dt_max = float(np.max(np.diff(time_s))) if time_s.size > 1 else 0.0
    if expected_c_angular is not None and dt_max > 0:
        expected_ratio = abs(wavenumber * expected_c_angular * dt_max) / np.pi
        # Which alias would reconcile the fit with the expectation: the number of
        # whole turns of phase per sample the fit cannot see.
        turns = wavenumber * (expected_c_angular - c_ang) * dt_max / (2 * np.pi)
        alias_order = int(np.round(turns))
        if expected_ratio >= 1.0:
            risk = "severe"
            notes.append(
                f"ALIASING RISK SEVERE: the expected speed advances the phase "
                f"{expected_ratio:.2f} x pi per sample, past Nyquist. The fitted speed is "
                f"an alias and cannot be corrected after the fact"
                + (f" (it is off by {alias_order} whole turns per sample)." if alias_order else ".")
                + " Re-run with a shorter output cadence."
            )
        elif expected_ratio > 0.5 and risk == "none":
            risk = "marginal"
            notes.append(
                f"the expected speed advances the phase {expected_ratio:.2f} x pi per "
                "sample: resolved, but with little margin"
            )
        if alias_order:
            notes.append(
                f"the fitted speed differs from the expectation by {alias_order} whole "
                "phase turns per sample, which is the signature of undersampling rather "
                "than of a physically different speed"
            )

    # **Is the mode even present on this circle?** Phase is defined for any nonzero
    # complex number, however tiny, so fitting the phase of a mode that is not
    # there returns a confident slope through pure round-off. This is not a corner
    # case: a mode with an antisymmetric meridional structure is identically zero
    # at the equator, so asking for it there is an easy and entirely reasonable
    # mistake that produces a precise, meaningless answer.
    total_power = float(np.sum(np.abs(coef[:, 1:]) ** 2))
    mode_power = float(np.sum(amplitude**2))
    variance_fraction = mode_power / total_power if total_power > 0 else 0.0
    mode_present = variance_fraction > 1e-6
    if not mode_present:
        notes.append(
            f"MODE ABSENT: wavenumber {wavenumber} carries {variance_fraction:.2e} of the "
            "variance on this latitude circle, which is round-off. The fitted speed is "
            "meaningless. A mode with an antisymmetric meridional structure vanishes at "
            "the equator; try a circle where it has amplitude."
        )

    ratio = amplitude[-1] / amplitude[0] if amplitude[0] > 0 else np.inf
    if not amplitude_weighted and (ratio > 10 or ratio < 0.1):
        notes.append(
            f"the mode's amplitude changed by a factor {ratio:.3g} across the window; "
            "consider amplitude_weighted=True"
        )

    c_linear = None
    if latitude_rad is not None and radius_m is not None:
        c_linear = float(c_ang * radius_m * np.cos(latitude_rad))

    return PhaseSpeedFit(
        wavenumber=int(wavenumber),
        c_angular_rad_s=float(c_ang),
        c_angular_stderr_rad_s=c_ang_err,
        c_linear_m_s=c_linear,
        latitude_rad=latitude_rad,
        n_samples=int(time_s.size),
        span_s=float(time_s[-1] - time_s[0]),
        phase_range_rad=float(phase[-1] - phase[0]),
        amplitude_first=float(amplitude[0]),
        amplitude_last=float(amplitude[-1]),
        residual_rms_rad=float(np.sqrt(np.mean(residual**2))),
        nyquist_ratio=float(nyquist_ratio),
        aliasing_risk=risk,
        variance_fraction=float(variance_fraction),
        mode_present=bool(mode_present),
        expected_c_angular_rad_s=expected_c_angular,
        expected_nyquist_ratio=expected_ratio,
        alias_order=alias_order,
        notes=notes,
    )


def synthetic_hovmoller(
    wavenumber: int,
    omega_rad_s: float,
    amplitude: float = 1.0,
    n_longitude: int = 96,
    duration_s: float = 20 * 86400.0,
    n_time: int = 480,
    noise_fraction: float = 0.0,
    seed: int = 0,
):
    """A Hovmöller diagram whose phase speed is known exactly: ``c = omega / m``.

    ``h'(lambda, t) = A cos(m lambda - omega t)``, sampled on the same kind of
    uniform longitude grid and regular output cadence a real run produces, with
    optional Gaussian noise as a fraction of the amplitude. This is the ground
    truth the fitter is required to recover, and it is deliberately built here
    rather than in the test file so that the same generator can be reused to
    characterise the fitter on new sampling regimes later.
    """
    rng = np.random.default_rng(seed)
    lon = np.linspace(0.0, 2 * np.pi, n_longitude, endpoint=False)
    time_s = np.linspace(0.0, duration_s, n_time)
    field = amplitude * np.cos(wavenumber * lon[None, :] - omega_rad_s * time_s[:, None])
    if noise_fraction:
        field = field + rng.normal(0.0, noise_fraction * amplitude, field.shape)
    return field, time_s
