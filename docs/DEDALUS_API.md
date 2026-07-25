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

---

# Eigenvalue problems (appended by Session L5)

Session L1's introspection above covered the **initial-value** path only. Sessions
L5 onward need the eigenvalue path for extensions B (Hough modes) and C (jet
stability), so it was introspected the same way — signatures from the installed
package, then a live micro-example whose answer is known analytically.

## 9. `EVP` construction

```python
EVP(variables, eigenvalue, **kw)          # class: EigenvalueProblem
```

From its docstring: the class supports problems of the form `λ*M.X + L.X = 0`.
The left-hand side must be **linear in the variables and affine in the
eigenvalue**; the right-hand side must be zero. The eigenvalue is itself a
`Field` (a bare one, with no basis), not a symbol or a string.

```python
coords = d3.S2Coordinates('phi', 'theta')
dist   = d3.Distributor(coords, dtype=np.complex128)   # complex dtype REQUIRED
basis  = d3.SphereBasis(coords, (Nphi, Ntheta), radius=R, dtype=np.complex128)
psi    = dist.Field(name='psi', bases=basis)
sigma  = dist.Field(name='sigma')                       # the eigenvalue
problem = d3.EVP([psi], eigenvalue=sigma, namespace=locals())
problem.add_equation("sigma*psi + lap(psi) = 0")
solver  = problem.build_solver()                        # class: EigenvalueSolver
```

**`dtype=np.complex128` is required** on both the distributor and the basis. The
`float64` used for the IVP path will not carry complex eigenvalues, which is the
whole point of a stability calculation.

## 10. Subproblems: the sphere decomposes by azimuthal wavenumber

The sphere basis block-diagonalises by azimuthal wavenumber `m`, and Dedalus
exposes each block as a *subproblem*. This is exactly the structure the theory
wants — `theory/derivations.tex` §6 and §9 both pose their eigenvalue problems
per-`m` — so no reshaping is needed.

```python
solver.subproblems                    # list; each has .group == (m, None)
solver.subproblems_by_group[(m, None)]   # direct lookup by azimuthal wavenumber
```

For a `(2N, N)` sphere basis the groups run over both signs of `m`. Solve one
block at a time:

```python
sp = solver.subproblems_by_group[(m, None)]
solver.solve_dense(sp)                # signature: (subproblem, rebuild_matrices=False,
                                      #             left=False, normalize_left=True, **kw)
eigvals = solver.eigenvalues          # ndarray, complex; may contain inf/nan
eigvecs = solver.eigenvectors         # ndarray, (n_modes, n_modes)
```

`solve_sparse` also exists, for when only a few eigenvalues near a target are
wanted.

**Spurious entries are normal and must be filtered.** `solver.eigenvalues`
contains non-finite values corresponding to constraint rows; filter with
`np.isfinite` before use. This is not an error condition.

## 11. Live confirmation against a known spectrum

The Laplace–Beltrami operator on the unit sphere has eigenvalues `−n(n+1)`, so
`sigma*psi + lap(psi) = 0` must return `sigma = n(n+1)` exactly. At `m = 2` on a
`(32, 16)` basis the solver returned, after filtering non-finite values:

```
6, 12, 20, 30, 42, 56   for n = 2, 3, 4, 5, 6, 7
```

matching `n(n+1)` to all printed digits. The API translation above is therefore
confirmed, not assumed — the same standard Session L1 applied to the IVP path.
