# MA-C independent source/design review

Decision: REJECTED pending one Important offline correction. Critical: 0; Important: 1; Minor: 0. This is source/design review only, not runtime or performance acceptance.

## Important MA-C-I1 — Guard speculative diagonal lookup

The plan at lines 39–43 passes a scalar diagonal to eligibility and checks it before row arithmetic, but original src/markowitz_factorization.jl:509–516 reads `backend.diagonal[pivot]` only after every multiply/subtract. A malformed shortened diagonal plus a two-term Rational{BigInt} row with an initial zero-times-infinity product yields original DivideError (Base gmp.jl:1059–1063), whereas eager diagonal lookup yields BoundsError. An in-bounds unassigned diagonal likewise yields an early UndefRefError. This violates the stated malformed-input exception parity even though neither path publishes the current row.

Concrete fix: eligibility receives the diagonal vector and pivot, tests `checkbounds(Bool,diagonal,pivot)` and `isassigned(diagonal,pivot)` before reading, and returns false on failure. The fallback must perform the original row arithmetic before the original final diagonal lookup. Add both combined-error regressions; do not catch/retry arithmetic exceptions. This is a bounded contract/plan correction; no candidate or numerical execution is needed now.

## Independently verified source claims

All 20 read-time SHA-256 bindings match. Both continuation before-copies match mapped hashes. HEAD/master match the stated baselines and git diff for tracked src/test/Project is empty. Full bound hashes are in review.json. Host evidence records 44 unique groups and no matches, plus boot/ref/protected-state information; this review binds that snapshot, not a fresh numerical-run admission or a replay of historical audits.

Installed SaQfc Project is MA 1.8.1. Its BigFloat buffered sub_mul computes a separate product into ambient-precision scratch, then subtraction with the untouched seed. Base mpfr.jl:575–626 creates fresh ambient BigFloat results. This supports the first-term rule; rounding the seed into scratch first would add an operation. MA uses ROUNDING_MODE[] while Base mpfr.jl:247 consults CURRENT_ROUNDING_MODE. The proposed whole-loop mismatch fallback is necessary and appropriately retained.

MA Rational.jl product buffer has two rationals and one BigInt (five leaves), product output has two, subtraction buffer three, accumulator two: twelve independently created BigInt leaves. The first seed is read directly and subsequent subtraction aliases only the private accumulator. Source shows the relevant GMP in-place integer operations; runtime leaf identity checks remain required. Base rational.jl:424 routes rational `/` through `//`; Base gmp.jl:1093–1097 implements the exact Rational{BigInt} method with two fresh BigInt owners. Exceptional branches assign into those new owners. Ordinary final division is therefore the right publication boundary, without an extra copy; qualification still must test identity, zero/unit/exceptional cases.

Finite rational guarding preserves Base nonfinite branches; finite exact arithmetic does not need widened precision. Finite BigFloat operands can overflow/underflow, and the planned ordered-operation, signed-zero and flags checks remain necessary. No runtime equivalence claim follows from these reads.

Caller inspection confirms PFI, triangular forward, hypersparse dense fallback, recovery and precompile routes. The explicit recovery method inspected is MarkowitzBackend{Float64}, and precompile currently warms Float32/64; these are fallback controls, not evidence of target-type MA execution. Frequency is per selected sparse row per backend forward solve, including repeated solves in larger workflows. No selected work exists for dense-core-only factors.

## Work, allocation and retained-memory assessment

No unnecessary NEW production work, allocation or retained-memory cost is introduced by this documentation-only milestone; production source is unchanged. The prospective candidate adds O(K) eligibility reads/checks, per-call lazy scratch (two BigFloat objects or twelve rational BigInt leaves), and retains independent per-row division outputs. Scratch reuse is only within a call and limb growth is unbounded in operand bit size. There is no new backend storage, vector/matrix copy, solve, conversion or persistent cache. Correctness checks must not be weakened for speed.

K rational multiplies/subtracts are high-level counts, not equal GMP work: MA decomposes rational operations into integer gcd/div/mul/sub calls while Base uses GMP rational kernels. The prospective full-solve measurement, construction/first-use split, per-call scratch accounting, kernel attribution and post-growth small cases are therefore essential. The future schedule is deliberately not runnable yet and requires exact total budgets/admission in MA-E. No benchmark is required for the current documentation change; no speedup, native release or performance acceptance is claimed.

No Julia process/import/parser/compilation/numerics or old auditor was launched. No production, plan or report file was mutated by this review. Only this fresh review.md and review.json were created.
