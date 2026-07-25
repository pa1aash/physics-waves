"""Zonal and space-time (Hayashi) spectral decomposition of a longitude-time field.

Physics first. A field on a latitude circle at one instant tells you what scales
are present. A field on a latitude circle *through time* tells you something
strictly stronger: what scales are present **and which way each of them is going**.
That distinction is the entire content of this module, and it is the distinction
the project's central hypothesis turns on — a Rossby wave must travel west, and a
measurement that cannot separate west from east cannot test that.

**Why a plain power spectrum cannot do it.** ``cos(m lambda - omega t)`` and
``cos(m lambda + omega t)`` have identical zonal power spectra at every instant
and identical frequency spectra at every longitude. They differ only in the
*joint* structure, so only a joint transform can tell them apart. Taking the
two-dimensional Fourier transform of ``f(lambda, t)`` and reading off the sign of
the frequency at positive zonal wavenumber is exactly that: for ``m > 0``, positive
frequency is eastward and negative frequency is westward. This is the
decomposition Hayashi introduced for exactly this purpose in atmospheric analysis.

**Why this module exists here rather than in Session L8.** The observational
comparison needs it — ``docs/CONVENTIONS.md``, "Observational comparison: Doppler
correction", requires the observed field be decomposed in wavenumber-frequency
space and the westward branch isolated, because the observed 500 hPa pattern is
advected eastward by the jet while the model measures an *intrinsic* westward
speed in a resting mean flow, and comparing raw ground-relative speeds would be
straightforwardly wrong. That session's data is real, noisy and expensive to
reason about. This session's is fabricated, so the tool can be validated where the
answer is known and then applied where it is not.

**Two numerical points that change the answer, not just the tidiness.**

*Detrending.* The time mean at each longitude is a stationary pattern, not a
wave. Left in, it puts all of its (typically dominant) power on the zero-frequency
line, where it leaks into the low-frequency bins of both branches. It is removed.

*Windowing.* A record of finite length is implicitly periodic to a discrete
transform, and a wave that does not complete a whole number of cycles in the
record has a discontinuity at the seam. The resulting spectral leakage spreads
power across frequencies — including, crucially, **across the sign of the
frequency**, which manufactures a spurious counter-propagating branch out of a
purely one-way wave. A Hann window suppresses that at the cost of frequency
resolution, and its power normalisation is corrected for so that amplitudes
remain physical.
"""

from __future__ import annotations

import numpy as np

# One implementation of the zonal transform in the project, kept where the
# phase-speed fitter uses it most intimately and re-exported here so that a
# caller reaching for "the spectral module" gets the same normalisation.
from src.analysis.fit_phase_speed import dominant_wavenumber, zonal_coefficients

__all__ = [
    "dominant_wavenumber",
    "zonal_coefficients",
    "zonal_spectrum",
    "hayashi_decompose",
    "dominant_propagating_modes",
    "synthetic_two_branch_field",
]


def zonal_spectrum(field: np.ndarray, time_average: bool = True):
    """Amplitude of each zonal wavenumber on a latitude circle.

    ``field`` is ``(n_time, n_longitude)`` or a single ``(n_longitude,)`` profile.
    Returns ``(wavenumbers, amplitudes)`` with amplitudes in the units of the
    field, so that a pure ``A cos(m lambda + phase)`` returns ``A`` at ``m``.

    Time-averaging is over *power*, not over the complex coefficient: averaging
    the coefficient would let a propagating wave cancel itself out, which is
    exactly backwards — a travelling wave is the thing most worth detecting.
    """
    data = np.atleast_2d(np.asarray(field, dtype=float))
    coef = zonal_coefficients(data)
    power = np.abs(coef) ** 2
    if time_average:
        power = power.mean(axis=0)
    return np.arange(power.shape[-1]), np.sqrt(power)


