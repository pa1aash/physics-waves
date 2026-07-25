"""How a field's variance is distributed across scales: the spherical-harmonic spectrum.

Physics first. A single number — the total energy, the total enstrophy — says how
much there is. The spectrum says *where it lives*, and on a rotating sphere that
is the more physical question, because the fluid's behaviour is a function of
scale rather than of amplitude.

Total spherical-harmonic degree ``n`` is the honest measure of scale here. A mode
of degree ``n`` has ``n`` nodal lines on the sphere however they are oriented, so
its horizontal wavelength is roughly ``2 pi R / n`` regardless of how the pattern
is tilted between zonal and meridional. That is why the Rossby-Haurwitz phase
speed ``c_ang = -2 Omega / [n(n+1)]`` depends on ``n`` alone and not on the zonal
order ``m``: the restoring mechanism cares how tightly the flow is curved, not
which way the crests lean. Degree is the axis on which this project's central
dispersion relation is written, so it is the axis its spectra are computed on.

Azimuthal order ``m`` is the complementary cut, and it answers different questions.
It is the wavenumber that is actually observed — "zonal wavenumber 5" in a
reanalysis — it is the quantum number the barotropic instability selects (the
Galewsky jet picks ``m*`` around 6 and the eigenvalue problem predicts which), and
it is the label under which growth rates are fitted. So both spectra are provided:
:func:`power_spectrum` in degree, :func:`zonal_power_spectrum` in order.

**What a spectrum is diagnosing, beyond description.** Two-dimensional turbulence
on a sphere sends enstrophy *down* to small scales and energy *up* to large ones.
The hyperdiffusion in this solver exists solely to absorb the downward enstrophy
flux at the grid scale — it is a numerical regulariser and not physics. When it is
doing its job the spectrum falls steeply at the highest degrees. When it is not,
variance accumulates at the truncation because the cascade arrives and has nowhere
to go, and that pile-up is visible in the spectrum long before it corrupts anything
a snapshot would show. :func:`tail_power_fraction` measures exactly that. A
spectrum that turns up at its right-hand edge is a run whose dissipation is
under-strength, whatever its conservation series says.

**The transform, and why it is done this way.** A field is expanded as
``f = sum_{n,m} a_n^m Y_n^m`` with the orthonormal harmonics

    Y_n^m(lambda, mu) = Pbar_n^m(mu) exp(i m lambda) / sqrt(2 pi),
    integral |Y_n^m|^2 dlambda dmu = 1,

where ``mu = cos(theta) = sin(latitude)`` and ``Pbar`` is the associated Legendre
function normalised so that ``integral_{-1}^{1} Pbar^2 dmu = 1``. That is exactly
``scipy.special.assoc_legendre_p_all(..., norm=True)``, the same normalisation
``src/solver/evp_stability.py`` and ``theory/sympy_checks/check_rayleigh_kuo.py``
use for their Galerkin bases, so a coefficient computed here and a mode amplitude
computed there mean the same thing. The transform splits into

* a Fourier transform in longitude, exact because the grid is uniform and the
  field is band-limited — ``numpy.fft`` does it;
* a quadrature in ``mu``, exact because the solver's colatitude grid *is* the
  Gauss-Legendre grid in ``mu``. This is the reason the latitudinal integral must
  never be a plain mean over grid points: those points are clustered towards the
  poles, and an unweighted average would weight polar cells many times too heavily.

Both being exact, the transform is exact and Parseval holds to round-off. The
power reported is normalised so that

    sum over n of power(n)  =  the area average of f^2 ,

i.e. the mean square of the field, decomposed by scale. That choice makes the
numbers directly comparable to a root-mean-square amplitude, and makes the
spectrum of two runs at different resolutions comparable without rescaling.

**Where the truncation is.** A Gauss-Legendre rule on ``Ntheta`` nodes integrates
polynomials of degree ``2 Ntheta - 1`` exactly, and the product of two Legendre
functions of degree ``n`` has degree ``2n``, so degrees up to ``Ntheta - 1`` are
recovered exactly and nothing beyond them exists on the grid at all. For this
project's L0 grid, ``64 x 32``, that is ``n <= 31`` — which is also the solver's
own spectral truncation, not a coincidence but the same statement seen from the
grid side.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.special import assoc_legendre_p_all, roots_legendre

from src.diagnostics.slices import read_handler

#: How far a run's colatitude grid may sit from the exact Gauss-Legendre nodes
#: before the quadrature is refused. This is not a physical tolerance: the grid is
#: either the one the quadrature weights belong to or it is not, and on a grid it
#: is not, every coefficient below is silently wrong.
GRID_ATOL = 1.0e-10


def max_representable_degree(n_colatitudes: int, n_longitudes: int) -> int:
    """The highest total degree this grid actually carries.

    Bounded from the latitudinal side by exactness of the Gauss-Legendre rule
    (``Ntheta - 1``) and from the zonal side by the Fourier grid (``Nphi/2 - 1``,
    excluding the Nyquist wavenumber, which a real field carries only half of).
    This project sets ``Nphi = 2 Ntheta``, so the two bounds coincide.
    """
    return int(min(n_colatitudes - 1, n_longitudes // 2 - 1))


def gauss_legendre_weights(colatitude_rad: np.ndarray) -> np.ndarray:
    """Quadrature weights in ``mu = cos(theta)`` for a run's own colatitude grid.

    Returned in the order the file stores the grid in, so they can multiply a field
    array directly. The grid is checked against the exact Gauss-Legendre nodes
    rather than assumed: applying Gaussian weights to a grid that is not Gaussian
    produces a plausible, wrong spectrum, with no symptom.
    """
    mu = np.cos(np.asarray(colatitude_rad, dtype=float))
    nodes, weights = roots_legendre(mu.size)
    order = np.argsort(mu)
    if not np.allclose(mu[order], nodes, atol=GRID_ATOL, rtol=0.0):
        raise ValueError(
            f"this {mu.size}-point colatitude grid is not the Gauss-Legendre grid "
            "in cos(theta); the largest departure is "
            f"{np.max(np.abs(mu[order] - nodes)):.3e}. Gaussian quadrature weights "
            "do not apply to it and the resulting spectrum would be wrong without "
            "looking wrong."
        )
    ordered = np.empty_like(weights)
    ordered[order] = weights
    return ordered


@lru_cache(maxsize=4)
def _legendre_table(nmax: int, mu_bytes: bytes, count: int) -> np.ndarray:
    """``Pbar_n^m(mu)`` for ``0 <= m <= n <= nmax``, indexed ``[n, m, node]``.

    Cached because a time series evaluates the same table at every output time, and
    building it is the whole cost of the transform. Memory grows as
    ``nmax^2 * Ntheta``, which is 16 MB at L1 and comfortably too much at L3 — at
    that resolution a dense transform is the wrong tool and a fast spherical
    transform is the right one.
    """
    mu = np.frombuffer(mu_bytes, dtype=np.float64, count=count)
    table = assoc_legendre_p_all(nmax, nmax, mu, norm=True, diff_n=0)
    return np.ascontiguousarray(table[0, :, : nmax + 1, :])


@dataclass(frozen=True)
class SphericalHarmonicTransform:
    """The machinery of one grid's transform, built once and reused.

    Holds the Gauss-Legendre nodes and weights and the normalised Legendre table
    for a given colatitude grid and truncation. Constructing it is the expensive
    part, so a spectrum of a hundred snapshots costs one construction.
    """

    colatitude_rad: np.ndarray
    mu: np.ndarray
    weights: np.ndarray
    legendre: np.ndarray
    nmax: int

    @classmethod
    def for_grid(cls, colatitude_rad, nmax: int | None = None) -> SphericalHarmonicTransform:
        colatitude = np.asarray(colatitude_rad, dtype=float)
        mu = np.cos(colatitude)
        weights = gauss_legendre_weights(colatitude)
        if nmax is None:
            nmax = mu.size - 1
        nmax = int(nmax)
        if not 0 <= nmax <= mu.size - 1:
            raise ValueError(
                f"nmax = {nmax} is outside what a {mu.size}-point Gaussian grid "
                f"represents exactly (0 to {mu.size - 1})"
            )
        table = _legendre_table(nmax, np.ascontiguousarray(mu).tobytes(), mu.size)
        return cls(
            colatitude_rad=colatitude,
            mu=mu,
            weights=weights,
            legendre=table,
            nmax=nmax,
        )

    @property
    def degrees(self) -> np.ndarray:
        return np.arange(self.nmax + 1)

    def coefficients(self, field: np.ndarray) -> np.ndarray:
        """The complex coefficients ``a_n^m`` for ``0 <= m <= n <= nmax``.

        ``field`` has shape ``(n_longitudes, n_colatitudes)``, longitude first, as
        every task in this project is stored. Only non-negative orders are
        returned: a real field satisfies ``|a_n^{-m}| = |a_n^m|``, so the negative
        half carries no independent information, and every power routine below
        folds it back in explicitly rather than leaving the factor of two implied.
        """
        values = _as_map(field, self.mu.size)
        n_lon = values.shape[0]
        if self.nmax > n_lon // 2 - 1:
            raise ValueError(
                f"a {n_lon}-point longitude grid resolves orders only up to "
                f"m = {n_lon // 2 - 1} below the Nyquist wavenumber, so a "
                f"truncation at n = {self.nmax} would alias the sectoral modes"
            )
        # Mean of f * exp(-i m lambda) over the uniform longitude grid; exact for a
        # band-limited field, so the longitude integral is 2*pi times this.
        fourier = np.fft.fft(values, axis=0) / n_lon
        weighted = self.legendre * self.weights  # [n, m, node]
        return np.sqrt(2.0 * np.pi) * np.einsum(
            "nmk,mk->nm", weighted, fourier[: self.nmax + 1], optimize=True
        )


def _as_map(field, n_colatitudes: int) -> np.ndarray:
    """Validate that an array really is one ``(longitude, colatitude)`` map."""
    values = np.asarray(field, dtype=float)
    if values.ndim != 2:
        raise ValueError(f"expected a 2-D (longitude, colatitude) map, got shape {values.shape}")
    if values.shape[1] != n_colatitudes:
        if values.shape[0] == n_colatitudes:
            raise ValueError(
                f"field has shape {values.shape} but the grid has {n_colatitudes} "
                "colatitudes; this looks transposed. Tasks are stored longitude-first."
            )
        raise ValueError(
            f"field has shape {values.shape}, which does not match a grid of "
            f"{n_colatitudes} colatitudes"
        )
    return values


def _fold_orders(coefficients: np.ndarray) -> np.ndarray:
    """Squared moduli with the negative orders folded in, ``|a_n^m|^2`` weighted.

    ``m = 0`` counts once; every ``m > 0`` counts twice, because a real field's
    ``-m`` coefficient has the same modulus. Entries with ``m > n`` do not exist
    and are zeroed.
    """
    n_index, m_index = np.indices(coefficients.shape)
    squared = np.where(m_index <= n_index, np.abs(coefficients) ** 2, 0.0)
    multiplicity = np.where(m_index == 0, 1.0, 2.0)
    return squared * multiplicity


def power_spectrum(
    field: np.ndarray,
    colatitude_rad: np.ndarray,
    *,
    nmax: int | None = None,
    transform: SphericalHarmonicTransform | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Power in each total spherical-harmonic degree ``n``.

    Returns ``(degrees, power)`` with ``power`` normalised so that its sum is the
    area average of ``field**2`` — the mean square of the field, sorted by scale.
    For a vorticity field that sum is twice the enstrophy per unit area; for a
    height field it is the mean square free-surface displacement.
    """
    transform = transform or SphericalHarmonicTransform.for_grid(colatitude_rad, nmax)
    folded = _fold_orders(transform.coefficients(field))
    return transform.degrees, folded.sum(axis=1) / (4.0 * np.pi)


