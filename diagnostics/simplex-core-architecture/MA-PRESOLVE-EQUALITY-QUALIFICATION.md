# MA-J: MutableArithmetics in equality-implied bound checks

Date: 2026-10-14. Throwaway component qualification; no production integration.

## Decision

The sum-only prototype preserves all 1,126 tested decisions and input values/owners. The complete function, including fresh lazy scratch setup per call, has a narrow measured benefit for the eight-term general Rational{BigInt} fixture. It is not accepted as an unconditional replacement: smaller/simple rows regress, and BigFloat256/512 do not meet the predeclared time-benefit gate. Broader presolver MA remains open; no automatic tuning or repeated measurement follows.

## Scope and ownership

Reference is the exact current `_equality_implies_column_bounds` source with only its diagnostic name changed. Qualification additionally calls the actual production function. Candidate changes only the two nonzero activity additions. Products, coefficient conversions, unit/zero shortcuts, shared fixed-activity reuse and every final bound predicate remain identical. No solver, presolve pass, basis solve or factorization is called. All model arithmetic is exact Rational{BigInt} after conversion, including Float64/BigFloat models.

Scratch is allocated inside the function only when a nonzero activity must be added: three private rationals plus three BigInt addition buffers, nine BigInt objects with variable limb storage. At most four identity comparisons select a destination different from both live endpoint sums. Equal denominators use an MA numerator addition, denominator copy and exact gcd normalization; other denominators use MA buffered rational addition. No new full-vector/matrix scan, copy, persistent cache, solver work or retained scratch is introduced. No scratch leaves the Bool result. This is not a native allocation/free or general exception/OOM-equivalence proof.

## Correctness and input preservation

- 720 broad cases: four model scalar settings × 2/4/8 terms × six patterns × both pivot signs × five bound modes.
- 400 tight cases: four settings × 4/8 terms × five patterns (including fixed prefix followed by divergent bounds) × two signs × five tight bound modes.
- Six stored256 BigFloat low-bit cases at ambient64/512, offsets -1/0/+1, require false/true/false. Two additional deliberately rounded fixtures are rejected by the same expected predicate.
- Exact finite endpoint enumeration supplies the oracle; one-sided unbounded extrema are handled explicitly. Float conversions are compared using actual stored endpoints; sub-ulp offsets may collapse for Float64.
- Snapshots compare exact scalar values, BigFloat precision/data owners, Rational numerator/denominator owners, input array identities, sparse index values, domains and all bound flags/payloads. Direct scratch-leaf disjointness and a changed-value snapshot negative control are checked.
- All 1,126 cases and every measured/warm output/input comparison pass. Ambient precision/rounding restored. This is selected component coverage, not arbitrary exceptions, a presolve integration or full-suite proof.

## Short cost schedule

48 cases = four model settings × 2/4/8 terms × fixed/general/unit/cancellation patterns. Each has three warm and seven measured alternating pairs of 32 whole function calls per window: 960 windows total, 672 measured, 30,720 timed function calls including warmup. Lazy scratch construction and the Bool result consumption are inside timing; fixtures, exact oracle, snapshots and serialization are outside. The first timed one-call batch per side is recorded separately after correctness qualification; it is not cold import/function timing.

All 672 measured windows have zero compile and recompile time. One BigFloat512 two-term general reference window contains 0.052415711s GC; it remains in every statistic. No outlier filtering. A local gate requires median paired ratio <=0.95, at least6/7 faster pairs and lower median bytes/events. Only3/48 cases meet it (Float64 eight-term fixed/general and Rational eight-term general).

Paired time ratio is candidate/reference. Bytes and events are median batch values divided by32; fractional events reflect batch normalization, not fractional physical allocations. Counters are Julia aggregate GC allocation traffic and may include native-backed allocation, not live/native-memory accounting.

