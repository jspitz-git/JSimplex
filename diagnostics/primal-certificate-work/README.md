# Primal point certificate work

Follow-up to `diagnostics/residual-followup-probes` on baseline `c23b459`
(production baseline `c962506`). The user approved three sequential experiments:
owned scratch reuse, eliminating materialized activity bounds, and sharing native
row aggregates during one point certificate. No tolerance, precision, candidate,
pivot, perturbation or certificate acceptance rule may change.

## Validation design

Each stage is measured separately against frozen original functions, using the
same workspace/input/storage with alternating warmed batches. Synthetic native
Float32/Float64 cases include fast acceptance and cancellation that forces the
native fallback. Two original-LP medium handoffs are continued for 32 cleanup
iterations, then the certificate-only inputs are serialized for later identical
replays. These snapshots do not contain a valid continuation factorization.
Both medium origins use primal cleanup; they do not measure ordinary dual steps.

The runner pins source, tests, local environment, scripts and existing saved
inputs. One numerical Julia process / one Julia+BLAS thread, 8 GiB VM,
6 GiB available RAM floor and 1 GiB swap maximum are enforced. Attempts are
never overwritten. Local Manifest and LocalPreferences remain uncommitted.

Final verification must include exact native fallback tests, repeated-state and
ownership tests, independent frozen-function comparisons, wider semantic
regressions, all 100 existing external combinations and a full dual runtime
fingerprint/feasibility check. Bounded medium continuations verify the affected
cleanup path; no whole multi-hour medium speedup may be inferred from them.

## Stage 1: workspace-owned fallback scratch

The point buffer owns selected-row storage and lazily owns the native slot map,
three accumulators, uncertainty mask and unresolved-row storage. Every filter
call rebuilds its current row selection and clears active accumulators. The
exact fallback consumes unresolved rows synchronously. No matrix scan or solve
is added; the original standalone allocation path is preserved.

Additional retained payload is O(m + k): m integer slots, two peak-k integer
lists, three peak-k native arrays and k bits. Capacities are bounded by the
workspace problem's rows for the internal unique-row lists. Stage/workspace
adoption continues to create independent scratch. No numerical verdict survives
between calls.

The first valid allocation test failed on baseline with 183,000 / 248,536 bytes
(Float32 / Float64) while its 22 semantic checks passed. An earlier fixture used
an invalid zero SolverOptions tolerance and is preserved as a harness error,
not evidence of a solver regression. Stage 1 passed all 24 focused checks.

The first paired run reduced each medium endpoint from 18,784,280 to 9,391,752
bytes per certification. Baseline/candidate time ratios were 1.008 and 1.027;
this modest timing difference does not establish a whole-solver speedup. The
remaining large allocation is the materialized activity-bound vector. A world-age
warning in the frozen-function binding lookup was corrected with invokelatest
for subsequent probes; numerical calls already execute through invokelatest.


## Stage 2: bound view and one selection pass

The owned point certificate uses an indexed view of its already-finite stored
activities instead of materializing `Bound.(activities)`. Standalone callers
retain the original materialization and error behavior. Owned hardware-float
model checking selects uncertain rows in one pass; it no longer scans a
certified prefix twice after encountering the first uncertain row. A counting
bound-vector test detects that duplicate scan (66 accesses before, at most 36
after for a 32-row fixture).

Stage 2 passed 1,190 compiled allocation/fallback checks and 1,304 interpreted
semantic checks. Its first paired endpoint replay used 128 bytes per certificate
instead of 18,784,280; baseline/candidate median ratios were 1.127 and 1.125.
The later four-arm benchmark specializes its call sites differently and reports
zero bytes for the same native-only candidate path. Neither benchmark includes
workspace initialization in its steady-state allocation measurement.

## Stage 3: aggregates scoped to one certificate

The full point certificate resets the native scratch's valid-row count before
checking model bounds and stored activities. The first native fallback builds
its map and sums in bulk. The second may reuse those sums for overlapping rows,
append new rows, and scan the CSC matrix only if additional rows need sums.
For each row, coefficient order and arithmetic are unchanged. Bounds are tested
independently; native uncertainty still reaches exact integer fallback for each
bound set. No cached verdict or aggregate is used across point certificates.
Standalone calls do not opt into sharing.

The work probe counts native product-pair evaluations: both precisions require
384 instead of 768 evaluations for two checks of a 128-row, three-term fixture.
The second identical selection avoids one CSC traversal. Disjoint selections
still require two traversals. An initial implementation appended all first-call
slots individually; review identified that overhead, and the final version uses
bulk resize/fill for the first selection. Raw prototype results are retained.

