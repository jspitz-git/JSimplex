# Missing-zero Float64 candidate qualification

The independently accepted expected RED ran once: one exact missing-zero conversion,
correct -6 coefficient/upper12 and unchanged source, expected exit1 preserved.
Now qualify the separate ordinary candidate overlay. Actual src/test/environment/master
remain unchanged. Candidate changes only two fragments in presolve_aggregation.jl:
Float64 dictionary get with nothing sentinel, one original CSC read on miss, scalar
iszero(stored)&&!iszero(multiplier) skips conversion, and nothing joins old exact-zero
negation. All other types keep original get-do conversion. Dictionary hits always
use their staged Rational value; zero multipliers still require actual exact value.
Product calculation/representability/staging/fill caps/order/postsolve unchanged.

No BigInt mutation, new scratch/cache/vector/matrix/scan/solve. Frequency: each matrix
update attempted by sparse aggregation; existing O(m+nnz) and staged-storage costs
remain. Add scalar check on missing Float64 coefficients, remove an exact conversion
on eligible zero. Check union/sentinel overhead in sparse+dense/nonzero controls.

ONE green process, guard114/inclusive120 seconds, existing resource constraints,
no LP solve and no large external model. Candidate is actual loaded module source.
Reference aggregate/dispatcher/presolve are exact source copies with only scoped
function/call renames, no method overwrite. Both sides share unchanged helpers/types.
New 88 correctness/ownership assertions plus five exact existing focused files cover
four scalar types, tiny values/reduced ambient precision, staged hits/cancellation,
signed zero/zero multiplier/nonzero controls and rejection. Separate forwarded-work
probe: reference4 exact zero conversions, candidate0, full results equal.

Nine synthetic aggregation cases (four signed sparse targets, small target, explicit
negative-zero target, nonzero and zero-multiplier controls, fully populated4x4 control)
plus three Netlib complete presolves afiro/adlittle/kb2. Each3warm+8measured pairs,
alternating order, explicit GC outside each dispatch. Entire aggregate/full-presolve
call including all internal scratch/setup timed; input construction/read and full
result/input-owner comparisons outside. Record every time/byte/event/GC/compile field.
Measured compile/recompile must be zero; full results and unchanged inputs required.
For EACH case median bytes AND median events must not increase; no noise waiver.
At least signed sparse targets must reduce both before performance acceptance.
Timing is descriptive paired distribution; no speedup from counts alone. Do not
promote if cost gate fails. Large-model qualification is separate and conditional
on this stage; no hidden rerun, full-suite success or general precision claim.

Reviewer must bind green-config required+config, manifest and candidate inverse,
reference inverse and exact overlay/source relationship. No Julia in review.
