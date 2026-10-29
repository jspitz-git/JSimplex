# Independent KLU/UMFPACK admission review — initial rejection

Decision: **REJECT the currently pinned launch pending the important growth-scaling correction below.** No Julia or native numerical process was executed by this reviewer. This review covers the concrete fixed workload and one guarded process with an absolute limit of at most 1800 seconds; it does not admit general solver, medium, large, update-chain, tuning, or repeat work.

Reviewed worktree: `/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl`. Baseline/worktree HEAD: `f9f1e9b4076bd541150dedba8df26efc6429d34a`. Local master/origin-master: `c0fa748ffa61ccb7c1caaf248c40324f60bc737b`. `git diff --name-only BASE -- src test Project.toml Manifest.toml` was empty. Review followed the supplied AGENTS.md work/memory requirements and the requesting-code-review independent-review assignment.

## Immutable bindings

All **45** entries of `source-pins.json` were independently rehashed and their resolved paths checked: zero differences. The complete inventory is incorporated by this exact manifest SHA-256: `45785c95299c6d29162ede626bcab335399db443c0ab54cae4ef330d8d06e670`.

Principal individual SHA-256 bindings:

- `driver.jl`: `5ec0a0bbeeffac38e091ae6135adbf30fa567287568f298201466b7ddfee7217`
- `PLAN.md`: `bf44aff683a3991d17f78f96c947bad00f746fca831eba8ab0da87c3fcbb2231`
- `command.json`: `f846ca7893c0680ea68500a5e98e40f39ee34c31321bb3756614161beb5e9e97`
- `run.py`: `dcc84f235fbcb9f2a55ba3e97fa14f628880b7c66617141c06b5914154596691`
- `host-before-review.json`: `39e6d6279fac873421916e09f1fe2bee72881f7b360512e7007f0d6536ab4f65`
- vendor `KLU.jl`: `12b02ec9286953c970d1f6bd802054eb383e7f5555478795f343058cbd29dd50`
- vendor `wrappers.jl`: `80741e95df39ddb3f53664d478eee3e632149685820b87d894f1fef319276603`
- upstream version-matched `klu.h`: `fb92acc4cf9fbc48a07ceaf98de3ad468840649e5f1015d3968b6439b4369c56`
- installed `libklu.so.2.3.5`: `4bee1c4607475cc1a618d47b372f86e6dfb2ed2c994e024f551aaaf16719f430`

## Important issue to fix before launch

`driver.jl:99–100` treats `f.Rs` as indexed by the original matrix row. KLU returns these scale factors in the **final pivot row order**. The vendored accessor copies the extracted native Rs directly, so `B.nzval[k]/s[B.rowval[k]]` is the wrong scaled entry when the final row permutation changes scale positions. This invalidates the intended growth metric and numerical growth gate; it can overstate or understate growth. Map the extracted factors through `f.p` into original row order before scanning B, or compute the same row-sum scaling consistently from B. Keep the scale convention as division and the existing threshold unchanged. This correction belongs outside the timed windows.

