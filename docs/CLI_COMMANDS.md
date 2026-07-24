# Operational commands

This is the project's operational surface. **Every capability here is a tracked
`make` target.** The optional editor slash-command wrappers (kept in a
gitignored, tool-local commands directory) do nothing but call the corresponding
target. Anyone who clones this repository — with or without any editor
integration — can run every `make` target below and get the identical result;
the reproducibility of this project never depends on any particular editor or
tool.

| Command | `make` target | Status (this session) | Completed by |
|---------|---------------|-----------------------|--------------|
| `/verify` | `make verify` | **Fully implemented** | — |
| `/refcheck` | `make refcheck` | **Partially implemented** (works now; full power once a real `.bib` exists) | Session L4 |
| `/manuscript` | `make manuscript` | **Partially implemented** (compiles whatever LaTeX exists now; full build with the Springer manuscript) | Session L11 |
| `/figure` | `make figure` | **Stub** (a style-preview mode works now) | Session L10 |
| `/sweep` | `make sweep` | **Stub — explicit NotImplemented** | Sessions L5 / L7 |

A stub is never a silent no-op: it prints which future session completes it and
exits non-zero, so invoking it early produces an informative message rather than
the appearance of nothing having happened.

## `make verify` → `scripts/verify.sh` — fully implemented

Runs, in order, and reports one consolidated result:

1. `make audit` — every accumulated repository-compliance check.
2. `pytest tests/` — the full test suite.
3. A check that `docs/CONVENTIONS.md`'s "Phase 0 gate" record still reads
   **PASSED** — i.e. the toolchain validation has not since been broken.

Exits non-zero if any of the three fails, naming which one. Its power grows
automatically as later sessions add audit checks and tests — it only calls those
two entry points, so it never needs its own list maintained.

**Expected output shape:** three labelled `[verify] audit … OK/FAIL`,
`[verify] tests … OK/FAIL`, `[verify] phase-0 gate … OK/FAIL` lines, then a
final `VERIFY: PASSED` / `VERIFY: FAILED (<stage>)` line and matching exit code.

## `make refcheck` → `scripts/refcheck.py` — partially implemented

Takes a `.tex` file (default `theory/derivations.tex`), extracts every
`\cite{...}` key, and for each looks up a matching entry in
`manuscript/references.bib`. For each match it confirms a `doi` field is present
and — network permitting — resolves it with an HTTP HEAD against
`https://doi.org/<doi>`. Flags: citation keys with no bibliography entry; entries
missing a DOI; DOIs that fail to resolve. With no argument it summarises across
every `.tex` file in `theory/` and `manuscript/`.

`manuscript/references.bib` does not exist yet (Session L4 creates it); until
then `refcheck` reports "no bibliography file found yet; nothing to check" and
exits 0 — not a tool failure, just nothing yet to check.

**Expected output shape:** per-file `[refcheck] <file>: N citations, …` lines
listing any unresolved keys / missing DOIs / dead DOIs, then a summary line and a
non-zero exit only if a genuine inconsistency is found (missing entry, missing or
dead DOI).

## `make manuscript` → `scripts/build_manuscript.sh` — partially implemented

Looks for `manuscript/main.tex` first; if absent (true until Session L11), falls
back to compiling `theory/derivations.tex` standalone and says clearly that this
is a fallback, not the real manuscript build. Reports compile success/failure and
the output PDF path.

**Expected output shape:** a `[manuscript] building <file> (fallback: …)` line,
the compiler result, and the output PDF path or a clear failure message.

## `make figure` → `src/figures/make_figures.py` — stub (style-preview works)

The full figure pipeline arrives in Session L10. Now, `--style-preview` renders
one small synthetic placeholder plot (a sine curve — nothing physical) in the
house style, so the visual language (fonts, colours, sizing) can be checked now
rather than nine sessions later. Without the flag it prints the standard
"not implemented until Session L10" message and exits non-zero.

**Expected output shape:** with `--style-preview`, a saved preview-PNG path and
exit 0; without it, the "implemented in Session L10" message and a non-zero exit.

## `make sweep` → Makefile stub — explicit NotImplemented

Prints that the run-configuration system and harness arrive in Session L5 and the
pod sweep generator in Session L7, then exits non-zero. No hidden behaviour.

**Expected output shape:** the two-line "NOT YET IMPLEMENTED" message and exit 1.
