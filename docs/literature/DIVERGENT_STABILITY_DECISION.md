# Divergent stability — decision memo

**Session L4b, Part 5.** Written to be acted on, not filed.

---

## The recommendation, first

**Take Option B: do not extend the stability analysis to the divergent case as a
research contribution.** The question fragment e1 proposed to answer was answered
and published in 2020, in a journal this project would submit to, for the same
class of problem on the same geometry.

**But Option B as originally framed is not enough**, and this is the part worth
reading. That published answer says the project's nondivergent growth rates are
*quantitatively wrong for the system it integrates* — by more than 50% at this
project's own layer depth. Limitation L1 currently reads as a scoping choice. It
is not: it is a known, sized bias. **Option B must be strengthened to state the
size of the bias and cite the paper that measured it.**

Concretely, three things follow, none of which requires new derivation:

1. **Cite Paldor, Shamir & Garfinkel (2020)** in §9 and in `GAP_STATEMENT.md` L1,
   and state that non-divergence biases growth rates for spherical jets, with the
   sign and rough magnitude they report.
2. **Stop quoting `σ = 2.0748×10⁻⁵ s⁻¹` to five figures**, and stop
   distinguishing `m = 6` from `m = 7` at 0.07%. A 0.07% discrimination inside a
   >50% modelling bias is not meaningful. Report the resolved band and the plateau.
3. **Keep `evp_stability.py` nondivergent**, as currently scoped, and say why in
   one sentence with a citation rather than leaving it as an unexplained choice.

---

## 1. What Parts 2–4 established

**Part 2 — Ripa (1983) and Hayashi & Young (1987).** Neither could be obtained as
full text; both publisher abstracts were obtained verbatim. Ripa's two sufficient
conditions for stability of a one-layer zonal flow **reduce cleanly** to the
classical Rayleigh–Kuo condition in the nondivergent limit — divergence does not
modify the classical condition, it adds a second, independent gravity-wave
criticality condition with no nondivergent analogue. Hayashi & Young **do** show
shallow-water instability with no potential-vorticity gradient at all, confirming
the width critic's report — but on an *equatorial* β-plane, by a negative-energy
mechanism that needs the flow to be comparable to the gravity-wave speed.

