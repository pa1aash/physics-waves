"""Physics tests for the solver core.

These are not unit tests in the usual sense. Almost every check here asks a
question about the *fluid* — does an exact steady solution stay steady, does the
divergent eigenvalue problem reduce to the nondivergent one when the surface is
made rigid, does a flow with a monotone potential-vorticity gradient refuse to
grow — and only incidentally about the code. A test that merely confirmed the
code does what it was written to do would pass just as happily on a wrong
implementation.

Three of them are load-bearing enough to name:

* :func:`test_williamson_case2_is_steady` is the project's blocking gate. Case 2
  is an exact steady solution of the full nonlinear equations, so any tendency at
  all is discretisation error. If this fails, nothing downstream means anything.

* :func:`test_lauter_alpha_zero_reduces_to_williamson_case2` checks a sign
  reconstruction rather than a computation. The Läuter PDF's text layer drops
  minus signs; the signs in ``lauter.py`` were fixed by requiring the reduction
  the paper itself asserts, and this test is what keeps that reasoning honest.

* :func:`test_hough_epsilon_limit_recovers_rossby_haurwitz` and
  :func:`test_stability_evp_matches_derivation_section_9` tie the production
  eigenvalue solvers to the symbolic checks in ``theory/sympy_checks/``. Those
  checks are the project's independent statement of what the answer should be;
  the solvers are not allowed to drift from them silently.
"""

from __future__ import annotations

import json
import stat
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = REPO_ROOT / "configs"

pytest.importorskip("dedalus.public", reason="solver tests need the pinned Dedalus build")

from src.solver import evp_hough, evp_stability, harness  # noqa: E402
from src.solver.equations import EARTH, build_problem, latitude_grid  # noqa: E402
from src.solver.initial_conditions import (  # noqa: E402
    CONSTRUCTORS,
    apply_initial_condition,
    galewsky,
    jet_family,
    lauter,
    williamson,
)
from src.solver.initial_conditions.common import (  # noqa: E402
    area_average,
    solve_balanced_height,
)

L0 = {
    "run_id": "V-00",
    "campaign": "verification",
    "description": "test fixture",
    "resolution": "L0",
    "physical": dict(EARTH),
    "numerics": {
        "timestepper": "RK222",
        "dt": 600.0,
        "dealias": 1.5,
        "hyperdiffusion_order": 4,
        "hyperdiffusion_coefficient": 0.0,
        "stop_sim_time": 3600.0,
    },
    "outputs": {
        "snapshot_cadence": 3600.0,
        "slice_cadence": 3600.0,
        "spectra_cadence": 3600.0,
        "write_full_fields": False,
    },
}


def make_config(**overrides) -> dict:
    config = json.loads(json.dumps(L0))
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(config.get(key), dict):
            config[key].update(value)
        else:
            config[key] = value
    return config


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #


def test_every_config_is_resolved_and_valid():
    """No config may still carry the Session-00 placeholder, or fail the schema."""
    paths = sorted(CONFIG_ROOT.glob("*/*.yaml"))
    assert paths, "no configs found"
    for path in paths:
        harness.load_config(path)


def test_constructor_table_matches_the_schema_enum():
    """The dispatcher and the schema must name the same initial conditions.

    A mismatch here is a config that validates and then fails at run time, which
    is the worst possible place to discover it.
    """
    schema = yaml.safe_load((CONFIG_ROOT / "_schema.yaml").read_text(encoding="utf-8"))
    enum = set(schema["properties"]["initial_condition"]["enum"])
    assert enum == set(CONSTRUCTORS)


def test_sentinel_is_rejected(tmp_path):
    path = tmp_path / "bad.yaml"
    config = make_config(initial_condition="williamson_2", initial_condition_params={})
    config["numerics"]["dt"] = "TBD_SESSION_L5"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(harness.ConfigError, match="placeholder"):
        harness.load_config(path)


# --------------------------------------------------------------------------- #
# grid and balance machinery
# --------------------------------------------------------------------------- #


