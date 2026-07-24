# Confirmed Dedalus v3 API for the installed build

**Every signature below was confirmed by introspecting the installed package**
(`inspect.signature`, `help`, and a live micro-example on a tiny sphere), not
copied from documentation for a possibly-different version. Session L5 reads this
instead of re-discovering the API; treat it as load-bearing.

- **Package version:** `dedalus` **3.0.5** (from `dedalus.__version__`).
- **Import convention:** `import dedalus.public as d3` (the public namespace).
- **Deviation from the documented hypothesis:** `d3.__version__` does **not**
  exist — the version attribute lives on the top-level `dedalus` package, not on
  `dedalus.public`. Other deviations are noted inline and summarised at the end.

The physics this API expresses: a rotating shallow-water fluid on the full
sphere. The state is a scalar height field `h(φ, θ)` and a tangent-plane vector
velocity `u(φ, θ)`; the dynamics are written in vector-invariant form so that the
Coriolis term, the pressure-gradient term and the advection term are each a
single spectral operator on `S²`.

## 1. Coordinates and distributor

```python
S2Coordinates(azimuth, colatitude)          # confirmed signature
Distributor(coordsystems, comm=None, mesh=None, dtype=None)
```

`S2Coordinates` names the two angular coordinates of the sphere: the first is the
**azimuth** (longitude, `φ`), the second the **colatitude** (`θ`, measured from
the north pole). The `Distributor` owns the MPI decomposition and the working
dtype.

```python
import numpy as np, dedalus.public as d3
coords = d3.S2Coordinates('phi', 'theta')       # 'phi'=azimuth, 'theta'=colatitude
dist   = d3.Distributor(coords, dtype=np.float64)
```

Note `dtype` is passed to the `Distributor` as a keyword; `comm`/`mesh` default to
the world communicator and an automatic decomposition.

## 2. Sphere basis

```python
SphereBasis(coordsys, shape, dtype, radius=1, dealias=(1, 1),
            azimuth_library=None, colatitude_library=None)
```

**Deviation from the hypothesis.** The sketch showed
`SphereBasis(coords, (Nphi, Ntheta), radius=R, dealias=dealias, dtype=dtype)`.
The real signature makes `dtype` the **third positional** argument, *before*
`radius` and `dealias`. Passing `dtype=` as a keyword (as the sketch does) works,
but code that relies on positional order must use `(coordsys, shape, dtype, …)`.
`shape` is `(Nphi, Ntheta)`, the spherical-harmonic truncation.

```python
Nphi, Ntheta = 8, 4
basis = d3.SphereBasis(coords, (Nphi, Ntheta), radius=1.0, dtype=np.float64)
# type(basis).__name__ == 'SphereBasis'
```

## 3. Fields — the shallow-water state

Fields are created from the distributor. A scalar (height) and a tangent-vector
(velocity):

```python
u = dist.VectorField(coords, name='u', bases=basis)   # tangent velocity on S^2
h = dist.Field(name='h', bases=basis)                  # free-surface height
```

Both return objects of class `Field` (a `VectorField` is a `Field` carrying the
coordinate system as its tensor signature). Confirmed working on the live sphere.

## 4. Grids

```python
Distributor.local_grids(self, *bases, scales=None)
phi, theta = dist.local_grids(basis)
# phi.shape == (Nphi, 1), theta.shape == (1, Ntheta)   # broadcast-ready
```

The grids come back shaped for broadcasting: azimuth varies down the first axis,
colatitude across the second.

## 5. Vector-invariant operators

The operators are exposed in the `d3` namespace as thin `*args, **kw` factory
wrappers that build typed spherical operators:

| Call | Builds (class) | Physical role |
|------|----------------|---------------|
| `d3.grad(h)` | `SphereGradient` | pressure-gradient / height gradient |
| `d3.div(u)` | `SphereDivergence` | mass-flux divergence |
| `d3.lap(h)` | `SphereLaplacian` | hyperdiffusion / smoothing |
| `d3.skew(u)` | (skew operator) | rotate a tangent vector by 90° |
| `d3.MulCosine(A)` | `MulCosine` | multiply by `cos(colatitude)` |
| `d3.curl`, `d3.cross`, `d3.integ` | — | vorticity, cross products, integration |

