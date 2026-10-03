# Public Huangfu–Hall basis updates

## Selected implementation

Promotion starts from master `b0d2afb` and the recommended diagnostic manager at
`6089f7c`. It imports no experimental triangular-manager changes. The original
PFI manager remains available and remains the default. Select the independent
middle-product-form manager with `basis_update=:huangfu_hall`, including through
`MOI.RawOptimizerAttribute("basis_update")`.

Included improvements, in their original sequence:

- Allocation-light update packing and reusable native LU workspace (`7776c8d`).
- Reachable preparation of the unit transpose solve U^(-T)e_p (`bc7b416`).
- Scaling verification without temporary absolute-value matrices (`db9311d`).
- Bounded recycling of retired, unshared update buffers (`456a844`).
- Bounded native factor-extraction scratch (`6089f7c`).

Excluded: copy-free prepared-direction packing (`2ea1ef5`) and sparse ordinary
FTRAN/BTRAN (`04be158`). Their mixed/negative timings do not justify promotion.
The implementation follows Huangfu and Hall, ERGO-13-001, section 3.1.2:
https://webhomes.maths.ed.ac.uk/hall/HuHa12/ERGO-13-001.pdf.

## Public contract and integration

The supported combination is Float64, native UMFPACK and 64-bit machine indices.
Input CSC indices are normalized to machine Int, matching the existing native
backend. Other public scalar/backend combinations raise ArgumentError before
factorization. MOI uses the same option validation, including transactional
rejection of unsupported attribute changes. Both public simplex algorithms and
strategies are supported; the manager does not change their policies.

Compared with the selected diagnostic source, integration adds factory dispatch,
option validation, index normalization and numerical-error classification. Internal
arithmetic rejection uses the existing recoverable numerical exception. Invalid
caller inputs remain argument errors. Extracted factors remain independent of the
mutable native scratch, including after failed refactors and saved copies.

The internal hypersparse pipeline deliberately falls back to the existing dense
MPF kernels, including aliased input/output. Precision transfer rejects a change
away from Float64. Explicit internal precision-boosting or LP-refinement policies
are rejected at solve entry; there is no silent precision or manager substitution.

## PrecompileTools coverage

The synthetic solver workload covers native refactorization with Float64 and
Float32 for all four original managers, both simplex algorithms and presolve
on/off. Markowitz is covered through its shared factorization, refactorization,
forward-solve and transpose-solve operations for both scalar types, exercising
sparse pivots and the dense trailing core. Complete Markowitz simplex entry-point
specializations remain compiled on demand.
Huangfu–Hall participates only in its supported Float64/native combination
on 64-bit platforms. Every workload solve asserts the optimum and original primal
feasibility. Neither the workload nor the public manager changes global precision
or thread settings. The new public manager is not automatically selected.

Local checkout preferences continue to disable workloads. Cache validation uses
an independent active environment pointing to this worktree with its own enabling
preference. That environment, its manifest, and compiled caches are not committed.

## Verification

- The selected 1,823 manager component assertions passed with normal compilation,
  including allocation, copy/alias, failure-isolation, signed-zero, scale and retained
  memory checks. Public selection added 22 assertions; initial integration added
  54 public-solve/MOI assertions and 11 boundary assertions (1,910 total).
- The broader semantic batch passed 11,618 assertions with `--compile=min`,
  including the additional explicit hypersparse-availability boundary check.
- The whole `test/runtests.jl` attempt hit its 600-second guard in LLVM while
  compiling `dual_entry_phase_tests.jl:15`. That file passed in the semantic batch.
- A separate normal-compilation batch hit its 600-second guard in LLVM while
  compiling `markowitz_tests.jl:211` (the all-scalar solver matrix). Neither timeout
  is a completed or passing test suite, nor an observed numerical assertion failure.

The first enabled cache attempt exhausted the 8 GiB virtual limit in LLVM native
image emission. The old generic cache measurement script
returned exit zero despite that compiler failure; this is explicitly a FAILED
cache attempt. A subsequent import tried to build it again and was stopped by the
controller before accepting any timing results. The dedicated cache builder now
uses strict error handling and asserts `Base.isprecompiled` before saving success.
A first retry applied `--heap-size-hint=2G` to the compiler worker without changing
optimization/cache flags. That retry was deliberately stopped when the user
authorized a 16 GiB compilation limit; it is not a failed or successful cache build.
The subsequent build uses the authorized 16 GiB limit, retains the GC hint and
keeps the available-RAM/swap safeguards. After stopping the earlier coordinating
process, its compiler child was found still finishing code emission and was
explicitly terminated before further validation; only the tracked owned process
was signaled. Subsequent process checks confirm one compiler worker.

The 16 GiB build also failed in LLVM register allocation during native image
emission after 1,248.51 seconds wall time, with 16,157,392 KiB peak RSS (15.41 GiB)
and no swap. The strict builder returned exit 1 and produced no success report.
This is a compiler resource failure, not a numerical assertion failure.

