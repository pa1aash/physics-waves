# configs/

One YAML file per run is the single source of truth for that run, and every file
validates against `_schema.yaml`. Subdirectories group runs by campaign:
`verification/`, `phase_speed/`, `instability/`, `evp/`. `RUN_REGISTRY.md` is the
master index of every run ID. A run parameter is never set by editing a script.
Stubs are created in Session 00 and finalised as each campaign is executed.