**Part 3 — the Skiba / Constantin–Germain / Cao–Wang programme.** All five papers
are **nondivergent** — barotropic vorticity equation or incompressible Euler on
the sphere — established from governing equations named in their abstracts, not
from titles. So that programme narrows fragment b1 (which is nondivergent, as the
project's is) more precisely than Session L4 could establish, and does *not*
occupy the divergent territory.

**Part 4 — the dialectic challenge.** Verdict **FULLY NARROWED**, the strongest
verdict any fragment has received in this project. The territory is occupied, and
none of the occupying work was in the 758-reference pool.

## 2. Fragment e1 verdict

> **FULLY NARROWED — not a contribution.**

Three independent kills, each sufficient on its own.

**(a) The exact comparison is published.** Paldor, Shamir & Garfinkel (2020),
*Geophysical & Astrophysical Fluid Dynamics* **115**(1), 15–34,
`10.1080/03091929.2020.1724996` — "Barotropic instability of a zonal jet on the
sphere: from non-divergence through quasi-geostrophy to shallow water". Zonal jet,
sphere, linear stability, growth rates compared across the nondivergent barotropic
vorticity equation, the quasi-geostrophic equation and the full shallow-water
equations. That is fragment e1's sentence, rearranged.

From the authors' own EGU2020 conference abstract of the same work — **the journal
paper is bronze open-access but blocked to scripted retrieval, so these numbers
are attributed to the conference abstract, not to the journal text**: for mean
depths between 5 and 10 km, growth rates from the shallow-water equations "can be
smaller by more than 50%" than the nondivergent and quasi-geostrophic predictions;
the three formulations converge only for depths of 30 km or more; and layer depth
controls growth rates in a way "completely lost in the ND equation and is overly
weak in the QG system."

**This project uses H = 10 km.** It is inside the band where the discrepancy is
largest.

**(b) Applying Ripa's conditions to guide numerical test cases is also published,
twice.** White & Staniforth (2009), *QJRMS*, `10.1002/qj.504`, extend Ripa's
criteria **to the sphere** with orography, in the stated context of "the use of
stable flows to test the formulation of discretized numerical models", with
"illustrative examples of how to apply the criteria." Staniforth & White (2008),
`10.1002/qj.240`, derive Ripa-class conditions to guide parameter choices for
shallow-water test cases so that "any significant time evolution … is of numerical
origin." The 2009 paper also closes the open question `RIPA_HAYASHI_YOUNG_NOTES.md`
left about whether Ripa's spherical conditions differ in form from the β-plane
ones — it should be cited regardless of this decision.

Related and equally unoccupied-by-us: Poulin & Flierl (2003), *JPO*, a divergent
shallow-water jet eigenvalue problem swept over Rossby and Froude number and
cross-validated against nonlinear runs; and Mak, Griffiths & Hughes (2016), *JFM*,
`10.1017/jfm.2015.718`, extending Howard's semicircle theorem and Høiland's bound
to shallow water and solving a jet numerically across Froude number.

**(c) For this jet, the test e1 proposes returns nothing.** Ripa's conditions are
*jointly sufficient* for stability. The Galewsky jet **fails condition (i)** — the
project's own `check_rayleigh_kuo.py` finds `dQ/dφ` changing sign at four
latitudes — so the theorem is silent about it. Not "stable", not "unstable":
silent. Testing whether a sufficient condition "holds, is modified, or is
violated" for a flow that already fails its first clause is not a well-posed test.
The 7.83× margin on condition (ii) is therefore *indicative* — the flow is far
from the regime where the free surface supplies its own instability mechanism —
but it certifies nothing, and the check script now says so.

## 3. Two costed options

### Option A — Extend

**What would have to happen:**

| Work | Scope |
|------|-------|
| New subsection of `theory/derivations.tex` posing the divergent stability EVP, building on §6's Hough-mode formulation | 1–2 days |
| New verification scripts under `theory/sympy_checks/` — a nondivergent-limit reduction check at minimum, plus a convergence check | 1 day |
| **Return through the operator sign-off gate** before L5 may consume it | Elapsed time, not effort |
| New or extended `configs/evp/EVP-jet-stability.yaml` covering the divergent case | Hours |
| Additional runs in Session R4's EVP campaign | Compute, plus analysis |

**Rough estimate: about a week of derivation-and-verification work**, plus a
second pass through a sign-off gate that is currently already open and awaiting a
decision on L3 and L4.

**Why the estimate is not the point.** The work is tractable. The problem is that
its result is already published, with numbers, by Paldor, Shamir & Garfinkel — and
would be discovered by any referee who knows the spherical-instability literature,
because it is in *GAFD*. Doing it would produce a reproduction presented as a
contribution.

### Option B — Do not extend, and strengthen the limitation

**What would have to happen:**

| Work | Scope |
|------|-------|
| Cite Paldor/Shamir/Garfinkel (2020) in theory §9 and in `GAP_STATEMENT.md` L1, stating the sign and size of the non-divergence bias | Hours |
| Cite White & Staniforth (2009) for the spherical form of Ripa's conditions, and Ripa (1983) for the conditions themselves | Hours |
| Downgrade the precision of the reported growth rates: report the resolved band and the `m = 6–7` plateau, not five significant figures | Hours |
| One sentence in §9 saying the analysis is deliberately nondivergent, and why | Minutes |

**Rough estimate: under a day**, no new derivation, no return through the sign-off
gate for new physics, no new runs.

**What is given up.** Nothing that was going to be a contribution. The project
keeps a nondivergent stability analysis and says so, with a citation for what the
approximation costs.

## 4. The recommendation, and why

**Option B**, strengthened as in the opening section.

The reasoning is not "extending is too much work." It is that **the extension's
result is known, published, and unfavourable to the project's current numbers**,
and the valuable move is to absorb that result rather than to re-derive it.

`PROJECT_BLUEPRINT.md` §2.3 says the contribution is not new theory but "a
controlled, systematically verified numerical isolation" with "quantified
numerical uncertainty." A study that knows its growth rates carry a >50%
formulation bias, says so, cites the measurement, and adjusts its reported
precision accordingly is doing exactly that. A study that quietly quotes five
significant figures from a biased operator is not — and the fix costs a day.

**One caveat on my own recommendation.** The >50% figure comes from a conference
abstract by the authors of the journal paper, not from the journal paper itself,
which could not be retrieved. It is their own description of their own result, so
it is good evidence, but the exact figure should be checked against the published
text before it is quoted in the manuscript. **Obtaining that one paper is the
highest-value literature action remaining in this project** — it is bronze
open-access and one browser click away.

## 5. What this changes about L1, L5, b1 and b2

| Item | Was | Now |
|------|-----|-----|
| **L1** | "The stability analysis is nondivergent; the jet is not" — a scoping statement | A **sized, cited** bias: non-divergence overestimates growth rates for spherical jets, by >50% at H = 5–10 km per Paldor et al. |
| **L5** | Four classical sources unobtained | Still four, but two are now **ABSTRACT-VERIFIED** with their central results extracted, and the spherical-form question is closed by White & Staniforth (2009) |
| **b1** | "Significantly narrowed" on the strength of titles | Same verdict, now on the strength of **governing equations** named in abstracts — all five programme papers are nondivergent |
| **b2** | "Survives, heavily caveated" | Weaker still. The negative search result stands, but the numbers are now known to carry a >50% formulation bias, so the reported precision must drop |

## 6. Escalations beyond the fragment

1. **Two errors in `check_ripa_divergent_condition.py` were caught by the
   dialectic critic and fixed this session**: it named runs P-08…P-12 as the
   jet rotation sweep when those are `single_harmonic` runs containing no jet (the
   jet sweep is I-06…I-09, and uses the idealised jet, not Galewsky's); and it
   implied the margin on Ripa's condition (ii) was reassuring about stability when
   the theorem is in fact silent for this jet because condition (i) fails.
2. **`configs/RUN_REGISTRY.md` shows all 42 runs "not started".** Fragment e1's
   own wording promised cross-validation "against the nonlinear initial-value runs
   already in the project's campaign". There are none yet. Any future fragment
   phrased that way should be checked against the registry first.