Two bounded direct-compiler tracing probes did not reach the offending native-image
function before their 600-second guards; neither produced a successful cache. The
first reduced matrix limited complete Markowitz solves to Float64 (13 combinations
instead of 17). It still exhausted 16 GiB in LLVM machine-instruction scheduling
after 1,044.44 seconds, with 16,178,680 KiB peak RSS. Restricting that scalar matrix
was not sufficient. The selected workload keeps the complete native solver coverage
and adds shared Markowitz backend operations, avoiding the additional complete
simplex specializations. This changes cache coverage, not supported solver modes.
The exact pathological LLVM function was not identified; no compiler-root-cause
fix or change to numerical kernels is claimed. This smaller backend workload also
failed at the 16 GiB ceiling after 754.32 seconds, peaking at 16,174,612 KiB RSS.
Unlike the broader matrices, its failure was during final DWARF line-table emission.
Successful validation uses `-g0` (no debug information) at unchanged `-O2`,
with matching flags for cache construction and reuse. Default `-g1` cache generation
failed within 16 GiB for this source on this machine; a reusable default cache was
not validated.

The `-g0 -O2` build succeeded in 680.38 seconds (684.28 seconds wall time), with
13,478,044 KiB peak RSS (12.85 GiB), one worker/image thread, and no swap. A fresh
process verified the loaded checkout and reusable cache. Its 18 sequential native
solves took 0.0224941 seconds in total, including 0.0206683 seconds of compilation;
Huangfu–Hall primal/dual took 0.0026421/0.0000344 seconds. All four Markowitz backend
cases passed; the 16 timed operations took 0.0003961 seconds with zero compilation.
These are sequential calls in one process, not independent cold-process samples.

The final targeted run passed all 1,911 assertions at `-g0 -O2`, including the
allocation-sensitive checks. The separate all-scalar Markowitz solver matrix passed
80 assertions with `-g0 --compile=min`. An initial targeted launch failed before
running assertions because the isolated cache environment did not expose MOI as a
direct test dependency; the successful launch adds the checkout to LOAD_PATH after
loading JSimplex from the enabled cache environment. No solver change was needed.

All 12 public external solves reached OPTIMAL, passed original-space feasibility
and independently recorded objective checks, and matched the reference exactly in
objective, iteration/refactor/restart counts, primal-vector digest and progress
digest. The corpus comprises afiro, adlittle, pk1, flugpl and fast0507 with both
algorithms, plus the separately warmed fast0507/runtime dual pair.

The warmed runtime solve completed in 166.9268 seconds, with 61,705 iterations,
788 refactorizations, no original-LP restart and objective 51,425,691.762104705.
Its measured compilation was 0.004922 seconds. The complete two-model process
peaked at 1,325,936 KiB RSS (1.26 GiB); this includes loading and warmup, and is not
a separate per-model peak. The external ten-solve process peaked at 1,078,288 KiB.
These runs used `-g0 -O2`, one Julia/BLAS thread and the 8 GiB virtual-memory guard.
They are not a new general performance comparison with the other basis managers.

`results/external.json` records all checked reports, first-use measurements,
resource summaries and raw-log/report digests. `reproduce/audit.py` validates their
provenance and complete unique coverage. The two broader compiler-limited test
attempts above remain incomplete; this is not a full-project test-suite pass.

## Reproduction

Use one numerical Julia process at a time and the established memory guard:
8 GiB virtual memory for numerical tests, 16 GiB for the user-authorized cache
build, at least 6 GiB available RAM and at most 1 GiB swap use.
The external driver verifies input hashes before loading, rejects excluded large
input names after resolving symlinks, and exercises the public manager option
without replacing solver methods. It records original-space certification,
reference objective checks, primal/progress hashes and compilation separately.

```bash
# Enable precompile_workload in an independent environment pointing to this checkout.
# Use the same debug/optimization flags for cache construction and reuse.
julia -g0 --startup-file=no --project=/path/to/cache-env diagnostics/huangfu-hall-public/reproduce/build-cache.jl /tmp/hh-cache.toml
julia -g0 --startup-file=no --project=/path/to/cache-env diagnostics/huangfu-hall-public/reproduce/first-solve.jl /tmp/hh-first.toml
julia -g0 --startup-file=no --project=/path/to/cache-env -e 'using JSimplex, Test; push!(LOAD_PATH, dirname(dirname(pathof(JSimplex)))); include("test/huangfu_hall_option_tests.jl"); include("test/huangfu_hall_tests.jl"); include("test/huangfu_hall_integration_tests.jl")'
julia -g0 --compile=min --startup-file=no --project=/path/to/cache-env diagnostics/huangfu-hall-public/reproduce/markowitz-semantic.jl
julia -g0 --startup-file=no --project=/path/to/cache-env diagnostics/huangfu-hall-public/reproduce/external.jl /tmp/hh-full full
julia -g0 --startup-file=no --project=/path/to/cache-env diagnostics/huangfu-hall-public/reproduce/external.jl /tmp/hh-external external
# The broader semantic batch used the checkout environment and its disabled workload.
julia --compile=min --startup-file=no --project=. diagnostics/huangfu-hall-public/reproduce/semantic.jl
```

Commands above assume the one-process memory wrapper is supplied by the caller.
Use fresh output paths. `reference.json` preserves the previously verified exact
numerical fields at `ecba7db`; the selected extraction optimization was already
checked to preserve those numerical results. Cache validation uses `-g0`; this does
not certify a reusable default `-g1` cache.
Cache timings are measured with a single compiler worker and image-generation
thread, separately from solve timings.
The first-solve probe runs all 18 cached native-solver configurations and four
Markowitz backend cases sequentially in one fresh process;
later configurations share compilation from earlier ones. It verifies the loaded
checkout and records source, harness, builder and active-environment digests. The
audit checks these digests, unique and complete input/configuration coverage, and
exact numerical fields against the reference.