**The Coriolis idiom.** The planetary rotation term `f k̂ × u` with
`f = 2Ω cos θ` is assembled on the sphere as:

```python
zcross = lambda A: d3.MulCosine(d3.skew(A))   # ~ (k̂ x A) weighted by cos(colatitude)
# then the Coriolis term is (2*Omega) * zcross(u)
```

`skew` supplies the 90° rotation (`k̂ ×`) and `MulCosine` supplies the latitudinal
`cos θ` weight that turns a constant rotation rate into the latitude-dependent
Coriolis parameter — the physical origin of the beta-effect this whole project
studies. Confirmed: `zcross(u)` builds a `MulCosine` operator.

## 6. Problem, solver, timesteppers

```python
IVP(variables, time='t', **kw)                 # class: InitialValueProblem
InitialValueProblem.add_equation(equation, condition='True')
```

Equations are added as **strings** parsed against the problem namespace:

```python
problem = d3.IVP([u, h], namespace=locals())
problem.add_equation("dt(h) = 0")              # equations are strings
problem.add_equation("dt(u) = 0")
solver  = problem.build_solver(d3.RK222)       # class: InitialValueSolver
```

**Timesteppers available in this build** (pass the class to `build_solver`):

```
RK111, RK222, RK443, RKGFY, RKSMR,
SBDF1, SBDF2, SBDF3, SBDF4,
CNAB1, CNAB2, CNLF2, MCNAB2
```

The IMEX Runge–Kutta schemes `RK222` and `RK443` and the semi-implicit
backward-difference `SBDF2` (named in the blueprint) are all present. The shipped
shallow-water example's choice is recorded in
`tests/phase0_gate/dedalus_reference/` after extraction (§3).

Other problem types present: `LBVP`, `NLBVP`, `EVP(variables, eigenvalue, **kw)`
— the last is the one extensions B and C (Hough modes, jet stability) will use.

## 7. Output / analysis handlers → HDF5

There is **no** top-level `Evaluator` or `FileHandler` class in `d3`. Snapshot
output attaches through the solver's evaluator:

```python
Solver.evaluator.add_file_handler(filename, parallel=None, **kw)   # -> H5GatherFileHandler
handler = solver.evaluator.add_file_handler('snapshots', sim_dt=1.0)
handler.add_task(...)     # e.g. add_task(h, name='height'); add_task(-d3.div(d3.skew(u)), name='vorticity')
```

`add_file_handler` returns an `H5GatherFileHandler` writing HDF5; `sim_dt` sets
the output cadence in simulation time, and `add_task(*args, **kw)` registers each
field/operator to be written (with an optional `name=`).

## 8. Summary of deviations from the documented hypothesis

1. **Version attribute:** `dedalus.__version__` (`= '3.0.5'`), not
   `d3.__version__` (which raises `AttributeError`).
2. **`SphereBasis` argument order:** `(coordsys, shape, dtype, radius=1,
   dealias=(1,1), …)` — `dtype` is the third positional argument, before
   `radius`/`dealias`. Keyword use is unaffected.
3. **`S2Coordinates` argument names:** `(azimuth, colatitude)` — the two names
   passed become the longitude and colatitude coordinate names.
4. **Operators** (`grad`, `div`, `lap`, `skew`, `MulCosine`, …) are exposed as
   `*args, **kw` factory wrappers; the concrete classes they build are
   `SphereGradient`, `SphereDivergence`, `SphereLaplacian`, etc.
5. **Output handler:** reached via `solver.evaluator.add_file_handler(...)`
   returning `H5GatherFileHandler`; there is no `d3.FileHandler`/`d3.Evaluator`.

Everything else in the hypothesis (the `Distributor(coords, dtype=…)` shape, the
`VectorField`/`Field` factories, `local_grids`, and the
`zcross = MulCosine(skew(·))` Coriolis idiom) was confirmed as sketched.
