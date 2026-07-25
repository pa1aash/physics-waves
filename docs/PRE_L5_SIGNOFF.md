# Pre-L5 consolidation — combined sign-off

**Session PRE-L5. Written 2026-07-25. Status: AWAITING OPERATOR SIGN-OFF.**

**This is the one document to read before Session L5 begins.** It replaces three
separate pending gates with one, because the three documents behind them are now
mutually consistent and `theory/derivations.tex` has been reconciled to match
them.

---

## 1. What changed in this session

No new research, no new derivation. Four reconciliations.

**The §9 correction was confirmed, not re-applied.** Two prior operator exchanges
flagged that `theory/DERIVATION_REVIEW.md` might predate a correction to
`theory/derivations.tex` §9 — the claim that the stability eigenvalue problem was
a "genuine sufficient computational test", which is false for a non-normal
operator. This session checked rather than assumed: `git log -S` shows the phrase
introduced in `b12eaa7` and removed in **`00a7524`**, with the replacement
non-normality caveat added in the same commit. The correction was real and is in
place. One gap did remain and was closed here — the scoping had never propagated
to the **H7 row of §12's hypothesis table**, which still read as an unqualified
prohibition. It now states that H7 forbids a growing normal mode, not finite-time
transient amplification.

**The precision downgrade is now in the theory document, not only around it.**
`derivations.tex` §9 previously justified reporting a plateau instead of a sharp
`m*` on the grounds that a 0.07% separation is small against base-state
uncertainty. That reasoning was overtaken by Session L4b. The section now states
directly, in the running text, that the eigenvalue problem is nondivergent while
the jet is not; that Paldor, Shamir & Garfinkel (2020) measure the resulting bias
at more than 50% for depths of 5–10 km with the nondivergent calculation
*overestimating*; and that discriminating two wavenumbers at sub-per-cent
separation inside a bias two orders of magnitude larger is arithmetic, not
physics. It also now carries Ripa's two conditions with their actual content, and
one cited sentence saying the nondivergent scope is a considered decision rather
than an oversight.

**Paldor, Shamir & Garfinkel remains unobtained — but its provenance improved.**
The journal PDF is still blocked to scripted retrieval. However the **published
abstract** was obtained this session, superseding L4b's reliance on the authors'
conference abstract. That upgrade also surfaced a qualification L4b did not have:
**their jets are polar and equatorial**, not mid-latitude like this project's.
The >50% figure is therefore propagated as an order-of-magnitude indication that
the bias is large and one-signed, not as a calibration constant. That
qualification is now stated identically in `derivations.tex`, `GAP_STATEMENT.md`
and `DIVERGENT_STABILITY_DECISION.md`.

**The two provenance ledgers are now one.** `theory/PROVENANCE_AUDIT.md` gained
`ABSTRACT-VERIFIED` and `TITLE-ONLY` as explicit categories alongside `READ`,
`DOI-ATTRIBUTED` and `INTERNAL`, each defined by what it *licenses* rather than
just what it means, and every citation Session L4b examined now has a row there.
There is one place in the repository that answers "how do we know this citation
says what we say it says."

---

## 2. The three documents, and their consistency

| Document | Status | Consistent with the other two, and with `derivations.tex`? |
|----------|--------|------------------------------------------------------------|
| `theory/DERIVATION_REVIEW.md` | Accurate; **superseded for sign-off purposes** by this document. Carries a new "Reconciliation notes" section recording the §9 confirmation, the item-(e) supersession, and the provenance merge | **Yes.** Its ten-item disposition table is unchanged and still correct; item (e)'s *conclusion* (report a plateau) stands, while its *reasoning* is now correctly attributed to the formulation bias rather than to base-state uncertainty |
| `docs/literature/LITERATURE_REVIEW.md` | Accurate; **superseded for sign-off purposes**. Its §6b already directs the reader to the divergent-stability decision | **Yes.** Its nine-fragment verdict table and the e1 verdict in `DIALECTIC_CHALLENGE.md` agree; L1 and L5 in `GAP_STATEMENT.md` now carry the same numbers and the same two qualifications as `derivations.tex` |
| `docs/literature/DIVERGENT_STABILITY_DECISION.md` | Accurate; **superseded for sign-off purposes**. Recommendation unchanged: **Option B**, do not extend | **Yes.** Its recommendation is now implemented in `configs/evp/EVP-jet-stability.yaml` and `configs/RUN_REGISTRY.md`, so Session L5 and R4 inherit the decision rather than re-litigating it |

