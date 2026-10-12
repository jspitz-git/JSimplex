# S3-E: three-wrapper counter seam rejected

SOURCE/EVIDENCE ONLY. S3-D inputs, all three inverse bodies, numerical oracles,
closure and whitespace publication supplement remain unchanged. No Julia/import/
compile/native call, executable driver, old script rerun or production/test/env/CI
change. This is the prescribed bounded decision before implementing a driver.

## Decision and concrete call boundary

Reject complete observed internal-attempt accounting for the frozen three-wrapper
route. Consequently stop this mixed-route qualification route without a launch.
The claim is scoped to those wrappers and unchanged factor dispatch, not a general
impossibility of Julia instrumentation or a defect in DSE. S3-C's unqualified
mixed-route evidence boundary remains open; S3-D's exact offline preparation remains
valid but is not runtime qualification.

| Source edge | Why an outer pre-forward counter is insufficient |
| --- | --- |
| hypersparse_updates.jl::_sparse_base_view! -> sparse_solve_view(factor.base) | base_builds increments only after return and base_ready publication. Extraction can throw before it; the counter cannot recover failed attempts. |
| hypersparse_factorization.jl::sparse_solve_view(::UMFPACKBackend) -> _umfpack_scale_mode -> F \\ rhs | Native orientation solve is nested and conditional after scaling scans. No passed counter/callback argument reaches this call. One extraction does not imply one orientation solve. |
| HuangfuHallFactorization constructor -> _hh_extract_base -> _hh_base_scale_mode -> _hh_scale_mode -> ldiv! | HH extraction happens during construction before a post-construction adapter exists. Scaling can skip the solve or fail; an outer constructor count does not distinguish those branches. |
| replace_column! for HH -> _hh_unit_transpose! | The internal operation is nested in replacement, outside the three cloned DSE/checked-weight bodies. Existing source-derived bounds are not pre-forward observations. |

The frozen checked wrapper calls the original _pipeline_basis_solve!; its private
mode keyword affects route choice only. Importing original methods into a new
module does not redirect their internal calls to newly named diagnostic helpers.
The installed functions continue to reference their original module bindings.
The two other private clones route DSE and weight update; neither intercepts native
extraction, orientation or constructor/update internals.

Concrete native ownership also rules out silently substituting a forwarding object:
UMFPACKBackend.factorization is Union{Nothing,Float64UMFPACK}; the native extraction
method uses the actual UMFPACK type. Replacing the factor/backend type would change
factor dispatch and depart from this plan. Counters added before outer calls can
count attempted outer work, but cannot observe the conditional nested attempts,
particularly exceptions before publication. Successful cache fields or post-return
snapshots are not substitutes. Inferring zero orientation from the initial -I
reference is likewise not an observed pre-forward count.

A counter inserted immediately before either native solve in its original method
would need changes outside the frozen three-body seam. Renaming a leaf alone does
not make original callers call it. Expanding constructor/factor/pipeline clones,
rewriting installed methods, debugger/native hooks or full-module cloning are not
qualified by this task. We neither implement them nor open another isolation audit.
No claim is made that every conceivable larger private clone would be impossible.

## Numerical and work consequence

No equations, operation order, tolerances, precision, finite checks, typed floor,
zero handling, residual bounds or certificate requirements change. We do not run
partial numerical cases, tune the fixture, drop managers, relabel inferred work as
observed, or soften the complete-accounting acceptance requirement. S3-D's ten
constructors/twenty updates/sixty outer solves, four internal HH operations and
<=10 orientation bound remain conditional source quantities, never measurements.

No production computation, allocation or retained memory is added. Avoiding an
unsupported driver also avoids speculative snapshots/counter owners or retained
factor copies. This source decision needs no benchmark. No speedup, fullsuite,
backend-cause or original-model certificate claim follows. CI remains disabled,
HH reuse remains disabled, all rejections and S4 bootstrap/cache/init/public-work/
native-retention limits remain unchanged.

## Distinct continuation

Reorder to the broader S5 precision-transfer ownership obligation already named in
S5-INVENTORY-NOTES.md and explicitly excluded by S5-ENTRY.md. The next bounded
question is active cost/bound journal transfer through _check_transfer_journal and
_copy_precision_journal!: independent source/destination ownership, metadata reset,
failed conversion/publication and existing test evidence. This is not a new
precision increase, cleanup-copy optimization, DSE counter workaround or HH audit.
Existing lp_refinement_state_tests.jl is a source reference, not presumed executed
coverage. First reconcile existing evidence and stop if already qualified; do not
invent a defect or rerun accepted S5/S6 restoration cases.

See docs/superpowers/plans/2026-10-13-precision-journal-transfer-contract.md.
