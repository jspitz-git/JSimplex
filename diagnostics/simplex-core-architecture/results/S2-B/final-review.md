# S2-B final independent review: bounded offline amendment

Decision: **ACCEPTED for source/design closure and the described offline S2-C candidate/test-source preparation only.** No unresolved Critical, Important or Minor findings remain in this bounded amendment review. This is not runtime, numerical, allocation or performance acceptance, and grants no Julia parsing/import/execution or production change.

The initial rejected review remains preserved in review.md. Its initial verdict was correct for the original packet. This final review assesses the single offline correction pass, including its preserved intermediate text and final exact-type clarification; it does not relabel the original text as accepted.

## Finding dispositions

**I1 — resolved at the design/plan level.** The report now requires the original vcat behavior whenever either input is empty and requires direct empty-adapter construction to fail before evaluation (S2-PRICE-AUDIT-STORAGE.md:39-57). The plan specifies an inner constructor that enforces the domain, factory fallback assertions, direct-construction rejection, and nonempty recognized-parent alias rejection (2026-10-13-price-audit-values-preparation.md:45-71). Thus the identified initially-empty compensation/error_sum owner cannot enter the borrowed adapter through the helper or its constructor. The fix retains both-parent dataids forwarding and fresh separately allocated normal quality scratch. It expressly does not promise general foreign-buffer/unsafe_wrap overlap detection (report:66-76; plan:65-70). This is a bounded ownership contract, not a modification to Base.mightalias or a runtime demonstration.

**M1 — resolved; the author's Important grading for next-plan eligibility is accepted.** The plan now requires two explicit factory methods, Vector{Float32}/Vector{Float32} and Vector{Float64}/Vector{Float64}; union-element and mixed-type inputs remain on generic vcat. The inner constructor additionally requires exact T equality with Float32 or Float64. Union-element fallback and direct-construction rejection are explicit offline test requirements (plan:45-59). The original upper-bound-only ambiguity is removed at the design level. Actual implementation dispatch remains subject to S2-C review and later separately admitted execution.

**M2 — resolved at the test-contract level.** Hardware floating comparisons must use UInt32/UInt64 reinterpretation equality, preserving NaN payload and signed-zero distinctions; nothing and exact values have explicit comparison rules. Only initialized scratch outputs are compared, with early-return state specified (plan:72-80). Expectations must be frozen before any future launch. These are planned assertions, not tests reported as passed.

Critical findings: none. Important findings: none unresolved. Minor findings: none unresolved.

## Work, memory and arithmetic scope

**No unnecessary new production work or memory cost is introduced by this documentation-only amendment.** It adds no production implementation. The original independent source verification remains the evidence for the unchanged source baseline; this bounded pass did not repeat the 513-file comparison or the 531-pin sweep.

The planned guard cost is explicit: up to four O(1) emptiness checks, two in the helper and two at the constructor, plus up to two exact-type comparisons (report:83-90; plan:55-58). Rechecking at construction is justified because direct construction otherwise bypasses the ownership domain. These are constant-size checks at each reached price audit, not full-vector scans. Whether compilation removes any of them is unmeasured and must not be assumed.

Eligible inputs still replace only one m+N-slot concatenation with two borrowed references. Any empty side and unsupported scalar/storage forms retain materialization. Per-access routing remains a potential cost proportional to the existing input and residual accesses; neither residual term order nor finite, compensated or wider fallback checks are changed by the design. Prediction copies, reconstruction, quality scratch, basis solves and certificates remain. There is no persistent cache, added update-chain-dependent work, or asserted native-memory release. The full numerical/work/memory assessment in the initial review remains applicable apart from the corrected domain and added constant-size guards.

The plan retains whole-price-audit sparse/dense fixed-input measurements, all samples, interleaving, allocation events/bytes, separate setup/import accounting and a distinct guarded admission (plan:94-104). No benchmark was required or run for this text amendment. No speedup, runtime alias correctness, arithmetic equivalence, default-policy benefit or whole-solver improvement is established.

## Bounded evidence verification

Read the final report and plan plus review-fix.json and review-fix-final.json. Used independent standard-library stdin file/hash checks only; no repository script, Julia parser/import, native or numerical work was executed.

- All seven final bindings in review-fix-final.json match their actual files, including the initial rejected review and reviewer-check.json.
- All four intermediate bindings in review-fix.json match their preserved states. Its two original live-path entries map to the corresponding *.after-empty-fix snapshots; they must not be compared as though they pinned the amended final live files. Its two *.before-review entries match directly.
- Both original report/plan *.before-review snapshots match their original source-check.json pins.
- The intermediate record contains four true checks; the final record contains five true checks. The RED/GREEN language describes offline textual criteria only.

The final report SHA-256 is `903391ed6c6ce1fed91a3dd503032ba3bde2874e868565f0b8f44fdab8752e83`; the final plan SHA-256 is `a2f76357e74c341bd97cb68ffb47c641bd3e7d895e3906ff2b016c0c91943d08`. review-fix-final.json SHA-256 is `341c42bce1d372b8d7e7a028c32271e88e9bf923df635ca03af1063f680ac1ab`. Exact bounded verification results are in final-review-check.json. No original/intermediate evidence was rewritten by this review.

The next eligible work is offline S2-C source/test preparation and independent review under the amended plan, followed by its separate closure. Runtime admission remains a later gate. S6-AQ's evidence wait remains local to S6-AQ; the S2-A, S6-J, whole-AF and broader controller/reconstruction rejections and gates remain intact.
