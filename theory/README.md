# theory/

The theoretical backbone of the project.

`derivations.tex` carries the full derivation in twelve sections, built on one
statement — material conservation of potential vorticity on a rotating, curved
surface, `Dq/Dt = 0` with `q = (ζ + f)/h`. Wave propagation and shear
instability are developed as the *same* mechanism seen at one potential-vorticity
interface and at two; the framing is recorded in `docs/CONVENTIONS.md` under
"Theoretical framework: the spine".

| Path | What it is |
|------|------------|
| `derivations.tex` | The derivation. Standalone LaTeX with its own preamble; Session L11 folds it into the Springer Nature class. |
| `sympy_checks/` | One executable check per derived result, with recorded verdicts in `sympy_checks/output/`. See its README. |
| `figures/` | The two conceptual schematics (F1, F2) and the script that generates them. |
| `DERIVATION_REVIEW.md` | The operator sign-off document. **Read this before treating anything here as ground truth.** |

## Building the PDF

    make manuscript          # -> theory/derivations.pdf

`scripts/build_manuscript.sh` falls back to this file until Session L11 produces
the real manuscript. The output PDF is a build artifact and is gitignored; the
source is what is tracked.

**Compile status (2026-07-25).** Builds clean with pdfTeX (TeX Live 2026), 19
pages: no errors, no undefined references, no undefined citations, no overfull
boxes. Packages used are all standard (`amsmath`, `amssymb`, `booktabs`,
`longtable`, `natbib`, `hyperref`, `geometry`).

## Regenerating the figures

    python theory/figures/make_schematics.py

Both figures are drawn programmatically through `src/figures/style.py`, so they
carry the same house typography and the same provenance sidecar as every later
data figure. They contain no data — they are schematics of the derivation.

## References

Eleven works are cited. Nine carry DOIs, all of them confirmed registered
against the Crossref REST API; two (Rossby 1939 and Haurwitz 1940, both
*Journal of Marine Research*) predate DOI registration and are archived by Yale
University Library instead.

Note for Session L4, which builds `manuscript/references.bib`: two of the nine
DOIs are AMS legacy identifiers,

    10.1175/1520-0469(1949)006<0105:DIOTDN>2.0.CO;2
    10.1175/1520-0485(1993)023<1346:GOMFAJ>2.0.CO;2

and the publisher answers an unauthenticated `HEAD` request to them with
HTTP 403. `scripts/refcheck.py` treats any status of 400 or above as a failure,
so it will flag these two even though both are registered and both resolve in a
browser. That is a false negative in the checker, not a bad citation.

## Status

**AWAITING OPERATOR SIGN-OFF.** `derivations.tex` must not be consumed as ground
truth by any later session until `DERIVATION_REVIEW.md` has been read and
explicitly approved.