**What "consistent" was checked to mean here**, concretely: the same three claims
— that the EVP is nondivergent, that the bias is >50% and one-signed at this
depth, and that the jets in the source paper are polar and equatorial — appear in
the same form in all four files, and `derivations.tex` compiles clean (22 pages,
no undefined references, no undefined citations, no overfull boxes) with all 15
of its citation keys resolving.

---

## 3. What remains knowingly open

Each with why it is acceptable to proceed.

**Longuet-Higgins (1968) and Swarztrauber & Kasahara (1985) — unobtained.**
Status `DOI-ATTRIBUTED`. Both are closed-access with no open-access copy indexed
anywhere. **Acceptable because** nothing in the derivation depends on their
contents: they are cited in §6 for historical attribution of the classical
formulation, while the project derives the Hough eigenvalue problem itself and
validates it against the `ε → 0` limit it derives independently. Kasahara (1976),
obtained in Session L4 and read, independently confirms the branch structure. The
mitigation has been recorded since Session 00b and is unchanged.

**Randel & Held (1991), or an equivalent observed eddy phase-speed anchor —
absent.** Sought across two search rounds in Session L4 and not found.
**Acceptable because** it bears on fragment c3, the observational comparison,
which no session has yet run. It is needed when the reanalysis-comparison session
happens — to defend the Hayashi decomposition rather than merely assert it — and
not before. Session L5 writes the solver and does not touch it.

**Paldor, Shamir & Garfinkel (2020) — `ABSTRACT-VERIFIED`, full text
unobtained.** *Geophysical & Astrophysical Fluid Dynamics* **115**(1), 15–34,
DOI `10.1080/03091929.2020.1724996`, at
`https://www.tandfonline.com/doi/full/10.1080/03091929.2020.1724996`. It is
**bronze open-access — free to read in a browser** — but Cloudflare blocks
scripted retrieval; three routes were tried across two sessions. **This is a
one-click manual action, not a research gap.** Acceptable to proceed because the
claim drawn from it is one the published abstract makes in its own words, and it
is used qualitatively — the bias is large and one-signed — rather than as a
number the project calibrates against. If it is obtained, the two qualifications
in §1 should be checked against the body, and its status upgraded to `READ`
in `theory/PROVENANCE_AUDIT.md`, `derivations.tex`, `GAP_STATEMENT.md` and
`DIVERGENT_STABILITY_DECISION.md`.

**Ripa (1983) and Hayashi & Young (1987) — `ABSTRACT-VERIFIED`.** Both closed
with no open-access copy. **Acceptable because** the claims drawn from them are
claims their abstracts state explicitly, no equation-precise pointer is taken
from either, and the translation of Ripa's conditions into inequalities is
flagged as the project's reading wherever it appears. The margin calculation that
depends on it is robust by a factor of about eight, so it survives a considerable
misreading.

**Two Skiba papers are `TITLE-ONLY`.** Skiba (2008) supports no claim at all and
is listed only for completeness of the programme; Skiba (2024) is taken to work
in the barotropic vorticity equation because its title names that equation.
**Acceptable because** the conclusion they contribute to — that the
Skiba/Constantin–Germain/Cao–Wang programme is uniformly nondivergent — rests on
the three `ABSTRACT-VERIFIED` members, not on these two.

**Commit granularity.** Parts 1 and 2 of this session landed in a single commit
(`7f7ff67`) rather than the two the brief specified. All content is present and
pushed; pushed history was not rewritten to re-split it.

---

## 4. Closing statement

```
THIS DOCUMENT REQUIRES OPERATOR SIGN-OFF BEFORE SESSION L5 MAY BEGIN.
IT SUPERSEDES SEPARATE SIGN-OFF OF DERIVATION_REVIEW.MD, LITERATURE_REVIEW.MD,
AND DIVERGENT_STABILITY_DECISION.MD INDIVIDUALLY — APPROVING THIS DOCUMENT
APPROVES ALL THREE TOGETHER, SINCE THEY ARE NOW MUTUALLY CONSISTENT AND
DERIVATIONS.TEX HAS BEEN RECONCILED TO MATCH THEM.
```
