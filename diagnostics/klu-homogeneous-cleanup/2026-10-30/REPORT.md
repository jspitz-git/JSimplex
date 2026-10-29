# Existing homogeneous cleanup did not repair the saved weight RHS

**Verification FAILED; no production integration is accepted.** Ordinary Test reports99pass/3fail/0error/102total, exit1. The three failed assertions are exactly the expected acceptance of the post-correction point, one each for native KLU, graph-local KLU and UMFPACK. All other numerical, preservation, alias, small-component and rollback checks pass. The raw failures, original expectations, driver and strict auditor remain unchanged.

The existing `_clean_homogeneous_terms!` lowers the componentwise error from1 to about1.08868e-9, but the unchanged limit is2^-44≈5.68434e-14: the proposed point is still approximately19152times above the permitted error. The full check correctly refuses it. This bounded experiment answers the user's request to verify the proposed route: the existing cleanup alone is insufficient for this case.

## Method and scope

Use only frozen saved runtime-30000/B0 and its first unit-RHS witness from diagnostic8b97ba68. There are no new factorizations, basis solves, model parses, LP solves, simplex iterations or correction attempts. One tape and one witness deserialize; one independent sparse B assembly (dimension28453, hash `7b6ab789d7f49d73ec163eee3e2c5c5e9207dadd5f66a3b31972755b367c6d5c`). For each backend label, evaluate its saved original point and reconstruct its saved correction using the original ordered Float64 additions: six points total. These labels identify saved-point provenance, not new backend calls.

A diagnostic-only wrapper allocates a private proposal, calls the existing cleanup once, and evaluates the entire original system with unchanged production `solve_quality!`. Only changed finite reliable proposals may be returned; otherwise it returns an independent unchanged copy of the original input. Another ordinary quality call verifies the returned point. No wider solve_refinement flag, arithmetic precision, tolerance or production method is changed. The wrapper is not a production API or live-workspace publication implementation.

All full runtime input points are finite and initially have relative error1. Every cleanup proposal is refused; the returned point and quality match the original. Input solution, RHS, A/B, tape/witness hashes and basis are preserved. Both original helper and quality function are the current master source; all actual launch pins remain unchanged.

## Numerical outcomes

| Saved point | Cleared components | Proposed relative error | Proposed max absolute residual | Accepted |
|---|---:|---:|---:|---|
| native KLU / initial | 199 | 1.0886810988705967e-9 | 7.203382616825621e-14 | false |
| native KLU / post-correction | 195 | 1.0886809702691526e-9 | 7.203383572232641e-14 | false |
| graph-local KLU / initial | 188 | 1.0886810369911366e-9 | 7.203383076541066e-14 | false |
| graph-local KLU / post-correction | 185 | 1.0886809702691526e-9 | 7.203383572232641e-14 | false |
| UMFPACK / initial | 194 | 1.088681080763956e-9 | 7.203382751343635e-14 | false |
| UMFPACK / post-correction | 201 | 1.0886809702691526e-9 | 7.203383572232641e-14 | false |

Before cleanup, max absolute residual is approximately9.84e-17 for initial points and1.2522535092207576e-17 for saved correction trials. Thus the cleanup substantially improves the worst componentwise ratio but worsens the maximum absolute residual. No old strict criterion accepts a new point. Equal quality summaries across post-correction proposals do not imply bit-identical vectors; their hashes differ.

Source explains the limitation: after handling single active terms, the helper proposes clearing small solution components occurring in homogeneous equations, using a cutoff based on solve_tolerance*maximum(abs,x). That local amplitude criterion does not establish that a component can be removed without disturbing other coupled equations. For example, all three post-correction proposals remove component20573≈5.415001153430187e-14. The experiment does not prove its exact mathematical value or identify the maximum-residual equation; it proves that the aggregate proposed point still fails the same full componentwise check. No further numerical diagnosis or tuning was run.

## Controls that passed