def test_area_average_is_area_weighted():
    """``<1> = 1``, ``<sin(lat)> = 0``, ``<sin^2(lat)> = 1/3`` on the sphere.

    A plain arithmetic mean over the Gauss-Legendre colatitude grid gets the last
    one wrong, which would quietly corrupt every mean depth in the project.
    """
    swp = build_problem(make_config())
    _, lat = latitude_grid(swp.dist, swp.basis)
    assert area_average(swp, np.ones_like(lat)) == pytest.approx(1.0, abs=1e-12)
    assert area_average(swp, np.sin(lat)) == pytest.approx(0.0, abs=1e-12)
    assert area_average(swp, np.sin(lat) ** 2) == pytest.approx(1 / 3, abs=1e-12)


def test_the_two_balance_constructions_agree_for_a_zonal_jet():
    """Gradient-wind quadrature and the nonlinear-balance BVP must give the same field.

    ``theory/derivations.tex`` §11.2 asserts they agree to numerical precision for
    a zonal flow. They are genuinely different computations — a 1-D integral of an
    analytic relation against a 2-D spectral boundary-value solve — so agreement
    is evidence about both.
    """
    config = make_config(resolution="L1")
    swp = build_problem(config)
    apply_initial_condition(
        swp,
        {
            **config,
            "initial_condition": "galewsky",
            "initial_condition_params": {"perturbation": False},
        },
    )
    quadrature = np.asarray(swp.h["g"]).copy()

    solve_balanced_height(swp, mean_height=0.0)
    bvp = np.asarray(swp.h["g"])

    scale = float(np.ptp(quadrature))
    assert np.max(np.abs(quadrature - bvp)) / scale < 2e-3


# --------------------------------------------------------------------------- #
# the benchmark cases
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("resolution", ["L0", "L1"])
def test_williamson_case2_is_steady(resolution):
    """**The blocking physics check.** Case 2 is an exact steady solution.

    Integrated for an hour with the dissipation switched off, every field must
    come back unchanged to within round-off on a field whose own scale is about
    1.9 km. Any real tendency here is an error in the equations, the Coriolis
    sign, the metric terms, or the balance — and every result the project will
    ever produce sits downstream of it.

    **On why L1 is about an order of magnitude looser than L0** (5.9e-14 against
    3.2e-15, measured in Session L5): this is round-off accumulation, not a
    convergence failure, and it is expected to get *worse* with resolution rather
    than better. The residual is a sum of rounding errors over the spectral
    coefficients, and L1 carries sixteen times as many of them as L0 — a random
    walk over N terms grows like sqrt(N), which is a factor of four, and the
    remainder comes from the larger dynamic range of the transform at higher
    truncation. The timestep count is identical (twelve steps of 300 s) at both,
    so it contributes nothing to the difference. Both numbers are ten orders of
    magnitude below any physical signal; the single tolerance below is set to
    accommodate the looser one rather than tightened per resolution, because the
    quantity being tested is "indistinguishable from steady", not the round-off
    itself.
    """
    mean_depth = 2363.021
    config = make_config(
        resolution=resolution,
        physical={"H": mean_depth},
        initial_condition="williamson_2",
        initial_condition_params={},
    )
    swp, meta = harness.build_run(config)
    assert meta["mean_depth_m"] == pytest.approx(mean_depth, rel=1e-5)

    h0 = np.asarray(swp.h["g"]).copy()
    u0 = np.asarray(swp.u["g"]).copy()
    solver = swp.build_solver("RK222")
    dt = swp.units.time(300.0)
    for _ in range(12):
        solver.step(dt)
    swp.h.change_scales(1)
    swp.u.change_scales(1)

    height_scale = float(np.ptp(h0))
    speed_scale = float(np.max(np.abs(u0)))
    assert np.max(np.abs(np.asarray(swp.h["g"]) - h0)) / height_scale < 1e-11
    assert np.max(np.abs(np.asarray(swp.u["g"]) - u0)) / speed_scale < 1e-11


