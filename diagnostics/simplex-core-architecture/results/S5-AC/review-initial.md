# S5-AC independent numerical/work/memory review — initial

Verdict: REJECTED pending the single source-accounting correction below.

Critical findings: none.
Important findings: I1, inaccurate initialization diagnostics claim.
Minor findings: none.
Unresolved findings: [I1].

I1 — Decision report line 23 says `kernel_timing=true` records FTRAN/BTRAN/pricing
calls during finish. Actual `recompute!` calls `_checked_basis_solve!` twice and
then `_recompute_reduced_costs!` directly (src/simplex.jl:464–473). The checked
solve wrapper times FTRAN/BTRAN (src/simplex_recovery.jl:490–499); the reduced-cost
body at simplex.jl:386–410 has no pricing timing wrapper. Thus one pricing pass
is actual source work, but not a `SimplexDiagnostics.kernel_calls[:pricing]`
increment at this boundary. Distinguish any historical diagnostic request counter
from production timed kernel accounting. Correct only that claim and preserve
the original report/pins; the two solve records and refactor_initial event still
establish the stated diagnostics obstruction. No Julia run or benchmark is needed.

## Scope and provenance

Reviewed report SHA256: `36e96502096ea0677fa13a4970c217b030375020202226d6b137ca054ac38ef7`.
Reviewed next-plan SHA256: `987e7f2a462c5b0d2d97bae05f2df4c24bee0f031d317d9801d8e0aee48c105f`.
Fresh reviewer script SHA256: `048c83be0ecb6936ba072c84c33ba5d5cfe2f739b5342a09c612ffc4e0510425`.
Reviewer evidence SHA256: `f182d982eda4cae9c68ca03656ad9c4d7304fe017026ba025f81c1f179b09f5d`.

New read-only Python verified 14 gates and 1919 distinct physical hashes: all
1910 entry pins, 25 source pins, author independent bindings, AB reviewer
preservation/amendment bindings and closure35, exact38 committed names and all37
listed blobs, 511 current source/test pairs, and all6 user hashes. Historical
physical resolutions already recorded in entry.json were rehashed directly;
current corrected AB report and current start test were not substituted with old
texts. Local/remote architecture98b380f and masterd02416c match. Same-boot host
inspection finds no Julia and no members of all26 old groups OR sessions. Tracked
changes are empty. Numerical evidence is reused within accepted A184/B/C and AB
scope, not rerun or promoted to exhaustive state equivalence. All frozen evidence
remains untouched. A reviewer read attempted nonexistent entry_check.py; its error
remains in the transcript and evidence scope, followed by reading actual entry.py.
No frozen script/auditor, Julia, compiler/parser or numerical code was executed.

## Numerical and design assessment

Apart from I1, the source supports the bounded decision. The policy stores
individual switches, and `_native_primal_kernel` does not test refinement or
precision recovery. Ordinary initializer assignment completes only after finish;
the null/workspace recovery distinction is real, while strictly ordinary policies
return the same numerical run from either recovery overload. The report correctly
does not turn that ownership fact into a demonstrated narrower-subset failure.

Construction owns costs/bounds, default slack factor, scratch and zero/unit
vectors. Finish validates the basis mask, reconstructs primal/prices and can touch
pipeline validity, quality and bounded checkpoint history under enabled switches.
Options and context supply distinct clocks, with solve refinement explicitly gated.
Restored recompute logs before refactor, increments work and emits refactor_other
before reconstruction; guarded caller exceptions retain identity. Projection and
restored fallback cannot justify a new hidden catch-and-retry. BigFloat stored
values and ambient arithmetic, exact types and separate precision initialization
remain distinct obligations; no certificate crosses into the original model.

Rejecting the weak flag gate and deferring a stricter subset is justified as a
missing proof, not an impossibility theorem or newly observed numerical failure.
The next provenance-only plan is a different explicit parent S6 obligation:
STATUS's separately reported test.mps HH/native320 failure and parent plan S6
require it remain unresolved. Locating preserved identity/output is appropriately
bounded; the plan grants no rerun, substitute model, cause assumption or new
numerical allowance. No new equivalent census is warranted.

## Work and memory assessment

No unnecessary NEW production work, allocation or retained memory was introduced.
There are zero new solver scans, basis solves, copies or conversions at setup,
refactorization, iteration, candidate, recovery or certification frequency, and
no new cache roots or update-chain retention. The possible deletion targets one
cold reconstruction per cleanup invocation: two checked solve requests plus one
reduced-cost traversal and O(m+n+nnz(A)) validation/RHS/state work outside backend
solves. Optional refinement/checkpoints can add work, so these are not universal
raw-solve counts. Constructor/factor/scratch ownership and later restored work
remain. S5-C's separate one-copy saving is not initialization reuse. Old entry/
ordinary timings are attribution only, without current speedup or scalar/backend
coverage claims. A documentation-only correction needs no sparse/dense benchmark.

Broader S5 and all prior rejection/CIoff/HHdisabled/fullsuite/x64/cause/runtime,
retention and controller limitations remain open. This review does not accept
publication closure; a corrected report needs a bounded follow-up review first.
