# Independent S5-I post-GREEN numerical and work review

Reviewer: fresh independent agent `s5i_green_review`. Disposition: ACCEPTED for
test-only commit and integration of the exact reviewed candidate, followed by at
most the separately planned single guarded two-case master validation. Findings:
Critical 0, Important 0, Minor 0. This is not acceptance of unexecuted master
validation or permission to repeat GREEN. No Julia, imports, numerical calls,
flag probes, old driver/auditor executions or production/test changes were made by
this reviewer. Only this new review file was written.

## Independently checked evidence

Streamed all 801 launch inventory files, totaling 3,577,243,028 bytes, with zero
hash or resolved-path mismatches. Both recorded src/test trees have exact current
membership. All six protected user-file hashes match. HEAD is
`ea3d47bda8ea611d2bda8cb9b9d0d1a197ddfd30`; master is
`0eb75c3190096946b0e91e5360230ccd7166f298`. Against master, src/test/.github changes
consist only of 203 added test lines. The actual test equals frozen H candidate,
which equals the 10583-byte original HEAD prefix plus the frozen H append. All
three expected hashes match. Reversing the three unique driver insertions in the
saved executed suffix recovers the append byte-for-byte. These insertions add only
setup entry, transfer entry and post-case record accounting; existing callbacks,
fixture options, numerical policy, assertions and requested 128 bits are unchanged.

Independently matched all seven original raw files to their portable copies and
to the SHA256 map in green-1-audit.json. The original raw log reports 300/300 PASS
and the TOML reports passes=300 with fails/errors/broken all zero. Driver source
contains exactly two additional completion assertions, so 298 permanent assertions
is inferred by subtraction, not a separately printed nested summary. The driver
loads only the actual test suffix, not the old testsets or results candidate.
Its checks bind actual module source and test/prefix/suffix. Entry counts are
[2,2,2] and modes are stop then throw. All 24 recorded audit checks are true.
Read the auditor independently rather than execute it again.

The 28 kernel and 64 event keys match their production definitions, including the
six-by-three generated hypersparse keys. Both cases record iteration delta 0,
refactor delta 1, one counted FTRAN/BTRAN/refactorization and all other kernel
deltas zero; refactor_other is 1 and all other event deltas are zero. Observer
hits are 1 each; true stop calls are 1 for stop and 0 for throw.

Process exit is reason exit0, returncode 0, pins_unchanged true, with inventory
identity matching the recorded pin digest. Runner PID/PGID/start ticks are
52773/52772/2121620 and child 52774/52774/2121743. Fresh /proc inspection on boot
`dade7243-9103-4398-bb45-fa28fbc0be72` found no Julia and no member of groups
52772/52774/49081/49084/23249/23257. current.json is the initial launch snapshot
(the guard writes it before changing reason to running); process.json is the final
outcome. Its initial launch_error placeholder is not a failed GREEN run.

All nine resource samples meet the guard: minimum available memory 22,452,140 KiB,
maximum swap used 0. Recorded elapsed wall interval is 9.014787 seconds including
startup/import/compilation and guarded execution; the Test summary says 6.6s.
Neither is a performance benchmark. Reviewed launcher, actual wrapper, nested
depot wrapper and unchanged guard establish the lock, prelaunch Julia exclusion,
thread environment, 8 GiB address-space limit, 2 GiB heap hint and 120-second wall
limit, with sampled RAM/swap checks and process-group cleanup. Actual command uses
compiled-modules=existing, threads=1 and gcthreads=1,0; reported Julia/BLAS threads
are 1. This preserves ordinary compilecache admission limits, not cache confinement,
continuous whole-host process census or complete import/backend accounting.

Read H report/review/candidate/evidence and preserved G original audit (62/63,
all_passed=false) plus its separate seven-check outcome supplement. Their identity
is included in the rehashed inventory. The three prelaunch Important findings
were fixed once offline; preserved before files and amended after files match
review-fix.json, which reports structural RED3/GREEN4. No old failure was rewritten
as a passing original result.

## Numerical safeguards and work/memory review

Read actual precision transfer, recompute, checked solve, refinement and recovery
weight source. Stop/throw occurs at the final refactor_other observer after the
fresh workspace is rebuilt. Direct permanent assertions cover source selected
array identity and saved values, selected metadata and checkpoint keys, source
journal ownership, shared budget and work changes, ambient precision/rounding,
return versus DiagnosticObserverFailure with identical sentinel cause, fresh
journal/model/basis ownership and active aliases, cleared histories/cache/checkpoints,
unchanged levels/cooldowns/options/policy, and stored 128-bit finite values. Infinite
Bound values correctly bypass finite-payload precision checks. Source checkpoint
keys are preserved without asserting that the intentionally detached working
buffers still satisfy checkpoint matching. No fresh lazy cache is created.

The assertions preserve the intended distinction between selected source-state
preservation and shared consumed-work advancement. Identity checks on objects are
not deep checks of all private factor internals. Observer actions only count,
retain, and stop or throw; they do not snapshot arrays or call numerical routines.
No tolerance, safeguard, arithmetic policy or production behavior changed.

