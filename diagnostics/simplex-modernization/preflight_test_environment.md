# Standard test-environment repair

Date: 2026-09-22. Parent: 4044834. Julia: 1.13.0, aarch64 Linux.

The preparation failure is reproduced: `Pkg.test()` reported 183,653 passes,
zero failures, and one error. `test/runtime_lookup_tests.jl:1` imports
LinearAlgebra, which was missing from the isolated test project's dependencies.
Direct inclusion of the suite had made the library available through the main
project and therefore did not expose this declaration error.

Added LinearAlgebra, Logging, and Random to `test/Project.toml`, matching the
existing direct imports in the test suite. No numerical implementation, test
expectation, production dependency, or tolerance changed.

Validation command (full output captured locally):

```bash
JULIA_DEPOT_PATH=/tmp/jsimplex-modernization-depot:/home/jspitz/.julia JULIA_PKG_OFFLINE=true /home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/bin/julia --startup-file=no --project=. -e 'using Pkg; Pkg.test()'
```

Result: exit 0; 224,921/224,921 checks passed in 7m54.3s.
`pathof(JSimplex)` was separately verified to point into this worktree.
The root Manifest was recreated from the available local cache and is not
included in this commit. The isolated tests now reproduce the successful
direct-run count recorded during planning.

Full local logs are in the ignored plan workspace at
`.superpowers/sdd/2026-09-22-simplex-modernization/preflight-pkg-test.log`
and `preflight-pkg-green.log`. Initial F01 files are under development and
are not part of this preliminary commit or this validation claim.
