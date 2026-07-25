"""Measured against nondivergent against exact Hough: the project's central comparison.

Physics first. A Rossby wave on a rotating sphere has a phase speed, and this
project has three independent ways of saying what it is.

**One: theory with the free surface thrown away.** Section 5 of
``theory/derivations.tex`` assumes the fluid layer cannot change its depth. Then
material conservation of ``q = (zeta + f)/h`` forces the whole change in planetary
vorticity onto relative vorticity, and the answer is the Rossby-Haurwitz relation
``c_ang = -2 Omega / [n(n+1)]`` — a formula with no free parameters at all.

**Two: theory with the free surface kept.** Section 6 puts it back. A column can
now stretch, so part of the planetary-vorticity change is absorbed by stretching
instead of by relative vorticity, the restoring mechanism is diluted, and **the
wave must slow down**. How much depends on Lamb's parameter
``eps = 4 Omega^2 R^2 / (g H)``, and the amount is not a formula but an eigenvalue
of Laplace's tidal equations, solved by :mod:`src.solver.evp_hough`.

**Three: the simulation.** Integrate the full nonlinear divergent shallow-water
equations and measure the drift of the wave that comes out.

The three are computed by completely different mathematics — a closed form, a
linear eigenvalue problem, and a nonlinear time integration — and if the physics
is right they must agree in a specific pattern: the simulation should match the
*divergent* eigenvalue, not the nondivergent formula, and the gap between the two
theories should be exactly the amount the free surface slows the wave.

**Why this module exists.** Session L5 found that pattern by hand for one mode:
the ``(m, n) = (2, 4)`` wave of run P-17 came out 15.72% slower than the
nondivergent prediction, and the Hough eigenvalue at the same ``eps`` says 15.77%.
That was an unplanned by-product of looking at one run. This module makes it
routine, so that every phase-speed run produces the comparison as a matter of
course rather than when somebody happens to check — and so that the number is
regression-locked against later changes to the fitters or the solver.

**One safeguard is wired in deliberately.** The measured speed is fitted with the
nondivergent prediction supplied as ``expected_c_angular``. That is not to bias
the fit — the fit does not use it — but because aliasing in a phase measurement is
undetectable from the data alone (see :mod:`src.analysis.fit_phase_speed`), and an
external expectation is the only thing that can catch it. A run whose output
cadence was too coarse would otherwise report a confident, precise, wrong slowing.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field

import numpy as np

from src.analysis.extract_hovmoller import extract_hovmoller
from src.analysis.fit_phase_speed import fit_phase_speed
from src.diagnostics import slices, spectra
from src.solver import evp_hough

# Spectral truncation for the Hough eigenvalue solve. Session L5 used 60 for the
# EVP-hough sweep and the branch it tracks is converged well below that.
HOUGH_TRUNCATION = 60


@dataclass
class ThreeWayComparison:
    """One mode's phase speed, said three ways, with the departures between them."""

    run_id: str
    wavenumber_m: int
    degree_n: int
    lambs_parameter: float
    latitude_deg: float
    measured_c_angular_rad_s: float
    measured_stderr_rad_s: float
    nondivergent_c_angular_rad_s: float
    hough_c_angular_rad_s: float
    measured_vs_nondivergent: float
    hough_vs_nondivergent: float
    measured_vs_hough: float
    aliasing_risk: str
    mode_present: bool
    degree_source: str
    notes: list[str] = dataclass_field(default_factory=list)

    @property
    def agreement_percentage_points(self) -> float:
        """How far apart the two slowings are, in percentage points.

        This is the headline number: the simulation and the eigenvalue problem
        each say the free surface slows this wave by some percentage, and this is
        the difference between those two percentages. Session L5's value for
        ``(2, 4)`` was 0.05.
        """
        return abs(self.measured_vs_nondivergent - self.hough_vs_nondivergent) * 100

    def as_dict(self) -> dict:
        out = dict(self.__dict__)
        out["notes"] = list(self.notes)
        out["agreement_percentage_points"] = self.agreement_percentage_points
        return out

    def summary(self) -> str:
        return (
            f"{self.run_id} (m={self.wavenumber_m}, n={self.degree_n}, "
            f"eps={self.lambs_parameter:.4f}): "
            f"measured {self.measured_c_angular_rad_s:.6e} rad/s "
            f"({100 * self.measured_vs_nondivergent:+.2f}% vs nondivergent), "
            f"Hough {self.hough_c_angular_rad_s:.6e} rad/s "
            f"({100 * self.hough_vs_nondivergent:+.2f}%), "
            f"agreement {self.agreement_percentage_points:.3f} pp"
        )


def nondivergent_angular_phase_speed(degree_n: int, omega_si: float) -> float:
    """``c_ang = -2 Omega / [n(n+1)]``, eq. (rhdisp). Negative is westward."""
    return -2.0 * omega_si / (degree_n * (degree_n + 1))


