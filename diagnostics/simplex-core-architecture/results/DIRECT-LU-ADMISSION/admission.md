# Direct LU RED/correctness admission preparation

Date: 2026-10-15. OFFLINE package only, following the accepted 2026-10-14 plan
Tasks1–2 and candidate preparation commit 5921784. No Julia/query/parser/import/
compile/numerics, no numerical reservation and no launch in this preparation.
Standing user permission covers short attempts; it does not replace exact stage
sealing and independent admission. Actual production/tests/env/CI/master unchanged.

## Scope and fixed sequence

Two serial one-attempt stages: reference contract RED <=30 seconds inclusive,
then candidate correctness <=90 seconds inclusive only after expected RED audit
passes and green's concrete sealed admission is independently accepted. Limits
include guard startup, hashing, import, compilation and termination. Guard's
work deadline is limit-6, supervisor TERM at that deadline, final KILL at limit-2,
reap by limit. A timeout consumes that stage attempt; no automatic retry or
increased time. No cost, large MPS, public solver or Task3/4 execution is included.

`prepare.py` constructed two fresh ordinary overlays under
`.superpowers/direct-lu-markowitz-admission/{reference,candidate}`. Both have the
same 71 tracked src/Project files and a byte-identical existing dependency
Manifest from `.superpowers/presolve-exact-cache/reference` with matching Project.
No dependency resolution/install or user Manifest/LocalPreferences edits. Only
candidate adds the two already reviewed implementation files and two root includes.
Both copy unchanged frozen red/correctness/fixture texts. `staging.json` records
six exact unchanged focused selections; no old driver or installer executes.

`config.json` freezes command arguments, projects, output paths and expected
counts. The actual cross-worktree wrapper and its second wrapper, resolved Julia
1.13.0 binary/runtime and existing dependency source/library paths are pinned.
`--compiled-modules=existing` prevents fresh compilecache workers; source fallback
and ordinary dependency initialization remain possible. Offline preferences and
one Julia/BLAS thread are configured, startup file disabled, heap hint2GiB,
RLIMIT_AS8GiB, available RAM>=6GiB, swap<=1GiB. Runtime loaded package path,
Julia/BLAS threads and BigFloat256/RoundNearest are checked in the same process.
No cache-confinement, complete import-work or actual loader-closure proof is claimed.
The historical external path inventory is a discovery list only; this package
hashes those paths anew, excluding MPS inputs and old experiments.

## Test runner and result preservation

The new `CaptureSet` type records Test results without suppressing failures.
Only methods for that new type are defined. Nested results are aggregated; each
of 12 explicit groups writes a start marker and detached TOML counts immediately.
Any mismatch stops before the next group. Final raw is written before exit and
includes fatal errors, exact counts and loaded source. Load-time failures before
main may lack raw; the process/launcher logs remain required and the auditor fails
closed. There is no post-result fixture/count tuning.

RED calls the exact frozen `run_direct_lu_red` and expects zero pass, exactly three
contract failures, zero errors/broken, child exit1. GREEN explicitly calls all six
frozen correctness functions in their wrapper order, then six unchanged focused
selections. Its expected 19,527 assertions are source-derived, not executed proof.

| Group | Expected assertions | Derivation |
| --- | ---: | --- |
| exports | 100 | 2 empty×5 +12 nonempty×7 +5 coupled +1 core |
| rejections | 66 | 9 malformed+1 unsupported sentinel+6 precision/backend cases×9+2 singular |
| orientation | 12 | 2 conventions×3 +2 unresolved cases×3 |
| normalization | 200 | 4 rejection cases×2 +24 manager/backend/scale/mode cases×8 |
| lifecycles | 18,272 | 24 n<2 cases×58 +60 n>=2 cases×281 +20 BG ownership assertions |
| fallback | 288 | 12 cases×24 |
| Markowitz sparse/core | 62 | 4 sparse scalar cases×12 +4 dense×3 +empty/singular2 |
| Markowitz fill | 8 | 2 scalar cases×4 |
| Markowitz triangular | 144 | 3 managers×4 types×12 |
| prepared spikes | 195 | (1+6×20+2) +3×12 +12×3 |
| preparation lifecycle | 96 | 6 cases×(3×4+4) |
| stability first block | 84 | 2 managers×3 types×2 backends×7 |

Focused block byte offsets and source hashes are fixed. Other Markowitz testsets
(including large storage, public solves and allocation checks) and other stability
blocks are not executed. No full-suite or whole-file coverage is implied for sliced
files. Full prepared-spike and preparation-lifecycle files are copied unchanged.

## Explicit numerical work ledger (prospective, not measured)

Counts below refer to explicit API entries in the tests on the successful path;
failed expected constructions/refactors are counted as attempts. Refactor's internal
factorization is included in `factor attempts`. Copy sharing is not a new solve.