Independent source confirmation: upstream SuiteSparse v7.10.1 [klu_factor.c](https://raw.githubusercontent.com/DrTimothyAldenDavis/SuiteSparse/v7.10.1/KLU/Source/klu_factor.c), lines 109–115 and 323–331, explicitly permutes `Rs[k] = original_Rs[Pnum[k]]`; [klu_extract.c](https://raw.githubusercontent.com/DrTimothyAldenDavis/SuiteSparse/v7.10.1/KLU/Source/klu_extract.c), lines 93–98, copies `Numeric->Rs` without undoing that permutation. Read-only fetched byte SHA-256 values were respectively `053b6316f5ffe0b0e9cf444eda647650e6ecbf923befa57e71e1edc00d3f7538` and `c8e06cef23ae9024679586616062a3b13b7b2309221ae6bf00a1ea8542293856`. These are upstream source evidence, not proof of the installed build. UMFPACK's original-row multiplicative `f.Rs` convention matches the installed Julia source identity `L*U == (Rs .* A)[p,q]` and the existing UMFPACK metadata expression.

## Reviewed numerical behavior and APIs

The module is included before driver definitions and main execution; it is the pinned exact source, with ordinary Test and no Pkg/cache installation. Static Julia/API review found no additional obvious syntax or dispatch defect; this is not a Julia parse or runtime certification. The native 64-bit common/symbolic/numeric fields and invoked factor/solve/tsolve/extract signatures match the saved KLU 2.3.5 header. Header macros state 2.3.5. The header is version-matched upstream source, not an installed-build artifact; binary hashes and the runtime version/loaded-library checks remain required.

Both constructors own colptr, rowval, and nzval, as shown by their source copies. The chosen KLU constructor avoids the aliasing convenience `klu(B)` path. The caller-value poisoning tests exercise retained solve independence; source inspection establishes index ownership. Full native KLU solves retain L/U and F coupling. The transpose dispatch uses `klu_l_tsolve`, and cold known-point tests check both directions. No reference factor or extra reference solve is present.

UMFPACK changes only pivot tolerance to 1 and refinement to 0; automatic strategy and its other defaults stay in place. KLU uses diagonal-preference tolerance 1, BTF, AMD, row-sum scaling, and bounded matching work 10. These backend policies have different pivot/ordering rules and must not be described as identical partial-pivot behavior. Controls are recorded.

The directed 256-bit cold residual enclosure is valid for the supplied finite Float64 matrix/RHS/solution values: conversion is exact, separate downward/upward sparse accumulation bounds the residual, and a downward denominator times tolerance gives a conservative acceptance threshold. For transpose, the row/column target and induced norm are reversed correctly. No production precision is raised. Ordinary residuals, known-point error, stored factor size, input hashes, and compilation assertions complement this check. Failed cold qualification remains recorded and suppresses measurements; the enclosing Test failure must reject the overall run. Runtime results and exact counts still need independent postrun review.

The controls have provable structure: the sparse cycle is strongly connected with a nonzero diagonal and one full 256-row block; every dense-control entry is nonzero, giving one block; the 32 dense eight-row blocks have only forward interblock coupling and therefore 32 blocks with nonempty F. For one irreducible block KLU still uses its sparse left-looking factorization on that whole block, and F is empty. The workload does not implement a dense fallback or factor dropping.

## Work, allocations, and retained memory

I found **avoidable cold diagnostic work**, but no unnecessary production work (there are no production changes), no extra hot-loop invariant scan, no reference factor, and no material avoidable retained-memory issue that independently blocks this fixed experiment. Each new factor performs its intended O(n+nnz) owned CSC copies and zero-base conversion plus fresh symbolic/numeric analysis; there is no symbolic reuse or chain-length dependence. Julia KLU and UMFPACK API locks/checks remain inside their respective measured solve calls. Each KLU solve necessarily copies an n-element RHS into its destructive native API buffer in the chosen adapter; UMFPACK's three-argument API consumes distinct RHS/output buffers directly. This API-cost difference must be reported, not described as pure kernel savings. Scratch outputs x/y/z are reused across repetitions and allocated outside solve windows.

Cold `metadata` currently reads f.L, f.U, f.F, and f.Rs separately. The wrapper invokes native sort/extract separately for these accessors (up to four calls, fewer for empty F), despite the comment/plan saying 'only once'. Mapping via f.p adds another extraction if that accessor is chosen. This is outside every timed sample, bounded to one metadata collection per cold arm/case, and does not justify changing vendor code. Document the actual calls; native `mempeak` observed afterward may include this sort/extraction workspace. A direct combined native extraction would avoid repeated work but is unnecessary for admission once accounting is honest.

Untimed validation performs three residual/norm checks plus whole-input/RHS hashes after each sample, with O(nnz+n) scans and temporary residual vectors. The induced infinity norm is recomputed for two forward RHSs; it could be cached, as could invariant cold residual denominator metadata, but this is finite untimed certification work, not a measured speed claim. Cold directed enclosures allocate O(n) BigFloat vectors and scan nonzeros. All 12 cases are retained intentionally, O(sum(n+nnz)); returned results retain scalar metadata, control copies and hashes, not the factors or extracted L/U/F. GC between samples is outside the timing windows, while GC incurred within windows is recorded. The fixed run measures the plausible sparse/dense API differences; no before/after performance assertion is made at admission.

Native KLU current/peak bytes, UMFPACK size-unit-based symbolic/numeric reports, Julia summarysize, allocation events, and RSS are different quantities. Julia summarysize excludes native pointed-to allocations. RSS is process context affected by compiler/allocator retention; release RSS is not native free proof. Native callback allocations may enter Julia GC counters. Compilation, case preparation, warm samples, measured samples, cold qualification and cleanup must remain separate in reporting.

Literal count audit: 12 cases × 2 arms × (1 cold + 2 warm + 5 measured) = 192 successful main factor builds; 2 ownership builds + 2 expected singular attempts = **196 factor attempts**. Warm/measured solves total 24 × (2×8 + 5×32) = 4224 triplets, hence 8448 FTRAN + 4224 BTRAN. Cold qualification adds 72 FTRAN + 48 BTRAN; ownership adds 2 FTRAN: **8522 FTRAN, 4272 BTRAN**. There are **24 cold qualifications, 48 warm samples, 120 measured samples**, 168 warm/measured samples total. No assumed Test assertion count is used.

## Resource and launch admission scope

The recorded host check covers all **711** historical groups and sessions, with no conflicts, about 22.7 million KiB available RAM and zero swap usage. Master refs match the required unchanged value. This snapshot must be refreshed immediately before launch. Guard/run Python files all pass static AST parsing. Reviewed launch uses one Julia, one Julia/BLAS thread, existing compiled modules only, 2 GiB heap hint, 8 GiB address-space limit, a global advisory lock, live-Julia rejection, parent-death/startup identity handshake, pidfd ownership checks, memory pressure checks, immutable pins and bounded cleanup under the shared deadline. No numerical work is done on medium or original MPS files.

After the important correction, regenerate exact source pins and obtain a follow-up independent acceptance bound to those new bytes. A final launch manifest may add the accepted review and source-pins manifest as stated by the coordinator, without source mutation. Rejected current bytes must not be launched under this review. No other blocking finding was identified.
