# S4-L fresh numerical and computational-work contract review

Fresh gpt-6-astra/high read-only review: no Critical or Important findings in the
reviewer's classification; two Minor findings. The author regraded both Important
because they affect the premise of future measurement and the central memory
classification, then fixed them in one offline pass before any numerical execution.
No second review or numerical rerun was requested.

1. Phase0 was always reference-first and phase1 always candidate-first. The fixed
   eight-round phase sequence is 0,0,1,1,0,0,1,1 with odd RC/even CR ordering.
   Each phase now has two observations in each ordering per fixture. Counts unchanged.
2. The report called wrapper-owned CSC storage native-owned storage. It now explicitly
   identifies those arrays as Julia CSC arrays owned by the UMFPACK wrapper; pointed-to
   native Symbolic/Numeric storage remains a separate memory category.

Before report/plan preserved; review_fix.py observes RED3false -> GREEN3true,
exit0, no Julia. The original source-contract inventory's plan hash intentionally
matches the preserved BEFORE plan. Closure verifies that original binding and the
new plan's separate hash; no rewriting or rerunning accepted source evidence.
No new deferred Minor. Old unrelated deferred findings stay unchanged.

Reviewer independently recomputed four exact rational fixtures, dominance, nnz,
coefficient/RHS binary64 representability, all RHS bits and CSC-value hashes.
All stated work counts and source-derived orientation bounds were confirmed.
Selected native Info sizes survive the internal orientation solve; their origin
and units remain distinct from global native allocation accounting. GC outside
windows limits future conclusions to measured refactor windows, not the total
allocation/free lifecycle. Native-retention qualification remains OPEN.

Reviewer sampled30of527 source inventory hashes, all matching; this is not the
separate author's full527 rehash/15checks. No Julia, stored script execution or
reviewer edits. Source/test/CI diff from master empty. No unnecessary production
computational work, allocation or retained memory found. The proposed candidate
adds O(n+nnz) index comparisons at refactor frequency, without coefficient scans
or additional basis solves. Bounded diagnostic copies/GC/graph scans are disclosed;
no documentation benchmark or production promotion is justified by this review.
