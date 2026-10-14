# Independent final review: common factor export and Markowitz direct LU plan

**Verdict: ACCEPTED as a plan for subsequent offline candidate/test preparation. No unresolved actionable plan findings remain.** This acceptance does not admit a Julia launch, validate an implementation, establish performance or numerical stability, or authorize production promotion. The plan's separate implementation reviews and sealed numerical/work-memory admissions remain required.

This was a source/document review only. No Julia process, import, probe, compilation, test, benchmark or historical script was run. This reviewer wrote only review artifacts and did not modify the spec, plan or production files.

## Reviewed versions and provenance

Checkout HEAD: `9ea533ebcba2d5611a839b8e4bb03b59c2b1c371`.

Current document SHA-256:

- `docs/superpowers/specs/2026-10-14-direct-lu-markowitz.md`: `1f53fca7568e94a0302eb646b405715ac81e00121172f4e29e17b2f085f381fc`
- `docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md`: `fb0b3609260394b0719423301284a0713475af793db53e1a828c0dce12efb5d7`

The unchanged `review-initial.md` has SHA-256 `fcfe8cadcc5e529ccfad688679da60335548ea15528ef6b263b65b88c0ae4d20`. Preserved `spec.before-review.md` and `plan.before-review.md` match the respective initial reviewed hashes recorded there. The intermediate `plan.after-first-review.md` has SHA-256 `e4e431f147c2e7600960845d8911b8f46c224b49637f15f67c846c5332f7f6df`; an additional defect found in that intermediate amendment is documented below, rather than erased from the review record.

## Resolution of initial findings

1. **Sparse/core permutation coverage — resolved.** Task1 now freezes a coupled block fixture and requires a negative discriminator: leaving the sparse-to-core lower coefficients unpermuted must fail the full exported-identity oracle. The final five-entry E produces a source-derived sparse pivot sequence 4, then 3, with two distinct nonzero multipliers affected by the core row permutation. The executable fixture must assert these properties rather than infer coverage from matrix shape.

2. **Conflicting entering-FTRAN RHS — resolved.** Task3 explicitly orders entering FTRAN of `a_t`, DSE FTRAN in a different destination, replacement using the unchanged entering direction, then unit-RHS BTRAN. It removes the unused alternating RHS, freezes B4/B8 and entering-vector tokens outside timing, and updates the explicit reference basis with precisely the entering column. This matches the direction/provenance contract in `src/triangular_factorization.jl:847–871` and `src/triangular_spikes.jl:1–4,79–95`.

3. **Missing reusable-refactor regime — resolved for the stated bounded workload.** A second refactor now follows update eight, with separate first/second timing. This reaches the ordinary backend spare/output branch (`src/factorization.jl:323–338`; `src/markowitz_factorization.jl:561–574`). Native symbolic reuse still depends on matching sparsity; the second refactor is not a universal promise of symbolic reuse. The plan limits selection to this eight-update/two-refactor workload, with no long-chain or recovery-heavy extrapolation. Final reachable-memory reports explicitly include ordinary spares and pools, and explicitly exclude long-history, peak and native live memory claims.

4. **Native refinement limitation — resolved.** Spec and plan explicitly state that direct native substitution loses UMFPACK combined-solve iterative refinement while outer recovery and final certification remain unchanged. The limitation must remain in results/selection; equivalent native stability is not claimed. This is consistent with `diagnostics/basis-direct-lu/README.md:11–15`. The small experiment does not qualify general scaled/cancellation-sensitive stability, and the text no longer implies that it does.

The additional recommendations are also addressed: exact native `_hh_extract_parts`/`_hh_scale_mode` selection; finite-coefficient export validation; BG-owned stable row map and dirty upper initialization; a stable concrete fallback wrapper plus direct/fallback/direct tests; and explicit valid public solver options including `presolve=false`, `scaling=:off` and steepest-edge pricing. The fallback injection seam remains test-local and must be frozen/reviewed before execution.

## Intermediate amendment finding and correction

The intermediate plan used `E[:,1]=[1,2,3,4]/8`, with other E entries zero. That would not satisfy its new coverage assertions. `_markowitz_pivot` takes singleton columns first and pops them from the end (`src/markowitz_factorization.jl:208–212`), while initialization pushes singleton columns in increasing order (`:371–373`). Columns 4 and 3 would therefore be eliminated before the coupled column 1. The nonzero counts would be 24, 23, 22 as the remaining dimensions decrease 8, 7, 6; the dense-switch test at `:377–379` then fires before any coupling enters the sparse lower columns. L21 would still be zero.