def hayashi_decompose(
    field: np.ndarray,
    time_s: np.ndarray,
    window: str = "hann",
    detrend: bool = True,
) -> dict:
    """Split a longitude-time field into eastward- and westward-propagating power.

    Parameters
    ----------
    field
        ``(n_time, n_longitude)`` samples on one latitude circle, uniformly spaced
        in longitude over the full circle and uniformly spaced in time.
    time_s
        Sample times in seconds; must be uniform for the frequency axis to mean
        anything, and this is checked rather than assumed.
    window
        ``"hann"`` (default) or ``"none"``. See the module docstring: without a
        window, leakage from a record containing a non-integer number of cycles
        manufactures a counter-propagating branch that is not there.
    detrend
        Remove the time mean at each longitude first.

    Returns
    -------
    dict
        ``wavenumbers`` (``m >= 0``), ``frequencies_rad_s`` (``>= 0``),
        ``eastward`` and ``westward`` power arrays of shape
        ``(n_wavenumber, n_frequency)``, and ``eastward_amplitude`` /
        ``westward_amplitude``, which are what a physical amplitude comparison
        should use.

    The sign convention, stated once because everything depends on it: a
    disturbance ``cos(m lambda - omega t)`` with ``m, omega > 0`` has crests moving
    towards **increasing longitude**, i.e. **eastward**, and appears in the
    ``eastward`` array at ``(m, omega)``. ``cos(m lambda + omega t)`` is
    **westward**.
    """
    data = np.asarray(field, dtype=float)
    time_s = np.asarray(time_s, dtype=float)
    if data.ndim != 2:
        raise ValueError(f"expected a (time, longitude) array, got shape {data.shape}")
    if data.shape[0] != time_s.size:
        raise ValueError("field's leading axis must match time_s")
    steps = np.diff(time_s)
    if steps.size and np.ptp(steps) > 1e-6 * np.median(steps):
        raise ValueError(
            "space-time spectral analysis needs uniform time sampling; "
            "interpolate onto a regular cadence first"
        )

    n_time, n_lon = data.shape
    if detrend:
        data = data - data.mean(axis=0, keepdims=True)

    if window == "hann":
        taper = np.hanning(n_time)
        # Preserve power: a Hann window removes a known fraction of the variance.
        taper = taper / np.sqrt(np.mean(taper**2))
    elif window == "none":
        taper = np.ones(n_time)
    else:
        raise ValueError(f"unknown window {window!r}; use 'hann' or 'none'")
    data = data * taper[:, None]

    dt = float(np.median(steps)) if steps.size else 1.0
    spectrum = np.fft.fft2(data) / (n_time * n_lon)
    freq_index = np.fft.fftfreq(n_time, d=dt)  # cycles per second, signed

    n_m = n_lon // 2 + 1

    # **The sign of the frequency index, worked out rather than guessed.** numpy's
    # kernel is exp(-2 pi i j q / N), so bin j holds the component of the signal
    # that varies as exp(+2 pi i f_j t). An eastward wave cos(m lambda - omega t)
    # contains exp(i m lambda) exp(-i omega t), which lands at zonal index +m and
    # at *negative* frequency index. A westward wave cos(m lambda + omega t) lands
    # at positive frequency index. Getting this backwards swaps east and west
    # while leaving every magnitude looking entirely reasonable, which is the
    # failure this comment exists to prevent.
    def _branch(mask):
        freqs = np.abs(2 * np.pi * freq_index[mask])
        order = np.argsort(freqs)
        block = spectrum[mask][:, :n_m][order]
        return freqs[order], np.abs(block).T ** 2

    frequencies, eastward = _branch(freq_index < 0)
    _, westward = _branch(freq_index > 0)

    span = float(time_s[-1] - time_s[0]) + dt
    return {
        "wavenumbers": np.arange(n_m),
        "frequencies_rad_s": frequencies,
        "eastward": eastward,
        "westward": westward,
        "frequency_resolution_rad_s": 2 * np.pi / span,
        "window": window,
        "detrended": bool(detrend),
    }


