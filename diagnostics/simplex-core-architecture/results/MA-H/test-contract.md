# MA-H prospective tests and work ledger

UNEXECUTED. No Julia parser, import, compilation or runtime validation in MA-H.
`candidate-tests.jl` is byte-identical to MA-E qualified semantic test source.
Its original six child counts remain62/31/96/42/78/72 =381. No assertion removed.
`route-tests.jl` is a separate file, loaded only AFTER those original tests into
Main by a future scoped collector; `reference-forward.jl` is exact original
forward body with only the function name changed. Its MarkowitzBackend alias is
JSimplex.MarkowitzBackend and ldiv! comes from the existing LinearAlgebra import.
No replacement of a production method, helper override or runtime counter hook.

| New child | Cases | Assertions |
| --- | ---: | ---: |
| MA route complete forward |14:7scalar settings × star8/core3 |126 |
| MA route exceptional forward |6:BigFloat signedzero/Inf/NaN, rational0×Inf, BF/Q bounds |54 |
| MA route scoped rounding forward |8:4outer modes × outer/nested |86 |
| Total |28paired comparisons |266 |

Each comparison performs nine assertions; the rounding child adds8 effective/global
rounding checks,4outer restoration checks and2final restoration checks. Future
qualification total647 =381+266, nine children; no count represents an executed test.
New cases use existing star8 and core3 constructions from the old tests, not new
cost fixtures. Full work/value/precision/sign/NaN comparison against the exact
reference catches a numerical routing mistake. Structural RED/GREEN is the route
absence oracle: values alone cannot prove that a helper call was bypassed.

Each pair: one real MarkowitzBackend construction, one _copy_backend (private work
and core_work; shared factor storage, marked shared), one exact-reference full
forward, one candidate full forward. Total28constructors/28copies/56full calls,
28reference+28candidate. Three pairs deliberately throw (rational0×Inf and two
bounds):6expected throwing entries,50successful. Retained RHS/upper/diagonal values
must match, copied work must be distinct, partial work at throw must match and
neither destination may publish on those failures. No refactor/update/public solver.
Fourteen scalar/family cases include Float32/64/Rational{Int}/Rational{BigInt},
BigFloat128/256/512 and both zero/positive sparse pivot routes. Existing381 include
scalar/leaf alias, flags, malformed arrays, lifetime and precision-growth coverage;
new tests do not claim additional MPFR flag or native lifetime observations.

All new assertions/copies/snapshots are cold qualification work, never timed kernel
work. Per comparison two destination vectors and RHS/matrix construction, observed
value/precision/sign tuples, copied indices and copied scalar values are additional
bounded test work (n<=8), not free observation. Each observed(v) deep-copies every
scalar. _copy_backend adds two work containers, shares core/upper/lower/diagonal
and marks source shared; tests mutate only private fresh factors before copying.
The sharing comparison does not prove whole factor independence or native freeing.
No new per-solve snapshots, counters or retained state enter production candidate.

Rounding qualification constructors and RHS creation run under the tested mode;
the exact reference and candidate share those resulting stored factors and inputs.
This is a comparison at equal actual inputs, not a universal constructor rounding
proof. A later auditor must require all647 assertions, all48 independent fixture
oracles and original memory/resource gates. Exceptions do not excuse missing raw
records; fail closed. Do not run the copied qualified driver directly: its old
paths and includes are source references, not a new executable admission.