For Float32 and Float64, in both transpose orientations:

* A known exact3x3 solution has essential components delta,-delta,1, with delta2^-40 or2^-60. The tiny pair cancels in a homogeneous equation but is required by another equation. The helper proposes removing it; the entire-system check refuses that proposal and the exact original point is retained.
* A2x2 identity case with a false tiny component is repaired and accepted by the same full quality check.
* A genuinely wrong large component remains unreliable after cleanup and is refused.
* Inf/NaN inputs skip cleanup and remain refused with original values preserved.

The12finite control records and8nonfinite assertions pass. They establish the tested proposal/validation/retention mechanism, not an all-input guarantee, a proof that real-case deleted components are exactly necessary, or callback/cache/exception-safe publication into a live solver.

## Execution, rejection and evidence

Independent concrete admission:20checks/100bindings; original source inventory95, actual launch101bindings. One guarded process, fixed1800s ceiling, actual9.1477s including launch/JIT/diagnostics. Ordinary Test3.0s,99pass/3fail. Nine resource samples: minimum available RAM22083756KiB, swap0, child maxRSS686180KiB. Exit1 and rejected supervisor are preserved; no timeout or kill. Supervisor attempted abnormal-result cleanup after the expected-zero contract failed; saved/full727groups AND sessions are absent afterward, no Julia. No numerical retry or modified expectation.

The frozen strict auditor was executed once and refused at `native-KLU/post-correction_expected_pass`, exit1; `strict-auditor-rejection.json` preserves stdout/stderr. A separate new post-exit `classify_rejection.py` passes280checks/109bindings and verifies **rejection classification only**: all six saved-point returns are refusals, exactly the original three expected-acceptance failures occur, all other controls/pins/input/ownership/resource closures hold. Its `diagnostic_accepted=true` and `candidate_accepted=false` are intentionally distinct; this is no waiver or passing qualification.

`results-1.toml` records before/proposed/returned qualities, changed solution indices and IEEE bits, preservation hashes and descriptive observation costs. The separate local returned-point witness is1821348bytes, SHA256 `1d6bd28e096d42cadc8edd3527b990bab7ebe7424ff8cc87e021e15b135e3db1`; its recorded path is under `.superpowers/klu-homogeneous-cleanup/2026-10-30`. Every returned runtime point is the original because every proposal was rejected. Old first-RHS witness remains unchanged, SHA256 `3e8bf2b4c22471872fc8f72b0c7511b3fca7967139aa01a037b74ce341aaf66d`.

## Work and memory assessment

No production change or added production work/memory. Actual diagnostic work:18whole quality evaluations,6cleanup calls,12quality scratch constructions,3saved-trial vector reconstructions and6retained output copies, plus constant-size controls and hashing. Passes cost O(n+nnzB); proposals/copies/metadata cost O(n), and include compensated scratch allocations. The wrapper deliberately copies refused inputs to keep returned ownership independent. The fixed six returned vectors use6*n*8=1365744bytes of Float64 payload, plus basis/RHS/serialization metadata; the observed witness is about1.74MiB.

Admission review identified a bounded avoidable diagnostic allocation: each transposed cleanup receives a new length-n Int singleton buffer although that branch does not use it. This is six transient227624-byte arrays, about1.30MiB cumulative. It is charged rather than changed after admission; production has no such new allocation. Each large wrapper record reports2049480bytes/27events and approximately1.55–2.20ms in this process. These are single descriptive diagnostic calls with private copies/scratch; they are not a before/after benchmark, production cost forecast or speedup evidence. JIT/runtime/input/scratch contribute to process maxRSS; it is not a native-memory ledger.

The failed cleanup must not be integrated as a successful fix or used to reopen the failed complete-weight benchmark. A future targeted repair would need to account for coupled equations and still meet the unchanged full criterion. This experiment supplies no permission to increase tolerance, blindly snap additional values, drop coefficients, enable a broad numerical profile or make another attempt.