def test_lauter_alpha_zero_reduces_to_williamson_case2():
    """Läuter Example 3 at zero tilt must be Williamson case 2, up to a constant.

    The paper asserts this reduction, and it is what fixed the signs in
    ``lauter.py`` after the source PDF's text layer dropped them. Only the free
    surface's *gradient* is physical — an additive constant is absorbed into
    ``k1`` — so the comparison is made after removing each field's mean.
    """
    config = make_config()
    swp = build_problem(config)
    u_l, v_l, phi_free, _ = lauter.analytic_fields(swp, {"alpha": 0.0}, t_si=0.0)

    phi, lat = latitude_grid(swp.dist, swp.basis)
    a, Om = EARTH["R"], EARTH["Omega"]
    u0 = williamson.U0_12DAY * a / williamson.A_EARTH
    u_w = u0 * np.cos(lat) + 0.0 * phi
    gh_w = 2.94e4 - (a * Om * u0 + u0**2 / 2) * np.sin(lat) ** 2

    assert np.max(np.abs(u_l - u_w)) < 1e-9
    assert np.max(np.abs(v_l)) < 1e-12
    delta = (phi_free - np.mean(phi_free)) - (gh_w - np.mean(gh_w))
    assert np.max(np.abs(delta)) / np.ptp(gh_w) < 1e-12


def test_williamson_case6_reports_its_validity_window_and_warns():
    """The Rossby-Haurwitz benchmark is only a benchmark for a few days.

    Thuburn & Li (2000) showed the wavenumber-4 wave is itself unstable with a
    1.3-day e-folding, so a 14-day integration measures that instability rather
    than the scheme. The config asks for 14 days on purpose — that is the
    published protocol — and the harness must say so rather than truncate.
    """
    config = harness.load_config(CONFIG_ROOT / "verification" / "V-05.yaml")
    _, meta = harness.build_run(config)
    assert meta["max_stable_window_s"] == pytest.approx(3 * 1.3 * 86400)
    messages = harness.check_physics_consistency(config, meta)
    assert any("validity window" in m for m in messages)


def test_mean_depth_disagreement_warns():
    """A config whose H does not describe its own case must not pass silently."""
    config = make_config(
        physical={"H": 10000.0},
        initial_condition="williamson_2",
        initial_condition_params={},
    )
    _, meta = harness.build_run(config)
    messages = harness.check_physics_consistency(config, meta)
    assert any("mean free surface" in m for m in messages)


def test_single_harmonic_is_nondivergent_with_the_right_vorticity():
    """A streamfunction flow must have zero divergence and vorticity ``lap(psi)``.

    For a single spherical harmonic the second statement is sharper: the
    vorticity must equal ``-n(n+1)/R^2`` times the streamfunction pointwise. That
    is exactly the property that makes the mode an *exact* solution of the
    nondivergent barotropic vorticity equation, and therefore the reason the
    phase-speed campaign can measure one clean number.
    """
    import dedalus.public as d3

    n, m = 4, 2
    config = make_config(resolution="L1")
    swp = build_problem(config)
    phi, lat = latitude_grid(swp.dist, swp.basis)

    from src.solver.initial_conditions.common import streamfunction_velocity
    from src.solver.initial_conditions.single_harmonic import harmonic_streamfunction

    psi_grid = harmonic_streamfunction(phi, lat, n, m, amplitude=1e-3)
    psi = streamfunction_velocity(swp, psi_grid)

    div = d3.div(swp.u).evaluate()
    div.change_scales(1)
    zeta = (-d3.div(d3.skew(swp.u))).evaluate()
    zeta.change_scales(1)
    psi.change_scales(1)

    radius = swp.units.length(EARTH["R"])
    expected = -n * (n + 1) / radius**2 * np.asarray(psi["g"])
    assert np.max(np.abs(np.asarray(div["g"]))) < 1e-12 * np.max(np.abs(np.asarray(zeta["g"])))
    assert np.max(np.abs(np.asarray(zeta["g"]) - expected)) < 1e-10 * np.max(np.abs(expected))


# --------------------------------------------------------------------------- #
# the jet family and its criterion
# --------------------------------------------------------------------------- #


def test_critical_shear_parameter_brackets_the_sign_change():
    """The closed-form critical ``S`` must be exactly where ``dQ/dy`` first reverses."""
    S_crit = jet_family.critical_shear_parameter(EARTH["R"], EARTH["Omega"])
    assert 0.05 < S_crit < 0.1

    lat = np.linspace(-np.pi / 2, np.pi / 2, 200_001)
    below = jet_family.rayleigh_kuo_diagnostic(
        lat,
        galewsky.jet_profile(lat, 0.98 * S_crit * galewsky.UMAX),
        EARTH["R"],
        EARTH["Omega"],
    )
    above = jet_family.rayleigh_kuo_diagnostic(
        lat,
        galewsky.jet_profile(lat, 1.02 * S_crit * galewsky.UMAX),
        EARTH["R"],
        EARTH["Omega"],
    )
    assert not below["sign_change"]
    assert above["sign_change"]


