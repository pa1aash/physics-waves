# Literature campaign review — operator sign-off required

**Session L4. Written 2026-07-25. Status: AWAITING SIGN-OFF.**

Self-contained: readable without any other file open. It is the thing to read
before Session L11 drafts or finalises the manuscript's Introduction, Related Work
or novelty claim.

**The short version.** The campaign built a 758-reference verified corpus and a
506-entry bibliography, and then used it to attack the project's own novelty
claims. Most of them did not survive. That is the campaign working as intended:
the project's own blueprint says at §2.3 "The contribution is not new theory", and
the first draft of this campaign's scope contract had drifted away from that. The
drift is corrected, three factual errors in the project's own records were found
and fixed, and one finding about the phase-speed campaign's design needs the
operator's attention.

---

## 1. The scope contract, and how the campaign satisfied it

The contract (`SCOPE_CONTRACT.md`) fixed three things before any retrieval: what
had to be established, what must not be chased, and five checkable exit criteria.

**What had to be established.** Grounding for the potential-vorticity spine;
grounding for the claimed contributions; and a novelty statement narrow enough to
survive a knowledgeable referee. The spine is grounded — the historical line from
Rossby and Haurwitz through Kuo to the potential-vorticity synthesis of Hoskins,
McIntyre & Robertson and the counter-propagating picture of Bretherton and
Heifetz, Bishop & Alpert is fully covered, and every one of those papers is held
and read. The contributions were established mostly by being *narrowed*: see §3.

**What must not be chased.** Four exclusions (baroclinic theory, operational
forecasting, turbulence closure, machine-learning weather models). The Step 1
critique found that two of them were secretly load-bearing — X1 excluded exactly
the observed-eddy-phenomenology literature the project's own Hayashi
decomposition needs to defend, and X3 excluded the jet-spacing literature while
theory §7 claims a terrestrial-versus-Jovian contrast. Both were rewritten with
explicit in-scope boundary cases.

**Exit criteria.** All five met, with one qualification recorded at §5:

| # | Criterion | Status |
|---|-----------|--------|
| 1 | ≥ 60 verified references, DOI resolved *and* title matched | **758** verified |
| 2 | Zero unverifiable references retained | 20 candidates dropped outright |
| 3 | Every H1–H10 and §1–§12 maps to a citation or a named internal artefact | Done in `CLAIM_MAP.md` |
| 4 | Every claim fragment has a recorded prior-art search and a verdict | Done in `DIALECTIC_CHALLENGE.md`, nine fragments |
| 5 | Every citation marked READ or IDENTIFIER-ONLY | Done; **16 READ of 758** |

## 2. Bibliography count, and hallucinated-DOI confirmation

- **`manuscript/references.bib`: 506 entries.** Requirement was ≥ 60.
- **Zero hallucinated DOIs.** Every entry traces to a row in
  `CANDIDATE_POOL.csv` carrying the query string that surfaced it and a UTC
  retrieval timestamp. Nothing was written from memory.
- **Verification was stricter than "the DOI resolves".** Each DOI was resolved
  against the Crossref work record *and* the returned title required to match the
  recorded title at ≥ 0.85 similarity. A resolving identifier proves an identifier
  exists, not that it points at the intended paper — this project has already
  shipped one file that was the wrong Haurwitz paper.
- **All 27 keys actually cited by the drafts were re-resolved live.** 26 resolve
  by DOI; 1 (Rossby 1939) is pre-DOI and carries a stable archive URL. Zero
  failures. One transient rate-limit on the Hoskins DOI resolved on retry.
- **Two entries carry a URL instead of a DOI**, and this is a deliberate,
  narrow exception: Rossby (1939) and Haurwitz (1940b) appeared in the *Journal of
  Marine Research*, which predates DOI registration. They are the origin of the
  result this paper tests; dropping them to satisfy a DOI-only rule would be worse
  than the exception. Audit check 35 accepts a DOI *or* an archive URL and would
  fail on an entry with neither.

## 3. Dialectic-challenge outcomes

The scope contract's three "contributions" were split into nine separately
challengeable fragments, because several bundled claims with very different
novelty profiles. Verdicts, with the one-line reason exactly as recorded in
`DIALECTIC_CHALLENGE.md`:

