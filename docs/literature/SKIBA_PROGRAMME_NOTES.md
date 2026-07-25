# Skiba / Constantin–Germain / Cao–Wang notes

**Session L4b, Part 3.** One question per paper, asked identically of each:

> **Does this paper pose and solve the linear stability eigenvalue problem for
> the full divergent shallow-water system — free-surface height as a dynamical
> variable — or does it restrict to the nondivergent barotropic vorticity
> equation?**

The question matters because Session L4's dialectic challenge narrowed fragment
b1 ("the stability EVP as a method") on the strength of this programme. If the
programme covers the *divergent* case, an extension into it would be occupied
territory. If it does not, the gap is real and documented rather than assumed.

## Source status, stated before the findings

**None of these five papers was obtained as full text.** All are closed-access
except the Cao–Wang preprint. What was obtained is the publisher's own abstract
in each case where one exists. Findings below are therefore **ABSTRACT-VERIFIED**
in the sense defined in `docs/literature/MISSING.md`, with one exception noted.

This is weaker than the brief asked for — it specified deep reads with page and
equation pointers, and states that "no claim in this section may rest on a title
or abstract alone." That standard could not be met, and the honest response is to
say so rather than to dress an abstract up as a close reading. **What saves the
Part 3 question is that it is unusually coarse:** whether a paper works in the
barotropic vorticity equation or in the divergent shallow-water system is stated
in the first sentence of an abstract, in every one of these cases, because it is
the paper's governing equation. A page-precise reading would add detail but could
not reverse the answer.

## 1. Skiba & Pérez-García (2004) — `10.1002/num.20042`

*"On the structure and growth rate of unstable modes to the Rossby–Haurwitz
wave"*, **Numerical Methods for Partial Differential Equations**.
Status: **ABSTRACT-VERIFIED** (Crossref-hosted publisher abstract).

**Governing equation, from the abstract verbatim:** the Rossby–Haurwitz wave "is
exact solution of the **nonlinear barotropic vorticity equation** describing the
dynamics of an ideal fluid on a rotating sphere, as well as the large-scale
barotropic dynamics of the atmosphere."

**Answer: NONDIVERGENT.** No free surface, no height variable.

**What it does contain, and it is substantial:** the structure of the spectrum of
the linearised operator for an ideal fluid; a conservation law for perturbations
to the Rossby–Haurwitz wave, used to obtain **a necessary condition for
exponential instability**; an estimate of the **maximum growth rate** of unstable
modes; an orthogonality result for non-neutral or non-stationary mode amplitudes
in two inner products; and — directly relevant to this project's method — use of
the analytical results "to test and discuss the accuracy of a numerical spectral
method used for the normal mode stability study of arbitrary flow on a sphere."

That last clause is the one that narrows fragment b1: this is a spherical
normal-mode stability calculation with growth rates, cross-checked against
analytic constraints, published in 2004. The base state is a Rossby–Haurwitz
wave, not a Galewsky-type jet, so it is not the same calculation — but the
*method* is unambiguously prior art.

## 2. Skiba (2008) — `10.1007/s10958-008-0091-3`

*"Nonlinear and linear instability of the Rossby–Haurwitz wave"*, **Journal of
Mathematical Sciences**.
Status: **TITLE-ONLY.** No abstract in Crossref or OpenAlex; full text not
obtained.

**Answer: NOT ESTABLISHED.** The subject is the Rossby–Haurwitz wave, which is a
solution of the barotropic vorticity equation, so a nondivergent setting is very
likely — but *likely is not verified*, and this entry is marked accordingly
rather than folded in with the others. Nothing in the decision memo rests on it.

## 3. Skiba (2024) — `10.4310/dpde.2024.v21.n3.a1`

*"Stability of a class of solutions of the barotropic vorticity equation on a
sphere"*, **Dynamics of Partial Differential Equations**.
Status: **TITLE-ONLY** (no abstract available; the title itself names the
governing equation).