# --------------------------------------------------------------------------- #
# eigenvalue solvers, against the symbolic checks
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("m,n", [(1, 2), (1, 3), (2, 2), (2, 5), (3, 4)])
def test_hough_epsilon_limit_recovers_rossby_haurwitz(m, n):
    """As the surface is made rigid the Hough frequency must become ``-m/[n(n+1)]``.

    This is the derivation's own validation target for extension B, and it is
    stronger than agreement with a published table because the limit is a closed
    form the project derives independently. At ``eps = 1e-6`` the residual should
    be of the same order as ``eps``, since the divergent correction enters at
    first order.
    """
    sigma = evp_hough.track_rossby_mode(m, n, 1e-6, nmax=40)
    expected = -m / (n * (n + 1.0))
    assert abs(np.real(sigma) - expected) / abs(expected) < 1e-5
    assert abs(np.imag(sigma)) < 1e-10


def test_hough_matrices_match_quadrature():
    """The closed-form Legendre recurrences must equal their quadrature definitions.

    ``evp_hough`` uses the recurrence because it is exact and cheap; the
    quadrature form is the definition. They are computed here two entirely
    different ways and must agree at machine precision, which is what licenses
    the substitution.
    """
    from scipy.special import assoc_legendre_p_all, roots_legendre

    for m in (1, 2, 3):
        nmax = 24
        M, D, degrees = evp_hough.legendre_matrices(m, nmax)
        mu, w = roots_legendre(nmax + 8)
        table = assoc_legendre_p_all(nmax, m, mu, norm=True, diff_n=1)
        P = np.array([table[0, n, m] for n in degrees])
        dP = np.array([table[1, n, m] for n in degrees])
        norms = np.sqrt((P**2 * w).sum(axis=1))
        P, dP = P / norms[:, None], dP / norms[:, None]
        Mq = (P * w) @ (mu * P).T
        Dq = (P * w) @ ((1.0 - mu**2) * dP).T
        assert np.max(np.abs(M - Mq)) < 1e-12
        assert np.max(np.abs(D - Dq)) < 1e-12


def test_hough_at_earth_matches_the_derivation_table():
    """Spot values from ``theory/derivations.tex`` §6, recomputed by the solver.

    The sectoral row is included deliberately: ``(m, n) = (2, 2)`` is slowed by
    only 7.5% while its neighbour ``n = 3`` is slowed by 19.8%, which looks like
    an error until one notices that a sectoral mode sits at the bottom of its
    degree ladder with one Coriolis partner instead of two.
    """
    eps = 4 * EARTH["Omega"] ** 2 * EARTH["R"] ** 2 / (EARTH["g"] * EARTH["H"])
    expected = {(1, 2): -0.4038, (1, 5): -0.1332, (2, 2): -0.0751, (2, 3): -0.1980}
    for (m, n), slowing in expected.items():
        sigma = evp_hough.track_rossby_mode(m, n, eps, nmax=60)
        sigma_nd = -m / (n * (n + 1.0))
        assert float(np.real(sigma)) / sigma_nd - 1.0 == pytest.approx(slowing, abs=5e-4)


def test_solid_body_rotation_has_a_real_spectrum():
    """Hypothesis H7 as a prohibition: no sign change in ``dQ/dy``, no growing mode.

    Solid-body rotation has ``dQ/dy = 2(Omega + U0/R) cos(phi)``, single-signed at
    any speed. The Rayleigh-Kuo argument then forbids a complex eigenvalue, and a
    complex pair appearing here would falsify the criterion rather than reveal an
    instability — which is why this test is worth more than a smoke test.
    """
    profile = evp_stability.solid_body_profile(40.0)
    for m in (1, 3, 6):
        c = evp_stability.stability_evp(m, 96, profile, EARTH["R"], EARTH["Omega"])
        spread = float(np.ptp(c.real)) or 1.0
        assert float(np.max(np.abs(c.imag))) / spread < 1e-8