This was reported as a blocking amendment defect before any run. The final plan instead sets E11=E22=E33=E14=1/8 and E44=1/2. Its 25 initial nonzeros are below the dense threshold, and none of the first four columns is singleton. The singleton-row search takes row 4, then row 3 (`:217–235`): counts fall 25→22→20, and the core starts at k=2. The first sparse lower column contains 1/8 and 1/2 at original rows 5 and 8. The remaining identity rows do not alter C, whose specified row swap exchanges the unequal entries through the dense core permutation. That is precisely the relocation at `src/huangfu_hall_factorization.jl:236–239` that the initial fixture failed to test.

This is static reasoning from the implementation, not numerical execution evidence. The final plan correctly labels it prospective and requires executable assertions and the incorrect-unpermuted negative check. The correction is an offline review amendment, not fixture tuning after numerical results.

## Remaining contract and feasibility checks

The original factor, permutation and normalization algebra is unchanged and sound. `B0=inv(S)*P'*L*D` gives forward lower solve `inv(D)*inv(L)*P*S` and transpose lower solve `S*P'*inv(L')*inv(D)`. Owned Float64 factor data and read-only lower sharing remain compatible with the stated manager copy contracts. Complete candidate construction before publication supports failed/resized refactors without modifying the old live factor. Unsupported scalar/backend exports remain distinct from malformed output and factorization exceptions.

The native helper choice avoids the older orientation helper's absolute sparse-matrix copies while retaining a checked orientation and possible backend solve (`src/huangfu_hall_factorization.jl:156–199`, versus `src/hypersparse_factorization.jl:17–49`). Markowitz extraction already folds dense-core pivots into owned output (`src/huangfu_hall_factorization.jl:205–255`); no duplicate decomposition or HH upper-row index is needed. BG initialization is consistent with its `UpperRowIndices` field type and shared owned row map (`src/triangular_factorization.jl:18–45,441–499`).

Factory routing remains narrow and feasible at the existing options dispatcher (`src/factorization.jl:428–432`). The planned checks preserve ordinary PFI/HH/adaptive/other-precision routes; the public LP now pins valid options (`src/options.jl:149–156,225–232`) and asserts actual selection without assuming a particular trajectory or refactor count.

The amended work counts are correct: 2 processes × 24 cells × 10 pairs × 2 sides = 960 lifecycles. These contain 960 initial constructions, 1,920 explicit refactors, 7,680 updates, 15,360 FTRAN and 7,680 BTRAN. Orientation solves, detached checks and additional correctness calls must be ledgered separately as the plan requires. Stage process ceilings still sum to 420 seconds. Source review cannot establish that compilation, all checks and measurements fit these ceilings; the exact admission must retain timeouts as outcomes and cannot silently extend the schedule.

## Explicit computational work and memory assessment

**I found no remaining unnecessary computational work, allocation or retained-memory requirement mandated by the amended plan.** This is a design assessment, not certification of an unwritten implementation or a speedup claim. The exact helper choice resolves the initial avoidable full-matrix-copy concern, and the second-refactor segment resolves the identified comparison gap within the now-explicit workload scope.

Setup/refactor still legitimately incurs backend construction, extraction, validation, permutation/scaling assembly, optional normalization and packed-U construction. Markowitz extraction scans the dense core twice, O(core_dimension^2), and allocates triplets plus CSC output, with additional sparse-factor traversal and O(nnz(L)+nnz(U)+n) output storage (`src/huangfu_hall_factorization.jl:208–255`). Native orientation may add one solve, four factor traversals and work vectors. Transient backend/export/normalization/packed storage coexistence must remain in allocation accounting. The plan forbids duplicate factorization, discarded identity U, unused HH indices and retaining temporary U/backend/workspace after successful direct export.

Each direct solve adds no planned full-factor validation or export: lower solve/scaling costs O(nnz(L)+n), followed by unchanged upper/history algorithms whose work depends on factor fill and update-chain length. Existing prepared-spike checks/copies remain; numerical safeguards are not removed to improve timings. Recovery/final certification are separate from component timings and remain unchanged. Ordinary reusable backend state versus fresh direct candidate construction is now represented in the second-refactor comparison.

Retained memory is deliberately scoped to the state after the second refactor, including pools, capacities and ordinary backend spares. It does not measure long active histories, peak memory or native-owned live memory; ownership tests in Task2 do not convert into such memory measurements. No production-code benchmark is required for these document-only changes. Actual work/allocation evidence, zero measured compilation, pair variability, GC and scoped numerical results remain prerequisites to any later selection claim.

Proceed only to the next stated offline preparation/review step. No numerical or production acceptance is implied.