| Fragment | Verdict | Reason |
|----------|---------|--------|
| **a1** Hough-mode slowing quantification | **SIGNIFICANTLY NARROWED** | The `ε`-dependence of Hough eigenfrequencies *is* the classical Hough literature (Longuet-Higgins 1968; Kasahara 1976) |
| **a2** `ε → 0` as validation target | **SURVIVES (as practice, not a result)** | Sound verification hygiene; no prior art needed and none claimed |
| **a3** Sectoral-mode departure + mechanism | **PARTIALLY NARROWED** | Almost certainly implicit in the classical eigenstructure; the causal demonstration was not found in the corpus, but the classical sources are unread |
| **b1** Stability EVP method | **SIGNIFICANTLY NARROWED** | Skiba & Pérez-García (2004) solve a spherical normal-mode instability problem with growth rates; Kuo (1949) is the flat-plane original |
| **b2** Galewsky-jet spectrum numbers | **SURVIVES, HEAVILY CAVEATED** | No published spectrum found in 208 forward citations plus 5 targeted searches — but the project's operator is nondivergent while the jet is shallow-water |
| **c1** Doppler correction | **FULLY NARROWED — not a contribution** | Standard in space–time spectral analysis of atmospheric waves |
| **c2** Two-season ENSO design | **SURVIVES (as design, not a result)** | A robustness control the project chose; no novelty claimed |
| **c3** Westward branch resolvable at 500 hPa? | **SURVIVES** | A genuine diagnostic question with a reportable answer either way |
| **d** One-/two-interface identification | **NOT NOVEL — exposition** | Bretherton (1966) originated it; Heifetz et al. (1999) explicitly present it as pedagogy |

### What the paper originally set out to claim, versus what it may now claim

**Originally:** an internally validated quantification of the divergent
dispersion departure; a linear-stability solution closing the "necessary but not
sufficient" gap; and a two-season Doppler-corrected observational closure — three
contributions, phrased as if each were a result.

**Now:** none of those three is a contribution in the sense first written.

- The divergent-dispersion physics is classical. What remains is the numbers for
  this configuration, used as the solver's own validation target.
- The stability eigenvalue problem is a standard calculation with direct spherical
  precedent in Skiba's programme. What remains is careful application, with the
  spurious-mode filter and the growth-rate plateau stated explicitly.
- The Doppler correction is hygiene. Omitting it would be an error; performing it
  earns nothing. The two-season design is a control, not a result.

**What the paper may claim instead**, and this is what `GAP_STATEMENT.md` now
says: one mechanism carried across two regimes with one solver and one
uncertainty budget; rotation rate as a genuine free parameter over a sixteen-fold
range; verification reported separately from validation; and one narrow
observational question with a reportable answer either way. That is blueprint
§2.3's own framing, arrived at independently by adversarial search.

## 4. Full text of the gap statement

The complete document is `docs/literature/GAP_STATEMENT.md`. Its substance:

**One-sentence version.** *This paper does not contribute new theory. It
contributes a controlled, separately-verified numerical isolation of the beta
effect across the whole range from linear wave propagation to nonlinear shear
instability, in one model and one framework, with quantified numerical uncertainty
and an explicit closure against reanalysis.*

**Genuinely new** (four items): one mechanism across two regimes with one solver,
one set of conventions and one uncertainty budget, so wave and instability numbers
are commensurable — a contribution of integration, not discovery; rotation rate
swept `0.25 Ω₀`–`4 Ω₀`, turning a physical constant into an independent variable
so the `Ω` scalings are tested rather than assumed; verification reported as its
own activity, separate from validation; and the narrow question of whether a
westward barotropic branch is separable at all in reanalysis at the levels
examined, with the ERA5-versus-NCEP spread as observational uncertainty.

**Builds incrementally** on: the classical Hough eigenstructure; the `ε → 0`
verification check; the zonal-jet stability eigenvalue problem; the Galewsky
balanced initial condition; the Doppler correction; and the
counter-propagating-wave picture.

**Explicitly not claimed:** new physics; a new numerical method; the first
spherical barotropic-instability eigenvalue calculation; the first quantification
of divergent Rossby-mode dispersion; a new observational diagnostic; the
counter-propagating-wave picture; anything about baroclinic dynamics.

**Seven limitations the paper states itself** (L1–L7): the stability analysis is
nondivergent while the jet is not; a normal-mode spectrum is not a stability
proof; the initialised Rossby–Haurwitz waves may themselves be unstable; the
`ε → 0` rate is fitted three decades from where the numbers are quoted; two
classical sources central to the divergent results were never obtained; the Rhines
scale is an arrest scale and not a jet-spacing law; and the sectoral-mode result is
not claimed as new.

## 5. Coverage gaps and their disposition