Additional scratch retains O(m + k) storage, where k is now the peak union of
selected rows in a certificate, with logical length at most m. Allocated vector
capacity may exceed the logical length. This can exceed the larger individual
selection. It replaces repeated allocations with owned capacity; it is not a
claim that all retained memory decreases. Workspace and phase scratch remain
independent. Generic precisions keep their existing path.

## Harness issues retained separately

- `red1`: invalid zero SolverOptions tolerance, corrected before the valid red test.
- `step1-targeted`: normal compilation remained in LLVM; its own guarded process
  group was deliberately stopped after about 253 seconds. It is not a solver
  numerical failure or a completed test run. Semantic checks were rerun with
  `--compile=min`; allocation checks were run with ordinary compilation.
- `step2-allocations`: a new test incorrectly expected `Bound(Inf)` to be valid;
  corrected to expect an error.
- `step2-paired`: a script macro parsing error; fixed in `step2-paired-v2`.
- `step3-targeted`: a new test broadcast a scalar Bound without Ref; corrected
  to fill! in `step3-targeted-v2` (1,216 checks passed).

These attempts are preserved in the raw local output. They are not counted as
passing validations. The valid failing allocation, duplicate-scan, and product
count probes are distinct from these harness errors.

## Reproduction commands

Run one command at a time from this checkout, with fresh output directories.
The runner rejects a second Julia process and pins its dependencies.

```sh
python3 diagnostics/primal-certificate-work/reproduce/run.py /tmp/pcw-allocation-new 180 -O2 diagnostics/primal-certificate-work/reproduce/targeted.jl allocation
python3 diagnostics/primal-certificate-work/reproduce/run.py /tmp/pcw-semantic-new 120 --compile=min diagnostics/primal-certificate-work/reproduce/targeted.jl semantic
python3 diagnostics/primal-certificate-work/reproduce/run.py /tmp/pcw-products-new 120 -O2 diagnostics/primal-certificate-work/reproduce/count-products.jl
python3 diagnostics/primal-certificate-work/reproduce/run.py /tmp/pcw-differential-new 180 -O2 diagnostics/primal-certificate-work/reproduce/differential.jl
python3 diagnostics/primal-certificate-work/reproduce/run.py /tmp/pcw-stages-new 300 -O2 diagnostics/primal-certificate-work/reproduce/stages.jl /tmp/pcw-stages-new/results.toml
python3 diagnostics/primal-certificate-work/reproduce/run.py /tmp/pcw-cleanup-new 600 -O2 diagnostics/primal-certificate-work/reproduce/cleanup.jl /tmp/pcw-cleanup-new/results.toml
```

`stages.jl` replays the local certificate inputs under
`.superpowers/primal-certificate-work/capture`. Recreate them with
`paired.jl <fresh-output.toml> capture` through the same runner when necessary;
this performs 32 cleanup steps from each original handoff before serializing
certificate-only inputs. The saved points are not restart checkpoints.
The handoffs and established wrapper paths are host-local dependencies.
The `.baseline`, `.step1` and `.step2` files freeze the reference function
bodies used by the paired comparison; only the six named functions are loaded.

The final four-arm controls also expose the tradeoff: when only activity
consistency needs native sums, stage 3 is about 0.3% (Float32) / 1.5% (Float64)
slower than stage 2 in this run. Sharing has no overlapping work to remove there.
The combined final implementation is still about 21% / 22% faster than the
original certificate for those controls. These small stage-to-stage differences
are not whole-solver results and need more repetitions to distinguish small
systematic overhead from timing variation. No adaptive gating is introduced.

The final Float32 fast-path control was about 3.0% slower than baseline,
whereas the Float64 control was about 3.0% faster. Earlier fast-control timings
also varied in sign. These short controls establish neither a fast-path speedup
nor the absence of a small regression; the reported gains concern fallback
certification. Raw samples are retained rather than treating allocations alone
as speed evidence.

The first randomized differential probe was strengthened after review: default
nonnegative column bounds rejected many sampled negative points too early, and
mutating the original input matrix did not change the model's owned copy. The
replacement uses free columns, explicitly checks acceptance before each isolated
rejection, and mutates the owned matrix at a coefficient with nonzero primal
value. It passed 1,680 comparisons with the frozen original functions: 720
explicit acceptances and 960 explicit rejections. The first probe is retained
as `final-differential/weak-fixture.jl` in the raw local outputs.

## Final results

Production changes were committed separately as `d1eeef1` (scratch), `fddd560`
(bounds and selection scan), and `e08ea83` (within-certificate aggregates).
See [the compact result summary](results/SUMMARY.md), the raw timing samples in
[final-stages.toml](results/final-stages.toml), and the independently checked
[review](results/review.md). The results distinguish warmed kernel measurements,
bounded cleanup trajectory checks, full runtime certification, and compilation.
They do not establish an end-to-end speedup for medium or runtime.
