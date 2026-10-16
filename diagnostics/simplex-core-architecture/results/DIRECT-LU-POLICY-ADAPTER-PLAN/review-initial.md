# Independent initial review — changes requested

Scope: direct LU policy adapter plan; source/design only. No Julia or project execution.

1. The Task1 negative-test paragraph promises a factorize-keyword zero-call sentinel for every supported fallback precision, but its specified exporter/factorize seam accepts only AbstractMatrix{Float64}. The generic four-argument factory instead delegates directly to Factor(B,backend,policy). Separate the Float64 sentinel evidence from generic negative tests and source/inverse evidence of current production rejection before work; do not claim generic runtime call counting through an unavailable seam.
2. Task2 says “failed singular/resized refactors”. Frozen correctness.jl:280–287 expects singular failure and successful resizing to a 3×3 factor. State failed singular construction transactionality and successful resize/copy independence separately so future test implementation preserves the contract.

The policy propagation design, frozen extraction algebra, matched cost schedule, and source-only scope are otherwise consistent with the sources inspected. No unnecessary new production work or memory cost was found in this documentation change. The proposed enum and constructor-only forwarding are constant-size work; future full-manager rebuilding and extraction costs remain to be measured, not asserted as a speedup. Final acceptance is withheld until the two test-contract issues are corrected.
