# Compilation findings after legacy stability validation

The severalfold increase in first-solve compilation is reproducible on the
local machine. It predates the last performance branch. A separate pathological
compilation case is present in the unpublished stability branch. The second
computer's exact revision is still unknown; these measurements do not identify
its environment-specific cause.

## Ordinary first solve

All observations use the same AFIRO input, primal legacy behavior, steepest-edge
pricing, Bartels–Golub updates, native factorization, interval 80, Julia 1.13.0,
MathOptInterface 1.54.0, and one Julia/BLAS thread. Every solution is optimal,
objective-matched, and independently checked against original-input bounds.

| Revision | First solve seconds | Compilation seconds |
| --- | ---: | ---: |
| Before modernization, `a52e194` | 6.932 | 6.930 |
| Shared feasibility recovery, `0086b19` | 14.405 | 14.403 |
| Hypersparse integration, `ea0f8b7` | 18.886 | 18.883 |
| Modernization complete, `b69e266` | 39.627 | 39.624 |
| Last pushed master, `0065da8` | 39.501 | 39.499 |
| Stability source, `d5472bc` | 42.793 | 42.790 |
| Adopted signature repair | 43.176 | 43.173 |

The modernization comparison is about 5.7 times. Each is one fresh-process
observation, not a statistical performance estimate. The approximately 8% gap
between the master and original stability rows is not sufficient to establish a robust regression:
a separate unchanged-master process takes 42.388 seconds for the same ordinary
solve. Warm repetitions take roughly 1–2 milliseconds. Package loading is
separately recorded; first-solve compilation remains after package loading.

No representative solver precompile workload is declared in the package.
The measurements establish missing coverage of these first-call specializations
in the loaded cache, not that all package code is uncached. Expanded driver and
kernel code also mixes runtime numerical-policy decisions with ordinary solves;
legacy selection does not by itself make every optional branch disappear from
type inference. This is a source-level explanation to investigate with isolated
compiler boundaries, not proof that one specific optional feature accounts for
the entire increase.

## Diagnostic callback specialization

In a single master process, otherwise identical no-op observer types A, B, and C
each require roughly 36–37 additional seconds of compilation after a normal solve
has already warmed up. Reusing A costs 0.006 seconds with zero compilation.
All five results have the same objective and nine pivots. Recompilation timing
is zero: these are additional type specializations, not measured invalidations.

The source explains this controlled result: `SimplexDiagnostics{F}` embeds the
observer type; it propagates through `SimplexProgressContext{T,D}` and
`SimplexWorkspace{T,F,M,R,D}`. Consequently, changing only the observer type
changes the type used throughout the solver. This is relevant to tests and
instrumented runs. The user's ordinary `solve` call has no diagnostic observer,
so this mechanism alone does not explain that call's cold latency.

## Precision-recovery compilation

The unchanged existing 30-check recovery-state test completes on master in
220.508 seconds inside the timer (221.565 seconds process wall time), of which
220.458 seconds are compilation. One trace request for
`solve_with_precision_recovery` takes 95.218 seconds; additional diagnostic
variants take about 23–25 seconds each. These trace entries include dependencies
and are not exclusive costs of the named method body.

The stability source is interrupted deliberately after 388.921 seconds while
still compiling the first case. This is an incomplete measurement, not a test
assertion failure or a completed timing. Its captured stack is in Julia's
`subtype_unionall`, `_typename_add_backedge`, and `store_backedges`. It reproduces
the kind of compiler work seen in the earlier monolithic production gate.
Resident memory was approximately 2 GiB in the sampled process; allocation
counts must not be read as simultaneous memory consumption.

A diagnostic override asserting that successful BigFloat transfers return a
`SimplexWorkspace{BigFloat}` also fails to finish the first case before deliberate
interruption at 253.614 seconds. That experiment does not establish an
improvement and is not adopted. It does not prove that all possible inference
barriers are ineffective.

