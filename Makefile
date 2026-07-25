# Makefile for the physics-waves project.
# Every target that produces tracked files ends by invoking the commit-and-push
# helper so that provenance is never left uncommitted.

SHELL := /bin/bash
COMMIT := bash scripts/autocommit.sh

# NCEP/NCAR winter(s) to acquire. Never hard-coded in the fetcher: override on
# the command line, e.g. `make data-ncep YEARS="2013 2014"`.
YEARS ?= 2015 2016

# Argument passthroughs for the operational commands (see docs/CLI_COMMANDS.md).
FILE ?=
ARGS ?=

# Run configuration for `make run`. No default: a run must be named explicitly,
# because "configs are the single source of truth" only means anything if the
# config is chosen deliberately.
CONFIG ?=

.PHONY: env lock test hooks data data-ncep data-era5 data-torch licenses \
        audit sync clean reproduce help verify refcheck manuscript figure sweep \
        run configs

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

env: ## create the pinned conda environment (name: pw)
	mamba env create -f environment.yml || conda env create -f environment.yml

lock: ## regenerate the byte-level environment lock and commit it
	conda env export --no-builds > environment.lock.yml
	$(COMMIT)

test: ## run environment + repository-hygiene tests
	pytest tests/ -v

hooks: ## install the git and pre-commit hooks
	cp scripts/hooks/commit-msg .git/hooks/commit-msg
	chmod +x .git/hooks/commit-msg
	pre-commit install
	pre-commit install --hook-type commit-msg

data: data-ncep data-era5 ## fetch the default external datasets (D1-D3)

data-ncep: ## fetch NCEP/NCAR Reanalysis 1 (D3); pick winters with YEARS="2013 2014"
	python src/data/fetch_ncep.py --years $(YEARS)
	$(COMMIT)

data-era5: ## fetch ERA5 monthly + daily fields (D1, D2)
	python src/data/fetch_era5.py
	$(COMMIT)

data-torch: ## fetch the optional torch-harmonics cross-check (D4)
	python src/data/fetch_torch_harmonics.py --include-d4
	$(COMMIT)

licenses:
	curl -fsSL https://creativecommons.org/licenses/by/4.0/legalcode.txt -o LICENSE-DATA.full
	@test -s LICENSE-DATA.full || (echo "fetch failed" && exit 1)

audit: ## run the repository compliance audit
	bash scripts/audit.sh

verify: ## run the full verification suite (audit + tests + Phase-0 gate record)
	bash scripts/verify.sh

refcheck: ## check \cite keys resolve to bib entries with live DOIs; `make refcheck FILE=x.tex`
	python scripts/refcheck.py $(FILE)

manuscript: ## build the manuscript PDF (falls back to theory/derivations.tex until L11)
	bash scripts/build_manuscript.sh

figure: ## figure pipeline (L10); preview now with `make figure ARGS=--style-preview`
	python src/figures/make_figures.py $(ARGS)

run: ## integrate one run: `make run CONFIG=configs/verification/V-02.yaml [ARGS=--dry-run]`
	@test -n "$(CONFIG)" || (echo "usage: make run CONFIG=configs/<campaign>/<ID>.yaml" && exit 2)
	python -m src.solver.harness $(CONFIG) $(ARGS)

configs: ## re-derive every solver-dependent config value from the stated policy
	python scripts/resolve_configs.py $(ARGS)

sweep:
	@echo "NOT YET IMPLEMENTED."
	@echo "One run at a time works now: make run CONFIG=configs/<campaign>/<ID>.yaml"
	@echo "The multi-run pod sweep generator arrives in Session L7."
	@exit 1

sync: ## mirror the working tree to the compute pod
	bash scripts/sync_pod.sh

clean: ## remove Python caches and scratch
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache scratch

reproduce: ## regenerate the figure set (available from Phase 10)
	@echo "available from Phase 10"
