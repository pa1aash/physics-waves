# Makefile for the physics-waves project.
# Every target that produces tracked files ends by invoking the commit-and-push
# helper so that provenance is never left uncommitted.

SHELL := /bin/bash
COMMIT := bash scripts/autocommit.sh

.PHONY: env lock test hooks data data-ncep data-era5 data-torch licenses \
        audit sync clean reproduce help

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

data-ncep: ## fetch NCEP/NCAR Reanalysis 1 (D3)
	python src/data/fetch_ncep.py
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

sync: ## mirror the working tree to the compute pod
	bash scripts/sync_pod.sh

clean: ## remove Python caches and scratch
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache scratch

reproduce: ## regenerate the figure set (available from Phase 10)
	@echo "available from Phase 10"
