# Direct LU / Markowitz — isolated candidate and test preparation

Date: 2026-10-15. Scope: Tasks 1–2 of the accepted
[plan](../../docs/superpowers/plans/2026-10-14-direct-lu-markowitz.md).
This is OFFLINE preparation. No Julia query, parser, import, compilation, test,
solve or measurement has been executed. Numerical correctness, dispatch and cost
remain unqualified. Actual src/test/Project/environment/CI/master are unchanged.

## Candidate

New files are under [reproduce](../direct-lu-markowitz/reproduce/):
`factor-export.jl`, `direct-factor.jl`, `fixtures.jl`, `correctness.jl`,
`red.jl` and `prepare-overlay.py`. The last file makes a fresh ordinary source
overlay, refuses existing destinations, copies only tracked src/Project files,
and inserts exactly two includes after the HH implementation. Its inverse
recovers the original root source. User Manifest/LocalPreferences are not copied.
The overlay is source preparation, not a launch or environment admission.

The private Float64 export owns canonical CSC L/U, permutations and original-row
scaling for P*S*B*Q=L*U. Existing HH extraction is reused without enabling HH
symbolic reuse. Malformed exports throw; unsupported backends/types and ambiguous
native scaling have explicit fallback. Other precisions keep ordinary factories.

FT, SS and BG are initialized from exported packed U and q. One ordinary backend
is constructed per setup/refactor; successful direct construction creates no
identity U. A stable typed lower wrapper supports direct/fallback transitions.
Refactor builds a complete replacement before publishing fields. Copies share
only read-only Float64 lower/permutation/scaling/diagonal data; upper state and
scratch stay private, with ordinary history ownership rules. Successful direct
factors retain neither the full ordinary backend nor temporary CSC U/workspace.
Native combined-solve UMFPACK refinement is absent on the direct path; this
experiment makes no equivalent-stability claim. Outer recovery/certification and
all production defaults remain unchanged.

## Prospective tests

RED contains three missing-contract assertions on the unchanged reference;
these are not claimed to have failed. GREEN has six test groups: owned export
identity/core permutation, malformed/unsupported exports, actual orientation selection,
normalization/scaling,
manager lifecycles/aliases/indexed solves, and direct/fallback transitions.

Seven nonsingular fixtures include empty/scalar, diagonal, coupled sparse/dense
core, pure dense core, scaled/permuted n16 and explicit stored zeros. The coupled
fixture and wrong unpermuted-L21 discriminator are copied from the accepted
plan. Independent Rational{BigInt} evaluation uses exact stored Float64 tokens
and the predeclared residual bounds. Both scaling conventions are exercised
through constructed parts. A separate test calls the actual orientation helper
with real dense LU factors for both conventions, plus neither-match and
both-match cases that must return nothing. This adds three prospective dense LU
constructions and four helper calls/solves; inputs must remain unchanged.

There are 84 planned paired lifecycle setups (7 fixtures × 3 managers × 2
backends × 2 normalization modes). For n>=2, each has eight updates, entering
FTRAN followed by distinct DSE FTRAN, unchanged direction replacement and
unit-RHS BTRAN. Copies diverge after update2; original refactors after update4.
Tests also cover source-backend mutation after export, unsupported Float32 /
BigFloat256 / Rational{BigInt}, unsafe normalization, aliased RHS, indexed modes,
singular and resized refactors, preserved old factors and forced fallback.
These are source schedule counts, not observed calls or assertion totals.
Test-only residuals, snapshots, source-backend mutations, additional solves and
factorizations must all be counted by the later admission. No claim of a complete
runtime/backend budget is made here.

## Computational work and memory review ledger

| Frequency | New candidate work/storage | Qualification limit |
| --- | --- | --- |
| Setup and every refactor | One ordinary factorization; owned extraction of L/U/p/q/scaling; structural/finite scans O(nnz(L)+nnz(U)+n), one n-bit permutation scratch reused twice | Markowitz extraction includes dense-core scans and triplet-to-CSC work; native extraction includes conversion and private HH workspace |
| Native export | Two private n-vectors passed to orientation helper; helper can perform a native solve plus its own residual temporaries/scans | Source-derived conditional work; not a measured native call budget |
| Normalization | n diagonal lookups, one nnz(U) candidate-values buffer and scan, commit copy only after all divisions pass; retained n-vector D on success | Unsafe divisions retain unnormalized direct; no small coefficient is discarded |
| Packed initialization | Own indices/values for each U column, q inverse, ordinary manager scratch/history/cache; BG has one shared owned row-order object | Temporary CSC U is released from the resulting graph; GC/native release timing is unproved |
| Each FTRAN/BTRAN | O(nnz(L)+n) lower substitution plus permutation/scaling and optional D operations; one persistent n-vector for transposed lower work | No new per-solve validation, factorization, allocation API, growing ledger or full-L copy; actual allocation behavior unmeasured |
| Copy | Read-only lower arrays shared; fresh lower scratch and ordinary deep upper/maps/scratch, existing shared-history retirement | Retained old copies deliberately prolong history/lower lifetime in correctness tests only |
| Refactor publication | Complete new manager constructed before swapping fields; old state remains reachable until replacement and by any saved copies | Sacrifices ordinary refactor workspace reuse for transactional safety; whole-lifecycle cost including this penalty must be measured |

Source review is required to state whether any avoidable work or memory remains.
No allocation count, retained-memory bound, speedup or production promotion is
inferred from these source counts. Task3's paired lifecycle measurement includes
setup/export/normalization and both refactors; it is not prepared or run here.

## Evidence and next stage

Evidence is in `results/DIRECT-LU-PREPARATION`. A fresh host preflight records boot,
PID/start_ticks/command identities, complete prior groups AND sessions and no
Julia; baseline hashes bind 514 tracked source/test/Project/CI files. The accepted
plan/spec remain frozen. Initial ordinary overlay is preserved under
`.superpowers/direct-lu-markowitz-preparation/candidate`.

Initial independent review requested changes for missing direct orientation-helper
coverage. The initial six candidate files/report, review and 26 read-file bindings
are preserved. A separate test-only amendment adds that coverage; six offline
text/inverse checks pass, not Julia tests. The independent final disposition is
recorded in `results/DIRECT-LU-PREPARATION/review-final.md`; any acceptance
applies to offline preparation only. Next stage after offline acceptance is
concrete RED/correctness admission: explicit calls, complete test-only counts,
focused unchanged test selection, dependency/runtime bindings, fail-closed raw
and log handling, fresh host preflight and independent admission review. Only
then may the bounded RED<=30s and correctness<=90s processes run. Standing short
run permission is sufficient; no automatic cost run or production integration.
