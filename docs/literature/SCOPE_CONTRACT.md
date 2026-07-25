# Literature campaign — scope contract

**Session L4, Step 1. Written before any retrieval, deliberately, so the campaign
has a boundary it can be held to.**

A literature campaign without a stated boundary sprawls until it is abandoned
rather than finished. This document fixes what the campaign must establish and
what it must not chase, and it is the thing Step 16 checks the finished
bibliography against.

## The frame

Everything below is tied to the theoretical spine already derived in
`theory/derivations.tex`: material conservation of potential vorticity on a
rotating, curved surface,

    Dq/Dt = 0 ,    q = (ζ + f) / h

and its two regimes — wave propagation at one potential-vorticity interface,
shear instability at two. The campaign does not depend on Session L3's sign-off,
only on its *scope* being stable, which it is: the twelve section headings and
the hypothesis set H1–H10 are fixed.

## MUST establish

### M1. Grounding for the spine itself

That material PV conservation is the common source of both Rossby-wave
dispersion and barotropic instability, with citations adequate to support the
historical line from Rossby (1939) and Haurwitz (1940b) through Kuo (1949) to
the PV-thinking synthesis of Hoskins, McIntyre & Robertson (1985) and the
counter-propagating-wave picture of Bretherton (1966) and Heifetz, Bishop &
Alpert (1999).

### M2. Grounding for three claimed contributions

Each is stated here in the form it will be *challenged* in Step 11, not in its
most flattering form.

**(a) Divergent-dispersion quantification with an internal validation target.**
That the departure of the divergent shallow-water system's Hough-mode
eigenfrequencies from the nondivergent Rossby–Haurwitz prediction
`c_ang = −2Ω/[n(n+1)]` is quantified, and validated against the closed-form
`ε → 0` limit the project derives itself rather than against a published table.

**(b) A sufficient stability test, not merely a necessary one.** That a linear
stability eigenvalue problem about each zonal base state supplies actual growth
rates `σ(m)` and eigenmode structure, closing the gap left by the Rayleigh–Kuo
criterion, which forbids instability but cannot predict it.

**(c) A two-season, Doppler-corrected observational closure.** That the modelled
*intrinsic* phase speed is compared against reanalysis after correcting observed
ground-relative phase speeds for advection by the mean flow, in both an
ENSO-neutral (DJF 2013/14) and a strongly perturbed (DJF 2015/16) winter.

### M3. A defensible novelty statement

What is specifically new here, stated narrowly enough to survive a referee who
knows this literature. The campaign is instructed to *try to defeat* each of the
three claims above (Step 11) before allowing any of them into the gap statement.
An honest "this applies a standard method carefully to a new configuration" is a
better outcome than an overclaim that a referee dismantles.

## MUST NOT chase

Stated as explicitly as the first list, because these are the directions this
topic naturally bleeds into.

| # | Out of scope | Boundary condition — the one thing that *is* in scope |
|---|--------------|------------------------------------------------------|
| X1 | Full baroclinic instability theory | Enough only to state *why* this project deliberately stays barotropic, and what that excludes. Eady/Charney/Green model detail is not needed. |
| X2 | Numerical weather prediction and operational forecasting | Nothing. The project makes no forecasting claim. |
| X3 | Turbulence-closure modelling | Only the single Rhines-scale connection already in §7 of the theory. No closure schemes, no LES, no spectral-transfer theory beyond Rhines (1975) and Vallis & Maltrud (1993). |
| X4 | Machine-learning weather models | A brief acknowledgement only, where the optional `torch-harmonics` cross-check touches it. Not a survey. |

## Exit criteria

The campaign is finished when all of the following hold, and not before:

1. **≥ 60 verified references** in `docs/literature/VERIFIED_POOL.csv`, each with
   a DOI or stable URL confirmed to resolve *during this session* — not assumed
   from a plausible title.
2. **Zero unverifiable references.** Anything whose identifier cannot be
   confirmed is dropped from the pool entirely, not downgraded and retained. An
   unverifiable reference is not a weaker citation; it is not a citation.
3. **Every hypothesis H1–H10 and every theory section §1–§12** has at least one
   supporting or motivating citation, or an explicit written statement that it
   needs none because it is derived internally.
4. **Every one of the three contributions has been adversarially challenged**
   and the novelty claim narrowed wherever the challenge succeeded.

## The paper trail rule

Every reference that reaches `manuscript/references.bib` traces back to a row in
`docs/literature/CANDIDATE_POOL.csv` recording the query string that surfaced it
and the timestamp at which it was retrieved. A citation with no retrieval row is
treated as unverified and dropped, however plausible it sounds. This is the same
standard Session L3-PATCH applied to the CRW benchmark constants after review
found one instance of a value stated from familiarity rather than from a source:
the rule exists because that failure mode is quiet and this project has already
seen it once.