def test_stability_evp_matches_derivation_section_9():
    """The Galewsky jet's growth rate must reproduce eq. (galewskygrowth).

    ``theory/derivations.tex`` §9 reports ``m* = 6``, ``sigma = 2.07e-5 /s``,
    e-folding 0.56 days, computed by ``check_rayleigh_kuo.py`` at truncation
    240/480. The production solver is a different piece of code and must land on
    the same numbers.
    """
    profile, physical, _ = evp_stability.profile_for_run("I-00")
    rows = [
        evp_stability.resolved_growth_rate(m, profile, physical["R"], physical["Omega"])
        for m in range(4, 9)
    ]
    resolved = [r for r in rows if r["resolved"]]
    peak = max(resolved, key=lambda r: r["growth_rate_s"])
    assert peak["m"] == 6
    assert peak["growth_rate_s"] == pytest.approx(2.07e-5, rel=2e-2)
    assert peak["e_folding_days"] == pytest.approx(0.56, rel=5e-2)


def test_ripa_certifies_a_subcritical_jet_and_is_silent_about_the_anchor():
    """Ripa's conditions are *sufficient*; the output must show which way that cuts.

    Below the Rayleigh-Kuo threshold the potential-vorticity gradient is
    single-signed, a constant ``c0`` outside the velocity range satisfies
    condition (i), and the gravity-wave criticality condition is satisfied with an
    enormous margin — so the flow is *certified* stable. On the Galewsky jet
    condition (i) fails and the theorem says nothing at all, which is not the same
    as saying the jet is unstable even though it is.
    """
    physical = dict(EARTH)
    weak = evp_stability.ripa_diagnostics(
        lambda lat: galewsky.jet_profile_derivatives(lat, 0.05 * galewsky.UMAX), physical
    )
    assert weak["certifies_stable"]
    assert weak["criticality_margin"] > 50

    anchor, _, _ = evp_stability.profile_for_run("I-00")
    strong = evp_stability.ripa_diagnostics(anchor, physical)
    assert strong["pv_gradient_sign_change"]
    assert not strong["condition_i_pv_gradient"]
    assert not strong["certifies_stable"]
    assert strong["condition_ii_criticality"]


# --------------------------------------------------------------------------- #
# harness bookkeeping
# --------------------------------------------------------------------------- #


def test_provenance_is_written_read_only_and_records_the_environment(tmp_path):
    path = tmp_path / "V-02.yaml"
    config = make_config(
        run_id="V-02",
        initial_condition="williamson_2",
        initial_condition_params={},
        physical={"H": 2363.021},
        numerics={"stop_sim_time": 3600.0, "dt": 1200.0},
        outputs={"snapshot_cadence": 3600.0, "slice_cadence": 0, "spectra_cadence": 3600.0},
    )
    path.write_text(yaml.safe_dump(config), encoding="utf-8")

    result = harness.run(path, output_root=tmp_path / "runs")
    record_path = result.output_dir / "provenance.json"
    assert record_path.exists()
    mode = stat.S_IMODE(record_path.stat().st_mode)
    assert not mode & stat.S_IWUSR, "provenance must be read-only once written"

    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["outcome"]["status"] == "completed"
    assert record["environment"]["dedalus"]
    assert record["git"]["commit"]
    assert record["config_sha256"]

    with pytest.raises(harness.ConfigError, match="immutable"):
        harness.run(path, output_root=tmp_path / "runs")


def test_registry_update_touches_only_the_named_row(tmp_path):
    registry = tmp_path / "RUN_REGISTRY.md"
    registry.write_text(
        "| Run ID | Purpose | Status |\n"
        "|---|---|---|\n"
        "| V-01 | a | not started |\n"
        "| V-02 | b | not started |\n",
        encoding="utf-8",
    )
    assert harness.update_registry("V-02", "complete 2026-07-25", registry)
    text = registry.read_text(encoding="utf-8")
    assert "| V-02 | b | complete 2026-07-25 |" in text
    assert "| V-01 | a | not started |" in text
    assert not harness.update_registry("V-99", "complete", registry)
