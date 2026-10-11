# S3-A: scratch support invalidation at refinement and witness publication

> **For agentic workers:** Use superpowers:executing-plans sequentially.

**Status:** Both hypotheses reproduced; minimal repair passed smoke32 and
extended1645. Existing integration regressions active; cost/review/integration pending.

**Parent:** 2026-10-11-simplex-core-architecture.md S3, its design spec, and
S3-INVENTORY-NOTES.md. This is a narrow prerequisite repair, not a sparse pipeline
optimization or acceptance of the whole S3 stage.

## Observations and bounded hypotheses

`refine_basis_solve!` accepts AbstractVector destinations. Its accepted correction
copies into destination and calls `_pipeline_changed!`, which matches only exact
identity of the six owned Vector objects. A full view into an owned rho has a
different identity. Existing whole-vector regression does not exercise that case.
Hypothesis: a previously empty valid support remains empty after the view receives
a nonzero correction, and the next sparse pricing omits a real coefficient.

`_lp_project_certificate` constructs a fresh workspace without recomputation,
then publishes a separately certified primal and dual. `_lp_workspace` emits
refactor_other before returning the new owner. An observer can populate metadata
for the zero rho without changing any numerical value. The subsequent rho copy
has no explicit support invalidation. Hypothesis: the accepted witness is correct,
but its next sparse pricing uses stale empty support.

Both hypotheses require real RED observations before any source edit. Keep controls
for whole Vector and no metadata-producing observer. A failure elsewhere in setup
is not the intended RED. Test output must show accepted correction/projection,
correct dense values, and wrong support/pricing only in the targeted cases.

## Constraints

Wait for S0-L/medium-dual-counted-1 process.json and separate host identity/absence
verification. Do not edit old baseline or currently pinned diagnostic files while
it runs. One guarded Julia/BLAS thread,2GiB heap hint,8GiB VM,6GiB available RAM,
1GiB swap; no forbidden model or alias. Preserve every attempt/environment.
No new numerical model is necessary for these small deterministic regressions.
No tolerance, arithmetic, precision or policy-default change is proposed.

## Intended change only if reproduced

Owning files: src/hypersparse_pipeline.jl and src/lp_refinement_driver.jl.
Regression destination: test/hypersparse_boundary_invalidation_tests.jl, registered
in the existing hypersparse test group. Initial diagnostic driver is
reproduce/pipeline_boundary_regressions.jl; promote verified cases, not untested
assumptions, into the production suite.

Keep `_pipeline_changed!(ws, values::Vector)` on its existing exact-identity path.
For other AbstractVector destinations, invalidate every owned buffer for which
Base.mightalias reports overlap. There are exactly six buffers: bounded metadata
checks, no full-vector scan, no new persistent cache or per-element work. A
conservative overlap result may invalidate extra metadata; never preserve stale
support to save a rebuild. Do not reject legitimate views merely to hide this bug.
Unknown unsupported alias types must follow Base.mightalias's conservative contract;
do not invent pointer arithmetic or depend on a specific SubArray layout.

Immediately before the certified dual copy in `_lp_project_certificate`, call the
existing invalidation helper for probe.scratch.rho. Do not change the observer
ordering, certification, work budget or publication of primal/reduced costs.
The helper is a no-op without a cache. Never reuse original-workspace support.

If RED reveals a different source of failure or either hypothesis is false,
record that result and revise the smallest plan necessary before implementation.

## Sequential gates

### B1: reproduce and freeze

- [x] Independently review the test and bounded alias/publication contract.
- [x] Once S0 exits, freeze current architecture sources/tests/environment and
  exact diagnostic script in a new S3-A attempt; verify one-process preflight.
- [x] Run smoke regression on unchanged production with normal compilation.
  Expected: whole-vector/no-metadata controls pass; view support/pricing and
  observer-created probe support/pricing assertions fail for the named reasons.
- [x] Read exit/pins and verify runner/Julia absence on the host before any edit.

### B2: minimal repair and contracts

- [ ] Apply only the verified invalidation changes, then run the same smoke GREEN.
- [ ] Extend the view case to Float32,Float64,BigFloat,Rational{Int64}/BigInt,
  all five managers and native/Markowitz where supported. Check direct Vector,
  full view, reordered view with unchanged dimensionality, and independent
  external destination. Preserve RHS/private/model alias rejection tests.
- [ ] Verify no-cache and unrelated-view cases introduce no metadata ownership;
  owned metadata rebuilds after accepted alias writes, not rejected corrections.
- [ ] Verify observer-created witness support, no-observer control, source owner
  isolation, preserved certificate and unchanged callback exception propagation.
- [ ] Run existing hypersparse pipeline/storage/edge/recovery and refinement
  regressions, plus LP refinement projection/guard tests. Unsupported combinations
  must be reported; do not silently skip a failing manager/precision.

### B3: work review and integration

- [ ] Compare repeated whole-vector invalidation with/without cache on frozen
  sparse and dense scratch fixtures, at least three interleaved warm pairs.
  Record allocation events/bytes and spread; no new per-vector scans/solves or
  persistent metadata. Keep compilation and new alias-path work separate.
- [ ] Use work counts to establish that witness publication adds at most the
  existing bounded identity lookup, once per accepted probe. No cold-path
  benchmark is required absent a material concern; broader solver speedup is
  not this fix's claim.
- [ ] Independent numerical/work-memory review. State explicitly whether
  unnecessary work or retention was found and cite the executed evidence.
- [ ] Commit only passing production/test changes; integrate into current master,
  preserve user dirt/local environments, run focused integration and push under
  standing user authorization. Diagnostics remain on their branch.
- [ ] Update STATUS and parent plan without completing broad S3 checkboxes.

Reordering rationale: reproducing and repairing a stale-support safety boundary
precedes new support reuse or the S2 private experiment. The S0 live run is
uninterrupted. No benchmark already completed is repeated without a changed
implementation or a new explicit contract test.

Independent static review accepts the prepared reproduction and bounded change
contract. It confirms the assertions do not repair stale support before the
subsequent pricing check. Runtime reproduction and all implementation gates remain
open while S0 owns the numerical process.

B1 executed: boundary-red-1 normal compilation,27 pass/5 intended failures,
no setup errors. View has3 stale support/pricing failures, observed witness2;
whole-vector and no-metadata controls pass. Exit1/pins unchanged; runner280106,
Julia280107 and driver absent verified before edits. Minimal two source changes
now applied; identical smoke GREEN is next.

B2 extended matrix passed1645 tests normally:1500 across250 combinations
(5precisions x5managers x2backends x5destination forms),105 ownership/rejected/
model-alias assertions,40 witness/publication/observer-provenance assertions.
Exit0/pins unchanged; runner280408/Julia280409/driver absent before focused launch.
