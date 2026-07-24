"""Pipeline stage 9: zonal-mean jet, Rayleigh-Kuo diagnostic, observed spectra, drift.

Blueprint sections 7.3 and 12.

Observational phase-speed comparison MUST follow the Doppler-correction
convention (docs/CONVENTIONS.md, "Observational comparison: Doppler correction").
In brief: the observed 500 hPa height field is advected by the jet and propagates
eastward relative to the ground, whereas the model measures the *intrinsic*
Rossby speed in a resting mean flow. Decompose the observed field in
wavenumber-frequency (Hayashi) space (not a simple time high-pass), isolate the
westward branch if it resolves, and compare `c_intrinsic = c_ground - ū` against
the model prediction — never the raw ground-relative speed. Propagate the
two-season spread of `ū` into the uncertainty. Read that section before
implementing.
"""

# Implementation: Session L6
