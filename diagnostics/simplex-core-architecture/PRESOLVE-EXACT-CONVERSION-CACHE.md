# Exact Float64 conversion cache in dependent-row presolve

## Decision

The unchanged per-call cache passes the new whole-presolve correctness experiment
and shows useful presolve savings on three real LPs. It does **not** pass the
user's no-increase-in-allocations requirement across all controls. Do not integrate
this unconditional Float64 specialization. No production, test, environment, CI
or master changes were made. This result supports the narrower performance
hypothesis; it does not establish a generally safe/profitable dispatch predicate.
No selective variant was tuned or admitted here.

The user explicitly revised the objective during the first experiment: improvement
of the presolver without increased allocations is sufficient; whole-solver
acceleration is unnecessary. The new plan honors that criterion. Whole-solve
benefit is not a gate of the successful pipeline experiment.

## What was measured

Original attempt `results/PRESOLVE-EXACT-CACHE`: independently admitted four-process
ABBA plan, stopped after the first process at46.803587974seconds/exit1.58/59 reached
checks passed; all observed result/input checks passed. The candidate sc50a
component window8 contained6.682501ms compile and89.252609ms GC. No particular
compiling method or causal attribution is captured. Raw false gate and all inputs
are preserved; stages2–4 did not run. The original attempt is NOT accepted and
its fixed analyzer was not executed. Its generic/boundary/exception comparisons
are reused as scoped correctness evidence, not repeated.

New `results/PRESOLVE-EXACT-CACHE-PIPELINE`: same byte-identical candidate and ordinary
source overlays, separate admission and user-updated target, no whole solve.
Four serial reference/candidate/candidate/reference processes finished in47.204951727
seconds total, each within its70-second inclusive cap. Combined numerical-process
elapsed including both experiments94.008539701seconds; not benchmark time.
Each process performs eight models x(1cold+3warm+7measured) whole
`presolve_problem` calls:352 calls total,320 windows of which224 measured.48/48
named driver checks and all four17-gate audits pass. Every recorded output and
input-owner/value check passes, and all eight whole reduced-model/postsolve-map
signatures match across all four processes. All measured compile/recompile and
in-window GC counters are zero. There is no broader CI/full-suite claim.

Eight inputs: afiro, adlittle, sc50a, primal-chain130 and unchanged sparse24/dense16
repeated/unique dyadic models. Cache creation and all presolve passes are inside
timing. Parsing/import are outside; package/driver load8.112/7.572/7.518/7.635seconds
and cold presolve costs are separately recorded. One explicit, separately timed
GC after the three warm calls per case (32total) warms GC/finalizer paths. This
is not an explanation for the original compile sample and does not measure
uninterrupted long-run GC throughput. No sample was discarded.

## Whole-presolve results

Ratios below are candidate/reference side medians in the two opposite-order
blocks C2/R1 and C3/R4. Less than1 is lower. Each side median has seven measured
samples. Raw min/max/MAD, cold and explicit-GC times are retained in analysis.json.

| Input | Time, block1 / block2 | Bytes, block1 / block2 | Events, block1 / block2 |
| --- | --- | --- | --- |
| afiro | 0.8319 / 0.8921 | 0.9496 / 0.9490 | 0.9161 / 0.9161 |
| adlittle | 0.8841 / 0.9264 | 0.9576 / 0.9575 | 0.9363 / 0.9363 |
| sc50a | 0.9722 / 1.0300 | 0.9557 / 0.9558 | 0.9344 / 0.9344 |
| primal-chain130 | 0.6972 / 0.7198 | 0.8199 / 0.8198 | 0.5578 / 0.5578 |
| sparse-repeated | 1.0064 / 1.1255 | 0.9249 / 0.9253 | 0.8927 / 0.8927 |
| sparse-unique | 1.0133 / 1.0434 | 1.0206 / 1.0209 | 1.0012 / 1.0012 |
| dense-repeated | 0.9342 / 0.9799 | 0.9552 / 0.9549 | 0.9429 / 0.9429 |
| dense-unique | 1.1774 / 1.0247 | 1.0156 / 1.0156 | 1.0003 / 1.0003 |

Afiro presolve is10.8–16.8% faster, adlittle7.4–11.6%, primal-chain13028.0–30.3%.
Those three meet the >=5% criterion in both blocks with lower bytes and events.
Sc50a time ranges from2.8% faster to3.0% slower, so its timing is inconclusive;
its bytes/events decrease in both blocks. This is a small-fixture exploratory
measurement, not statistical significance or universal/end-to-end speedup.

The allocation gate fails on both unique-value controls in both blocks:
sparse-unique adds8928/9040bytes and13events per call (about2.1% bytes);
dense-unique adds34672/34640bytes and18events (about1.6% bytes). These are reported
as failed gates, not dismissed as allocator noise. The <=5% time-regression guard
also fails for sparse-repeated block2(+12.5%) and dense-unique block1(+17.7%).
Timing variation is visible; no runtime cause for these changes is asserted.
The entire unconditional specialization is therefore NOT ACCEPTED for integration.

## Source change, work and memory review

A specialized `reduce_dependent_rows(::LinearProblem{Float64})` in the experimental
overlay differs from the original by exactly three edits: specialized signature,
local `Dict{Float64,ExactValue}` after the existing size/nnz gate, and `get!` at
coefficient conversion. The generic method and69other source files in each70-file overlay remain intact. Both overlays use ordinary package loading, not global
method replacement. Actual package source and method route were checked.

Each reached nonzero adds a hash lookup; only the first reached occurrence of a
Float64 value constructs its exact Rational{BigInt}. Cache lifetime is one pass,
O(u) entries and rational owners, u<=10000. No new preliminary matrix scan.
Old row/nnz/work caps, ordering, exact arithmetic, bound checks, tolerances and
safeguards remain. The initial component matrix distinct counts are upper bounds,
not observed conversion counts when a pass exits early. No complete backend or
import work budget is claimed.

Exact cached scalar owners are private to the pass. Normalization,
_subtract_scaled! and implied intervals replace dictionary entries and use
nonmutating arithmetic; local exact caches/pivots/proofs do not escape in the
presolve result. Float64 input scalars have no mutable leaves; the generic
Float32/BigFloat/Rational routes are unchanged. Original16normal cases cover
four scalar types x removable/necessary/inconsistent, signed stored zeros,
finite extremes and both size cutoffs; two mutated nonfinite cases compare
return/exception behavior. These scoped tests do not replace full validation.

The experiment **does find unnecessary work and allocation cost** for unique
values: the cache pays lookup/table growth and temporary retention without saving
coefficient conversions. The measured allocation increases support rejection.
No persistent cache or retained model graph is introduced. Allocation counters
are aggregate GC traffic, potentially including native allocations, not a
native-allocation/free balance, peak-live-memory or GC-release proof.

## Integrity and continuation

Original admission verified4367files; original launch4369. Pipeline admission
verified4399files; pipeline launch4401, including preserved original raw results.
Fresh independent review preceded each experiment. Postcheck16/16 verifies all
pins, source514/protected6, both refs, combined bound, output checks and all186
historical/new PGIDs OR sessions absent with no Julia. Minimum observed available
RAM across pipeline processes22182712KiB, swap0. Independent result review follows.

All old and new frozen launchers/drivers/auditors/raw/reviews remain unchanged;
no numerical rerun or candidate tuning follows this result. Broad plan remains
open; HH reuse disabled, CI off, automation paused. MA-Y remains rejected and is
not reopened. A future selective cache would need its own concrete cost/eligibility
case and independent tests; this report does not prescribe or admit one.