def mode_amplitude(
    decomposition: dict, direction: str, wavenumber: int, n_band: int = 3
) -> tuple[float, float]:
    """Peak frequency and physical amplitude of one branch at one wavenumber.

    The amplitude is taken from a **band sum** of power around the peak rather
    than from the peak bin alone. A wave whose frequency falls between two bins —
    which is the generic case, since nothing makes a real wave commensurate with
    the record length — spreads its power over neighbouring bins, and the window
    that suppresses leakage spreads it further. Reading the peak bin would then
    under-report the amplitude by tens of per cent, in a way that depends on the
    record length rather than on the physics. Summing the band recovers it,
    because the window is normalised to preserve total power.

    The frequency is refined **below the bin spacing** by fitting a parabola to
    the log-power of the peak bin and its two neighbours. Without that refinement
    the answer is quantised to the frequency resolution ``2 pi / T``, which for a
    twenty-day record is a third of the frequency of an ``n = 4`` Rossby wave — an
    error of tens of per cent on a quantity the project reports to three figures.
    Interpolation is not cosmetic here; it is the difference between a
    resolution-limited number and a measurement.

    Returns ``(frequency_rad_s, amplitude)``. The factor of two converts the
    half-plane coefficient of a real field into the amplitude of the physical
    cosine.
    """
    power = decomposition[direction][wavenumber]
    frequencies = decomposition["frequencies_rad_s"]
    peak = int(np.argmax(power))
    lo, hi = max(peak - n_band, 0), min(peak + n_band + 1, power.size)
    amplitude = float(2 * np.sqrt(power[lo:hi].sum()))

    frequency = float(frequencies[peak])
    if 0 < peak < power.size - 1:
        left, centre, right = (
            float(np.log(max(power[i], 1e-300))) for i in (peak - 1, peak, peak + 1)
        )
        denominator = left - 2 * centre + right
        if denominator < 0:  # a genuine maximum
            offset = 0.5 * (left - right) / denominator
            if abs(offset) <= 1.0:
                spacing = float(frequencies[peak + 1] - frequencies[peak])
                frequency += offset * spacing
    return frequency, amplitude


def dominant_propagating_modes(decomposition: dict, n_modes: int = 3) -> list[dict]:
    """The strongest ``(wavenumber, frequency, direction)`` peaks, most powerful first.

    Each entry carries the implied angular phase speed ``c_ang = omega / m``, signed
    so that negative is westward — the same convention as the phase-speed fitter
    and as ``theory/derivations.tex``, so the two can be compared without a mental
    sign flip.
    """
    found = []
    for direction, sign in (("eastward", +1.0), ("westward", -1.0)):
        power = decomposition[direction]
        for m in range(1, power.shape[0]):
            omega, amplitude = mode_amplitude(decomposition, direction, m)
            found.append(
                {
                    "direction": direction,
                    "wavenumber": int(decomposition["wavenumbers"][m]),
                    "frequency_rad_s": omega,
                    "amplitude": amplitude,
                    "power": amplitude**2,
                    "c_angular_rad_s": float(sign * omega / m),
                }
            )
    found.sort(key=lambda row: row["power"], reverse=True)
    return found[:n_modes]


def synthetic_two_branch_field(
    eastward: tuple[int, float, float],
    westward: tuple[int, float, float],
    n_longitude: int = 96,
    duration_s: float = 20 * 86400.0,
    n_time: int = 480,
    noise_fraction: float = 0.0,
    seed: int = 0,
):
    """A field containing one eastward and one westward wave, both known exactly.

    Each argument is ``(wavenumber, angular frequency in rad/s, amplitude)``. Give
    them the **same wavenumber** to build the case that matters for Session L8: an
    observed field in which a stationary-frame eastward signal and an intrinsic
    westward signal share a zonal scale and can only be separated in
    frequency-wavenumber space. A tool that cannot split that superposition cannot
    do the Doppler correction the conventions require.
    """
    rng = np.random.default_rng(seed)
    lon = np.linspace(0.0, 2 * np.pi, n_longitude, endpoint=False)
    time_s = np.linspace(0.0, duration_s, n_time)
    m_e, w_e, a_e = eastward
    m_w, w_w, a_w = westward
    field = a_e * np.cos(m_e * lon[None, :] - w_e * time_s[:, None])
    field = field + a_w * np.cos(m_w * lon[None, :] + w_w * time_s[:, None])
    if noise_fraction:
        scale = noise_fraction * max(abs(a_e), abs(a_w))
        field = field + rng.normal(0.0, scale, field.shape)
    return field, time_s
