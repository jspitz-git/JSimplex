# Independent final source review — Direct LU Tasks 1–2 preparation

Date: 2026-10-15. Decision: **ACCEPTED FOR OFFLINE PREPARATION ONLY**. No unresolved findings. This disposition is neither numerical acceptance nor permission to execute Julia; a separately bound and independently accepted RED/correctness admission is still required.

HEAD remains `675f5a5293384d53990985e4482511d04cf5bdf3`; master remains `6f68e24e8ddac42b948da8fcc2d636c010751194`. The initial review and its bindings remain preserved. This final review incorporates the initial implementation/algebra/ownership/work assessment and independently reviews the exact corrective test addition and revised preparation report. Exact current and initial file hashes, comparison results, and baseline verification are in `review-final-bindings.json`.

## Resolution of R1 (P2)

`diagnostics/direct-lu-markowitz/reproduce/correctness.jl:124–152` adds `test_scale_selection`, and the main test runner calls it at line 322. The test now calls the actual `_hh_scale_mode`, rather than supplying the expected orientation directly to the exporter. The revised correctness SHA256 is `403f5e2e096312cd56c1fa43b4d69d6660ee72a56f42f563bbaa4676ea6bfdf0`.

For each of the two conventions, the input construction `B[p,q] = (L*U)./scale[p]` enforces the required `P*S*B*Q=L*U` identity. A real dense LU of B supplies the helper solve; the expected Boolean comes from the independently constructed convention. These calls use nontrivial p/q, a nonidentity unit-lower L, signed U diagonal, and nonunit scaling. Detached snapshots check B and the factor/permutation/scaling parts remain unchanged.

The identity-LU cases address both reasons for an unresolved result. With scaling `[2,0.5]`, the helper's identity transformed RHS matches neither the multiplicative nor divisive target. With two entries `nextfloat(1.0)`, the all-one shortcut is avoided, while both targets differ from the identity response by order epsilon and fall within the existing `64*n*eps` allowance; both matches therefore return `nothing`. These are algebra/source deductions, not executed floating-point results. Matrix/scaling snapshots cover input preservation.

There are exactly three additional prospective dense LU constructions (two loop iterations plus one reused identity factor) and four helper calls. The source reaches the helper solve in each case: the finite positive scale vectors are nonunit, so neither early scaling return is taken. These are four intended `ldiv!` calls, plus the helper's multiplication/residual work and test preparation/snapshots; the later admission must include them. No mock, production method replacement, new implementation seam, or hot-path change was introduced. R1 is resolved for offline preparation.

## Independent change and scope verification

A byte comparison of all six current candidate/preparation files against `results/DIRECT-LU-PREPARATION/initial` found only `correctness.jl` changed. Its complete diff consists of the new helper test group and its runner call. `factor-export.jl`, `direct-factor.jl`, `fixtures.jl`, `red.jl`, and `prepare-overlay.py` are byte-identical to their initial reviewed copies. The two implementation files therefore retain the initial review's assessment without hidden implementation changes.

Independently recomputing every hash in `baseline.json` found all 514 tracked source/test/Project/CI entries unchanged. The preparation report (SHA256 `6ab51d24813c97d38da1ee5a990a1767259a491b0fb40167db5330a9fb5f928e`) accurately distinguishes six prospective test groups and three/four added constructions/helper calls from executed results. Its final-disposition reference and admission boundary are appropriate. The saved six PASS amendment checks are text/inverse assertions, not Julia RED/GREEN evidence.

## Work and memory disposition

No unnecessary computational work, allocation, or retained-memory defect was found. The initial review's supporting source assessment still applies: setup/refactor has one ordinary factorization, owned export/validation/packing and conditional native orientation work; per-solve lower operations are O(nnz(L)+n) with owned scratch and no new full-factor validation or factor copies; successful direct state does not retain the ordinary backend or temporary CSC U. Immutable extracted lower data/history may remain shared by saved copies. Full transactional refactor sacrifices ordinary backend and manager-buffer reuse; that explicit lifecycle cost remains to be measured, not interpreted as a speedup.

The correction adds only bounded test work on 2-by-2 matrices. It changes no production or candidate hot path, allocation behavior, retained state, precision or tolerance. No benchmark was needed or authorized for this review. Actual parse/dispatch behavior, numerical results, compilation, timing, allocation counts and retained/peak memory remain unqualified.

No Julia query, parser, import, compilation, solve, test, benchmark or historical script was executed during either review. Native direct solves still omit UMFPACK combined-solve iterative refinement; these prospective residual checks cannot establish equivalent stability. Task3 cost work, Task4 public-solver integration and any production promotion remain outside this acceptance.
