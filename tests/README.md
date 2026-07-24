# tests/

Repository tests. `test_environment.py` asserts the solver stack imports and is
MPI-capable; `test_repo_hygiene.py` asserts no forbidden attribution strings, that
tooling files are gitignored, and that every commit author is Palaash Gang. Run
with `make test`.
