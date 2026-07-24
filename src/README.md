# src/

Project source. `solver/` sets up the equations, run harness and eigenvalue
problems; `diagnostics/` defines runtime diagnostics; `analysis/` implements the
post-processing pipeline (blueprint §12); `figures/` produces the publication
figure set; `data/` holds the external-dataset fetchers. Most modules are stubs
until Sessions L5/L6; the `data/` fetchers and `figures/style.py` are implemented
now.