def dominant_degree(run, wavenumber: int, field: str = "vorticity", index: int = 0) -> int:
    """The total spherical-harmonic degree carrying most power at a given order.

    Used when a config does not declare which mode it seeded. The measurement is
    made on **vorticity** rather than height by default, and the reason is
    physical rather than incidental: for a single-harmonic initial condition the
    streamfunction and hence the vorticity are exactly one degree, but the
    balanced height field is not. The nonlinear balance multiplies by
    ``sin(latitude)``, and ``mu P_n^m`` couples only to ``n +/- 1``, so the height
    of a clean ``n = 4`` mode sits almost entirely in degrees 3 and 5 with almost
    nothing at 4. Reading the degree off the height field would give the wrong
    answer while looking perfectly reasonable.
    """
    grid = slices.snapshot_map(run, field, index=index)
    transform = spectra.SphericalHarmonicTransform.for_grid(grid.colatitude_rad)
    coefficients = transform.coefficients(grid.values)
    power = np.abs(coefficients[:, wavenumber]) ** 2
    power[:wavenumber] = 0.0  # degrees below the order do not exist
    return int(np.argmax(power))


def compare_run(
    run,
    wavenumber: int | None = None,
    degree: int | None = None,
    latitude_deg: float = 45.0,
    truncation: int = HOUGH_TRUNCATION,
) -> ThreeWayComparison:
    """Measure a run's phase speed and set it beside both theoretical predictions.

    ``wavenumber`` and ``degree`` default to what the run's config declares, and
    fall back to reading them off the run's own initial field — the order from the
    zonal spectrum of the Hovmöller, the degree from the spherical-harmonic
    spectrum of the initial vorticity.

    Every number returned is an angular phase speed in rad/s, negative westward,
    so the three are directly comparable without a conversion.
    """
    provenance = slices.load_provenance(run)
    config = provenance.config
    params = config.get("initial_condition_params") or {}
    physical = {k: float(v) for k, v in (config.get("physical") or {}).items()}
    notes: list[str] = []

    diagram = extract_hovmoller(run, latitude_deg, field="height")
    if wavenumber is None:
        wavenumber = int(params.get("order_m") or 0) or None
    if wavenumber is None:
        from src.analysis.fit_phase_speed import dominant_wavenumber

        wavenumber = dominant_wavenumber(diagram.values)
        notes.append(f"zonal order not declared in the config; read m={wavenumber} from the run")

    degree_source = "config"
    if degree is None:
        declared = params.get("degree_n")
        if declared is not None:
            degree = int(declared)
        else:
            degree = dominant_degree(run, wavenumber)
            degree_source = "initial vorticity spectrum"
            notes.append(f"degree not declared in the config; read n={degree} from the run")

    nondivergent = nondivergent_angular_phase_speed(degree, physical["Omega"])
    fit = fit_phase_speed(
        diagram.values,
        diagram.time_s,
        wavenumber=wavenumber,
        latitude_rad=diagram.latitude_rad,
        radius_m=physical["R"],
        expected_c_angular=nondivergent,
    )
    notes.extend(fit.notes)

    eps = evp_hough.lambs_parameter(physical)
    sigma = evp_hough.track_rossby_mode(wavenumber, degree, eps, nmax=truncation)
    hough = evp_hough.angular_phase_speed(sigma, wavenumber, physical["Omega"])

    return ThreeWayComparison(
        run_id=provenance.run_id,
        wavenumber_m=int(wavenumber),
        degree_n=int(degree),
        lambs_parameter=float(eps),
        latitude_deg=diagram.latitude_deg,
        measured_c_angular_rad_s=fit.c_angular_rad_s,
        measured_stderr_rad_s=fit.c_angular_stderr_rad_s,
        nondivergent_c_angular_rad_s=float(nondivergent),
        hough_c_angular_rad_s=float(hough),
        measured_vs_nondivergent=fit.c_angular_rad_s / nondivergent - 1.0,
        hough_vs_nondivergent=hough / nondivergent - 1.0,
        measured_vs_hough=fit.c_angular_rad_s / hough - 1.0,
        aliasing_risk=fit.aliasing_risk,
        mode_present=fit.mode_present,
        degree_source=degree_source,
        notes=notes,
    )


def compare_runs(runs, **kwargs) -> list[ThreeWayComparison]:
    """The three-way comparison for several runs, for the campaign-wide figure.

    The manuscript's eventual figure is measured, nondivergent and Hough against
    degree ``n``; this returns exactly the rows that plot needs.
    """
    return [compare_run(run, **kwargs) for run in runs]


def main(argv=None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", nargs="+", help="run IDs, e.g. P-17")
    parser.add_argument("--latitude", type=float, default=45.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = compare_runs(args.runs, latitude_deg=args.latitude)
    if args.json:
        print(json.dumps([r.as_dict() for r in results], indent=2))
    else:
        for result in results:
            print(f"[hough] {result.summary()}")
            for note in result.notes:
                print(f"[hough]   note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
