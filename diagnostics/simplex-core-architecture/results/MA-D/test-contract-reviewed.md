# Prospective regression contract (UNEXECUTED)

Canonical test input: candidate-tests-reviewed.jl -> test/markowitz_ma_upper_tests.jl.
Initial candidate-tests.jl remains unchanged at the preparation.json hash. The
complete version adds MPFR flag/underflow/overflow/divide-by-zero comparisons and
large->small rational lifecycle, and uses Base directly. Neither file was parsed
or run by Julia. candidate-runtests.jl appends exactly one include. No current
production/test changes, no claim of Julia RED/GREEN or exact assertion total.

Original source: two `isdefined` assertions fail, remaining new tests are guarded;
no undefined-helper exception should mask RED. Candidate: both assertions pass
and all six named testsets execute. Driver must separately count each testset,
failed/error/broken tests and actual file/module entry. Missing coverage is fatal.
The future auditor must derive exact assertion counts from the frozen expanded
schedule before launch, not infer pass from process exit. Tests do not themselves
serve as timing drivers or a full solver regression suite.

1. MA upper dispatch and fallback: scalar types Float32/64, Rational{Int}, BigFloat,
   Rational{BigInt}; empty, one/two terms, empty problem and dense-only core.
   Method identity distinguishes target entries from hardware generic dispatch.
2. MA upper scalar ownership: genuine shared scalars and rational BigInt leaves,
   zero and unit division, private scratch2/12 leaves, retained results across
   calls. Scratch owner enumeration is source-version-specific diagnostic code.
3. MA upper sequential arithmetic: ambient128/256/512, high-precision seed
   discriminator, zero/cancellation, prefix row publications, rational limb sizes.
4. MA upper rounding fallback: nested effective/global mode checks and sequential
   parity. No global rounding mutation to force eligibility. Precision/mode restores.
5. MA upper exceptions: missing/unassigned diagonal plus 0*Inf, ordinary malformed
   storage/work indices, partial previous-row publication, nonfinite rationals,
   zero division, BigFloat exceptional values and all six MPFR flags. Flag reset
   is outside each observed kernel, equal for reference and candidate; this test
   intentionally consumes/clears test-process flags, not a production change.
6. MA upper lifecycle: 128->512->128 and8->2048->8 limb inputs; actual small PFI
   construction/copy/refactor, in-place public RHS/destination, preserved RHS.

Local reference is an exact textual transcription of the original loop with only
backend field accesses replaced by arguments. It does not share candidate logic.
Independent Fraction oracle for finite fixtures is additional; reference equality
alone is not an independent mathematical proof. No candidate output is captured
mid-loop; prefix invocations validate successive published subsets with explicit
inputs. Prior row state on thrown errors is compared after unwind.

Named existing Markowitz tests are source coverage references only in MA-D. The
first numerical admission should run the new file and its exact bounded public
lifecycle cases. Broader existing testfiles belong to later integration, where
call counts/time caps must first be frozen. No unbounded public solver here.

Review R1: dense-core floating equality is replaced by exact64eps scaled residual
validation; Rational remains exact. Cost comparisons separately require original/
candidate bits. Initial complete test and its old dense equality remain preserved.
