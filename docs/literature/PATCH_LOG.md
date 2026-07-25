# Patch log — critique integration and readability calibration

**Session L4, Steps 14–15.**

## A note on how this was actually done

The brief anticipates a patch cycle: draft first, then integrate the critiques
from Steps 5, 7, 10 and 11. In practice the critiques landed *before* the drafts
were written, because Step 11's dialectic challenge substantially changed what the
paper is allowed to claim, and drafting an overclaiming Introduction in order to
patch it afterwards would have been wasted work with a real risk — that a
narrowing recorded in `GAP_STATEMENT.md` fails to propagate into the prose, which
is exactly the failure mode the brief warns about.

So the drafts were written *from* the narrowed claims. This log records, for each
critique finding, where in the drafts it landed, so the integration is auditable
either way.

## Findings integrated

| # | Finding | Source step | Where it landed |
|---|---------|-------------|-----------------|
| P1 | The three "contributions" overclaimed relative to blueprint §2.3, "The contribution is not new theory" | Step 1 instruction-critic | `introduction.tex` §1.3 opens by conceding this in the blueprint's own words; the four contributions are integration, `Ω` as free parameter, V-vs-V separation, and one narrow observational question |
| P2 | M2(a) was three claims bundled as one; the sectoral result (a3) was absent entirely | Step 1 | `SCOPE_CONTRACT.md` §M2 split into nine fragments a1–d; a3 named and challenged in `DIALECTIC_CHALLENGE.md` |
| P3 | "A sufficient stability test" is mathematically false — the operator is non-normal | Step 1 | Theory §9 gained an explicit caveat paragraph (this session); `introduction.tex` §1.4 states it; `GAP_STATEMENT.md` L2 |
| P4 | X1 excluded the observed-eddy-phenomenology literature the project's own Hayashi method needs to defend | Step 1 | `SCOPE_CONTRACT.md` X1 rewritten with two in-scope boundary cases; gap row G3 searched; **Randel & Held remains absent and is reported as such** |
| P5 | X3 excluded the jet-spacing literature while theory §7.3 claims a Jovian-banding contrast | Step 1, Step 7 | `SCOPE_CONTRACT.md` X3 rewritten; `related_work.tex` §5 states the Rhines scale is an arrest scale and explicitly declines the jet-spacing reading; `GAP_STATEMENT.md` L6 |
| P6 | Exit criteria 3 and 4 were unfalsifiable | Step 1 | Five checkable criteria; criterion 4 now requires a recorded search per fragment |
| P7 | Ω-sweep run IDs wrong in theory §7.3 (P-14–P-18) | Step 1, verified against blueprint §8.2 and `configs/phase_speed/` | Corrected to **P-08–P-12** in `theory/derivations.tex`; `introduction.tex` §1.3 uses the range without run IDs |
| P8 | Skiba's programme is direct prior art for fragment b1 and was absent | Step 5 corpus-critic | Gap row G1; `skiba2004`, `skiba2008`, `skiba2024`, `constantin2022` now cited in both drafts; b1 verdict **significantly narrowed** |
| P9 | `Kasahara 1976` was marked as cited by the theory but is not | Step 5 | Now genuinely cited in both drafts; `MISSING.md` records it as obtained, with its **venue corrected** |
| P10 | The stability operator is nondivergent; the jet is divergent shallow water | Step 7 width-critic, verified by inspection (`grep divergen` returns nothing in §8–§9) | `introduction.tex` §1.4 states it as a limitation; `related_work.tex` §3 cites `ripa1983` as the correct divergent reference; `GAP_STATEMENT.md` L1 |
| P11 | Ripa (1983) and Hayashi & Young (1987) absent from the whole corpus | Step 7 | Both retrieved and verified; cited in `related_work.tex` §3 |
| P12 | 185 Galewsky forward citations are a discretisation corpus, not stability analyses — a strong unrecorded negative result | Step 7 | `related_work.tex` §6 states it; `DIALECTIC_CHALLENGE.md` b2 reports the negative search as the evidence it is |
| P13 | Williamson (1992): held PDF is ORNL/TM-11895, not the JCP article | Step 10 depth-critique | `ANCHOR_NOTES.md` §1 records the mismatch; **no page-precise pointer is drawn from it anywhere** |
| P14 | Thuburn & Li (2000) was held but never extracted, and it constrains the phase-speed campaign | Step 9 | `introduction.tex` §1.2 third difficulty; `related_work.tex` §1; `GAP_STATEMENT.md` L3 |
| P15 | Kasahara (1976) venue was wrong in the project's own records since Session 00b | Step 3 | `MISSING.md` corrected with the correction called out |
| P16 | Heifetz et al. present the CRW picture as pedagogy, not new theory | Step 10 | `related_work.tex` §4 quotes their framing; fragment d verdict **not novel — exposition** |
| P17 | The `ε → 0` rate is fitted three decades away from where the numbers are quoted | Step 11 | `GAP_STATEMENT.md` L4 |
| P18 | Venue whitelist silently dropped the two strongest prior-art papers | Found while building the bibliography | `scripts/lit_curate.py` gained applied-maths venues and a forced-include for targeted retrievals; both papers now cited |

