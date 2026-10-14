# Direct LU / Markowitz — RED accepted, correctness stopped

2026-10-15. The requested two short attempts were independently admitted and
executed once each. **RED passed its expected-failure contract. GREEN is NOT
ACCEPTED:**89 assertions passed, then one unexpected test error stopped the first
of12 groups. The remaining11 groups were not run. No cost experiment, public
solver integration, retry, candidate edit or production promotion followed.

## Observed results and admission

| Phase | Observed result | Inclusive process time | Result audit |
| --- | --- | ---: | --- |
| Reference RED | 0PASS,3expectedFAIL,0ERROR; child exit1 | 5.838962662s | 15/15 PASS |
| Candidate GREEN | 89PASS,0FAIL,1ERROR; child exit2 | 8.769139723s | FALSE: incomplete phase evidence |

The time includes launch/import/compilation/termination and is not a benchmark.
RED and GREEN sealed inventories contained4,407/4,425 entries; independent
admissions bound4,254/4,272 exact paths. Launch inventories contained4,409/4,427
entries. All remained unchanged. Exact phase reviews and raw/log/pin/reservation/
invocation/process records are preserved under results/DIRECT-LU-ADMISSION.

RED's three failures are the intended missing export/factory definitions on the
reference. GREEN reached the candidate package at the pinned path and the exports
group; its record expected100PASS but captured89PASS+1ERROR. started-1/group-1/raw
and logs survive. Later start/group files are absent because execution stopped;
the canonical auditor correctly refuses the incomplete phase. Its original false
record remains unchanged. A separate postcheck records17 true and3 false gates
(audit acceptance, expected GREEN exit and complete counts), not a replacement PASS.
Both stages' full pin checks, source identity, resource/termination records pass.

RED had5 memory samples plus terminal, GREEN8 plus terminal; minimum available
RAM22,431,504/22,228,584KiB and maximum swap0. Postflight covered198 then200 unique
prior/runner/child PGIDs AND sessions with no matches or Julia. The guard enforced
one Julia/BLAS thread,2GiB heap hint,8GiB VM,6GiB available-RAM floor and1GiB swap
ceiling. No timeout occurred. Both one-attempt slots are consumed.

## Cause and coverage limits

The actual stack reports `ArgumentError: pattern of the matrix changed` from
SparseArrays/UMFPACK, reached by correctness.jl:74:
`lu!(backend.factorization,sparse(2.0*B))`. This is the test's deliberate mutation
of the original source backend after exporting factors, not a direct-manager
update or a public solver failure.

Fixed fixture order plus89 passed assertions locates the exception at the native
stored-zero fixture: six preceding fixtures contribute86 assertions, followed by
three export checks. That fixture explicitly stores16 CSC entries,12 of them zero.
Installed source routes scalar multiplication through sparse broadcast, which
omits zero results for ordinary mutable CSC; the following sparse call copies the
result. Thus the source-derived refactor input has4 stored diagonal entries,
whereas the original factor's symbolic pattern used16. Installed lu! defaults to
reuse_symbolic=true and copies the replacement CSC before numerical factorization.
This explains the captured pattern-change error. Intermediate CSC arrays were not
captured;16→4 is a source deduction, not an extra runtime measurement.

The89 successful assertions cover only the executed export-test prefix, including
the permutation-sensitive mixed Markowitz case. They do not qualify full export
ownership on the final fixture, all three direct managers, updates/refactors,
other precisions, fallback transitions or the focused unchanged tests. The planned
19,527 assertions and complete work ledger are prospective, not executed counts.
No numerical defect of the candidate or original solver is established by this
harness failure, and candidate correctness remains unqualified.

Both logs also contain a world-age binding-access warning before invokelatest.
The calls executed on pinned Julia1.13.0; the actual fatal error is the distinct
UMFPACK pattern mismatch. No claim of future-version/Revise compatibility is made.

## Disposition

Use a separately preserved and reviewed test-only repair next: create an owned
copy of the fixture and scale only its nzval buffer, keeping colptr/rowval and
explicit stored zeros intact for the source-backend refactor. Qualify that pattern
contract explicitly; retain the final ownership checks and original fixtures.
Any driver warning cleanup must also be separately bound and reviewed. Do not
rewrite this candidate/test/driver or any accepted/rejected manifest, raw result
or audit in place, and do not reuse either consumed output reservation.
A new short attempt needs its own exact admission; standing user permission
already covers short runs and need not be requested again. No such attempt is
prepared or launched by this result record.

Actual src/test/Project/environment/CI and master6f68e24 remain unchanged. The
supplemental postcheck and source analysis are new post-execution records, not
launch pins. No production work/allocation/retention change or speedup claim is
introduced. Independent result review is recorded in
results/DIRECT-LU-CORRECTNESS/review.md; the broader plan remains open and Tasks3–4
cannot advance on this failed correctness run. CIoff/HHdisabled/automationpaused.
