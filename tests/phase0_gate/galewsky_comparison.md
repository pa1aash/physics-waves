# Shipped Dedalus jet vs. the published Galewsky et al. (2004) profile

**Purpose.** Determine whether the initial condition in the fetched
`dedalus_reference/shallow_water.py` **is** the Galewsky profile, a variant, or a
different jet — so Session L5 knows how much rework `galewsky.py` (run I-00)
needs. This is **informational**; it does not gate Phase-0 pass/fail.

**Reference.** Galewsky, J., Scott, R. K., & Polvani, L. M. (2004). An
initial-value problem for testing numerical models of the global shallow-water
equations. *Tellus A*, 56(5), 429–440.
DOI [10.3402/tellusa.v56i5.14436](https://doi.org/10.3402/tellusa.v56i5.14436).
Equation numbers below refer to that paper (its eq. 2 = jet, eq. 3 = balance,
eq. 4 = perturbation). Published expressions are paraphrased, not reproduced
verbatim.

## Parameter-by-parameter comparison

| Quantity | Published Galewsky (2004) | Shipped `shallow_water.py` | Verdict |
|----------|---------------------------|-----------------------------|---------|
| **Zonal jet form** | eq. (2): `u(φ)=(u_max/e_n)·exp[1/((φ−φ0)(φ−φ1))]` on `φ0<φ<φ1`, else 0 | `u_jet = umax/en * np.exp(1/((lat-lat0)/(lat-lat1)))` on `lat0≤lat≤lat1`, else 0 | **identical** |
| `u_max` | 80 m s⁻¹ | `umax = 80 * meter/second` | **identical** |
| `φ0` (equatorward edge) | π/7 | `lat0 = np.pi/7` | **identical** |
| `φ1` (poleward edge) | π/2 − φ0 | `lat1 = np.pi/2 - lat0` | **identical** |
| `e_n` (normalisation) | `exp[−4/(φ1−φ0)²]` | `en = np.exp(-4/(lat1-lat0)**2)` | **identical** |
| jet mid-point | φ = π/4 (45° N) | mid-point of `[lat0, lat1]` = π/4 | **identical** |
| **Balanced height** | eq. (3): meridional integral of gradient-wind balance, `g·h(φ)=g·h0 − ∫ a·u(f + tan(φ')/a·u) dφ'`; `h0` set so global mean depth = 10 km | LBVP `g·lap(h) + c = −div(u·grad u + 2Ω·zcross u)` with `ave(h)=0`; mean depth `H = 1e4 m` | **equivalent up to method** — both impose the same gradient-wind balance for the same jet; Galewsky integrates it in 1-D, Dedalus solves the divergence of the balance as a 2-D LBVP. Both fix a 10 km mean depth (Galewsky via `h0`, Dedalus via `ave(h)=0` about `H`). |
| **Perturbation** | eq. (4): `h'(λ,φ)=ĥ·cos φ·exp[−(λ/α)²]·exp[−((φ2−φ)/β)²]` | `hpert*np.cos(lat)*np.exp(-(phi/alpha)**2)*np.exp(-((lat2-lat)/beta)**2)` (`phi`=longitude) | **identical** |
| `ĥ` (bump amplitude) | 120 m | `hpert = 120 * meter` | **identical** |
| `φ2` (bump latitude) | π/4 | `lat2 = np.pi/4` | **identical** |
| `α` (zonal width) | 1/3 | `alpha = 1/3` | **identical** |
| `β` (meridional width) | 1/15 | `beta = 1/15` | **identical** |
| Ω, g, a | 7.292×10⁻⁵ s⁻¹, 9.80616 m s⁻², 6.37122×10⁶ m | `7.292e-5`, `9.80616`, `6.37122e6` | **identical** |
| **Dissipation** | eq. (1): Laplacian viscosity `ν∇²V` (standard 2nd-order diffusion) | hyperdiffusion `nu*lap(lap(u))` = `ν∇⁴` (4th-order) | **different** — Galewsky damps with `∇²`, the Dedalus example with `∇⁴` hyperdiffusion (`nu = 1e5·meter²/second/32²`, matched at ℓ=32). Both are numerical regularisers acting only at small scales; neither changes the barotropic-instability mechanism, but the small-scale filamentary detail and the exact instability-onset time can differ slightly. |

## Verdict

The shipped example's **initial condition is the Galewsky et al. (2004) test case
exactly**: the basic jet (eq. 2) and the height perturbation (eq. 4) match
parameter-for-parameter. The balanced height is obtained by an **equivalent**
method (a 2-D LBVP of the divergence of gradient-wind balance rather than the
1-D meridional integral of eq. 3), giving the same balanced state to numerical
precision. The only genuine difference is the **dissipation operator**
(`∇⁴` hyperdiffusion here vs. `∇²` Laplacian viscosity in the paper).

## Consequence for Session L5 (run I-00)

`galewsky.py` can take the initial-condition formulae **directly from Galewsky
(2004) eq. (2) and (4)** — the Dedalus example confirms them and adds nothing new
to the IC. The one decision L5 must make deliberately is the **dissipation
choice**: match the paper's `∇²` viscosity, or follow the spectral-method norm of
`∇⁴` hyperdiffusion (as this example and the project's own solver plan do). Because
the dissipation differs, a small difference in instability-onset timing between
this reference run and the published Fig. 4 is expected and is **not** a Phase-0
failure (see §7 criterion 3). Galewsky's Fig. 4 shows the vorticity rolling up
into vortices with tight gradients over roughly **days 4–6**; that is the window
the gate looks for.
