"""Meridional structure of a single zonal mode, and its comparison with an eigenfunction.

Physics first. A growth rate is one number; the *shape* of the disturbance that
grows is a whole function of latitude, and it carries information the rate cannot.
Where the disturbance is centred says which part of the jet the instability is
feeding on. How wide it is says whether it is trapped on one flank or spans both.
And the way its phase tilts with latitude is the thing that actually transports
momentum — a disturbance whose crests lean against the shear is extracting energy
from the mean flow, and one whose crests are meridionally aligned is not.

So this module exists to ask a sharper question than "does the growth rate match":
**is the simulation growing the same mode the eigenvalue problem predicts?** Two
different modes can share a growth rate by coincidence. Two different modes cannot
share a meridional structure.

**Why the shape settling down is itself a result.** A seeded bump is not a normal
mode; it is a superposition of all of them. As the fastest-growing one outruns the
rest, the *normalised* shape stops changing even while the amplitude climbs
through orders of magnitude. :func:`structure_convergence` measures that
settling, and it is the cleanest available evidence that a run has entered the
regime where comparison with a normal-mode calculation is meaningful at all — more
direct than the log-linearity of an energy curve, which several superposed modes
can mimic.

**A note on what "the amplitude profile" is.** For zonal wavenumber ``m`` the field
is projected onto ``exp(i m lambda)`` at each latitude, giving a complex
``A_m(phi)``. Its modulus is the amplitude profile and its argument is the phase.
Both are needed: comparing only moduli would call a mode and its mirror image the
same thing.
"""

from __future__ import annotations

import numpy as np


def zonal_mode_profile(field: np.ndarray, wavenumber: int) -> np.ndarray:
    """Project a field onto ``exp(i m lambda)`` at each latitude.

    ``field`` is ``(n_longitude, n_latitude)`` for a single time, or
    ``(n_time, n_longitude, n_latitude)``. Returns the complex ``A_m(phi)``, with
    the same leading time axis if one was given, normalised so that the physical
    disturbance at that latitude is ``|A_m| cos(m lambda + arg A_m)``.
    """
    data = np.asarray(field, dtype=float)
    axis = -2  # longitude is always the penultimate axis
    n_lon = data.shape[axis]
    if not 0 <= wavenumber <= n_lon // 2:
        raise ValueError(f"wavenumber {wavenumber} not resolvable on {n_lon} longitudes")
    coef = np.fft.rfft(data, axis=axis) * (2.0 / n_lon)
    return np.take(coef, wavenumber, axis=axis)


def normalise_profile(profile: np.ndarray) -> np.ndarray:
    """Scale a complex profile to unit maximum modulus and zero phase at that point.

    Removing the overall complex factor is what makes two profiles comparable: an
    eigenvector is defined only up to a complex multiple, and a growing disturbance
    changes its own amplitude and phase every timestep. What is physical is the
    *relative* variation with latitude, and that is what survives this.
    """
    profile = np.asarray(profile, dtype=complex)
    peak = int(np.argmax(np.abs(profile)))
    if np.abs(profile[peak]) == 0:
        raise ValueError("profile is identically zero")
    return profile / profile[peak]


def pattern_correlation(a: np.ndarray, b: np.ndarray, lat: np.ndarray) -> float:
    """Area-weighted correlation between two meridional profiles, in ``[0, 1]``.

    Weighted by ``cos(phi)``, because a degree of latitude near the pole covers far
    less of the sphere than one at the equator, and an unweighted correlation would
    let polar noise outvote the jet. The modulus of the complex correlation is
    returned, so a constant phase offset between the two profiles does not count as
    a disagreement — only a difference in *shape* does.
    """
    a, b = np.asarray(a, dtype=complex), np.asarray(b, dtype=complex)
    w = np.cos(np.asarray(lat, dtype=float))
    inner = np.sum(w * a * np.conj(b))
    norm = np.sqrt(np.sum(w * np.abs(a) ** 2) * np.sum(w * np.abs(b) ** 2))
    return float(np.abs(inner) / norm) if norm > 0 else 0.0


