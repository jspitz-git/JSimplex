# KLU and UMFPACK fixed-basis comparison implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compare fresh factorization, FTRAN/BTRAN, numerical behavior and memory of KLU and UMFPACK on identical preserved basis matrices.
**Architecture:** Isolated diagnostic module from byte-exact pinned KLU.jl source, using the already installed KLU 2.3.5 shared library. Two arms, fresh factors, no symbolic reuse or basis-update implementation; no production method overwrite or environment installation.
**Tech Stack:** Julia 1.13.0, ordinary Test, SparseArrays/UMFPACK, vendored KLU.jl revision 2975044cb3ac1f76f9d3eeef7ee6deedfe8375a0, Python resource guard and offline summary.
**Spec:** docs/superpowers/specs/2026-10-29-ss-block-graph-design.md, KLU gate only. User now explicitly requested execution of this comparison. This does not authorize graph-local SS implementation or direct KLU export.

## Global constraints

- One Julia, Julia/BLAS 1, 2 GiB heap hint, 8 GiB VM, available RAM >=6 GiB, swap <=1 GiB; absolute shared 1800 s guard. Fixed short workload, no multi-hour loop or tuning.
- Preserve existing sources/tests/environments/master/CI and all frozen evidence. No MPS parse/public LP solve; no medium factorization, big/largo/AnyMOD or aliases.
- Fresh host refs and full 711 groups AND sessions/noJulia, independent concrete admission before launch; source/runtime/library/input hashes immutable during execution. No package manager or compilecache worker: --compiled-modules=existing.
- KLU uses its native L*U+F representation and complete native solves. No factor extraction inside timed windows and no dense L*U reconstruction.
- UMFPACK controls are exactly existing _NATIVE_PIVOT_ONE (PIVOT_TOLERANCE=1, IRSTEP=0, other defaults including automatic strategy unchanged). KLU tol=1, BTF=1, AMD=0, scale=sum=1, positive maxwork=10. These are backend-policy comparisons, not proof of identical numerical pivot rules. Record full controls.
- Match numerical matrix and RHS bytes across arms. Normwise residual tolerance min(1e-10,128*n*eps64), independent directed 256-bit residual enclosures, known-point error<=1e-6, factor growth<=1e8 and stored L/U/F<=5M. No numerical tolerance changes or promotion of production precision.

## Review focus

- KLU CSC constructor must own values and indices; convenience klu(B) aliases Float64 values in this source. Poisoned tiny caller input must not change retained solve.
- Transpose solve and nonempty F coupling remain exercised; no dropped inter-block coefficients.
- A single irreducible block is expected for both sparse-cycle256 and dense256 controls; block-triangular control must have32 blocks.
- KLU major-version2/native ABI and local wrapper source agree; downloaded header is version-matched upstream, not installed-build proof. Capture actual loaded library paths and hashes at runtime.
- Input preparation, library API RHS-copy cost, compilation, GC, numeric/symbolic native memory, Julia graph and RSS have different meanings and must be reported separately.

### Task 1: Prepare concrete driver and numerical/resource admission

**Files:** diagnostics/klu-umfpack/2026-10-29/{driver.jl,inputs.toml,vendor/**,native-source/**,vendor-provenance.json,native-source.json,library-pins.toml,guard/**,run.py,historical-groups.json,command.json,pins.json,REVIEW-ADMISSION.md}.

**Interfaces:** driver.jl receives one fresh output TOML path; run.py owns a new exclusive run directory; source includes precede main function definitions/call (no world-age boundary). Vendored source is never modified.

- [ ] Prepare first160 accepted exchanges from runtime-30000/runtime-40000/fast0507 tapes; assemble explicit B at0/80/160 with negative-identity artificial columns. Use actual next entering column, deterministic dense cost RHS and actual next leaving unit RHS. Preserve/check binary hashes and provenance; no original MPS numerical work.
- [ ] Add exact deterministic sparse irreducible, dense irreducible and32 coupled-block controls (all256 rows), ownership poison and singularity tests. Ordinary Test only; no custom test recorder/testset stack.
- [ ] Record one cold qualification/factor arm per case: three normal RHS solves plus two known-point solves; directed residual on three normal outputs; one factor extraction outside all hot windows for fill/scaling/growth/native statistics. RSS before, factor held and after release are process context, not native free proof.
- [ ] For each case/arm run two warm complete build+solve samples (8 triplets each), then five alternating measured build+solve samples (32 triplets each). One triplet=two FTRAN+one BTRAN. GC before each sample is outside windows. Constructor/input conversion and complete API solve costs stay inside their windows. Check output residuals and immutable input hashes after every sample. Measured compile/recompile zero required, GC retained.
- [ ] Expected full workload:12 cases x2 arms x(1 cold+7 samples)=192 successful main builds;2 ownership builds+2 expected singular attempts=196 total factor attempts. 8522 FTRAN and4272 BTRAN total (including known-point and ownership solves),No extra reference factors/solves. Expected168 warm/measured samples,120 measured samples,24 cold qualifications. Counts must match literal driver before launch; no assumed test assertion count.
- [ ] Bound loaded shared libraries to the pinned Julia SuiteSparse files. Pin every new driver/helper/vendor/header, launch command and guard; no old script rerun. Obtain independent source/admission review before a fresh launch.

### Task 2: Execute, analyze and publish

**Files:** fresh comparison-1/**,results-1.toml,analyze.py,analysis.json,summary.csv,REPORT.md,REVIEW-RESULTS.md,closure/publication records.
**Interfaces:** standard TOML records contain case/arm/round, stage timing/bytes/events/GC/compilation, residuals and output hashes; analyzer joins round-identical pairs and rejects missing/changed inputs or controls.

- [ ] Fresh full host check; freeze review-bound pins; execute once under the existing owned runner/child identity handshake and guards. If only a deadline fails, preserve evidence and use a separately reviewed longer unchanged run as already authorized; no tuning for numerical failure.
- [ ] Verify exit, pins, assertions, all cases, counts, compile/recompile, controls, residuals, actual libraries, full-group closure and memory guards. A failing numerical case is not accepted or silently removed; keep its cold records and any skipped measurements.
- [ ] Summarize paired medians/ranges/MAD for factor, per-FTRAN and per-BTRAN time, bytes/events and native reported current/peak sizes; report whole fixed workload and preparation separately. GC counters may include native callback traffic, not pure Julia objects. Native size reports and Julia graph/RSS are not interchangeable. No full-solver speedup claim.
- [ ] Explain one-block behavior: same KLU sparse left-looking algorithm, ordering over whole block, F empty, normal FTRAN L then U and BTRAN U' then L'; permutation/scaling still apply, including singleton and no-BTF cases. Distinguish genuinely irreducible pattern from merely lacking visually obvious blocks. Evaluate controls against real matrices.
- [ ] Independent result/work/memory review; exact new staged/committed blobs and failfast diagnostic commit/push with remote refs verified. No master change.
