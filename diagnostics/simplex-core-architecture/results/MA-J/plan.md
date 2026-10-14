# MA-J: equality implied-bound private addition spike

The human requested this new presolver experiment and approved short numerical
attempts without repeated permission. This is a throwaway component candidate,
not production integration or a reopening of MA-I. Actual src/test/env/CI/master
remain unchanged. Existing evidence stays frozen.

Only the two nonzero activity additions in `_equality_implies_column_bounds`
change. Preserve coefficient conversion, products, zero/unit shortcuts, shared
fixed activity reuse, endpoint handling and the complete final bound predicates.
Allocate scratch lazily inside each call: three independently owned rationals
and three BigInt addition buffers (nine BigInt objects, variable limb capacity).
Choose a destination different from both live activity sums; no mutable scratch
escapes the Bool result. Products never reference the scratch pool. Preserve
same-denominator specialization with an exact MA numerator addition, denominator
copy and gcd normalization. Other denominators use buffered rational addition.
No new vector scans, solves, matrix copies, persistent cache or retained scratch.
Per changed addition: at most four identity comparisons; same denominator adds
an explicit denominator copy, normalization is still required. Exception/OOM
allocation timing is not identical; this experiment makes no general exception
or arbitrary invalid-input contract claim. Only valid nonzero pivots are used.

One guarded process, maximum 180 seconds including startup, no retry/tuning.
Ordinary JSimplex import with compiled-modules=existing; installed MA imported
through a copied existing environment. No package installation or precompile
workers. Julia/BLAS1, heap2GiB, VM8GiB, availableRAM6GiB, swap1GiB; full prior
134 groups AND sessions absent before launch. Fresh immutable source/runtime/
input/driver/guard/launcher pins and fresh independent admission required.

Correctness uses independent exact endpoint enumeration, compares actual source,
byte-extracted reference and candidate, and checks all input scalar values and
owners before/after. Include Float64, BigFloat256/512, Rational{BigInt}, 2/4/8-term
rows, both pivot signs, fixed/general/units/zero/cancellation/unbounded cases,
containing/excluding/one-sided/free pivot bounds. Test stored BigFloat256 low bits
under ambient64 and512 separately. A deliberate inverted-result and a mutated
snapshot control must be rejected by the diagnostic oracles (not a production
RED test). Scratch isolation is additionally checked directly.

Cost grid: same four scalar types, 2/4/8 terms, fixed/general/units/cancellation patterns,
48 cases. Three warm and seven measured alternating pairs, 32 whole function
calls per window. Scratch creation/normalization and result consumption occur
inside each call. Fixture construction, exact oracle, snapshots and serialization
outside windows. Record all time/bytes/GC allocation events/compile/recompile/GC
and all results, no dropping outliers. Record the first timed batch separately after correctness qualification; this
is not a cold-import or cold-function measurement. Compare paired medians, range,
MAD and allocation counts. A local benefit requires >=5% median time reduction,
6/7 faster pairs and fewer median bytes/events; other outcomes reported unchanged
or regressed, not tuned. No universal/full-presolver/solver speedup claim.
After execution, independently review correctness, allocation/work and statistics,
preserve raw failures, source pins, processes and portability; publish a bounded
report and update continuation with explicit before-text mappings.

## Admission amendment (before numerical execution)

Initial review rejected inadequate boundary/low-bit sensitivity, missing binary
pins, measured-compile acceptance and shutdown reserve. Original files/manifest/
review preserved as *.before-review; their old path bindings resolve only to
those copies. Canonical files below are a new prospective admission, no rerun.
Add 400 tight finite-bound cases: four scalar types, 4/8 terms, five patterns
including fixed-prefix then divergent endpoint, two signs, five endpoint-bound
modes. Float conversions are checked against their actual stored endpoints; a
sub-ulp offset may legitimately collapse for Float64. Replace the two cancelling
low-bit cases with six offset -1/0/+1 cases at ambient64/512, requiring false/true/
false even though conversion at ambient64 would erase the perturbation. Total
1126 correctness cases. Check all bound stored scalars, including unbounded zero
payloads and all row/column bounded flags. Cost remains exactly48 cases.
Measured compilation now rejects in both driver (after raw save) and supplemental
postcheck. Launch uses174s with6s polling/termination reserve inside the180s
experiment cap; terminal audit still enforces<=180. Pin bash and actual Python.
First timed batches follow qualification and are not cold measurements.

## Oracle-context correction (still before the sole numerical attempt)

The revised admission found direct `Q(stored_BigFloat)` in the diagnostic oracle
and snapshot could round via Base.ldexp at ambient64. Preserve that review and
its files/manifest as *.before-oracle-fix. A diagnostic qexact conversion now
sets precision to max(stored, ambient), restoring the ambient context afterward.
Use it for every BigFloat oracle/snapshot conversion. Two additional deliberately
rounded low-bit fixture constructions (oracle only, outside timing) must fail the
same expected predicate at offsets -1/+1. Production candidate unchanged.
The check grid remains1126 and cost48; negative controls are separately recorded.
