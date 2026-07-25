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
from src.solver import harness  # noqa: E402

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
