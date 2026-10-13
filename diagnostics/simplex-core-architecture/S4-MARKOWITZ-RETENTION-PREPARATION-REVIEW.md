# S4-Y independent review

S4-Y ACCEPTED — OFFLINE PREPARATION ONLY. No unresolved findings.

Independent reviewer: `/root/s4y_retention_review`, fresh gpt-6-astra. The author
recorded this result and the exact reviewer-provided hashes in `results/S4-Y/review.json`.
The initial rejected review remains in `review-initial.md`.

Both initial findings are resolved. `driver-reviewed.jl` differs from the
preserved original solely in the two solution comparisons: explicit componentwise
absolute errors use the unchanged `64*eps(Float64)` bound. NaN and infinite errors
fail those comparisons. The ledger now correctly distinguishes ten helpers,
50 explicit vector results, twenty backend solves and twenty solve predicates.
The author classified the ledger correction as Important for admission-budget
accuracy; no Minor finding is deferred.

The historical dimension-512 graph guards and intentional capacity-retention
policy are documented without claiming new runtime evidence. The prospective
schedule remains two constructors, two copies, six refactors, eight captures and
66 predicates. Sparse/dense routes, partial-record failure obligations,
overlapping graph estimates, regrowth contracts and the separate numerical
permission boundary remain satisfactory.

No unnecessary new production computational work, allocations or retained memory
were found. Production remains unchanged. The diagnostic's bounded scans, graph
walks, input copies and solve-check storage are justified and disclosed. No
benchmark or speedup claim follows from this review.

The reviewer inspected, but did not execute, `publish.py`. Its explicit 19-file
evidence whitelist plus five external documents and two generated records yields
exactly 26 publication names. It requires accepted independent review, checks
initial/final/user bindings and repository scope, writes separate closure and
publication records exclusively, verifies exact staged and committed names and
bytes, stops on subprocess failure, and verifies remote branch/master refs.
The future fresh host record and final review artifacts remain publication
prerequisites; review acceptance does not claim publication occurred.

Independent checks passed for all 13 correction bindings, three historical
bindings, 21 original source bindings with only the four explicit before-review
mappings, exact oracle-only inverse and unchanged tolerance, 11 entry-source
and three user-file bindings, all six original S3-G continuation bindings,
unchanged original source.json, empty index, unchanged production/test/CI, and
expected HEAD/master refs. The 12 final artifact hashes are in review.json.

No Julia, supplied verifier/fix/publisher, old audit or numerical diagnostic was
executed. The reviewer changed no files. Acceptance permits the specified offline
admission preparation. Numerical execution requires its own accepted admission
and fresh explicit human permission. Automation remains paused.