def structure_diagnostics(profile: np.ndarray, lat: np.ndarray) -> dict:
    """Where the disturbance sits, how wide it is, and how much its phase tilts.

    ``centroid_lat_rad`` is the amplitude-weighted mean latitude — the latitude the
    instability is drawing on. ``width_lat_rad`` is the amplitude-weighted standard
    deviation. ``phase_tilt_rad`` is the total change of phase across the region
    where the disturbance has appreciable amplitude, which is the momentum-flux
    signature: a mode with no tilt transports no momentum and cannot convert mean
    to eddy energy.
    """
    profile = np.asarray(profile, dtype=complex)
    lat = np.asarray(lat, dtype=float)
    amplitude = np.abs(profile)
    weight = amplitude * np.cos(lat)
    total = weight.sum()
    if total <= 0:
        raise ValueError("profile has no amplitude to characterise")
    centroid = float(np.sum(weight * lat) / total)
    width = float(np.sqrt(np.sum(weight * (lat - centroid) ** 2) / total))

    core = amplitude > 0.25 * amplitude.max()
    phase = np.unwrap(np.angle(profile))
    tilt = float(phase[core][-1] - phase[core][0]) if core.sum() > 1 else 0.0
    return {
        "centroid_lat_rad": centroid,
        "centroid_lat_deg": float(np.degrees(centroid)),
        "width_lat_rad": width,
        "width_lat_deg": float(np.degrees(width)),
        "peak_lat_deg": float(np.degrees(lat[int(np.argmax(amplitude))])),
        "phase_tilt_rad": tilt,
    }


def structure_convergence(field: np.ndarray, wavenumber: int, lat: np.ndarray) -> dict:
    """How fast the normalised meridional shape stops changing, sample by sample.

    Returns the pattern correlation between consecutive normalised profiles. A
    sequence rising towards 1 is a run in which one mode has taken over; a sequence
    that stays low is one in which several are still competing, and any comparison
    with a single eigenfunction from such a run is meaningless however well the
    growth rates happen to agree.
    """
    profiles = zonal_mode_profile(field, wavenumber)
    if profiles.ndim != 2:
        raise ValueError("structure_convergence needs a (time, longitude, latitude) field")
    correlations = [
        pattern_correlation(normalise_profile(profiles[i]), normalise_profile(profiles[i - 1]), lat)
        for i in range(1, profiles.shape[0])
    ]
    correlations = np.array(correlations)
    return {
        "correlations": correlations,
        "final": float(correlations[-1]) if correlations.size else float("nan"),
        "settled": bool(correlations.size and np.all(correlations[-3:] > 0.99)),
    }


def compare_with_eigenfunction(
    field: np.ndarray,
    wavenumber: int,
    lat: np.ndarray,
    eigenvector: np.ndarray,
    degrees: np.ndarray,
    time_index: int = -1,
) -> dict:
    """Compare a run's measured mode structure against a predicted eigenfunction.

    The eigenvector is a set of spectral coefficients from
    :func:`src.solver.evp_stability.stability_evp`; it is evaluated on the run's own
    latitude grid by the routine that owns that basis, so the two are being compared
    on the same footing rather than through two independent transcriptions of a
    normalisation.

    Returns the correlation and both sets of structure diagnostics. A correlation
    near 1 means the simulation is growing the mode the eigenvalue problem
    predicts; anything much below that is a result in its own right and should not
    be smoothed over.
    """
    from src.solver.evp_stability import eigenfunction_on_latitudes

    measured = zonal_mode_profile(field, wavenumber)
    if measured.ndim == 2:
        measured = measured[time_index]
    measured = normalise_profile(measured)
    predicted = normalise_profile(eigenfunction_on_latitudes(eigenvector, degrees, wavenumber, lat))
    return {
        "wavenumber": int(wavenumber),
        "correlation": pattern_correlation(measured, predicted, lat),
        "measured": structure_diagnostics(measured, lat),
        "predicted": structure_diagnostics(predicted, lat),
    }
