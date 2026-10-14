# Current-master short time breakdown

Human authorization: perform a short representative measurement of current master,
then recommend the next concrete optimization. Standing authorization permits short
numerical experiments without another permission question; no multi-hour runs.
Master is 6f68e24e8ddac42b948da8fcc2d636c010751194. This is a new characterization,
not a baseline comparison, old-script rerun, or production candidate qualification.

Three serial processes, Float64 / BigFloat256 / Rational{BigInt}; each at most114s
plus6s cleanup, total at most360s, stop on first failure, no retries. Existing
single Julia/BLAS thread,2GiB heap hint/8GiB VM,6GiB availableRAM/1GiB swap guards.
No CI, automation, HH reuse, source/test/environment changes. Use actual master
source via a byte-identical diagnostic checkout. Pinned ordinary existing-cache
loader is not cache confinement or a complete import-work proof.

Fixtures: repository afiro, sc50a in all three precisions; adlittle and generated
primal-chain130 additionally Float64. All use default options except finite10s
per-solve deadline,2000iterations, and primal algorithm for the chain. Original
tolerances, safeguards, scaling, presolve, native PFI backend remain. Small sparse
Netlib models and a degenerate chain do not represent large/dense production LPs,
HH or Markowitz. No representativeness claim outside this scope.

Each case:1 cold plain,1 cold diagnosed,1 warm plain,1 warm diagnosed,1 batch-warm
plain;3 interleaved plain/diagnosed pairs, then64(F64) or8(BF/Q) sampled plain
solves. Thus75calls/F64case and19calls/BF-or-Qcase;376public-solver entries maximum.
One read_mps per case, parsing/load/cold timings separate. Diagnostic allocation
and construction occurs outside measured solve windows. Existing kernel timers
are overlapping inclusive subsets and must never be summed into total time.
No observer or method replacement. Profile output storage retains bounded solutions
only during sampling; ordinary solve measurements retain only individual outputs.
Input-value tokens and endpoint comparisons run outside measured windows.

Acceptance: every public result OPTIMAL and objective within1e-7 relative/absolute
of the independently cross-checked repository expected objective; chain expected-1.
Exact value/precision/signed-zero endpoint and input-token equality across modes,
iterations/refactorizations/message match; no changes of tolerances or trajectory.
This is reproducibility plus existing solver certification, not an independent new
exact primal/dual certificate for each result. Profile samples must be nonempty,
not truncated; measured windows and sampling compile/recompile zero. Preserve all
GC and timing outliers. Failures preserve raw records and stop without tuning.

Sampling at1ms;2million-IP buffer(16MB). Export raw IP sequence and resolved frames.
Exclusive category priority, defined before results: presolve(any presolve source
frame); cleanup/certification(any cleanup,certificate,certification,restore_basis,
_retry_original frame); factorization(any refactor,factorize,lu!,lu frame); basis
solve(any ftran,btran,forward_solve,transpose_solve frame); pricing(any pricing,
price_,update_duals frame); model/setup(any scaling,transformations,workspace,
initialize,initialise frame); other. Match case-insensitively, C frames retained.
This categories-by-ancestry convention attributes child costs to parent phase and
is approximate statistical attribution, not exact phase timing. Also report
inclusive JSimplex function hit counts (unique per sample), which overlap.
GC/native/runtime attribution remains visible in raw stacks; it is not allocated
or freed native memory accounting. Report counts and sample-size limits.

One new independent gpt-6-astra admission review before Julia; separate result
review, evidence closure and exact publication before diagnostic commit/push.
Recommendation must follow measured repeated costs, distinguish fullsolve from
component savings, and cannot reopen stopped routes without a new design.
