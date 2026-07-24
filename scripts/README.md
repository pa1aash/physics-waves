# scripts/

Project infrastructure. `env.sh` sets threading hygiene sourced before any run;
`sync_pod.sh` mirrors the working tree to the compute pod; `audit.sh` runs the
compliance checks (`make audit`); `autocommit.sh` is the commit-and-push helper;
`hooks/commit-msg` is the attribution guard. Not scientific code.
