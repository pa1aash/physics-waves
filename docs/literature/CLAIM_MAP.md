# Claim-to-citation locus map

**Session L4, Step 6** (finalised after Steps 8–12, so it reflects the gap-filled
corpus and the narrowed novelty claims).

Every claim this project will make maps here to the citation that supports,
motivates or provides the comparison baseline for it — or, where the claim is
derived internally, to the specific internal artefact that establishes it. The
scope contract forbids a bare "needs no citation": the mapping must point at
something either way.

This is what makes Session L12's adversarial "every claim traces to a run ID or a
citation" check tractable. Built now, while the material is fresh, rather than
reconstructed later under referee-simulation pressure.

## Legend

- **Citation** — a DOI in `VERIFIED_POOL.csv`. `[R]` = PDF held and read;
  `[I]` = identifier verified, paper not read (nothing page-precise claimed).
- **Internal** — a `theory/sympy_checks/*.py` script, a theory section, or a run ID
  from `configs/`.

---

## Hypotheses H1–H10

| ID | Claim | Support | Baseline / comparison |
|----|-------|---------|----------------------|
| H1 | All initialised modes propagate westward | Rossby (1939) `[R]`, Haurwitz (1940b) `[I]`, pre-DOI — cited bibliographically | Internal: theory §5 eq. (28)/(32); `check_rh_dispersion.py` arm 3 derives the sign |
| H2 | `c_ang ∝ 1/[n(n+1)]` at fixed `Ω` | Haurwitz (1940b) `[I]` | Internal: `check_rh_dispersion.py` arm 2, exact for 9 `(n,m)` pairs |
| H3 | `c_ang ∝ Ω` at fixed `n` | — (no prior study sweeps `Ω`; this is the point) | Internal: theory eq. (28); runs P-08…P-12 |
| H4 | Measured speeds match `−2Ω/[n(n+1)]` to a few per cent at low `n` | Williamson et al. (1992) `10.1016/0021-9991(92)90060-c` `[R, but see note]`; Jakob-Chien et al. (1995) `10.1006/jcph.1995.1125` | Internal: theory eq. (28). **Constrained by** Thuburn & Li (2000) `10.3402/tellusa.v52i2.12258` `[R]` — the RH wave is unstable, so the measurement window matters |
| H5 | Departure from the nondivergent prediction grows as the scale approaches `L_d` | Longuet-Higgins (1968) `10.1098/rsta.1968.0003` `[I]`; Kasahara (1976) `10.1175/1520-0493(1976)104<0669:nmouwi>2.0.co;2` `[R]`; Swarztrauber & Kasahara (1985) `10.1137/0906033` `[I]` | Internal: `check_hough_epsilon_limit.py` arms 3–4; run EVP-hough |
| H6 | Benchmark error decays spectrally | Williamson et al. (1992); Jakob-Chien et al. (1995) | Internal: resolution ladder L0/L1/L2; runs V-01…V-09. Note blueprint §11.1's Richardson extrapolation presumes algebraic convergence — a tension to resolve |
| H7 | Jets failing Rayleigh–Kuo remain stable | Kuo (1949) `10.1175/1520-0469(1949)006<0105:diotdn>2.0.co;2` `[R]` §5; Bretherton (1966) `10.1002/qj.49709239302` `[R]` p. 331 eq. (13) | Internal: `check_rayleigh_kuo.py` arm 4a. **Bounded by** L2 (non-normality) and by the open question on Hayashi & Young (1987) `10.1017/s0022112087002982` `[I]` |
| H8 | Growth rate rises with supercriticality | Kuo (1949) `[R]`; Skiba & Pérez-García (2004) `10.1002/num.20042` `[I]` | Internal: theory eq. (55)/(56); runs I-01…I-05 |
| H9 | Increasing `Ω` at fixed jet shape stabilises | — (the `Ω` sweep is the project's own) | Internal: theory eq. (46) — raising `Ω` raises `β`, so the curvature term less easily reverses `dQ/dy`; runs I-06…I-09 |
| H10 | Model dominant wavenumber is of the same order as observed | Hersbach et al. (2020) `10.1002/qj.3803` `[R]`; Kalnay et al. (1996) `10.1175/1520-0477(1996)077<0437:tnyrp>2.0.co;2` `[R]` | Internal: run EVP-jet-stability; blueprint §10.4 caps this at order-of-magnitude and dominant wavenumber |

## Theory sections §1–§12

| § | Subject | Support | Internal artefact |
|---|---------|---------|-------------------|
| 1 | PV conservation from Kelvin + column mass | Hoskins et al. (1985) `10.1002/qj.49711147002` `[R]` | `check_pv_conservation.py` |
| 2 | Sphere as a curved manifold | Vasil et al. (2019) `10.1016/j.jcpx.2019.100013` `[R]` (spherical basis) | `check_christoffel_symbols.py`, `check_spherical_laplacian_eigenvalue.py` — both self-contained, no external source needed |
| 3 | Shallow-water equations, PV on the sphere | — | `check_pv_conservation.py`: exact identity for arbitrary fields |
| 4 | Nondimensionalisation, `Ro` and `ε` | Kasahara (1976) `[R]` (Lamb's parameter in context) | theory eq. (21)–(24) |
| 5 | Waves on rest; Rossby–Haurwitz | Rossby (1939) `[R]`, Haurwitz (1940b) `[I]` | `check_rh_dispersion.py` |
| 6 | Divergent correction, Hough modes | Longuet-Higgins (1968) `[I]`; Kasahara (1976) `[R]`; Swarztrauber & Kasahara (1985) `[I]` | `check_hough_epsilon_limit.py` (5 arms) |
| 7 | Rhines scale | Rhines (1975) `10.1017/s0022112075001504` `[R]`; Vallis & Maltrud (1993) `10.1175/1520-0485(1993)023<1346:gomfaj>2.0.co;2` `[R]` | theory eq. (42)–(44). **See L6** — neither supports a jet-spacing law |
| 8 | Rayleigh–Kuo on the sphere | Kuo (1949) `[R]`; Bretherton (1966) `[R]` p. 331; Ripa (1983) `10.1017/s0022112083000270` `[I]` for the divergent case | `check_rayleigh_kuo.py` arms 1–3 |
| 9 | Linear stability EVP | Skiba & Pérez-García (2004) `[I]`; Skiba (2008) `10.1007/s10958-008-0091-3` `[I]`; Bretherton (1966) `[R]` p. 332 (critical layer) | `check_rayleigh_kuo.py` arm 4; run EVP-jet-stability. **See L1, L2** |
| 10 | Counter-propagating Rossby waves | Bretherton (1966) `[R]` p. 329 eq. (6); Hoskins et al. (1985) `[R]`; Heifetz et al. (1999) `10.1002/qj.49712556004` `[R]` p. 2838 eq. (6) | `check_crw_two_interface.py` |
| 11 | Galewsky jet and balanced IC | Galewsky et al. (2004) `10.3402/tellusa.v56i5.14436` `[R]` eqs. (2)–(4) | `tests/phase0_gate/galewsky_comparison.md`; run I-00 |
| 12 | Hypotheses-to-equations table | — | theory §12; this document |

## The three contribution areas, as narrowed

Fragment labels are those of `SCOPE_CONTRACT.md` §M2. Verdicts are from
`DIALECTIC_CHALLENGE.md`.

| Fragment | Verdict | Prior art that narrowed it | What the paper may now claim |
|----------|---------|---------------------------|------------------------------|
| a1 | Significantly narrowed | Longuet-Higgins (1968); Kasahara (1976) | The numbers for this configuration, as a solver validation target |
| a2 | Survives as practice | — | That the `ε → 0` limit was used as the target. No novelty |
| a3 | Partially narrowed | none found; classical sources unobtainable | An observation with a demonstrated mechanism, not claimed as new |
| b1 | Significantly narrowed | Kuo (1949); Skiba & Pérez-García (2004); Skiba (2008, 2024) | Application of a standard method, with the filter and plateau stated |
| b2 | Survives, heavily caveated | none found in 208 forward citations + 5 targeted searches | A negative search result, plus nondivergent modal growth rates — see L1 |
| c1 | Fully narrowed | standard practice | Nothing; the correction is performed because it is correct |
| c2 | Survives as design | — | A robustness control, not a result |
| c3 | Survives | — | The most defensible empirical fragment |
| d | Not novel — exposition | Bretherton (1966); Hoskins et al. (1985); Heifetz et al. (1999) | The exposition only |

## Structural gaps recorded rather than closed

| Gap | Status |
|-----|--------|
| Rossby (1939) and Haurwitz (1940b) are pre-DOI | Invisible to a DOI-keyed pool by construction, not by a missed search. Cited bibliographically; H1–H4 rest on internal derivation, not on these papers |
| Randel & Held (1991) or equivalent, for observed eddy phase-speed spectra | **Absent after two search rounds.** Outstanding |
| Ripa (1983), Hayashi & Young (1987), Longuet-Higgins (1968), Swarztrauber & Kasahara (1985) | Verified but unobtained. Nothing page-precise claimed from any of them |
| CFD verification-and-validation canon | Absent. Blueprint §2.3 claims V-vs-V separation as a distinguishing feature; the methodological literature for that claim is not in the corpus |
| Dealiasing rule and `ν∇⁴` hyperdiffusion choices | No supporting rows. These are the two discretisation choices a computational-physics referee reads hardest |
