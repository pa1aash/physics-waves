"""Initial-condition constructors, one module per benchmark or campaign case.

Physics first. An initial condition is a statement about what the fluid is doing
at ``t = 0``, and in a rotating shallow-water system that statement is not free:
the height field and the velocity field must be consistent with each other or the
run begins with a gravity-wave adjustment nobody asked for. Every constructor here
therefore delivers a *balanced* pair — either from an analytic balance published
with the case, or from one of the two balance constructions in ``common.py``.

This module is only the switchboard. It maps the config's ``initial_condition``
string onto the function that builds it, so that no other part of the codebase
has to know the mapping, and so that adding a case is one line here plus one
module.

Every constructor takes ``(swp, params)`` — a built
:class:`src.solver.equations.ShallowWaterProblem` and the config's
``initial_condition_params`` block — writes into ``swp.u`` and ``swp.h``, and
returns a dictionary of metadata. That dictionary is not decoration: the harness
writes it into the run's provenance record, and three of its keys change what the
harness does.

``kind``
    ``"shallow_water"`` or ``"advection"``. Williamson case 1 is the only
    advection case, and it must not be pushed through the full shallow-water
    system — the report is explicit that it "does not deal with the complete
    shallow water equations".

``topography``
    A Dedalus field, present only for cases with a non-flat bottom (Williamson
    case 5, Läuter). The problem must be *rebuilt* with it, because the bottom
    enters the equations, not the state.

``mean_depth_m``
    The case's own area-mean free surface. When it disagrees with the config's
    ``physical.H`` the equations remain exact but the implicit/explicit split
    stops matching the physics, so the harness warns.
"""

from __future__ import annotations

from src.solver.initial_conditions import galewsky, jet_family, lauter, single_harmonic, williamson

# Config `initial_condition` value -> constructor. The names are fixed by
# configs/_schema.yaml, so this table and the schema must agree; the audit checks
# that they do rather than leaving it to a runtime failure at run time.
CONSTRUCTORS = {
    "williamson_1": williamson.case1_cosine_bell,
    "williamson_2": williamson.case2_steady_zonal,
    "williamson_5": williamson.case5_mountain,
    "williamson_6": williamson.case6_rossby_haurwitz,
    "lauter": lauter.lauter_unsteady,
    "galewsky": galewsky.galewsky_jet,
    "single_harmonic": single_harmonic.single_harmonic,
    "jet": jet_family.idealised_jet,
}

# `jet` covers two physically different base states — an analytic family and an
# observed profile — distinguished by the config's `initial_condition_params.
# profile` field rather than by a separate schema entry, because they are the
# same *kind* of state and differ only in where the profile comes from.
JET_PROFILES = {
    "idealised_jet": jet_family.idealised_jet,
    "reanalysis_djf": jet_family.reanalysis_jet,
}


def apply_initial_condition(swp, config: dict) -> dict:
    """Build the initial condition named by ``config`` and return its metadata."""
    name = config.get("initial_condition")
    if name is None:
        raise ValueError(
            f"config {config.get('run_id', '<unknown>')} has no initial_condition; "
            "only the eigenvalue campaign may omit it, and that path does not "
            "build an initial-value problem"
        )
    if name not in CONSTRUCTORS:
        raise ValueError(f"unknown initial_condition {name!r}; known: {sorted(CONSTRUCTORS)}")

    params = dict(config.get("initial_condition_params") or {})
    constructor = CONSTRUCTORS[name]
    if name == "jet":
        profile = params.get("profile", "idealised_jet")
        if profile not in JET_PROFILES:
            raise ValueError(f"unknown jet profile {profile!r}; known: {sorted(JET_PROFILES)}")
        constructor = JET_PROFILES[profile]

    if config.get("seed") is not None:
        params.setdefault("seed", config["seed"])

    metadata = constructor(swp, params)
    metadata.setdefault("initial_condition", name)
    return metadata


__all__ = [
    "CONSTRUCTORS",
    "JET_PROFILES",
    "apply_initial_condition",
    "galewsky",
    "jet_family",
    "lauter",
    "single_harmonic",
    "williamson",
]
