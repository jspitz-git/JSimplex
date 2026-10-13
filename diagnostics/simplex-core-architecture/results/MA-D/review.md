# MA-D initial independent whole-package review

Decision: **NOT ACCEPTED pending R1 and R2**. Offline source review only; no Julia/parser/import/compilation/Pkg/launcher or old scripts. All36 current bindings and all four complete source inverses verified independently.

## R1 — important: Dense-core floating endpoint assertion overstates the mathematical oracle

candidate-tests-complete.jl: The dispatch test asserts out == ones for I+ones(3,3). Generic LU includes rounded 1/3 multipliers; exact all-ones mathematical solution does not guarantee bit-exact all-ones computed floating output. The dense cost fixtures have the same distinction. This can reject unchanged correct reference behavior before the candidate is qualified. Preserve exact rational endpoints; require candidate/reference exact value/sign/precision parity and a frozen, independent exact-arithmetic residual bound for floating full solves, without loosening upper-row sequential parity.

## R2 — important: Isolated-upper attribution lacks a bounded first-use wrapper call

cost-schedule.md: Each fresh side process budgets one first full solve and four isolated upper calls in one timed window, while MA-E requires zero compilation in measured windows and forbids hidden solves. The separately renamed reference upper function and its measurement wrapper are not necessarily compiled by a full backend solve. The same issue applies to a separate scratch measurement wrapper. Freeze an explicit first-use/steady partition of already-budgeted calls or explicitly recount added warmup calls and total terms/copies/deadlines. Do not rely on earlier warm process pairs to warm fresh processes.

## Review class 1: source-consistent, runtime outstanding

Private scratch only; first seed direct; MA BigFloat mul/sub buffers and Rational 12-leaf composition read borrowed operands; original division publication retained. Actual aliases, retained outputs and scratch leaf identity tests prepared.

## Review class 2: changes required: R1

Ordered nonfused products/subtractions and ambient precision retained; scoped/global mode guard invokes generic path. Nonthrowing diagonal bounds/assignment precede speculative read; original fallback preserves combined-fault order. Base flag symbols exist. Finite exact binary oracle arithmetic reviewed; its eight synthetic checks are mathematically consistent, not independently rerun or runtime qualification.

## Review class 3: source-consistent

All 36 source-check hashes independently matched; complete Markowitz/module/Project/runtests inverses matched (Project byte and semantic checks). Only two exact target entries; generic hardware caller path shares the original loop. Original RED guards avoid missing helper execution. Prospective runtests is integration-only, admission must invoke only the new test file.

## Review class 4: changes required: R2; no performance acceptance

48 cases, 20 processes, 960 visits/constructors, 4800 full solves, 3840 upper calls/reset copies, 76800 reset assignments, 82080 upper multiply/subtract pairs, 640 separate scratch calls reconcile. Star singleton-column-first then density stop at2 gives S=n-2,K=n-1,E=1; dense core E=0. Extra O(K) eligibility and call-local scratch are correctness costs; actual GMP/native retained memory remains unmeasured.

## Review class 5: source-consistent; admission deferred

Frozen initial test preserved; complete canonical extension and offline-TDD override recorded. Source-check is structural evidence only. Qualification120+costglobal600=720sec; RED30 gives750sec; individual cost process60sec does not extend global600. MA-E must still enumerate test/observer calls, exact loading, audit/refusal and current resource guards.

## Work and memory ruling

No unnecessary production work or memory cost is introduced: actual production src/test/Project is unchanged against master. Candidate adds explicit O(K) read-only row eligibility and one lazy scratch set per eligible solve; no extra basis solve, matrix conversion, output copy, persistent cache or backend retention was found. These costs are justified safeguards but their benefit is unmeasured. R2 requires making diagnostic first-use work explicit, not hiding additional solves. No speedup or runtime correctness claim is accepted.

Exact reviewed-file hashes are in review.json. Preserve this rejected review and every original before corrections; a subsequent review must bind corrected canonical artifacts explicitly.
