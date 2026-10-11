# S3-B: consume freshly canonical pipeline support

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans sequentially.

**Goal:** Remove a repeated support compaction immediately after a successful
producer has already returned canonical indexed output, preserving all checks.

**Architecture:** Keep the six existing borrowed scratch owners and validity
flags. Convey only a local successful-producer fact to the existing output-support
helper; do not turn cache.valid into a universal canonical-support certificate.
Ordinary input compaction, dense output rebuild and external checks remain.

**Tech Stack:** Julia existing IndexedVector/pipeline, Test, TOML, guarded Python.
**Spec:** 2026-10-11-simplex-core-architecture-design.md, S3.
**Status:** Source proof prepared; characterization and RED pending. No production edit.

## Scope and source proof

The controlled legacy baseline has hypersparse=false. This change concerns an
existing optional pipeline; never silently enable it or claim a whole-legacy
speedup. Force outer kernel modes during measurements so timing-based selection
cannot masquerade as arithmetic savings. Internal indexed :auto occupancy fallback
remains its existing deterministic policy, with successful reload proved below.

Producers in hypersparse_updates.jl and hypersparse_factorization.jl:

- _hypersparse_solve! returns compact_support!(dest), in both directions.
- _load_indexed_solution! clears destination and assigns every distinct index
  once through finite set_entry!, so dense fallback produces canonical support.
- PFI forward returns _copy_indexed!, which compacts; PFI transpose returns one
  of the two canonical base-solve paths. Alias checks exclude private work owners.
- FT/SS/BG forward explicitly compact the final permuted destination; transpose
  returns canonical base solve. Intermediate cancellation/rotation need not be
  canonical until the successful public return.
- sparse_price! compacts output after ordered accumulation, including exact
  cancellation. Noncanonical CSC fallback preserves its existing numerical order.
- _pipeline_empty_output! clears/reset support and sets owned validity only after
  constructing zero output. Its support is canonical and empty.
- HH and DenseLUBackend cannot use the indexed pipeline producer; their selected
  outer mode becomes dense. Dense writes leave validity false and require rebuild.

There is no user callback or source mutation between successful kernel return and
_output_support on these call sites. BigFloat scope restoration is not a value
write. Failure never reaches successful output counting and still invalidates
owned support in the outer catch. Later input calls must still compact because
valid support may contain cancellation zeros from other legitimate writers.

## Proposed minimal interface, contingent on evidence

Only src/hypersparse_pipeline.jl:
`_pipeline_output_support!(ws, cache, index, values, canonical::Bool=false)`.
For positive owned index and canonical=true return length(cache.buffers[index].indices).
Otherwise execute the existing implementation unchanged. Both successful producer
call sites pass `mode in (:sparse,:empty)` using the actual selected outer mode.
External output index0 always retains all(isfinite) plus count; dense owned output
retains _pipeline_vector! and full rebuild. Existing four-argument callers retain
conservative behavior. No new workspace field, support cache, arithmetic, tolerance,
public switch or mutable mode policy. A future producer must preserve this contract.

The Boolean is an internal local capability, not validation of arbitrary caller
assertions. It must never be inferred from cache.valid alone or propagated beyond
the immediate successful return. Keep generic reads and externally invalidated
views covered by S3-A; no relaxation of alias invalidation.

## Sequential gates

- [ ] Guarded unchanged-production census: all five public managers, native and
  Markowitz, all five supported precisions, empty/sparse/dense input and genuine
  update history. Check exact dense values, canonical indices/membership and modes.
  Count compact calls/elements globally and inside output-support; separate rebuilds.
- [ ] Intended small RED: successful indexed solve/pricing should have zero
  output-consumer compaction; unchanged control has one. Dense/external controls
  and ordinary input cancellation continue to require their original work.
- [ ] After final exit/pins and separate host process absence, implement only the
  above local fact and rerun identical GREEN. Add permanent regressions that fail
  if noncanonical generic inputs are trusted or post-write support stays stale.
- [ ] Repeat extended matrix because source changed. Cover signed zeros, exact
  cancellation, retained BigFloat precision, dense fallback, aliasing, empty
  outputs, exceptions and both basis directions; no old S3-A rerun without scope.
- [ ] Existing indexed/hypersparse factorization/update/pipeline regression groups.
- [ ] At least three interleaved warm sparse/dense pairs: whole solve/pricing and
  focused support work, separate compilation/setup, actual work and allocations.
  Baseline clone changes only this helper call/parameter, same fixed policies.
- [ ] Independent numerical/work/memory review, minimal production commit,
  isolated integration tests and authorized master push; diagnostics separate.

## Process and ownership

One guarded Julia process, Julia/BLAS1, heap2GiB, VM8GiB, availableRAM6GiB,
swap1GiB. No excluded large inputs or aliases; synthetic bounded fixtures only.
Preserve environments, old worktrees, failures and pinned snapshots. The census
may instrument exact parsed methods inside its isolated process; no source file
is overwritten. Instrumented results are counts, never authoritative timings.

Ruling: this is a concrete execution subplan under the already authorized S3
architecture investigation and standing instruction to continue without repeated
confirmation. It adds no public behavior or optimization policy. If canonical
producer proof or cost validation fails, keep the experiment isolated/reject it;
do not broaden trust or remove numerical checks to rescue a result.
