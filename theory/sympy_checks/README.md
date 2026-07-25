# theory/sympy_checks/

Executable verification of every equation that `theory/derivations.tex` presents
as established. The standing rule for this project is that no derived result is
asserted in the theory document without a script here that actually runs and
reports a verdict, and no script here is trusted without its recorded output.

Each script is self-contained, prints `VERIFIED` or `MISMATCH` with the
discrepancy shown, exits non-zero on `MISMATCH`, and writes its full report to
`output/<script-name>.txt`. Those output files are tracked: they are small plain
text, and committing them gives a permanent, inspectable record of what the
verdict was at the commit that produced it. Audit check 30 in `scripts/audit.sh`
enforces that every script has one.

Run one:

    python theory/sympy_checks/check_pv_conservation.py

Run all:

    for f in theory/sympy_checks/check_*.py; do python "$f" || echo "FAILED: $f"; done

| Script | Section | What it checks |
|--------|---------|----------------|
| `check_spherical_laplacian_eigenvalue.py` | §2, §5 | `∇²Y_n^m = −n(n+1)/R² Y_n^m`, symbolically for small `(n,m)` and numerically to degree 40 |
| `check_christoffel_symbols.py` | §2 | Christoffel symbols from the metric, against closed forms and against published 2-sphere values transported from colatitude; plus the divergence formula and the momentum-equation metric terms they generate |
| `check_pv_conservation.py` | §1, §3 | The exact identity `h Dq/Dt = curl(M) − q C` for arbitrary fields on the sphere, so `Dq/Dt = 0` follows from the equations of motion with no unaccounted residual |
| `check_rh_dispersion.py` | §5 | `c_ang = −2Ω/[n(n+1)]`, including the cancellation that makes it latitude-independent and the physical derivation of the westward sign |
| `check_hough_epsilon_limit.py` | §4, §6 | The divergent eigenvalue problem converges to the nondivergent result as `ε → 0`, with the convergence *rate* fitted (expected and found: first order); plus the H5 readout at Earth's `ε` |
| `check_rayleigh_kuo.py` | §8, §9 | The necessary condition follows from the linearised PV equation; and, numerically, that a base state without a sign change is provably stable while one with a sign change yields actual growth rates and an `m*` |
| `check_crw_two_interface.py` | §10 | The two-interface counter-propagating-wave model reduces exactly to the published Rayleigh dispersion relation, requires oppositely signed PV jumps, and reproduces the published cutoff, optimum and peak growth rate |

## Tolerances

Every numerical tolerance is a named constant at the top of its script, with a
comment saying what it means physically. They are also listed in
`theory/DERIVATION_REVIEW.md` for operator approval, because a tolerance chosen
without thought is a way of passing a check that should have failed.

## On a MISMATCH

A script that reports `MISMATCH` is not to be silently reconciled — neither by
adjusting the LaTeX to match the code nor the code to match the LaTeX. Both sides
of the discrepancy go into `theory/DERIVATION_REVIEW.md` for operator judgement.
