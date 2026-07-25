# Ripa (1983) and Hayashi & Young (1987) — divergent stability

**Session L4b, Part 2.**

## Source status, stated first

**Neither paper was obtained as full text.** Both are closed-access in the
*Journal of Fluid Mechanics*, with Unpaywall reporting `is_oa: false` and zero
open-access locations anywhere — including institutional repositories and
author-hosted copies, which Unpaywall aggregates.

What *was* obtained is each publisher's **verbatim abstract**. Both abstracts
state the paper's central result explicitly, which is why this session can reach
a conclusion at all. Everything below is marked **ABSTRACT-VERIFIED**: the claims
are claims the abstracts themselves make. **No page or equation pointer is
available for either paper, and none is given.**

The brief asked for precise page and equation pointers. That standard could not
be met and is not pretended to. Section 3.3 of the brief anticipated exactly this
and asked for a plain statement of how much it constrains the conclusion; that
statement is at the foot of this document.

---

## 1. Ripa (1983)

**Citation.** Ripa, P. (1983). "General stability conditions for zonal flows in a
one-layer model on the β-plane or the sphere." *Journal of Fluid Mechanics*
**126**, 463–489. DOI `10.1017/S0022112083000270`.

### The abstract, verbatim

> "Sufficient stability conditions are derived for a zonal flow on the β-plane or
> the sphere. Two conditions guarantee both *shear stability* (to perturbations
> with vanishing zonal average) and *inertial stability* (to longitude-independent
> perturbations). These conditions are not restricted to normal-mode disturbances,
> and are derived without making use of the quasi-geostrophic approximation. The
> main limitation of the model is to have only one layer.
>
> On the β-plane, the conditions are: (i) that the product of the meridional
> gradient of potential vorticity and the difference between an arbitrary constant
> and the zonal velocity be everywhere non-negative; *and* (ii) that the absolute
> value of this difference be nowhere larger than the local phase speed of long
> gravity waves. Inertial stability is independently assured if the Coriolis
> parameter and the potential vorticity are everywhere of the same sign (this
> well-known condition can be easily violated near the equator, but the flow may
> nonetheless be stable)."

### The conditions, in this project's notation

This translation is **the project's reading of prose**, not a transcription of a
displayed equation. With `c₀` an arbitrary constant:

```
(i)   (dQ/dy) · (c₀ − ū)  ≥ 0        everywhere
(ii)  |c₀ − ū|            ≤ √(gh)    everywhere
```

Four properties of this result matter, and three are stated by the abstract
itself rather than inferred:

- **They are *sufficient* conditions for stability, not necessary ones.** This is
  a different logical object from Rayleigh–Kuo, which is *necessary* for
  instability. Failing Ripa's conditions does not prove a flow unstable.
- **They are not restricted to normal modes.** This is stronger than the
  project's own eigenvalue analysis, which is modal by construction — and it
  sidesteps the non-normality caveat recorded as limitation L2.
- **No quasi-geostrophic approximation.** So they apply at finite Rossby number.
- **One layer only** — the same limitation the project has.

### The nondivergent-limit consistency check

This is what the brief (§3.1) identified as the critical check, and it **passes
cleanly**.

Condition (i) is the classical criterion in its Fjørtoft-strengthened form. A
monotone `dQ/dy` always admits a constant `c₀` lying outside the range of `ū`,
which makes the product single-signed; so (i) can only fail if `dQ/dy` changes
sign. That is Rayleigh–Kuo.

Condition (ii) involves `√(gh)`, the long-gravity-wave speed. The nondivergent
limit is the rigid-lid limit, in which the surface cannot deflect and long gravity
waves become infinitely fast: `ε = 4Ω²R²/(gH) → 0` means `gH → ∞`, so
`√(gH) → ∞` and (ii) is satisfied by *any* bounded zonal flow.

**So Ripa's condition reduces cleanly to the classical one.** The divergent case
does not *modify* Rayleigh–Kuo. It **adds a second, independent condition with no
nondivergent analogue** — a criticality condition on the flow speed relative to
long gravity waves.

That is a qualitative change to the *structure* of the stability theory, and it is
also the reason the answer for this project turns out to be undramatic: a second
condition can only matter where it is close to being violated.

### Is the extra condition binding for this project?

No, and not by a small margin. Computed in
`theory/sympy_checks/check_ripa_divergent_condition.py`:

| Quantity | Value |
|----------|-------|
| `√(gH)`, long-gravity-wave speed | 313.1 m s⁻¹ |
| Galewsky jet `u_max` | 80.0 m s⁻¹ |
| `max │c₀ − ū│` (best-case `c₀`) | 40.0 m s⁻¹ |
| **Margin** `√(gH) / max│c₀ − ū│` | **7.83×** |
| Froude-like ratio `u_max/√(gH)` | 0.256 |

Even the least favourable admissible `c₀` only doubles `max│c₀ − ū│` to 80 m s⁻¹,
still 3.9× below `√(gH)`. **The conclusion does not depend on how `c₀` is chosen.**