def zonal_power_spectrum(
    field: np.ndarray,
    colatitude_rad: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Power in each azimuthal (zonal) wavenumber ``m``.

    This is the spectrum in the wavenumber an observer names — "zonal wavenumber
    5" — and the one an instability's dominant mode is quoted in. It needs no
    Legendre functions: Parseval in longitude plus the same Gauss-Legendre
    quadrature in ``mu`` gives it directly, and the sum over ``m`` is again the
    area average of ``field**2``, so the degree and order spectra of one field have
    the same total by construction.

    ``m = 0`` is the zonal mean — the axisymmetric part of the flow, the jet
    itself in an instability run — so the eddy field is everything with ``m >= 1``.
    """
    colatitude = np.asarray(colatitude_rad, dtype=float)
    weights = gauss_legendre_weights(colatitude)
    values = _as_map(field, colatitude.size)
    n_lon = values.shape[0]
    fourier = np.fft.fft(values, axis=0) / n_lon
    signed = 0.5 * (np.abs(fourier) ** 2 @ weights)

    n_orders = n_lon // 2 + 1
    orders = np.arange(n_orders)
    power = signed[:n_orders].copy()
    # Every order except the mean and, for an even grid, the Nyquist wavenumber has
    # a negative-order partner of equal power.
    last = n_orders - 1 if n_lon % 2 == 0 else n_orders
    power[1:last] *= 2.0
    return orders, power


def tail_power_fraction(degrees: np.ndarray, power: np.ndarray, *, tail: float = 0.1) -> float:
    """Share of the power sitting in the highest ``tail`` fraction of degrees.

    The pile-up diagnostic. Hyperdiffusion is meant to absorb the enstrophy cascade
    at the grid scale, so a healthy spectrum has almost nothing here; a rising
    value across a run means variance is arriving at the truncation faster than the
    regulariser removes it, which is the failure mode blueprint section 9.3 calls
    an early warning when it shows up in potential enstrophy. This sees it one step
    earlier, and says at which scale.
    """
    if not 0.0 < tail <= 1.0:
        raise ValueError(f"tail must lie in (0, 1], got {tail}")
    degrees = np.asarray(degrees)
    power = np.asarray(power, dtype=float)
    total = power.sum()
    if total <= 0.0:
        return 0.0
    cutoff = degrees.max() * (1.0 - tail)
    return float(power[degrees > cutoff].sum() / total)


@dataclass(frozen=True)
class SpectrumSeries:
    """One field's power spectrum at every output time of a handler.

    ``power`` has shape ``(n_times, n_degrees)``. Watching a row evolve is watching
    the cascade: in an instability run the initial power sits at the jet's own
    scale and spreads outward in ``n`` as the flow rolls up.
    """

    run_id: str
    field: str
    time_s: np.ndarray
    degrees: np.ndarray
    power: np.ndarray
    si: bool

    @property
    def time_days(self) -> np.ndarray:
        return self.time_s / 86400.0

    def tail_fraction(self, *, tail: float = 0.1) -> np.ndarray:
        """The pile-up diagnostic at every output time."""
        return np.array([tail_power_fraction(self.degrees, row, tail=tail) for row in self.power])


def power_spectrum_series(
    run,
    field_name: str = "vorticity",
    *,
    handler: str = "snapshots",
    nmax: int | None = None,
    to_si: bool = True,
    runs_root: Path | None = None,
) -> SpectrumSeries:
    """The degree spectrum of one field at every time the handler wrote it.

    The transform is built once for the run's grid and reused across times, which
    is the only reason this is affordable at production resolution.
    """
    output = read_handler(run, handler, tasks=[field_name], to_si=to_si, runs_root=runs_root)
    values = output.tasks[field_name]
    if values.ndim != 3:
        raise ValueError(
            f"task {field_name!r} has shape {values.shape}; a degree spectrum needs "
            "a scalar field stored as (time, longitude, colatitude)"
        )
    if not output.grid_matches_tasks:
        raise ValueError(
            f"the {handler!r} handler's stored colatitude grid does not describe its "
            "tasks, so a latitudinal quadrature over it is meaningless; spectra are "
            "computed from the snapshot handler, which carries the full sphere"
        )
    transform = SphericalHarmonicTransform.for_grid(output.colatitude_rad, nmax)
    spectra = np.array(
        [power_spectrum(frame, output.colatitude_rad, transform=transform)[1] for frame in values]
    )
    return SpectrumSeries(
        run_id=output.run_id,
        field=field_name,
        time_s=output.time_s,
        degrees=transform.degrees,
        power=spectra,
        si=to_si,
    )


def real_harmonic_field(
    lon_rad: np.ndarray,
    colatitude_rad: np.ndarray,
    n: int,
    m: int,
    *,
    phase: float = 0.0,
) -> np.ndarray:
    """The real spherical harmonic ``Pbar_n^m(mu) cos(m lambda + phase)`` on a grid.

    Built with the same normalisation the transform assumes, so it is the exact
    field whose power must land entirely in degree ``n`` and order ``m`` — which is
    how the transform is checked. It is also the shape of a Rossby-Haurwitz mode:
    ``src/solver/initial_conditions/single_harmonic.py`` initialises the phase-speed
    campaign with precisely this pattern as a streamfunction, because a single
    harmonic is an exact solution of the nondivergent barotropic problem at any
    amplitude.

    Returns an array of shape ``(len(lon_rad), len(colatitude_rad))``.
    """
    if not 0 <= m <= n:
        raise ValueError(f"need 0 <= m <= n; got n={n}, m={m}")
    mu = np.cos(np.asarray(colatitude_rad, dtype=float))
    table = assoc_legendre_p_all(n, m, mu, norm=True, diff_n=0)
    legendre = table[0, n, m]
    azimuth = np.cos(m * np.asarray(lon_rad, dtype=float) + phase)
    return azimuth[:, None] * legendre[None, :]
