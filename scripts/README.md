# scripts/

Project infrastructure. Not scientific code — the physics lives in `src/`.

**Campaign execution** (Session L7a; see `docs/CONVENTIONS.md`, "Sweep
execution"). `sweep.py` plans a campaign — validates every config and scales its
output cadences to its rotation rate and mode — and writes a plan file without
executing anything. `run_mpi.sh` runs one config under MPI. `resume_check.py`
finds runs that did not finish and archives them so their IDs are free.
`cost_log.py` derives core-hours from provenance and updates `docs/COMPUTE.md`.
`sync_pod.sh push` sends code to the pod; `sync_pod.sh pull <RUN_ID>` brings one
run's output back, since `runs/` is gitignored and has no other route.

**Environment and provisioning.** `env.sh` sets the threading hygiene that must
be sourced before any run — an oversubscribed run does not fail, it quietly
produces wrong timing data. `pod_bootstrap.sh` provisions the compute pod.
`setup_cds_credentials.sh` configures the reanalysis data client.

**Configs and literature.** `resolve_configs.py` re-derives every
solver-dependent config value from its stated policy. `lit_sweep.py`,
`lit_curate.py`, `lit_verify.py` and `lit_bib.py` build the literature pool;
`refcheck.py` checks citation keys resolve to bibliography entries with live
DOIs.

**Repository hygiene.** `audit.sh` runs the compliance checks (`make audit`),
`verify.sh` runs the full suite, `build_manuscript.sh` builds the PDF,
`autocommit.sh` is the commit-and-push helper, and `hooks/commit-msg` is the
attribution guard.
