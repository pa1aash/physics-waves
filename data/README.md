# data/

Data root. `external/` holds unmodified external downloads (reanalysis, D1–D4);
`raw/` holds immutable simulation output by run ID; `reference/` holds L3
reference solutions; `processed/` holds derived quantities and result tables. The
binary contents of these directories are never committed — only fetchers,
manifests and checksums are. Reproduce downloads with `make data`.