**And the rotation sweep cannot activate it.** Condition (ii) contains `√(gH)` and
`ū` and no rotation rate at all. Across runs P-08 to P-12, Lamb's parameter rises
from 0.55 to 141 — the system becomes far more divergent *in the sense that
governs wave dispersion* — while the divergent *stability* condition is untouched.
Those are two different senses of "divergent", and the project's own §6 and §9 use
the word for both. That conflation is worth naming: **`ε` large does not imply the
divergent stability condition is near failure.**

### Also reported

The search record notes that Ripa investigates Gaussian jets centred at the
equator and finds that "easterlies with the width of a Kelvin wave and westerlies
with that width or wider may be unstable, even though the gradient of potential
vorticity is positive for any strength of the jet."

This is condition (ii) failing while (i) holds — instability with a monotone PV
gradient — and it is **equatorial**, at the Kelvin-wave width. **This statement is
from a secondary search summary, not from the publisher abstract, and is the least
well grounded claim in this document.** It is consistent with the abstract's own
remark about the equator, and with Hayashi & Young below, but it is flagged.

---

## 2. Hayashi & Young (1987)

**Citation.** Hayashi, Y.-Y., & Young, W. R. (1987). "Stable and unstable shear
modes of rotating parallel flows in shallow water." *Journal of Fluid Mechanics*
**184**, 477–504. DOI `10.1017/S0022112087002982`.

### The abstract, verbatim

> "This article considers the instabilities of rotating, shallow-water, shear
> flows on an equatorial β-plane. Because of the free surface, the motion is
> horizontally divergent and the energy density is cubic in the field variables
> (i.e. in standard notation the kinetic energy density is ½h(u² + v²)). Marinone
> & Ripa (1984) observed that as a consequence of this the wave energy is no
> longer positive definite (there is a cross-term Uh′u′). A wave with negative
> wave energy can grow by transferring energy to the mean flow. Of course total
> (mean plus wave) energy is conserved in this process. Further, when the basic
> state has constant potential vorticity, we show that there are no exchanges of
> energy and momentum between a growing wave and the mean flow. Consequently when
> the basic state has no potential vorticity gradients an unstable wave has zero
> wave energy and the mean flow is modified so that its energy is unchanged. This
> result strikingly shows that energy and momentum exchanges between a growing
> wave and the mean flow are not generally characteristic of, or essential to,
> instability."

### Does it show instability without a PV-gradient sign change?

**Yes — the width critic's report is confirmed**, and it was right to flag it.
The abstract states that when the basic state has *no* potential-vorticity
gradients at all, unstable waves exist (with zero wave energy). A constant-PV
basic state has `dQ/dy ≡ 0` everywhere, so *a fortiori* there is no sign change.
Rayleigh–Kuo's necessary condition does not transfer to the divergent system.

### But the regime is equatorial, and that is decisive here

Two qualifications, both from the abstract:

1. **The setting is an equatorial β-plane.** This project's jet is midlatitude,
   centred at 45° N.
2. **The mechanism requires the free surface to matter energetically.** Because
   the energy density is cubic (`½h(u²+v²)`), wave energy carries a cross-term
   `Uh′u′` and is not positive definite, so a negative-energy wave can grow by
   *giving* energy to the mean flow. For that cross-term to be competitive the
   flow must be a non-negligible fraction of the gravity-wave speed.

At the equator `f → 0`, no geostrophic constraint limits `ū` relative to
`√(gh)`, and the mechanism is available. For this project's jet the Froude-like
ratio is **0.256** — strongly subcritical — and the margin on Ripa's condition
(ii) is **7.8×**.

**The counterexample is real, and it does not reach this project's configuration.**

---

## 3. How much this constrains the conclusion

Per the brief's §3.3, stated plainly.

**What is solidly established**, because both abstracts state it directly:

- Ripa's divergent conditions reduce cleanly to the classical nondivergent
  condition, and add one extra gravity-wave criticality condition.
- Instability without a PV-gradient sign change is real in the divergent
  shallow-water system.
- That counterexample is equatorial and energetic in origin.

**What is *not* established, and would need the full texts:**

- The **exact functional form** of Ripa's conditions. The translation into
  inequalities above is a reading of prose. The *margin* calculation is robust to
  this — 7.8× survives a good deal of misreading — but a claim about the precise
  boundary of the stable region would not be.
- Whether Ripa's conditions on **the sphere** differ in form from the β-plane
  versions quoted. The abstract gives the β-plane forms explicitly and says only
  that conditions are derived "for a zonal flow on the β-plane or the sphere".
  **This project works on the sphere.** The margin is large enough that a
  metric-factor difference is very unlikely to change the answer, but it is an
  unclosed detail.
- Whether Hayashi & Young's constant-PV instability has any midlatitude analogue
  at finite `f` that their equatorial framing simply does not address.

**Net effect on the decision:** the finding that condition (ii) is satisfied with
a 7.8× margin, at every rotation rate the project runs, is robust to every one of
these uncertainties. The finding that would have been fragile — a claim that the
project sits *near* the divergent stability boundary — is not the finding.
