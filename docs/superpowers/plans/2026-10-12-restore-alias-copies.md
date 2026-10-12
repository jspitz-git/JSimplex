# S5-C: eliminate identity-duplicate restoration copies

> **For agentic workers:** Use superpowers:executing-plans inline, sequentially.

Goal: remove only the second copy to an identical destination during owned journal
restoration. This is a new production subplan, conditional on accepted S5-B census
and independent review. Do not remove invalidations, scans, events or reconstruction.

## Exact change and proof obligation

In src/simplex_perturbation.jl::restore_perturbations!, retain the first
copyto!(ws.costs,journal.original_costs). Skip the immediately consecutive second
copy only if journal.active_costs === ws.costs AND the original source is proven
nonoverlapping by a qualified contiguous storage-range predicate. Otherwise retain the original
copy. Identity alone is insufficient for a partially overlapping source/destination:
two memmoves need not be idempotent. Test partial overlap explicitly with an owned
backing vector/GC preservation and preserve the legacy result for that path.

Base.mightalias alone is insufficient: offset unsafe_wrap vectors may overlap
while their storage identifiers differ. S5-B alias-probe-1 demonstrates four
wrong skips with that test. A range predicate must use actual storage stride
(including reference-containing element layouts), handle empty buffers and checked
byte-length overflow, compare pointer distances without address-end overflow,
and preserve objects across pointer access with GC.@preserve. If disjointness
cannot be established, retain both copies. The diagnostic Float64 predicate is
not an all-scalar production proof; establish the supported layout contract first.

This removes at most one O(N) cost copy at cold restoration, adding only constant-
time identity/alias checks (verify specialization/allocation in cost gate). No
cache, scalar conversion, value-equality scan or certificate reuse. Bound copies
are excluded: intervening lower/upper writes complicate source cross-aliasing,
so deduplicating them is a separate unqualified hypothesis.

## RED/GREEN contract

- [x] Recheck host refs/processes and user hashes; existing memory guard, one Julia.
  Do not mutate source while another attempt has pins. Preserve failed attempts.
- [x] Add focused test/restoration_alias_copy_tests.jl with a process-local original
  baseline helper. First use a diagnostic copy forwarder/work assertion to show
  duplicate calls on original implementation (RED), with exact state/event oracles
  already passing. No failing public semantic oracle should be fabricated.
- [x] Cases: aliased/detached cost destinations; same-source and partially overlapping
  source/destination; inactive/no-bound journal; foreign owner; destination-length
  failure with partial publication; objective changed after journal snapshot;
  observer throws after restoration; signed zeros and stored BigFloat precision;
  Float16/Float32/Float64/BigFloat/RationalInt64/RationalBigInt and empty vectors.
  Include source/destination identity overlaps where representable; distinct
  buffers must retain both copies. Check caller-owned model and journal state.
- [x] Implement only identity and qualified storage-range guards, run GREEN on actual production bodies, inspect
  work removed. Compare baseline/candidate complete recorded state and events.
- [x] Run relevant existing restoration/perturbation/checkpoint/partial-pricing
  regressions on the changed source; assemble dependencies explicitly. Keep full
  historical CI failure separate; do not enable GitHub CI.

## Cost and integration gates

- [x] New changed-source paired cold-restoration kernel samples, alternating order,
  warm compilation separated, several rounds; alias and detached cases, small and
  large N, cost-only and bound-active journal restoration (bound copies unchanged), representative scalar precisions.
  Report copies/elements, allocated bytes/events, compile/GC/elapsed. Existing
  medium or HH component reference must not be repeated. Matrix sparsity does not
  change these copy kernels; include sparse/dense end-to-end small trajectories
  for numerical coverage, do not claim kernel samples as whole-solver speedup.
- [x] Reuse S5-B fixtures on baseline/candidate with exact selected-state/event
  equality; original feasibility/certification, shared budget, observer failures
  and foreign checkpoint rejection remain mandatory. No certificate reuse.
- [x] Audit process/source/pins, failure preservation, and independent numerical/
  work/memory review. Added work is constant-time identity/storage-range checks, no scans,
  solves, allocation or retained cache. Retained active journal buffers are still
  required for detached ownership; do not delete them.
- [x] Only after gates: separate production commit, integrate to master under
  standing authorization, focused master check, user-file hashes, push/verify;
  diagnostic results on architecture branch. Update STATUS/automation. No speedup
  claim from a single pair; detached overhead uncertainty must be reported.

Author gates complete: layout184, RED semantic462/work30pass12expectedfail,
GREEN504, focused1463, cost312compile0samples/52fixtures, trajectories152pairs/
153assertions. Process/source/pins verified. Cost byte equality is not established;
144/156pairs differ despite equal allocation events, initial analysis preserved.
Small/detached timing limitations in S5-COPIES.md. Final review accepted without findings; see S5-COPIES-REVIEW.md.
Production88a2411 -> mastere7014fb; master668/668,12audit gates/592pins.
Master push verified:e7014fb92ae6dce633afc714793a2f89b39aea76.
Diagnostic closure and automation record identify this completed subplan.
