# Unobtainable references and their mitigation

Two sources associated with **extension B** (the divergent shallow-water
eigenmodes — Hough functions / Laplace's tidal equations) could not be obtained
as full text. They are recorded here with full citations and DOIs, together with
the reason the project is not blocked by their absence and the accessible
substitutes to chase.

## The two sources

| Filename (if obtained) | Full citation | DOI |
|------------------------|---------------|-----|
| `longuethiggins_1968_laplace_tidal_eigenfunctions.pdf` | Longuet-Higgins, M. S. (1968). The eigenfunctions of Laplace's tidal equations over a sphere. *Philosophical Transactions of the Royal Society A*, 262(1132), 511–607. | [10.1098/rsta.1968.0003](https://doi.org/10.1098/rsta.1968.0003) |
| `swarztrauber_1985_vector_harmonic_analysis.pdf` | Swarztrauber, P. N., & Kasahara, A. (1985). The vector harmonic analysis of Laplace's tidal equations. *SIAM Journal on Scientific and Statistical Computing*, 6(2), 464–491. | [10.1137/0906033](https://doi.org/10.1137/0906033) |

Both are cited from their DOIs for historical attribution. They are the classical
references for the eigenstructure of the divergent tidal equations on a sphere.

## Why the project is not blocked

Neither source is required to *execute* extension B. The Hough-mode
eigenfrequencies are **not read from a published table**; the Laplace tidal
equation eigenvalue problem is derived from first principles in Session L3 and
solved numerically in Dedalus. The validation target is therefore internal, and
it is stronger than an external table would be — a table gives a handful of
tabulated numbers, whereas the solved eigenvalue problem gives the full
dispersion curve and eigenmode structure, at the project's own resolution and
parameters, checkable against a closed-form limit (below).

The physical validation argument (the `ε → 0` limit) is recorded in
`docs/CONVENTIONS.md` under "Authorised extensions to the blueprint": in the
nondivergent limit the divergent eigenfrequencies must reduce exactly to the
Rossby–Haurwitz angular speed `c_ang → −2Ω/[n(n+1)]`, which is hypotheses H1 and
H2 of the blueprint, so the solver is validated against a limit the project
derives independently rather than against a copied table.

## Accessible substitutes to obtain

Two open-access substitutes cover the same physics and should be obtained if
possible (flagged for the **Session L4 corpus-adequacy audit** to chase
open-access equivalents):

| Suggested filename | Citation | Availability |
|--------------------|----------|--------------|
| `kasahara_1976_normal_modes_ultralong_waves.pdf` | Kasahara, A. (1976). Normal modes of ultralong waves in the atmosphere. *Journal of the Atmospheric Sciences*, 33(3), 408–424. | Freely available from the AMS journals archive. |
| `paldor_2015_shallow_water_waves.pdf` | Paldor, N. (2015). *Shallow Water Waves on the Rotating Earth.* SpringerBriefs in Earth System Sciences. | SpringerBriefs monograph. |

Kasahara (1976) develops the normal modes (including the Rossby–Haurwitz /
Hough structure) of the linearised shallow-water system on the sphere; Paldor
(2015) is a modern, pedagogical treatment of the same wave physics. Either is an
adequate stand-in for the historical attribution the two unobtainable papers
would have provided.
