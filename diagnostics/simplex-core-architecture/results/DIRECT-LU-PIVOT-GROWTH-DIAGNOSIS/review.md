# Independent review: saved pivot growth diagnosis

Accepted. No actionable findings in the bounded offline diagnosis. This accepts
the report and supporting saved-data analysis, not numerical qualification, a
new solve, a policy implementation, a cost1 retry, or admission to cost2.

`independent-review-check-3.py` is the canonical independent check. It uses its
own binary64 bit-to-rational decoder and dense coordinate representation, reads
the frozen input and both factor snapshots, and executes none of the author or
previous diagnostic scripts. Its 33 checks pass. It independently recomputes the
exact factor products, all 269 nonzero representation errors, top-error ranking,
complete row ledger, full residual and representation/application vectors,
controls and metadata, growth ratios, and strict row-dominance condition bound.
All 11 analysis read-time bindings and all 514 baseline hashes match.

The saved evidence supports max U=231235.78947368418 at (31,31), final-factor
scaled growth=245688.02631578944, and cond_inf(B4)<=153/103. The zero at original
(87,1) corresponds to three stored-factor products summing exactly to -53/2^42.
At original row87 both representation and application consistency contributions
are nonzero; their difference is 9928545/144115188075855872, 18.861415966018026
times the unchanged bound. The earlier 15/18 passing residuals and three failed
DSE residuals remain failures; saved fresh, ordinary and base DSE outputs match.

The installed zero-based wrapper constants agree with the report's one-based
slots: unsymmetric strategy, pivot tolerance binary64 0.1, IRSTEP=0, DROPTOL=0.
The exact U-diagonal extrema and rounded diagonal ratio reproduce Info.
The retained header supports the threshold-pivoting interpretation and its
accuracy/work caveat, and describes RCOND as a diagonal ratio. Its documented
UMAX prose typo is correctly distinguished from its macro comment and data.
The report correctly limits upstream source evidence: it is neither installed
native-build proof nor a runtime pivot/rounding trace. The observations establish
stored growth and cancellation; no specific rounded native operation or separate
forward/back-substitution error is claimed. No FT update-history defect or
UMFPACK implementation bug is inferred from this evidence.

The next-direction paragraph is appropriately limited to a separate source/design
plan comparing pivot policy with refinement while preserving defaults initially.
It explicitly retains ownership, copy/refactor propagation, fill, work, scratch,
and memory obligations, and promises no remedy or automatic numerical admission.
The unexecuted continuation/closure sources were read; this review does not assert
their future runtime outcomes or bind mutable continuation output.

Work and memory: no unnecessary production work, allocations, or retained memory
were found. The 514-file baseline matches, and the changed scope is documentation
and bounded offline saved-data arithmetic only. No added setup, refactorization,
iteration, candidate, recovery, or certification cost exists in production. The
analysis allocates exact representations and product/ledger data for fixed 96x96
snapshots; this is one-time diagnostic work. No runtime speedup or allocation
claim is made, so a benchmark is neither warranted nor performed.

Failure preservation: the author's initial missing provenance filename and its
one-filename correction are verified. The reviewer's first new script/result are
preserved after a KeyError caused by assuming identical output-container schemas.
The second version/result preserve an overbroad all-output equality check; saved
non-DSE outputs need not match bitwise, and the report asserts only DSE equality.
Version 3 corrects that check to the actual claimed DSE vectors and passes. These
review-harness errors do not indicate an author-report defect. No failed version
was overwritten, and no old auditor, Julia process, native factorization/solve,
compilation, benchmark, or test suite was executed during this review.
