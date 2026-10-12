# S6-AE: dyadic dual factor component qualification

Status: accepted after fresh independent gpt-6-astra numerical/work review.
No Critical, Important or Minor findings. See S6-DUAL-DYADIC-COMPONENTS-REVIEW.md.
Base4ce8289/master3c0af5c. No production/test change. New eight Float64 cases:
four managers x fresh B or real -I setup/refactor B, using immutable AD exact inputs.

components-1:73/73 assertions,exit0,25audit gates626pins. Preflight517shared source/
test/runtime/environment/launcher hashes and AD11source hashes match. Input rational
strings are linked to AD SHA, converted exactly, actual CSC matrix reconstructed
independently by auditor. Original dual options/default native policy and threads1
recorded, globals preserved. All input vectors/matrix preserved, updates remain empty.
Runner409838/child409839/launchgroup409829 separately absent,noJulia,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0.

All eight real unit BTRAN outputs exactly equal[-2^22+1/2,2^22,0,0], prepared
FTRAN duplicate outputs e1, correction BTRAN outputs[2^-22,0,0,0]. Exact residuals
of all three equations are zero. PFI uses dense unit vector; triangular managers use
production _UnitTransposeRHS metadata. Prepared cache count0 ->1 for triangular
FTRAN, retained after different-destination correction BTRAN, then cleared by one
explicit destination invalidation. PFI fallback has no prepared cache. This does
not qualify cache ownership across a public candidate or future wrapper dispatch.

Eight production native compensated-quality entries on declared rho each returned
finite=true,reliable=true, residual exactly[h,h,0,0], h=2^-22. No replacement,
fallback forcing, certificate or redundant solve_quality call. The helper internally
performs compensated products/enclosure; eight is its entry count, not arithmetic
operation count. A reliable backward-error estimate does not imply correct pivot:
AD's duplicate row coefficient is-h while exact column pivot is0. No safeguards
have been weakened to reconcile them.

## Work and memory

Exactly8 initial factorization entries,4 refactor entries,24 basis solve entries
(8unitBTRAN,8preparedFTRAN,8correctionBTRAN),8quality entries,8explicit invalidations.
Source also shows3internal triangular destination invalidations per triangularcase;
these are not added basis solves. No factor update/copy, workspace/public iteration,
observer, adapter or old numerical replay. All entry counters increment before calls;
no exception occurred, so this run does not test throwing-call accounting.

Sparse native factor setup creates real UMFPACK base. Triangular wrappers initialize
identity upper/work/row scratch, not a second numerical factorization. Prepared
FTRAN creates/reuses2cache slots and copies spike/direction; no zero-allocation claim.
Diagnostic snapshots own tiny vectors (length4, at most8cases), and quality scratch
owns residual/compensation buffers. No production computational work, allocation or
retained-memory change; no cost benchmark or speedup inference is warranted.
Backend internal symbolic/numeric lifecycle is not instrumented here.

## Scope and next gate

AE qualifies raw component endpoints, native residual and separate-destination
prepared-cache behavior on local Julia1.13.0 AArch64. No general native symbolic
reuse, historical x64 factor/cause, hidden trajectory, observer neutrality or public
rejection/callback/cancellation proof. Same mathematical structural point is not
proof of same tolerance envelope or native historical arithmetic.

Next separate S6-AF bounded public-boundary qualification must install a real-forward
wrapper preserving factor sharing and production dispatch, two declared unit outputs,
all original policies/callbacks/assertions, complete pre-forward counts after budget
consumption and full-kernel counts. It must reject any unplanned numerical refactor,
not promote S6-J or call retry directly. Permanent repair requires later separate
RED/GREEN/review/master gate. Do not rerun AE/AD/old accepted drivers/auditors.
CI disabled,master unchanged,broaderS6/fullsuite/x64 unresolved.