| Gap | Source | Disposition |
|-----|--------|-------------|
| Skiba's spherical-instability programme absent | Step 5 | **FILLED** (gap row G1); four papers now cited; narrowed b1 |
| Ripa (1983), the divergent stability reference, absent from all 669 rows | Step 7 | **FILLED** by identifier; cited in Related Work. **Not obtained as PDF** |
| Hayashi & Young (1987) absent | Step 7 | **FILLED** by identifier. **Not obtained**; see §6 item 4 |
| No forward sweep on Williamson (1992) | Step 7 | **NOT FILLED.** A Methods-section concern; recorded for L11 |
| Randel & Held (1991) / observed eddy phase-speed spectra | Step 1 target, Step 5 | **NOT FILLED after two rounds.** Outstanding; needed to defend the Hayashi decomposition |
| Post-2010 spherical Rayleigh–Kuo treatment | Step 7 | **PARTIALLY FILLED** via Skiba and Constantin & Germain |
| Rhines scale as jet-spacing predictor: contested status | Step 7 | **ADDRESSED BY RETREAT** — the claim was withdrawn rather than sourced (L6) |
| CFD verification-and-validation canon absent | Step 7 | **NOT FILLED, recorded.** Blueprint §2.3 claims V-vs-V separation; the methodological literature is genuinely absent. A Methods decision for L11 |
| Dealiasing / hyperdiffusion-choice literature absent | Step 7 | **NOT FILLED, recorded.** Methods-section citations |
| `torch-harmonics`/SFNO primary reference absent | Step 7 | **NOT FILLED.** Data-provenance item, not Related Work |
| ML weather survey | Step 7 | **OUT OF SCOPE per X4**, acknowledgement only |
| Equatorial waveguide / Matsuno | Step 7 | **OUT OF SCOPE.** Midlatitude project; bears only on a non-load-bearing secondary argument |

## 6. Items a reviewer of this document should consciously approve

1. **Only 16 of 758 verified references were read.** The rest are
   identifier-verified. Every citation is marked, and nothing page-precise is
   claimed from an unread paper — but the ratio should be seen rather than
   discovered. In particular, **Longuet-Higgins (1968) and Swarztrauber & Kasahara
   (1985) are cited in theory §6 for "the classical formulation and its
   eigenstructure" and neither has been read.** Kasahara (1976), obtained this
   session, partially repairs this by independently confirming the branch
   structure.

2. **Three factual errors in the project's own records were found and corrected.**
   Each had been carried unchecked for several sessions:
   - **Kasahara (1976) venue was wrong** in `MISSING.md` since Session 00b —
     recorded as *J. Atmos. Sci.* 33, 408–424; it is *Mon. Wea. Rev.* 104(6),
     669–690. Wrong because the paper had never been obtained.
   - **The held Williamson PDF is ORNL/TM-11895**, an Oak Ridge technical
     memorandum, not the *J. Comput. Phys.* article the project cites. Same
     authors and title, different document and different pagination. No
     page-precise pointer is drawn from it anywhere.
   - **The Ω-sweep run IDs in theory §7.3 were wrong** — P-14–P-18 rather than
     P-08–P-12. Corrected against blueprint §8.2 and `configs/phase_speed/`.

3. **A correctness error in the theory was found and fixed this session.** Theory
   §9 described the stability eigenvalue problem as a "genuine sufficient
   computational test". That is false: the linearised operator is non-normal, so an
   all-real spectrum establishes asymptotic stability to infinitesimal normal-mode
   disturbances and does not exclude finite-time transient growth. A caveat
   paragraph was added to §9 and the claim restated. **This changes what H7 tests:
   it is a prohibition on *modal* growth only.** `theory/DERIVATION_REVIEW.md` was
   written before this correction and does not mention it.

4. **An open question that bears on H7 and could not be closed.** The Step 7
   critique reported that Hayashi & Young (1987) exhibit shallow-water shear
   instabilities with *no* potential-vorticity-gradient sign change. **That claim
   was not verified** — the paper was not obtained — and is therefore not asserted
   anywhere. If true, it bounds H7, which the blueprint calls its strongest test
   *because* it is a prohibition: the prohibition would hold for the nondivergent
   system and not necessarily for the divergent one the project integrates.
   **Recommend settling this before H7 is reported as passed or failed.**

5. **A finding that may affect the phase-speed campaign's design.** Thuburn & Li
   (2000) — held by the project since Session 00 and never extracted until now —
   show that the shallow-water zonal-wavenumber-4 Rossby–Haurwitz wave is
   dynamically unstable, breaks down when perturbed with an e-folding time of order
   1.3 days, and develops a potential-enstrophy cascade absent from the
   nondivergent case, with the outcome depending on the dissipation coefficient.
   The phase-speed campaign initialises single Rossby–Haurwitz modes and measures
   their phase speed. **The measurement window is therefore not a free choice**,
   and Williamson et al.'s selection of the wavenumber-4 wave as a test case rests
   on a stability belief since overturned. This is a scientific-design matter for
   the operator, not something this session should decide.

6. **The stability analysis is nondivergent; the runs are not.** Verified by
   inspection: `grep divergen theory/derivations.tex` returns hits in §3–§6 and
   none in §8–§9. The deformation radius is comparable to the jet width and the
   project's own §6 sizes the free-surface effect at 6–40%, yet §9 distinguishes
   `m = 6` from `m = 7` at 0.07%. Stated as limitation L1. Whether to leave it as a
   stated limitation or to extend the eigenvalue problem to the divergent system is
   an operator decision with real cost implications.

