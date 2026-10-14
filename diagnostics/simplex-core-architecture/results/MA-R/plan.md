# MA-R offline candidate preparation

Parent accepted plan: docs/superpowers/plans/2026-10-14-ma-denselu-bigfloat.md Task1.
Status: independently accepted for MA-S admission preparation. All Julia files UNEXECUTED.

## Loading boundary

Use the new environment/Project.toml and environment/Manifest.toml only under a
future MA-S admission. No install/resolve/instantiate or Julia query occurred here.
The copied manifest changes ONLY JSimplex's path to the current absolute checkout
and removes its obsolete root project_hash. JSimplex's dependency block is unchanged;
MA is a direct dependency of the diagnostic root, pinned exactly1.8.1. Existing
package trees and loader choices still need launch pins/admission; a text manifest
is not a successful import or cache-confinement proof. User env files are untouched.

The future sequence is include reference.jl (defines MADenseProbe with identical
JSimplex/MA imports for both sides), include tests.jl, reference_smoke(), route_red()
while candidate names are absent, then Base.include(MADenseProbe,candidate.jl) and
Base.include(MADenseProbe,instrumented.jl), then qualification(). MA-S must freeze
absolute paths, import/RED error handling and exclusive attempt/output reservation.
RED expects exactly two missing-route assertion failures; a loader or parser error
is a failure, not RED success. No loader or launcher is executed or supplied here.

## Candidate source and arithmetic

Seven source blocks have exact inverses, including both complete original backend
reference functions and pivot, LU, triangular-normalization and generic solve code.
Twelve literal product sites across all eight generic branches use one private
BigFloat. Ordinary subtraction, division, unit operations, scalar stores, all zero
products, dimensions, pivots and exception order are retained. No factor/RHS leaf
is mutated. Diagnostic-only instrumented entry copies count entry/scratch/fallback;
the measured candidate has no counters or hooks. The instrumented entry inverse
must match the uninstrumented entry code; no global method overwrite occurs.

source-map.json lists six normalized wrapper classes. The exact generic metadata
is derived using uplo_char, isunit_char, _wrapperop and _unwrap_at, not by assuming
that logical triangle orientation equals parent orientation. Nested triangular
wrappers keep their virtual unit/zero scalar indexing. All eight source branches
are copied, but only the six listed normalization classes are claimed reachable.
The private names _ma_apply_ma_ipiv_rows! and _ma_inverse_ma_ipiv_rows! reflect
literal chained renaming; they are private and all call sites/inverses agree.

Eligibility is constant-time: exact Vector BigFloat/storage LU, square/matching
sizes, n>=16, matching scoped/global MPFR rounding. Wrong dimensions/types and
small sizes delegate before mutation with zero product scratch. The exact square
three-argument ldiv! path is require_one_based_indexing then copyto! then LU solve;
the scratch is created before those operations. OOM timing remains excluded.
No precision adaptation, fused operation, zero omission, fallback after writes,
additional matrix scan or solve is introduced.

## Fixed unexecuted test budget

160 cases:96 grid +40 special +8 mixed stored/ambient precision +8 matching global
rounding +4 nested scoped mismatch +4 other scalar controls. Each case uses original,
candidate and instrumented sides, with identical owner graphs cloned from one
bundle. Two retained-output cases each call every side twice:162calls/side,
486backend solve entries. Separate reference_smoke adds2entries and2setups.
Thus qualification plus reference smoke is488backend entries,162factorization
setups (including2PFI constructors),2PFI copies, no public solve or eta update.
These are prospective explicit source counts, not complete backend work budgets.
The cost phase remains separate52cases/12480calls in the accepted parent plan;
there is no measurement driver in MA-R.

Fixtures are fully deterministic in fixtures.toml and tests.jl. Specials mutate
only privately constructed factor buffers before observation: zero diagonal1/8/16,
ipiv[8]=17, identity/row swap, cancellation packed identity with L21=U12=2^128,
b1=2^128,b2=2^256 and other RHS0, signed zeros,
Inf/NaN in fixed factor or RHS positions, RHS length15, destination length17,
RHS view, same container, shared leaves, factor/RHS leaf, actual PFI copy and prior
output retention. A short RHS alone need not throw: original copyto! fills only its
length and leaves the destination tail. The oracle expects success and compares
that original behavior. A length17 destination triggers the original triangular
dimension check. Invalid pivot must be BoundsError, zero pivot SingularException;
other fixture failure classes are explicitly required, not merely cross-compared.

Exact token comparisons include finite rationals, precision, signbit, NaN/Inf
class/sign. Factor/RHS leaf identity and old-leaf values remain; same-container RHS
is allowed its original array writes. Output alias patterns and links to old owners
are compared, including post-unwind partial state. A retained copied PFI owner stays
reachable during tests. Test assertions occur outside the solver exception catch.
No numerical exceptions are swallowed as successful correctness outcomes.

Diagnostic test cost is deliberately outside future measurement windows: three
whole-bundle deepcopies per case, factor/RHS/output token snapshots, retained old
leaves and IdDict owner maps O(n²) storage per observation at n<=64, plus fixed
output records. These checks are not production code or observer-neutrality proof.
The candidate retains only O(precision) scratch during a call, no update-history
cache; source constructor opportunity n(n-1)-1 is not allocation measurement.

## Next admission

After independent offline acceptance, MA-S prepares exact command/loader pins,
resource guards, exclusive reservations, raw schema and fail-closed audit. It must
account for all488correctness/reference entries plus12480cost calls and any explicitly
admitted calibration/loading work; no hidden extra warmups or numerical retry.
Three serial120s processes maximum, first alone correctness/RED, cost in all three.
All original parent correctness/per-case cost and later public-integration gates
remain. No production promotion, runtime/syntax validity, or speedup is claimed.

## Offline review amendment

The initial accepted review was superseded by P2: the original cancellation fixture
used ordinary LU diagonals near18 and did not force cancellation. The original
review/tests remain preserved. A separate offline fix uses the packed factor above,
so the F L and B U-transpose first update both subtract2^256 from2^256. The final
endpoint [2^128,0,...,0] is explicitly asserted, with no extra solve. Both global
precision and solve count remain unchanged. This exact integer argument is not a
Julia runtime result. Final independent review accepted this amendment without
unresolved findings; see review-final.md/json. All prior bindings are preserved
through review-fix-map.json and completion-map.json.
