"""Environment tests: the solver stack imports and is MPI-capable.

Verifies the pieces the project actually depends on — Dedalus v3 with a working
two-sphere basis, MPI, MPI-enabled HDF5, and the scientific/data/plotting stack —
and prints a version table for the whole stack (visible under ``pytest -s``).
"""

from __future__ import annotations

import importlib

import pytest

STACK = [
    "dedalus",
    "mpi4py",
    "h5py",
    "numpy",
    "scipy",
    "sympy",
    "xarray",
    "netCDF4",
    "cartopy",
    "cmocean",
    "cdsapi",
    "yaml",
    "jsonschema",
    "matplotlib",
]


def _version(module) -> str:
    return str(getattr(module, "__version__", "?"))


def test_print_version_table():
    print("\nEnvironment version table")
    print("-" * 40)
    for name in STACK:
        module = importlib.import_module(name)
        print(f"  {name:14s} {_version(module)}")


def test_dedalus_core_imports():
    import dedalus.core  # noqa: F401


def test_sphere_basis_instantiates():
    import dedalus.public as d3
    import numpy as np

    coords = d3.S2Coordinates("phi", "theta")
    dist = d3.Distributor(coords, dtype=np.float64)
    assert dist is not None
    basis = d3.SphereBasis(coords, shape=(128, 64), radius=1.0, dtype=np.float64)
    assert basis.shape == (128, 64)


def test_mpi_comm_world():
    from mpi4py import MPI

    assert MPI.COMM_WORLD is not None
    assert MPI.COMM_WORLD.size >= 1


def test_h5py_mpi_enabled():
    import h5py

    assert h5py.get_config().mpi is True


@pytest.mark.parametrize("name", ["cdsapi", "xarray", "netCDF4", "cartopy", "sympy"])
def test_data_stack_imports(name):
    importlib.import_module(name)