7. **The bibliography is a curated corpus, not a citation list.** 506 entries, of
   which the drafts cite 27. LaTeX emits only cited entries, so this costs nothing
   and lets L11 draw on the verified set without re-retrieving — but a reader
   opening the file should know it is deliberately a superset.

8. **Selection into the bibliography is rule-based, and the rules were wrong
   twice.** Citation-rank selection promoted "The Yamabe problem" and "4D flow MRI"
   into a geophysical bibliography; the topical filter that replaced it then
   silently dropped Skiba & Pérez-García (2004) and Constantin & Germain (2022) —
   the two strongest prior-art hits against the project's own claim — because their
   applied-maths venues were not on a whitelist. Both failures were caught and
   fixed, and the second is worth noting as a general hazard: **a relevance filter
   can quietly protect a novelty claim by discarding its counter-evidence.**

9. **A narrow relaxation of the attribution guard was authorised.** The literature
   pool CSVs contain third-party author names, several of which collide with a
   token the repository-wide guard screens for. Corrupting real author names to
   satisfy a guard would be worse than the risk. The two files are excluded from
   the blanket screen and covered instead by audit check 1b, which screens them in
   every column *except* `authors`. Recorded as authorised deviation 4 in
   `docs/CONVENTIONS.md`.

10. **No readability-for-precision trade was made.** The Step 15 pass tightened
    the physics-first framing and did not soften any limitation. If anything the
    drafts state the limitations more bluntly than a typical Introduction would.

---

## 6b. Session L4b — read this alongside, before signing off

**Session L4b ran after this document was written**, as a narrow follow-up to the
one open question the dialectic challenge could not close: whether Rayleigh–Kuo's
nondivergent necessary condition survives in the divergent shallow-water system
the project actually integrates. It **materially changes items L1, L5, b1 and
b2**, and its output should be read together with this review.

**Read `docs/literature/DIVERGENT_STABILITY_DECISION.md`.** Its recommendation, in
one line: *do not extend the stability analysis to the divergent case, because the
comparison was published in 2020 — but strengthen limitation L1, because that
published work says the project's growth rates carry a formulation bias of more
than 50% at its own layer depth.*

What changed:

| Item | Change |
|------|--------|
| **New fragment e1** | Extending the stability analysis to the divergent system: **FULLY NARROWED**, the strongest verdict any fragment has received. Paldor, Shamir & Garfinkel (2020), *GAFD* 115(1), 15–34, publish exactly that comparison for a spherical jet; White & Staniforth (2009) already apply Ripa's criteria on the sphere to guide numerical model testing |
| **L1** | Was a scoping statement; is now a **sized, cited bias**. The reported growth-rate precision must drop: `m = 6` versus `m = 7` at 0.07% is not meaningful inside a >50% formulation bias |
| **L5** | Two of the four unobtained sources are now **ABSTRACT-VERIFIED**, a status this project did not previously have. Ripa's conditions were extracted and shown to reduce cleanly to Rayleigh–Kuo in the nondivergent limit |
| **b1** | Verdict unchanged, but now rests on **governing equations** named in abstracts rather than on titles: all five papers in the Skiba/Constantin–Germain/Cao–Wang programme are nondivergent |
| **b2** | Weakened further, for the reason under L1 |
| **Open questions 1 and 3** | **Resolved.** Hayashi & Young's counterexample is real but equatorial and does not reach this configuration; Ripa's conditions add a gravity-wave criticality condition satisfied here with a 7.8× margin |

**One item added to §6 of this document by L4b:** the highest-value literature
action remaining in the project is obtaining Paldor, Shamir & Garfinkel (2020). It
is bronze open-access — free to read in a browser, blocked to scripted retrieval —
and its >50% figure is currently cited from the authors' own conference abstract
rather than from the journal text. That figure should be checked against the
published paper before it reaches the manuscript.

---

## 7. Closing statement

```
THIS DOCUMENT REQUIRES OPERATOR SIGN-OFF BEFORE SESSION L11 MAY BEGIN
DRAFTING OR FINALISING THE MANUSCRIPT'S INTRODUCTION, RELATED WORK, OR
NOVELTY CLAIM. THE BIBLIOGRAPHY AND DRAFTS PRODUCED IN THIS SESSION MAY
STILL BE READ AND REFERENCED BY OTHER SESSIONS, BUT THE GAP STATEMENT
ITSELF IS NOT FINAL UNTIL THIS REVIEW HAS BEEN READ AND EXPLICITLY
APPROVED BY THE OPERATOR.
```