| New groups | Factor attempts | FTRAN | BTRAN | Updates | Copies |
| --- | ---: | ---: | ---: | ---: | ---: |
| exports | 14 | 0 | 0 | 0 | 0 |
| rejections | 26 | 18 | 0 | 0 | 0 |
| orientation | 3 dense LU | 0 | 0 | 0 | 0 |
| normalization | 24 | 48 | 48 | 0 | 0 |
| lifecycles | 456 | 4,908 | 2,928 | 1,020 | 60 |
| fallback | 48 | 48 | 48 | 0 | 24 |
| focused selections | 99 | 346 | 115 | 115 | 22 |
| Total | 670 | 5,368 | 3,139 | 1,135 | 106 |

Additional separate work: six native source-backend `lu!` mutations after export;
28 export calls in export tests; 228 lifecycle exports and24 fallback actual exports
(280 total actual export entries, including empty/unit-scale returns), plus24
constructed normalization exports. At most132 native orientation solves from
nonempty actual exports, and exactly4 intended helper `ldiv!` calls in the new
orientation tests. Eighteen unsupported-type reference sparse triangular `\\`
solves and twelve dense reference `\\` solves in the focused lifecycle are additional.
The stability block additionally calls cond on twelve 2×2 Float64 matrices
(including its dense singular-value work). Prepared-spike focused tests have six
explicit private backend forward solves and
six row-update applications. Lifecycle alias tests additionally attempt 288 FTRAN
and288 BTRAN calls rejected before backend work (scratch/dimension checks).
There are 352 explicit refactor calls overall (324 candidate-group calls plus28
focused; includes96 expected failed candidate refactors and6 focused failures).
These figures do not count implicit LU internals, lower/upper substitutions inside
a backend entry, conditional refinement, extraction conversion/scans, residual
matvecs/exact Rational arithmetic, Test bookkeeping or package initialization as
zero. They are not a complete native/PREforward/import work bound. The inclusive
wall/resource guards bound attempts; no instrumentation overwrites production.

The 84 paired lifecycle setups have60 updated cases. Each updated case performs
16 original-side updates plus1 divergent-copy update, eight explicit entering/DSE
sequences per side, a refactor on both originals after update4, then candidate
singular and resized attempts. Expected candidate failures stop only at their
@test_throws boundary; any unexpected failure stops the group/stage.

Correctness uses owned snapshots, retained saved factors and exact rational
residuals outside any measured window. It is deliberately not a cost benchmark.
No new candidate production path, counters, data structures or per-solve work is
introduced by admission. Native direct solves still omit combined UMFPACK
refinement; no equivalent stability or speedup claim.

## Fail-closed sealing, review and execution

`preparation-pins.json` binds the current package, candidate/reference sources,
focused slices, preserved baseline and runtime/dependency files. Independent
`preparation-review.json` must accept its exact hash and exact `required.json` set.
No stage is runnable on that offline acceptance alone.

Future `seal.py red` checks all preparation pins, clean tracked checkout, master,
fresh boot/refs/full prior196 groups AND sessions/noJulia and creates exclusive
`red-seal-host.json` and `red-sealed-pins.json` only. A fresh independent stage
review writes `red-admission.json` with accepted=true, findings=[], exact sealed
manifest SHA and every manifest file plus manifest itself in sha256. `launch.py`
revalidates those bindings and current refs/boot/groups before an exclusive
reservation. Guard holds the common numerical lock and enforces single-process
and resource constraints. No old PID alone authorizes a signal: boot/start_ticks/
command identity and pidfd protect owned process cleanup.

Green sealing additionally requires the accepted RED audit and closed processes,
and binds all RED outputs/control records. Green stage review then binds its own
exact sealed manifest. A changed source, incomplete/changed review, failed RED,
existing seal/reservation/output or wrong refs refuses execution. No stage retry,
automatic continuation after failure, or silent artifact overwrite.

`audit.py` requires complete process/raw/progress/log records, exact exits and
counts, immutable pins/command/reservation, inclusive deadlines, memory bounds
including terminal sample, and no remaining groups/sessions/Julia. Missing records
produce a preserved false audit. Its result is correctness scope only.

Next action after this preparation: fresh stage sealing and independent numerical
admission, then bounded RED; inspect its expected-failure evidence before green.
No new human permission question is needed. CIoff/HHdisabled/automationpaused;
all previous evidence and accepted candidate files remain frozen.

## Offline preparation checks

Thirty-five synthetic Python helper/file checks pass; no launcher, supervisor
process or Julia was executed. They cover raw count/phase/path/error rejection,
review completeness/hash/refusal, input mutation, exclusive output preservation,
missing-process/raw false audit, source overlay inverse and exact focused slices.
The initial helper import failed before those checks due to one missing closing
parenthesis in raw_ok. Its source, failure record and original test script are
preserved; the corrected helper was checked by separate offline-tests-2.py.
These checks do not certify runtime Julia dispatch or OS process termination.
