# S6-I: explicit dual retry boundary qualification

The diagnostic helper explicitly selects transactional retry while preserving
public entry preparation. It is qualified locally for the declared fixtures,
not a replacement for public dual-iteration safety coverage or an x64 CI fix.
Qualification itself changes no production or permanent test file. The subsequent
S6-J permanent candidate is documented separately in S6-DUAL-FIXTURE.md.

## Entry and failure contract

explicit_dual_retry wraps the stop callback, checks cancellation, prepares auto
pricing, validates finite workspace/recoverable invalid weights, retains basis
iteration measurement, and invokes unchanged _retry_simplex_step! with dual,
workspace dual tolerance, basis_refreshed=false and perturb_degenerate=true.
Its catch preserves exact stop exception identity, rethrows nonnumerical observer
wrappers and converts numerical exceptions to DualTermination like public entry.
The only intentional difference is explicit retry selection; ordinary entry may
terminate/refactor before ever reaching that boundary. This narrower API contract
must be explicit in any future test names/comments.

Original selected assertions are unchanged: only four iteration callsites redirect
to the uniquely named helper. No production method is overwritten. The existing
public duplicate-column singular-basis safety test and consistent-small-pivot tests
remain untouched. The helper does not force numerical rejection or inject values.

## Evidence

boundary-1 passes140 qualification assertions plus108 original assertions, exit0.
All16 audit gates pass, whole pins independently match (603 files), and shared
source/test pins match the accepted S6-H census. Saved census TOML is pinned and
hashed; the accepted20 original/public pairs are not rerun. New boundary cases
match all declared selected fields (including status/message/wrapped type, state,
consumed refactors and budgets) from those saved records. Event counts explicitly
prove one rejection per case, refresh only in after-refresh mode, and no pivot or
bound-flip completion in failed/cancelled attempts. The omitted initial ordinary
attempt means event chronology/work is not asserted identical to public entry.

Four additional manager controls compare successful direct-boundary and ordinary
iterations: one completed pivot, exact selected-state equality and original
feasibility. Per-manager early cancellation retains selected state; a stop callback
throws the exact SingularException object; NaN primal entry returns NUMERICAL_ERROR
without an iteration. These controls distinguish the helper from unconditional
rejection and check entry responsibilities. They cover native Float64 fixtures,
not arbitrary precision, hypersparse or adaptive pricing paths.

Raw evidence: .superpowers/simplex-core-architecture/S6-I/boundary-1 and portable
results/S6-I. Julia1.13.0 AArch64, Julia/BLAS1. Previous runner377498/child377499/
driver377490 separately absent on boot20de7dde-704e-41c8-bee7-b8511c0a86b0; no Julia.

## Work and limits

Production cost, allocation and retention unchanged. Diagnostic helper repeats no
basis solve itself; production retry performs actual numerical work under existing
budgets. Entry checks are the public checks, not removed safeguards. Snapshot and
record allocations are bounded by20cases and four controls; retained arrays are
selected-state copies O(n+m). Successful controls use separate privately owned
workspaces. No timing benchmark or speedup claim is made.

This demonstrates a viable isolated recovery contract on the local platform.
It does not explain the actual historical CI row/backend, prove x64 success or
repair the full suite. The natural duplicate fixture's downstream arithmetic is
still platform dependent; successful qualification is not universal portability.
Next is the separate permanent RED/GREEN subplan, preserving public safety tests
and every original recovery assertion. Final independent review accepts this as local evidence but rejects the permanent
S6-J substitution: native downstream work remains platform dependent. See
S6-DUAL-BOUNDARY-REVIEW.md; permanent test restored and master unchanged.
