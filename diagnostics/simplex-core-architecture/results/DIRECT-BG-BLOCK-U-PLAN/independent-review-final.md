# Independent final design/work/memory review

Verdict: **ACCEPTED — final planning deliverable only.** No unresolved editorial or blocking design findings remain. This acceptance does not authorize implementation, Julia, numerical admission, benchmarks, production integration or claims that the memory/performance gates pass.

This bounded review compares the complete final documentation diff against the preserved files reviewed in independent-review-v1.md. The only changes are explicit cumulative row-growth costs/repeated-fill tests, composed delete/merge and split-staging counts, direct predecessor access in elimination, and the illustrative container-graph margin. Representation, B32/A256 constants, reserve policy, numerical/order/ownership/failure contracts and all fixed acceptance gates remain unchanged.

All six clarification checks agree with the actual diff. A new inline read-only Python check verified every hash in review-clarification.json and verified that original budget-check document hashes match the preserved before-review files. It did not execute budget-check.py or any historical script. The final spec/plan hashes below apply to current documents; the initial review/budget hashes apply ONLY to the preserved before-review versions. No retroactive PASS or hash substitution is implied.

Resolved review points:

- The capped row reserve now explicitly states worst-case Theta(f*d+f^2) copying and backref repair, distinct from linear cursor movement, with a repeated_row_fills test and future work counters.
- Work accounting explicitly adds deletion31 plus merge32 for up to63old moves; split33final assignments are separate from staging reads/writes. This removes the possible aggregate32 interpretation.
- Elimination explicitly uses the source predecessor rather than repeatedly searching through generic setters.
- Dense96 container arithmetic remains an illustrative model derived from old graph accounting, not a physical-header measurement or new graph PASS. The roughly800–900B prospective margin and4096B append risk are candidly stated.

Accepted design risks remain, not unresolved gaps: narrow/possibly failing checkpoint memory margins, quadratic cumulative row-growth traffic, row-container overhead, fragmented retained capacity and local block movement. Task1 must produce the full supported ledger and stop/revise if a proven lower bound already fails; later source/tests must establish correctness and later independently admitted fixed measurements must establish runtime gates. None of these risks is silently waived by accepting the plan.

No unnecessary production work or memory is introduced by this documentation-only clarification. The prospective costs identified in v1 are now explicitly assigned to future source review, repeated-fill tests and work/memory accounting. Numerical safeguards remain unchanged. No benchmarks were required or run. No Julia or foreign-process interaction occurred; no old evidence or author documents were edited by this reviewer. Only this new final report is written.

## Exact final bindings

- `docs/superpowers/specs/2026-10-16-direct-bg-block-upper.md`: `2dbd5c01efa9b9b2853decad11bddf9211df8bd16d4fc272c43509dd0378356f`
- `docs/superpowers/plans/2026-10-16-direct-bg-block-upper.md`: `839dcf646e28b27c8d1894f536169fd898796713543f4825e7b7a7f9294bfd39`
- `diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-U-PLAN/review-clarification.json`: `353f1630bcb70340667964bb5700f862987e5298ea4c25022fb157e9d7bcf3c4`
- `diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-U-PLAN/spec.before-review.md`: `edca28d6a17ece0219b1ec417c931348809d5a0a957a73edefc1309644d845f2`
- `diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-U-PLAN/plan.before-review.md`: `0bff6ece2badafa68019adb4af6f3f48f3f4452df5086a7dec98e0c6814308d2`
- `diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-U-PLAN/independent-review-v1.md`: `b1acc2713a91834e6a722e97149b65b9ff21e546e239ed536aa69c3ab2709c2f`
- `diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCK-U-PLAN/budget-check.json`: `f6baaa7f75964d30f28a67d663f561ca6829e9c7e8631e9e32ab04b39ee1767e`