| Model scalar | Terms | Pattern | Paired time ratio | MAD | Faster pairs | Bytes/call ref → MA | Events/call ref → MA | Local gate |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| Float64 | 8 | fixed | 0.8925 | 0.0864 | 6/7 | 10502.50 → 9967.00 | 333.03125 → 311.03125 | PASS |
| Float64 | 8 | general | 0.7987 | 0.1168 | 6/7 | 17351.00 → 15742.50 | 540.03125 → 477.03125 | PASS |
| Float64 | 8 | units | 1.0800 | 0.1771 | 3/7 | 7742.00 → 7806.50 | 254.03125 → 255.03125 | NO |
| Float64 | 8 | cancel | 1.0566 | 0.0888 | 3/7 | 7134.00 → 7198.00 | 235.03125 → 236.03125 | NO |
| BigFloat256 | 8 | fixed | 0.9909 | 0.0389 | 5/7 | 19976.00 → 18815.50 | 560.03125 → 536.03125 | NO |
| BigFloat256 | 8 | general | 0.9874 | 0.0080 | 6/7 | 32111.50 → 29119.00 | 868.03125 → 800.03125 | NO |
| BigFloat256 | 8 | units | 1.0158 | 0.0250 | 3/7 | 15278.50 → 15342.50 | 464.03125 → 465.03125 | NO |
| BigFloat256 | 8 | cancel | 0.9045 | 0.0796 | 5/7 | 14558.00 → 14622.00 | 445.03125 → 446.03125 | NO |
| BigFloat512 | 8 | fixed | 0.9924 | 0.0074 | 5/7 | 25928.00 → 24327.50 | 608.03125 → 585.03125 | NO |
| BigFloat512 | 8 | general | 0.9892 | 0.0081 | 6/7 | 41718.50 → 37519.50 | 937.03125 → 869.03125 | NO |
| BigFloat512 | 8 | units | 1.0206 | 0.0435 | 3/7 | 19118.00 → 19182.00 | 512.03125 → 513.03125 | NO |
| BigFloat512 | 8 | cancel | 1.0264 | 0.1261 | 2/7 | 18398.00 → 18462.00 | 493.03125 → 494.03125 | NO |
| RationalBigInt | 4 | fixed | 1.0902 | 0.0661 | 0/7 | 3222.00 → 3342.00 | 89.03125 → 96.03125 | NO |
| RationalBigInt | 4 | general | 1.0337 | 0.0266 | 1/7 | 5590.50 → 5246.00 | 150.03125 → 143.03125 | NO |
| RationalBigInt | 4 | units | 1.2319 | 0.0422 | 0/7 | 1166.00 → 1534.00 | 36.03125 → 49.03125 | NO |
| RationalBigInt | 4 | cancel | 1.5070 | 0.0135 | 0/7 | 670.00 → 1038.00 | 21.03125 → 34.03125 | NO |
| RationalBigInt | 8 | fixed | 1.0312 | 0.0147 | 3/7 | 5910.00 → 4990.00 | 160.03125 → 137.03125 | NO |
| RationalBigInt | 8 | general | 0.8849 | 0.0178 | 6/7 | 11131.00 → 8645.50 | 293.03125 → 225.03125 | PASS |
| RationalBigInt | 8 | units | 0.9730 | 0.0355 | 4/7 | 2064.00 → 2128.00 | 64.03125 → 65.03125 | NO |
| RationalBigInt | 8 | cancel | 0.9226 | 0.0228 | 7/7 | 1455.50 → 1519.50 | 45.03125 → 46.03125 | NO |

The eight-term general Rational case is about11.5% faster with22.3% fewer bytes and23.2% fewer allocation events. BigFloat256/512 general cases reduce bytes about9.3%/10.1%, but time only about1.3%/1.1%. Four-term Rational unit/cancellation cases are about23.2%/50.7% slower and allocate368 additional bytes per call. These short one-process observations are workload-specific: general fixtures contain large180-bit numerators, while unit/cancellation fixtures exercise cheap paths. No universal or whole-presolver speedup is established. Time changes without the full local gate are not accepted benefits.

## Failures and execution provenance

Two prospective admission rejections were preserved. The first required sensitive tight/low-bit cases, measured-compile rejection, executable pins and shutdown reserve. The second found that the diagnostic oracle/snapshot itself could lose BigFloat low bits through Base.ldexp; a protected diagnostic qexact conversion and lossy negative control corrected this before launch. Exact before versions and old manifests/reviews are retained; no retroactive launch pins.

Attempt1 failed after9.237906965994625s at a timing-record metadata assignment: Dict{String,Real} could not store a String. Its280 passing Float64 cases, incomplete raw, exit1, process records and false postcheck are unchanged. Some initial timing calls occurred, but zero complete cost cases were published; those are not accepted measurements.

The independently admitted repair creates driver-2.jl with exactly one change: Dict{String,Any} for the record assembled after @timed. Candidate, fixtures, arithmetic and schedule are unchanged. A separate launcher/output/manifest/review/host records the repaired attempt under the standing human short-run authorization. There was no benchmark tuning or retry loop.

Attempt2 exit0,11/11 postchecks PASS,217 immutable launch pins unchanged, fresh138 groups AND sessions absent/noJulia. Inclusive guarded runtime 10.241600389s is not a kernel benchmark;11 resource records, minimum availableRAM 21622516KiB, swap0. Julia/BLAS1, heap2GiB, VM8GiB;174s run guard plus6s shutdown reserve. Ordinary existing-cache loader admission is not cache-confinement/import-work proof.

## Work and memory review conclusion

The private addition strategy introduces a material setup cost for short/simple rows. Measured regressions show that unconditional deployment would impose avoidable work and allocation there; therefore this candidate is not promoted. On the eight-term general Rational fixture, the same fixed scratch cost is amortized and a local saving is measured. No production changes or new production retained memory were introduced. A future selective route needs its own concrete predicate and review; these results do not authorize automatic tuning.

## Evidence and continuation mappings

Evidence: results/MA-J/{plan.md,record-fix-plan.md,candidate.jl,reference.jl,driver-2.jl,pins-2.json,admission-review-2.*,run-2,postcheck-2.json}. Initial attempt and rejected reviews remain frozen. All MA-J launch sources/manifests/raw/auditors are frozen after their execution; do not rerun them.

MA-I current STATUS/roadmap bindings in its final closure/publication/closure-review and continuation-fix map ONLY to MA-J/STATUS.md.before-MA-J and roadmap.md.before-MA-J. Older MA-I incorrect-roadmap and MA-H/earlier mappings remain unchanged. Initial MA-J changed path bindings map ONLY to *.before-review; second rejected revision changed driver/plan/pins/review bindings map ONLY to *.before-oracle-fix. Actual source/test/project/user environment/CI/master6f68e24 remain unchanged. Automation remains paused; HH reuse disabled; broader plan open.
