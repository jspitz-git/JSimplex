# S4-H independent coverage and work review

Fresh reviewer: gpt-6-astra/high, read-only, after report/evidence and separate S4-I
plan preparation. No Julia, parser, auditor, diagnostic script execution or writes.
Reviewer independently checked nine targeted hashes and unchanged production/test/CI;
the full526hash verification remains separately identified author evidence.

## Findings and disposition

Critical: none. Important: one, corrected once offline. Minor: none.

The original report incorrectly claimed that all production `_basis_matrix!` calls
use recompute. Reviewer identified twelve additional callers in recovery, native
correction, pivot checks, phase transfer, cleanup and final witness correction.
Several are native-policy routes; checked flags do not exclude them in general.
Author independently enumerated all thirteen call sites and corrected the report's
inventory. S4-I now explicitly excludes those other routes by its actual call
sequence, not by a native-policy assumption. No numerical budget expansion.

Original report and future plan are preserved in results/S4-H/*-before-review.md.
One offline review-amendment.json records three missing documentation predicates
and five passing post-correction checks, including exact source locations/count13
and unchanged28HHsolve budget. No accepted evidence/script was edited or rerun.
No second review and no new deferred Minor. Accept S4-H with this correction.

## Supported scope

Reviewer confirmed setup includes initial HH factor and mandatory FTRAN/BTRAN.
S4-I budget remains2workspaces/2copies/8refactorattempts/10borrowedassemblies/
2publicassemblies/28HHsolves;10native numeric entries and UPTO8internal scaling
validation solves are source-derived counts/bounds, not observed native counters.
Failure discards native workspace before extracted-base publication. Caller basis,
mask and assembly mutations survive; failed kernel is counted but successful
refactor count/event/reconstruction do not execute. This is not workspace rollback.

Original24/25 parser failure and false all_passed remain intact. Reviewer checked
raw historical rows with literal caret escapes:2311passes separately in each failed
CI run. Supplement normalizes only eight stored rows. Assembly loops omit HH;
S4-C driver executes six HH files including integration but excludes the pinned
assembly file. Pin presence is not execution coverage.

## Computational work and memory

No unnecessary production work, allocations or retained-memory increase found:
production/test/CI diff against master is empty. Existing refactorizing recompute
validates twice, assembles once, then successful calls reconstruct vectors and
perform two solves. Proposed conditional guard adds at most m+1+nnz(B) index
comparisons per eligible refactor. Same-typed conversions do not add CSC copies.
Bounded diagnostic snapshots and held native owners are observation overhead;
they cannot establish native retention or speedup. No new benchmark is needed for
this source-only correction.

## Explicitly declined conclusions

S4-I numerical success is untested. Other borrowed-assembly consumers and populated
pricing/hypersparse caches remain outside its scope. Its empty histories cannot
requalify nonempty update-history/pool preservation; accepted G supplies only its
separate direct-factor evidence. Arbitrary controls, other shapes/scalars,
post-LU extraction/allocation failure, representative performance/native retention,
fullsuite/platform correctness and historical CI cause remain unproved. Native
HH reuse stays disabled; no production promotion or safeguard change.