## Bounded repair

Replacing seven union-constrained legacy workspace signatures with simple scalar
eligibility guards completes the same 30-check test in 161.446 seconds in an
isolated snapshot. The snapshot's production source is byte-for-byte identical
to the adopted four-file change (SHA-256
`14ddeb8612882564ada3397554f3bb903da99101027344d29a21e90c2df61415`).
This first successful experiment did not enable trace output; a final measured
replay with the original trace flags is recorded separately below.

The change keeps concrete Float32/Float64 arithmetic, tolerances, policy gates,
callbacks, and mutations unchanged. Other supported public scalar types return
from these hardware-only helpers before those operations. The guards are constant
for a concrete workspace scalar type. No adaptive algorithm or precision policy
is redesigned. The isolated intervention and the captured subtype/backedge stack
support a specific cause for this branch's pathological case: complex
union-constrained workspace method signatures make compiler dependency handling
expensive. This is not a general diagnosis of every long Julia compilation.

There are minor differences for previously unsupported internal calls: three
helpers now return false instead of lacking a method; a non-Bool correction
keyword can be rejected earlier for a non-hardware workspace; a hypothetical
workspace with a union scalar parameter fails the concrete-scalar guard. No
supported in-tree call depends on those cases. The read-only review found no
new method ambiguity or changed numerical path for supported calls.

The discarded BigFloat assertion override is retained only as diagnostic
evidence. It is not part of production code.

## Remaining work

This repair targets the pathological recovery compilation. It does not promise
to restore ordinary cold solves to the pre-modernization 7-second baseline.
The historical measurements locate increases across multiple feature groups;
they are not an individual-commit bisection or an exclusive compiler profile.

The next compilation work should separate rarely entered orchestration from
concrete numerical kernels, measure the ordinary legacy cold-call graph, and
add representative Float64 PFI/Bartels–Golub precompile workloads. Separately,
keep an observer's concrete type from propagating through every solver kernel
in diagnostic runs, while preserving exception provenance and callback behavior.
Both need their own cold/warm measurements; weakening numerical checks or
switching to interpreted execution is not justified by these results.

The earlier large-model attempts and broad validation belong to production
revision `d5472bc`. They have not been silently relabeled as measurements of this
compiler patch. Final targeted validation and compilation measurements follow.


## Final verification

The adopted worktree completes the original recovery-state test with identical
trace flags in **159.362 seconds**, including **159.287 seconds of compilation**;
all **30/30 checks pass**. This matches the successful untraced trial and is
faster than the 220.508-second traced master reference. The interrupted original
stability attempt supplies only a lower bound, not a completed before-time.
The largest recovery trace request drops from 95.218 seconds on master to
61.118 seconds after the repair.

The 14-file targeted validation passes **776/776 checks** in 313.287 seconds
process wall time. It includes the existing legacy numerical regressions,
precision-policy, phase, and exception tests, plus direct non-hardware exclusions
and primal/dual solves under both legacy and adaptive policies.

The adopted ordinary AFIRO cold solve takes 43.176 seconds (43.173 seconds
compilation); warm repetitions take 0.00208 and 0.00173 seconds. All three are
certified optimal with nine pivots and one refactorization. This confirms that
the targeted recovery repair leaves the ordinary cold-start cost unresolved.

The final external corpus completes **64/64 optimal solves and 200/200 checks**
in 157.543 seconds process wall time, covering eight NetLib/MIPLib LP
relaxations, both algorithms, and all four update schemes. Every result matches
the independent objective and passes original-input primal certification; input
hashes are checked. This small corpus does not establish convergence on runtime
or medium. No further large-model solve or unrelated full-suite replay was
performed for the signature-only change.

All jobs are sequential. Full logs remain in the worktree, and exported
measurements, trace summaries, source hashes, interrupted-trial reasons, and
reproduction scripts are in this directory. No merge or push is performed.