**Answer: NONDIVERGENT**, on the strength of the title naming the barotropic
vorticity equation explicitly. This is a weaker basis than an abstract, but a
title that names the governing equation is not ambiguous about it.

## 4. Constantin & Germain (2022) — `10.1007/s00205-022-01791-3`

*"Stratospheric Planetary Flows from the Perspective of the Euler Equation on a
Rotating Sphere"*, **Archive for Rational Mechanics and Analysis** 245, 587–644.
Status: **ABSTRACT-VERIFIED**.

**Governing equation, from the abstract verbatim:** "This article is devoted to
stationary solutions of **Euler's equation on a rotating sphere**."

**Answer: NONDIVERGENT.** The incompressible two-dimensional Euler equation on
the sphere is the nondivergent barotropic system; there is no free surface.

**What it contains:** rigidity results forcing solutions to be zonal or rotated
zonal; "a natural analogue of Arnold's stability criterion"; stability properties
of the lowest-mode Rossby–Haurwitz stationary solutions; and local and global
bifurcation of non-zonal stationary solutions from classical Rossby–Haurwitz
waves.

The Arnold-criterion analogue is worth noting for contrast: Arnold-type stability
theorems are energy–Casimir arguments, which is the same family Ripa's theorem
belongs to. Constantin & Germain do this for the **nondivergent** system; Ripa
(1983) did it for the **divergent** one, nearly forty years earlier.

## 5. Cao, Wang & Zuo (2023) — `10.48550/arXiv.2305.03279`

*"Stability of degree-2 Rossby–Haurwitz waves"*, arXiv preprint.
Status: **ABSTRACT-VERIFIED** (open-access preprint; abstract read from arXiv).
Not previously in `VERIFIED_POOL.csv` under this DOI.

**Governing equation, from the abstract verbatim:** "Rossby–Haurwitz (RH) waves
are important explicit solutions of the **incompressible Euler equation on a
two-dimensional rotating sphere**."

**Answer: NONDIVERGENT.**

**What it contains:** a proof of the orbital stability of degree-2
Rossby–Haurwitz waves, confirming a conjecture of Constantin & Germain (2022);
a variational approach using rearrangements of a fixed function; and application
to degree-1 RH waves, Arnold-type flows, and "zonal flows with monotone absolute
vorticity."

That last item is the interesting one. *Monotone absolute vorticity* is precisely
the nondivergent Rayleigh–Kuo-stable case — so this paper establishes rigorous
stability for exactly the class that Ripa's condition (i) describes, in the
nondivergent setting.

## Summary

| Paper | Status | Governing system | Divergent stability EVP? |
|-------|--------|------------------|--------------------------|
| Skiba & Pérez-García (2004) | ABSTRACT-VERIFIED | Barotropic vorticity equation, sphere | **No** |
| Skiba (2008) | TITLE-ONLY | not established | **Not established** |
| Skiba (2024) | TITLE-ONLY | Barotropic vorticity equation, sphere | **No** |
| Constantin & Germain (2022) | ABSTRACT-VERIFIED | Euler equation, rotating sphere | **No** |
| Cao, Wang & Zuo (2023) | ABSTRACT-VERIFIED | Incompressible Euler, rotating sphere | **No** |

**Finding: none of this programme treats the divergent shallow-water stability
problem.** It is uniformly nondivergent — barotropic vorticity equation or
incompressible Euler on the sphere.

**Two consequences, pulling in opposite directions:**

1. Fragment **b1**'s "significantly narrowed" verdict **stands, and is now more
   precisely justified**: the project's stability EVP *is* nondivergent, and the
   nondivergent spherical normal-mode stability calculation is exactly what this
   programme has been doing since at least 2004. Session L4 recorded this verdict
   on the strength of titles; it now rests on governing equations.

2. But the programme does **not** occupy the divergent territory. The prior art
   for that is older and different — Ripa (1983), and the equatorial work of
   Hayashi & Young (1987) and Marinone & Ripa (1984). Whether that leaves room
   for the project is the subject of `DIVERGENT_STABILITY_DECISION.md`.
