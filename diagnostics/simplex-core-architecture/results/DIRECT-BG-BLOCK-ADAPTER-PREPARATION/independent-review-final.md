# Independent Task2 final source acceptance

**PASS for OFFLINE Task2 source preparation only. No unresolved blocking findings remain in the reviewed scope.** This accepts the final private BlockBG adapter, differential-test source, exact frozen fixture reuse, full work/memory ledger, source map, exact inverse and ordinary overlay. It does not accept runtime correctness, Julia syntax/dispatch, numerical equivalence, allocation counts, performance or memory gates, production integration, or any Task3 execution. No Julia query/parser/import/compilation/test/numerical work was performed. Only newly written offline Python byte checks were executed; stopped artifacts/scripts remained read-only.

This final review incorporates the full numerical/work/test reasoning and five focus classes in preserved independent-review-v1.md, and preserves the two later blocking findings in independent-review-v2-findings.md. V1's original candidate/test hashes identify the corresponding preserved snapshots, not the canonical final versions. Final byte checks in reviewer-final-check.py/json independently confirmed forward and reverse exact derivation, all81 stage members/hashes,77 unchanged Task1 originals plus the exact root-include inverse, all three new source copies, original fixture bytes and preserved rejected snapshots.

## Exact accepted sources

- block-bg.jl: `5b6c7bd442c79459e7607e4301e087921196bbd285ccaaa3774fd5b9c918aa4d`
- block-bg-tests.jl: `d6997aa4d277f2d46242e9e78d8c891ef00b518677cf0b835ba66861b7fb2eed`
- fixtures.jl: `835b6e4241705b4c7a6a2625c904999ffe30e90ec99c937d257cbe2a2c289517`
- fixed Task1 block-upper.jl: `94529e9b8ed5fb647b210e609708bf8d73db5b260c2a873f6610e0227ac7314c`
- fixed Task1 block-oracles.jl: `87911ed1b6ef01f47c65fed56711f750697ab03599c6fcea6c2564e739dfce3f`
- MEMORY-WORK.md: `ccecab683f4e86a55a9ccbd8de009f27a342fe0e4794a3ffd65317fa10bf4329`
- SOURCE-MAP.md: `10f51db6fa01c1de5ee65912e27e09db4963798c095f82be7650ebbb879ffd44`
- adapter-inverse-reviewed.json: `a82c2c8b9f570dabdb337940958a1be027fb9426fad46d925ad61b25e22c9835`

The accepted ordinary overlay is `.superpowers/sdd/2026-10-16-direct-bg-block-upper/task2-stage-reviewed`, bound in overlay-reviewed.json and byte-identical adapter-source-bindings-reviewed.json. reviewer-final-check.json records the complete81-file stage binding and supporting evidence/runtime-source hashes. Packed semantics were compared with actual repository triangular files and the accepted stage: the staged triangular_factorization.jl differs in the previously accepted policy-aware constructor plumbing, not the reviewed solve/update/cache bodies. Accepted direct-factor.jl lower/export/normalization plumbing and unchanged Task1 storage are dependencies, not new production edits.

## Findings resolved without broadening the interface

1. Exact empty-work alias rejection is restored by checking destination identity before mightalias. Installed Julia source confirms mightalias returns false for empty arrays, so the original mightalias-only gate changed this behavior. Both FTRAN/BTRAN now have an empty-work sentinel assertion before backend access.
2. The newly added unsafe_wrap offset-pointer assertion was not supported by dataids-based mightalias. It is replaced with `Base.wrap(Array,Core.memoryref(scratch.ref,2),3)`, sharing the same Memory owner. Installed boot.jl/array.jl/abstractarray.jl source establishes the constructor/dataids chain; the test explicitly asserts mightalias before rejection. No pointer-range scan or foreign unsafe-wrapper support was added. All rejected source/test/ledger/map versions remain preserved.

Additional final tests cover non-Int CSC index rejection before a backend sentinel, malformed supplied q/CSC row ordering, and synthetic update handle exhaustion after mutation with structural/cache/history checks followed only by refactor. Source review found these assertions consistent with the intended call paths. They remain unexecuted. The initial author's vacuous adjunct is documented as superseded and is not independent evidence for acceptance.

## Numerical, work and memory conclusion

All five required classes remain covered at source level: stable nonidentity q and block-crossing swap/rotation; aliasing and two-RHS prepared provenance; checked capacity/multi-reserve failure and rollback distinction; signed/explicit zeros/cancellation/missing/Hessenberg/nonfinite branches; sparse headers and fragmented/high-water retained storage. Logical arithmetic order, pivot/exception checks, exact-zero policy and finite-prefix tracking are preserved by inspection. The direct predecessor/monotone row merge reloads repaired handles. No handle escapes into history or prepared caches, and no copied mutable upper child aliases the original by construction.

**No newly unexplained unnecessary work or retained-memory owner was found.** The review did find and resolve an alias correctness defect and an unsupported test assumption. Potentially avoidable bounded clearing inherited from Task1 is deliberately retained and explicitly charged; duplicate scalar diagonal metadata reads remain bounded, not extra full-matrix work. No solve-time mirror/packing/full invariant/row-index scan, full-arena copy per fill or extra adapter basis solve was introduced. The corrective identity checks add only up to two constant-time checks per solve and no buffer/scan.

The final ledger accounts for every upper field, manager/history/cache/base owner, retained prepared destinations, backing slack, lower/history sharing, setup/export/normalization coexistence, full-copy and refactor peaks. It correctly distinguishes nine explicit manager-side vector requests beyond U construction from library/native/boxing allocations. Solves scale with visited columns/entries/blocks and history; update costs include row searches/gaps, block moves, repairs, rotations, metadata growth and fixed capped-row-growth worst case Theta(f*d+f^2). The narrow dense96 historical-model margin remains a prediction, not a pass; no new retained field proves a lower-bound failure in this source scope.

No timing, allocation-event, peak-memory or sparse/dense before/after comparison was run, as explicitly prohibited here. Source counts do not establish allocation-free commits or a speedup. Exact runtime test-tree/budgets, dynamic failure coverage, measured graphs and the fixed performance gates require separate later Task3 admission. Task2 source acceptance authorizes none of them.
