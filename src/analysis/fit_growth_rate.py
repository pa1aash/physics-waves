"""Fit an exponential growth rate from an instability diagnostic time series.

Physics first. A barotropically unstable jet does not simply "become turbulent" —
for a while it does something much more specific and much more measurable. A small
disturbance projects onto the normal modes of the linearised operator, the
fastest-growing one outruns the rest, and from then until nonlinearity intervenes
the disturbance amplitude grows as ``exp(sigma t)`` with a *single* ``sigma``. That
window is the only part of an instability run where the simulation and the
eigenvalue problem of ``theory/derivations.tex`` §9 are talking about the same
quantity, and everything this module does is in service of finding it and
measuring its slope.

**Energy grows twice as fast as amplitude.** Eddy kinetic energy and eddy
enstrophy are quadratic in the disturbance, so they go as ``exp(2 sigma t)``. Get
that factor wrong and every growth rate in the project is out by a factor of two —
which is why the convention is an explicit argument here rather than a comment.

**Three things systematically bias a naive log-linear fit, and all three are real
in this project's runs.**

1. *Saturation.* Past the linear phase the disturbance stops growing and starts
   rearranging the jet. Including saturated samples flattens the fit. The window
   must end before that, and :func:`select_growth_window` finds where.
2. *The initial transient.* The seeded disturbance is not the fastest-growing
   normal mode; it is a bump. The first days are spent shedding the other modes,
   and during them the apparent growth rate is a weighted average over whatever
   was excited. The window must start after that.
3. *Oscillation.* Real eddy energy does not climb smoothly — it wobbles, because
   more than one mode is present and their interference beats. Least squares over
   a whole number of beat periods is unbiased; over a fraction of one it is not,
   and the bias does not shrink with more samples inside the same window. The fix
   implemented here is to detect the oscillation and fit it explicitly rather than
   hope the window happens to be commensurate.

The uncertainty returned is the standard error of the slope, and — per
``docs/CONVENTIONS.md``, "Uncertainty reporting" — the dominant source has to be
named rather than left implicit. For a **real** instability record, where a
transient and a saturation bracket the growth phase, that source is the choice of
window and not the sampling noise: :func:`window_sensitivity` measures it, and it
is typically an order of magnitude larger than the standard error. For a clean
exponential the ordering reverses, which is the correct statement that the window
does not matter there. Quote whichever is larger, and say which it was.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import numpy as np

# A quadratic diagnostic (energy, enstrophy) grows as exp(2 sigma t); a linear one
# (an amplitude) as exp(sigma t).
QUANTITY_EXPONENT = {"energy": 2.0, "enstrophy": 2.0, "quadratic": 2.0, "amplitude": 1.0}


@dataclass
class GrowthRateFit:
    """One growth-rate fit, with enough context to decide whether to believe it."""

    growth_rate_s: float
    growth_rate_stderr_s: float
    e_folding_days: float | None
    quantity: str
    window_start_s: float
    window_end_s: float
    n_samples: int
    log_range: float
    r_squared: float
    oscillation_period_s: float | None
    oscillation_amplitude: float | None
    notes: list[str] = dataclass_field(default_factory=list)

    def as_dict(self) -> dict:
        out = dict(self.__dict__)
        out["notes"] = list(self.notes)
        return out


def _loglinear(time_s: np.ndarray, log_series: np.ndarray, extra_columns=None):
    """Least squares of ``log_series`` on time, optionally with extra basis columns."""
    columns = [time_s, np.ones_like(time_s)]
    if extra_columns is not None:
        columns.extend(extra_columns)
    design = np.vstack(columns).T
    solution, *_ = np.linalg.lstsq(design, log_series, rcond=None)
    residual = log_series - design @ solution
    dof = max(time_s.size - design.shape[1], 1)
    sigma2 = float(residual @ residual / dof)
    covariance = sigma2 * np.linalg.pinv(design.T @ design)
    total = float(np.sum((log_series - log_series.mean()) ** 2))
    r_squared = 1.0 - float(residual @ residual) / total if total > 0 else 1.0
    return solution, float(np.sqrt(covariance[0, 0])), residual, r_squared


def _harmonic_columns(time_s: np.ndarray, period: float, n_harmonics: int):
    """Sine and cosine basis columns at ``period`` and its first few harmonics.

    Harmonics are not decoration. A diagnostic that oscillates *multiplicatively*,
    ``E = E0 exp(k sigma t) (1 + a cos w t)``, contributes ``log(1 + a cos w t)`` to
    the log-series, and that is a sinusoid only for infinitesimal ``a``. At the
    30-50% modulation real eddy energy shows, its second harmonic is at the
    per-cent level of the fundamental — comparable with the bias being chased —
    so fitting the fundamental alone leaves a systematic residue.
    """
    w = 2 * np.pi / period
    columns = []
    for k in range(1, n_harmonics + 1):
        columns.append(np.cos(k * w * time_s))
        columns.append(np.sin(k * w * time_s))
    return columns


def _oscillation_rss(period: float, time_s: np.ndarray, log_series: np.ndarray, n_harmonics: int):
    """Residual sum of squares of the full model at a trial ``period``.

    This is variable projection: the model is linear in every parameter except the
    frequency, so the linear ones are eliminated exactly at each trial frequency
    and only a one-dimensional search remains. That matters because a grid search
    over frequency is only as accurate as its spacing, and a 1% frequency error
    leaves a residual that correlates with time and biases the slope — which is the
    very thing the oscillation fit exists to remove.
    """
    _, _, residual, _ = _loglinear(
        time_s, log_series, extra_columns=_harmonic_columns(time_s, period, n_harmonics)
    )
    return float(residual @ residual)


def _detect_oscillation(time_s: np.ndarray, log_series: np.ndarray, n_harmonics: int = 2):
    """Find the dominant periodic component of the log-series, if there is one.

    Returns ``(period_s, amplitude)`` or ``(None, None)``. A coarse geometric scan
    brackets the best period, then a bounded scalar minimisation refines it — the
    scan alone is limited by its spacing, and refinement is what takes the
    frequency error from about a per cent to negligible.

    The threshold for "there is one" is that the oscillation must explain at least
    a third of the variance left by the straight-line fit. Below that, fitting
    sinusoids to noise would remove real degrees of freedom and make the slope's
    error bar dishonestly small.
    """
    from scipy.optimize import minimize_scalar

    span = float(time_s[-1] - time_s[0])
    if span <= 0 or time_s.size < 4 * (n_harmonics + 1):
        return None, None
    dt = float(np.median(np.diff(time_s)))

    _, _, plain_residual, _ = _loglinear(time_s, log_series)
    total = float(plain_residual @ plain_residual)
    if total <= 0:
        return None, None

    # Periods from a few samples (below that the harmonics alias) up to the whole
    # window (beyond that a "cycle" is indistinguishable from the linear trend).
    periods = np.geomspace(3.0 * dt * n_harmonics, span, 600)
    rss = np.array([_oscillation_rss(p, time_s, log_series, n_harmonics) for p in periods])
    k = int(np.argmin(rss))
    lo = periods[max(k - 1, 0)]
    hi = periods[min(k + 1, periods.size - 1)]
    if hi > lo:
        refined = minimize_scalar(
            _oscillation_rss,
            bounds=(lo, hi),
            args=(time_s, log_series, n_harmonics),
            method="bounded",
            options={"xatol": (hi - lo) * 1e-6},
        )
        period, best_rss = float(refined.x), float(refined.fun)
    else:
        period, best_rss = float(periods[k]), float(rss[k])

    if (total - best_rss) / total < 1 / 3:
        return None, None
    solution, _, _, _ = _loglinear(
        time_s, log_series, extra_columns=_harmonic_columns(time_s, period, n_harmonics)
    )
    amplitude = float(np.hypot(solution[2], solution[3]))
    return period, amplitude


def _curvature_significance(time_s: np.ndarray, log_series: np.ndarray) -> float:
    """How many standard errors the quadratic term of a log-fit sits from zero.

    This is the criterion for "is this stretch really exponential". It is used in
    preference to the more obvious ``R^2`` because ``R^2`` is useless here: over a
    window spanning several e-foldings the linear trend accounts for essentially
    all the variance, so ``R^2`` stays above 0.999 even while visible curvature
    from saturation is bending the series and dragging the slope down by ten per
    cent. Curvature significance asks the right question directly — *is there a
    systematic bend, relative to the scatter?* — and it is scale-free, so it does
    not need a threshold retuned for every noise level.
    """
    t = time_s - time_s.mean()
    design = np.vstack([t**2, t, np.ones_like(t)]).T
    solution, *_ = np.linalg.lstsq(design, log_series, rcond=None)
    residual = log_series - design @ solution
    dof = max(t.size - 3, 1)
    covariance = float(residual @ residual / dof) * np.linalg.pinv(design.T @ design)
    stderr = float(np.sqrt(covariance[0, 0]))
    return abs(float(solution[0])) / stderr if stderr > 0 else np.inf


def select_growth_window(
    time_s: np.ndarray,
    series: np.ndarray,
    min_points: int = 8,
    max_curvature_sigma: float = 3.0,
) -> tuple[int, int]:
    """Find the stretch spanning the most e-foldings while staying genuinely straight.

    This is the linear growth phase, located rather than assumed. The initial
    transient (the seeded bump shedding every mode that is not the fastest) and the
    final saturation (the disturbance rearranging the jet instead of growing) both
    bend the log-series, so the growth phase is the straight stretch between them.

    A window is accepted when a quadratic fit's curvature term is within
    ``max_curvature_sigma`` standard errors of zero — no *statistically detectable*
    bend. Three sigma is the default: tighter starts rejecting windows for noise,
    looser starts admitting visible saturation. Curvature significance is used in
    preference to ``R^2`` for the reason given in :func:`_curvature_significance`.

    **Among acceptable windows the objective is the number of e-foldings spanned,
    not the number of samples**, and the difference is not cosmetic. A saturated
    plateau is perfectly straight — it is a horizontal line — and is usually the
    *longest* straight stretch in an instability run, so maximising duration
    reliably selects the one part of the record where nothing is growing. Maximising
    log range asks the question actually intended: over which stretch did the
    diagnostic climb through the most e-foldings without bending?

    For each starting index the largest acceptable stop is found by bisection, which
    assumes curvature grows as the window is extended. That holds for the
    growth-then-saturation shape this is built for and not in general, so the result
    is a good window rather than a provably optimal one — and the bounds are
    reported in the fit, so the choice is visible rather than hidden.

    Returns half-open index bounds ``(start, stop)``.
    """
    time_s = np.asarray(time_s, dtype=float)
    series = np.asarray(series, dtype=float)
    positive = series > 0
    if positive.sum() < min_points:
        raise ValueError("series has too few positive samples to fit an exponential")
    log_series = np.where(positive, np.log(np.where(positive, series, 1.0)), np.nan)

    n = series.size
    best = (0, 0, -np.inf)
    for start in range(0, n - min_points + 1):
        if not positive[start]:
            continue
        limit = start
        while limit < n and positive[limit]:
            limit += 1
        if limit - start < min_points:
            continue
        lo, hi = start + min_points, limit  # largest acceptable stop lies in [lo, hi]
        if _curvature_significance(time_s[start:lo], log_series[start:lo]) > max_curvature_sigma:
            continue
        best_stop = lo
        while lo <= hi:
            mid = (lo + hi) // 2
            if mid - start < min_points:
                lo = mid + 1
                continue
            sig = _curvature_significance(time_s[start:mid], log_series[start:mid])
            if sig <= max_curvature_sigma:
                best_stop, lo = mid, mid + 1
            else:
                hi = mid - 1
        span = float(log_series[best_stop - 1] - log_series[start])
        if span > best[2]:
            best = (start, best_stop, span)

    if best[1] - best[0] < min_points:
        raise ValueError(
            f"no window of at least {min_points} samples is straight to "
            f"{max_curvature_sigma} sigma; this series has no clean exponential phase"
        )
    return best[0], best[1]


def fit_growth_rate(
    time_s,
    series,
    quantity: str = "energy",
    window: tuple[float, float] | None = None,
    auto_window: bool = False,
    remove_oscillation: bool = True,
    n_harmonics: int = 2,
) -> GrowthRateFit:
    """Fit ``sigma`` from a diagnostic time series growing as ``exp(k sigma t)``.

    Parameters
    ----------
    time_s, series
        Times in seconds and a strictly positive diagnostic.
    quantity
        ``"energy"``/``"enstrophy"`` (quadratic, ``k = 2``) or ``"amplitude"``
        (``k = 1``). There is no default that is safe to leave unexamined.
    window
        Explicit ``(t_start, t_end)`` in seconds. Preferred when the linear phase
        is known, because it makes the reported number reproducible.
    auto_window
        Locate the linear phase with :func:`select_growth_window` instead.
    remove_oscillation
        Detect a periodic component in the residual and fit it simultaneously,
        rather than leaving it to average out. See the module docstring.
    """
    if quantity not in QUANTITY_EXPONENT:
        raise ValueError(f"quantity must be one of {sorted(QUANTITY_EXPONENT)}, got {quantity!r}")
    exponent = QUANTITY_EXPONENT[quantity]

    time_s = np.asarray(time_s, dtype=float)
    series = np.asarray(series, dtype=float)
    notes: list[str] = []

    if window is not None:
        mask = (time_s >= window[0]) & (time_s <= window[1])
        idx = np.flatnonzero(mask)
        start, stop = int(idx[0]), int(idx[-1]) + 1
    elif auto_window:
        start, stop = select_growth_window(time_s, series)
        notes.append(
            f"window located automatically: {time_s[start] / 86400:.2f}-"
            f"{time_s[stop - 1] / 86400:.2f} d"
        )
    else:
        start, stop = 0, series.size

    block = slice(start, stop)
    t, y = time_s[block], series[block]
    if np.any(y <= 0):
        raise ValueError("series must be strictly positive inside the fitting window")
    log_y = np.log(y)

    solution, slope_err, residual, r2 = _loglinear(t, log_y)
    period, oscillation_amplitude = (None, None)
    if remove_oscillation:
        period, oscillation_amplitude = _detect_oscillation(t, log_y, n_harmonics=n_harmonics)
        if period is not None:
            solution, slope_err, residual, r2 = _loglinear(
                t, log_y, extra_columns=_harmonic_columns(t, period, n_harmonics)
            )
            cycles = (t[-1] - t[0]) / period
            notes.append(
                f"a periodic component of period {period / 86400:.2f} d and log-amplitude "
                f"{oscillation_amplitude:.3g} was fitted simultaneously ({cycles:.2f} cycles "
                "in the window); left in the residual it biases the slope unless the window "
                "happens to span a whole number of cycles"
            )
            if cycles < 2:
                notes.append(
                    f"only {cycles:.2f} cycles of that oscillation fit in the window, so the "
                    "oscillation and the linear trend are partly degenerate and the rate is "
                    "correspondingly less well determined"
                )

    slope = float(solution[0])
    growth_rate = slope / exponent
    log_range = float(log_y[-1] - log_y[0])
    if abs(log_range) < 1.0:
        notes.append(
            f"the series changes by only a factor {np.exp(log_range):.2f} across the window; "
            "an exponential fit over less than one e-folding is weakly constrained"
        )
    if growth_rate <= 0:
        notes.append("fitted rate is not positive: this window is not a growing phase")

    return GrowthRateFit(
        growth_rate_s=growth_rate,
        growth_rate_stderr_s=abs(slope_err / exponent),
        e_folding_days=(1.0 / growth_rate) / 86400 if growth_rate > 0 else None,
        quantity=quantity,
        window_start_s=float(t[0]),
        window_end_s=float(t[-1]),
        n_samples=int(t.size),
        log_range=log_range,
        r_squared=r2,
        oscillation_period_s=period,
        oscillation_amplitude=oscillation_amplitude,
        notes=notes,
    )


def window_sensitivity(
    time_s, series, quantity: str = "energy", trims=(0.0, 0.05, 0.10, 0.20)
) -> dict:
    """How much ``sigma`` moves when the fitting window is trimmed at either end.

    This is the honest uncertainty on a growth rate from a **real** run, where the
    record contains an initial transient and an eventual saturation and the answer
    genuinely depends on where the window is put. The standard error of the slope
    describes scatter about a line; it does not describe the question of whether
    the right samples were used, and for a real instability record that second
    question dominates.

    On a *pure* exponential the two are the other way round — trimming a clean
    series changes nothing, so the spread is smaller than the standard error. That
    is not a defect: it is the correct statement that for such a series the window
    does not matter. Quote whichever is larger.

    ``trims`` are fractions of the record trimmed from each end.
    """
    time_s = np.asarray(time_s, dtype=float)
    series = np.asarray(series, dtype=float)
    n = series.size
    offsets = sorted({int(round(f * n)) for f in trims})
    rates = []
    for head in offsets:
        for tail in offsets:
            stop = n - tail
            if stop - head < 6:
                continue
            fit = fit_growth_rate(
                time_s[head:stop], series[head:stop], quantity=quantity, remove_oscillation=False
            )
            rates.append(fit.growth_rate_s)
    rates = np.array(rates)
    return {
        "n_windows": int(rates.size),
        "median_s": float(np.median(rates)),
        "min_s": float(rates.min()),
        "max_s": float(rates.max()),
        "relative_spread": float((rates.max() - rates.min()) / abs(np.median(rates))),
    }


def synthetic_growth_series(
    growth_rate_s: float,
    quantity: str = "energy",
    initial: float = 1.0e-12,
    duration_s: float = 6 * 86400.0,
    n_time: int = 145,
    noise_fraction: float = 0.0,
    oscillation_period_s: float | None = None,
    oscillation_amplitude: float = 0.0,
    seed: int = 0,
):
    """A time series whose growth rate is known exactly.

    ``E(t) = E0 exp(k sigma t) (1 + a cos(2 pi t / T))`` with multiplicative noise —
    multiplicative because that is what a real diagnostic has: the scatter on eddy
    energy is a fraction of its own value, not an absolute amount, so an additive
    noise model would make the early samples look implausibly clean and the late
    ones implausibly noisy.
    """
    rng = np.random.default_rng(seed)
    exponent = QUANTITY_EXPONENT[quantity]
    t = np.linspace(0.0, duration_s, n_time)
    series = initial * np.exp(exponent * growth_rate_s * t)
    if oscillation_period_s:
        series = series * (1 + oscillation_amplitude * np.cos(2 * np.pi * t / oscillation_period_s))
    if noise_fraction:
        series = series * (1 + rng.normal(0.0, noise_fraction, t.size))
    return t, series