The work oracle is correctly partial. recompute! makes the counted FTRAN and BTRAN;
the factor attempt contributes one counted refactorization and source budget charge.
Weight rebuilding makes an additional direct, untimed unit BTRAN for this one-row
fixture. Its explicit refinement may perform zero to three correction BTRANs even
with solve_refinement=false, because that flag does not disable the correction
loop reached through weight rebuilding. The test therefore allows counted BTRAN
1..4 with reconciled correction events. GREEN observed zero corrections; this
must not become an exact-one-BTRAN general contract. Entry counters describe two
setup/transfer/completion lifecycles, not complete PREforward/backend attempts.

No unnecessary production computational work or memory cost was found: production
is unchanged. These cold regression cases add two setup/transfer lifecycles. Each
case makes 31 saved-array copies containing 76 entries, plus three intentional
working-buffer detachment copies containing nine entries: 34 copies/85 entries per
case, 68/170 for the pair, beyond fixture/checkpoint/solver allocations. Read-only
source-after and fresh predicates add bounded scans for distinct ownership/value/
precision contracts; they do not add basis solves or full graph snapshots. Their
cost scales with the copied/tested arrays, but this fixture is fixed at one row and
two structural variables. No growing update-chain ledger or per-iteration/per-
candidate instrumentation is introduced. The driver adds three integer counters,
two fixed record slots and post-case 28+64 dictionary lookups per row. Hashing,
text substitution and report serialization are per-run setup/offline/cleanup work.

Fixed metadata tuples and test infrastructure have additional allocations that
are not included in the explicit copy count. Both cases' source/fresh graphs may
remain GC roots; clearing retained[] is not proof of collection or bounded native
retention. No material avoidable diagnostic cost warrants new machinery. Sparse/
dense hot-path timing is not required for this test-only change and no speedup,
total allocation-byte or broad precision/backend claim is supported.

## Acceptance limits and next step

Accept only the exact test candidate below for test-only commit/cherry-pick. The
planned master run remains separately gated on matching actual source/test trees,
fresh pins and process/resource checks, with at most one run of these two cases.
No GREEN rerun, warmup, success-control matrix or old-file/full-suite execution is
part of this acceptance. No solver fix, original-model certificate transfer,
observer neutrality, whole-function rollback or broader S3/S4/S5/S6 qualification
is implied. All prior rejection, CI-off, HH-disabled, x64/historical/full-suite,
Q GC/outlier, bootstrap/cache/init and whole-controller/native-retention limits
remain in force.

Also read the proposed S5-J source/evidence-only handoff plan. Its bounded scope
is acceptable as a future investigation: reconcile existing exact-composition
coverage first, stop if already qualified, distinguish private rejection from
post-publication callbacks, and do not infer a new defect or authorize numerics.
This is plan-scope acceptance only; no dual auxiliary handoff source contract or
execution evidence was reviewed in this S5-I review. The plan does not reopen
HH/DSE or aggregate controller-budget audits.

## Reviewed SHA256 identities

- actual test / H candidate: 6b65d9194917ddde0e883fdb75c649a1d7eef229e57a210c11cc980fbc6d8616
- original prefix: 37fe8c270e8cc8c66155cccd23491df171eba34647a442c4a809fab705ddb24c
- H append: 697ed577c5dba0210eeaf6b1f17b90a0c007a24fba948f87162122d51c0cd273
- executed suffix: 29e39d8ad93f3c268d3f68b152d28100592988591979392ad87711754dd5303b
- GREEN pins: 942fdbddff88034d20ee485a9576a37d5a8acf3a6b5f38cf9d135a53d1b2209e
- GREEN process: 216b5779612d450437da5fc7e9609070cefc3877b8976f72274d26517706a890
- GREEN report: 1661218a97b3d25a9f778bc68e053d34a193580c5784498be48db3e48b36bbb6
- GREEN audit: 48f2a55232662f3dbd30f2369d274a7ac648b9a4a863bc0cf30a4584edeb5363
- driver.jl: 160d9d84dd5a9bcca91e311d70d7654ffb84bb3e2c62fd323abf004c4804de49
- insertions.toml: 95b565b65ad9f0d33463d62d6c0279ff36deaab1c3d2b75fa576d872ac35d1db
- launcher.py: 1585d44e5419cc3d340619236b433623e5977879f7f9df67ac2dbc28138acc36
- audit.py: 7ffa4f8c2e8d48b3a135ba1d9f48495c2d294b91137f5f052743329f1c9d0b34
- prelaunch-review.md: 304f32dbd5efc18b6db6d4dae7e4a6fb424403b8b16e53b59ead036369bd196e
- review-fix.json: 380fff4278ee11d88226fd6be18b3fac3a423f0119bf6da719d655c5927ef8c5
- proposed S5-J plan: 4b1c7a2bc7673a5b6a1820856fb378948e0bb22b78f2d0a96e916b85a6868ab2
