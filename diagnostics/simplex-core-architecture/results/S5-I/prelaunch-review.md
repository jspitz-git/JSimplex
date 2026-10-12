# Independent S5-I prelaunch numerical and work review

Reviewer: fresh independent agent `s5i_prelaunch_review`, reading the local source
and frozen evidence. Disposition: ACCEPTED for the bounded S5-I launch plan after
one offline amendment. Final unresolved findings: Critical 0, Important 0, Minor 0.
This is prelaunch acceptance, not a claim that Julia syntax, imports, assertions,
GREEN, master or the full suite have passed. No Julia invocation, import, flag
probe, numerical call, old driver/auditor rerun or actual-test edit occurred in
this review. Only this new review file was written by the reviewer.

## Findings and their resolution

Three Important findings were raised against the initial launch artifacts:

1. Freeze enumerated only the selected target trees. During master validation,
   new files in the diagnostic checkout could escape tree membership coverage.
   The amended launcher enumerates ROOT/src, ROOT/test and target/src, target/test.
2. The original auditor checked aggregate report counts but never the raw logged
   assertion summary required by the plan. It now requires a Pass/Total/Time
   header and the exact focused-test row, matching Pass and Total to report passes
   and requiring zero failures, errors and broken tests. Installed Test source
   confirms its default timing output and duration format match the parser.
3. The claimed master-to-GREEN source identity lacked a saved-inventory gate.
   Before master freeze, both current and master relative src/test file sets and
   SHA256 values must equal the accepted GREEN inventory. An exclusive comparison
   artifact binds the GREEN pins and audit; master audit rechecks that binding.

All three are resolved by source inspection. The original launcher, auditor and
prelaunch text remain as `.before-review` files. Independent Python parsing and
hash checks confirm all amended Python files parse, all recorded after hashes
match, and preserved before hashes match the original preparation inventory.
`review-fix.json` records structural RED3/GREEN4 only; it is not numerical testing.

## Independent evidence and execution scope

Independently streamed all 780 H input hashes, totaling 3,576,930,876 bytes, with
zero mismatches. The actual test is still the original 10583 bytes; candidate is
exactly that prefix plus the frozen append. Prefix, suffix and candidate SHA256
match expected.toml, and inverse replacement of the three insertions recovers the
append byte-for-byte. HEAD is ea3d47bda8ea611d2bda8cb9b9d0d1a197ddfd30; master is
0eb75c3190096946b0e91e5360230ccd7166f298. There is no src/test/.github delta against
master. Fresh process reading found no Julia or old groups 49081/49084/23249/23257
on boot dade7243-9103-4398-bb45-fa28fbc0be72. A separate fresh absence check remains
required immediately before each edit/launch by the execution plan.

Read the integration plan, H candidate/append/report/review/evidence/closure,
S5-I driver/insertions/expected/launcher/auditor/preparation/host snapshot and new
host checker, actual wrappers, general guard, installed Test implementation and
relevant production precision-transfer/recompute/weight-refinement source.

The driver reads the actual selected test file, verifies whole/prefix/suffix
identity and the loaded module source directory, then includes only the appended
suffix. Old testsets are not executed. The original assertions, fixture options,
policy, callbacks and 128-bit request remain unchanged. The three insertions are
PRE-setup, PRE-transfer and post-case bookkeeping; the driver adds only two
completion assertions. Installed TestCounts fields support the direct plus
cumulative aggregate calculation used for the report.

The amended freeze verifies every H input, with only the exact candidate hash
substitution allowed for the diagnostic test file. Actual wrappers, nested depot
wrapper, runtime/libs, guard, Test source, source/test/environment/user files and
new launch evidence are bound. Per-run audit checks pins, tree membership,
process exit, raw summary, actual module path, thread/resource samples,
source/prefix/suffix identity, counter/event/observer deltas and group absence.

The reused guard owns the advisory lock, rejects live Julia, applies single-thread
environment settings and 8 GiB address-space limits, and includes imports and
compilation in its 120-second monitored run. RAM/swap thresholds and cleanup are
unchanged sampled guard behavior. The command uses existing compiled modules,
threads1, gcthreads1,0 and heap2G. Installed loader admission excludes fresh ordinary
compilecache work in existing mode; this is not cache confinement or complete
import/backend work accounting. Exactly two new setup/transfer cases are allowed
for GREEN and, only after accepted GREEN and integration checks, two on actual
master. Failure must preserve evidence and stop; no silent retry is accepted.

## Numerical correctness, computational work and retained memory

No production behavior, numerical safeguard, tolerance, arithmetic policy or
precision choice changes. Source ownership/value preservation, fresh journal and
model ownership, active aliases, cleared histories/cache/checkpoints, saved
checkpoint keys, typed precision and restored ambient state remain directly
asserted. Observer code only counts, retains and requests stop or throws the
original sentinel. It adds no solver call or callback snapshot.

Source inspection confirms the partial finally oracle: one counted FTRAN and
refactorization, one counted BTRAN plus zero to three correction BTRANs, zero
other counted kernels, and reconciled correction events. Weight rebuilding also
performs one untimed unit BTRAN for this one-row fixture. Its correction loop is
permitted even with solve_refinement false; exact-one-BTRAN would be unjustified.
Entry counters measure two setup and two transfer entries, not complete kernel or
backend attempts. Budget, observer and event checks retain their original scope.

No unnecessary production computational work or memory cost was found: production
is unchanged. The cold regression cases each make 31 snapshot copies/76 entries
plus three detachment copies/nine entries, totaling 34 copies/85 entries per case
and 68/170 per two-case run, beyond existing fixture/checkpoint/solver allocations.
The new driver retains three integer counters and exactly two scalar/counter rows;
each post-case row adds bounded 28-kernel/64-event dictionary lookups, without array
snapshots or solves. File hashing, text replacement, report serialization and
inventory scans are offline or per-run setup/cleanup costs. These serve distinct
identity and work checks; no material avoidable cost warrants more machinery.

Source and fresh workspace graphs from both cases may remain GC roots; clearing
the observer Ref does not demonstrate collection. No total allocation, native
retention, performance, observer neutrality, certificate or full-suite claim is
supported or made. Sparse/dense hot-path benchmarks are unnecessary because no
production hot path changes. Existing H/G limitations, original G false audit and
separate supplement, CI-off/HH-disabled and broader rejection gates remain intact.

Reviewed amended identities:

- driver.jl: 160d9d84dd5a9bcca91e311d70d7654ffb84bb3e2c62fd323abf004c4804de49
- insertions.toml: 95b565b65ad9f0d33463d62d6c0279ff36deaab1c3d2b75fa576d872ac35d1db
- expected.toml: ec4560b65e4bffcb6679c2729dea62d15030d46945641b2f1f639f104f7bffdb
- launcher.py: 1585d44e5419cc3d340619236b433623e5977879f7f9df67ac2dbc28138acc36
- audit.py: 7ffa4f8c2e8d48b3a135ba1d9f48495c2d294b91137f5f052743329f1c9d0b34
- host_check.py: dc6541706c6f4605668a8cdd5f2474cedae14e36b6b218667fa631a60c281b69
- prelaunch.md: a00a45ed7fd8e55b3640c48b1dcfe5ef9b8d253d533ad846458bb5318ef15e91
- review-fix.json: 380fff4278ee11d88226fd6be18b3fac3a423f0119bf6da719d655c5927ef8c5