## Findings explicitly scoped out, with reasons

| # | Finding | Disposition |
|---|---------|-------------|
| S1 | ML weather-model survey | **Out of scope per X4.** Acknowledgement only. The `torch-harmonics` cross-check is optional and its primary reference belongs with the data provenance, not the Related Work. |
| S2 | CFD verification-and-validation canon (Roache, Oberkampf, ASME) | **Recorded as a gap, not filled.** Blueprint §2.3 claims V-vs-V separation as a distinguishing feature and the methodological literature for that claim is genuinely absent. Listed in `CLAIM_MAP.md`; a decision for Session L11, since it affects the Methods section rather than the Introduction. |
| S3 | Dealiasing and hyperdiffusion-choice literature | **Recorded as a gap.** These are Methods-section citations; noted in `CLAIM_MAP.md`. |
| S4 | Equatorial waveguide / Matsuno | **Out of scope.** The project works in midlatitudes. Relevant only to the secondary equatorial-confinement argument in theory §6.4, which is not load-bearing. |
| S5 | Eliassen–Palm / pseudomomentum, enstrophy-cascade canon | **Partially addressed.** `mcintyre1987` is in the pool; the enstrophy point enters via `thuburn2000`, which is the version that actually constrains this project. |

## Step 15 — readability and audience calibration

Target readership: *Theoretical and Computational Fluid Dynamics* — geophysical
fluid dynamics and numerical methods, not general science. Calibration checks
applied to both drafts:

1. **Physics before formalism.** The Introduction opens with a fluid column and a
   conserved label, and reaches the only two displayed equations
   (\eqref{eq:intro-pv} and the phase speed) after the physical statement they
   encode. No derivation appears in the Introduction; §1.2's three difficulties are
   stated as physical problems (the target is asymptotic; the criterion is
   one-sided; the test cases are not innocent), each with its consequence.
2. **Notation only where it earns its place.** `ε`, `L_d`, `q`, `c_ang` and
   `σ(m)` are introduced with their physical meaning attached. Christoffel symbols,
   the Legendre coupling matrices and the eigenvalue-problem operator are left to
   the theory section, where they belong.
3. **No passage where notation crowds out the physical statement.** Reviewed
   paragraph by paragraph. The one place this was a risk — the Lamb's-parameter
   discussion in §1.2 — states the physics first ("a column can stretch, so part of
   the budget goes into stretching, the restoring agent is diluted and the wave
   slows") and gives the symbol afterwards.
4. **Assumed knowledge appropriate to the venue.** Potential vorticity, Rossby
   waves, deformation radius, spectral methods and reanalysis are used without
   definition. Terms a numerical-methods reader may not carry — Lamb's parameter,
   the Rhines scale, non-normality — are glossed in a clause.
5. **Nothing traded for accessibility.** No precision was given up in this pass;
   the limitations in §1.4 are stated in their exact form rather than softened,
   which is the opposite trade and the correct one here.
