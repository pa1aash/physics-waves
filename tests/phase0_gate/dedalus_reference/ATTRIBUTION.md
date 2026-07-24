# Attribution — upstream Dedalus reference example

This directory contains **unmodified upstream example code from the Dedalus
Project**, reproduced here only to make the project's Phase-0 toolchain
verification reproducible. **It is not part of this project's own MIT-licensed
source** (`src/`, `configs/`, `scripts/`, `tests/` outside this directory). It is
third-party code carrying its own, different licence, isolated in this directory.

## Licence

- **Name:** GNU General Public License, version 3 (**GPL-3.0**).
  Confirmed two ways: the installed package metadata (`pip show dedalus` →
  `License: GPL3`, author Keaton J. Burns) and the first line of the fetched
  licence file (`LICENSE.dedalus` → "GNU GENERAL PUBLIC LICENSE").
- **Full text:** bundled verbatim as [`LICENSE.dedalus`](LICENSE.dedalus) in this
  directory (35,149 bytes), as GPL-3.0 requires the licence to accompany the
  code. Canonical copy: <https://www.gnu.org/licenses/gpl-3.0.txt>.
- **Upstream project:** the Dedalus Project — <http://dedalus-project.org>,
  source <https://github.com/DedalusProject/dedalus>.

Because these files are GPL-3.0, they are kept in this clearly-labelled,
self-contained directory and are **not** mixed into the MIT-licensed project
source. Nothing in `src/` imports from here; the project's own solver
(Session L5 onward) is written independently.

## Provenance — why fetched from upstream rather than `get_examples`

The intended mechanism is `python3 -m dedalus get_examples`, which extracts the
example set bundled with the installed package. **On this conda-forge build of
Dedalus 3.0.5 the bundled `examples.tar.gz` is empty** — it is a 58-byte gzip
that decompresses to a single empty tar block (zero entries), so `get_examples`
produces no files. The examples were therefore fetched, **unmodified**, from the
upstream repository at the git tag matching the installed version (`v3.0.5`), so
they are still guaranteed to match the installed 3.0.5 API rather than a drifted
documentation snapshot.

| File | Bytes | SHA-256 | Source (raw, tag `v3.0.5`) |
|------|-------|---------|----------------------------|
| `shallow_water.py` | 3318 | `4ed791e00f1678e355a0f0828028654d1f57beba2cb466bddb4afdcb8284a945` | `examples/ivp_sphere_shallow_water/shallow_water.py` |
| `plot_sphere.py` | 2941 | `5868b88c87bf70b771eaec98b0d1de3d361434fc38ea887dd1d5b8d283acf136` | `examples/ivp_sphere_shallow_water/plot_sphere.py` |
| `LICENSE.dedalus` | 35149 | `ba43a020cc332820987ecdb071b4b46e61e7ed1b76ce5e9b707221f330363409` | `LICENSE.txt` |

Base URL: `https://raw.githubusercontent.com/DedalusProject/dedalus/v3.0.5/`.
Retrieved 2026-07-25. The `shallow_water.py` docstring itself states it implements
the Galewsky et al. (2004) barotropically-unstable mid-latitude jet
(<https://doi.org/10.3402/tellusa.v56i5.14436>).

**These files must not be edited.** The Phase-0 gate runs them exactly as shipped;
any modification would defeat the purpose of validating the toolchain against
unmodified upstream code. A resolution-reduced *copy* for timing only lives
outside this directory as `shallow_water_L0.py`, clearly labelled.
