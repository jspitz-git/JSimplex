# S5-I: permanent active-journal precision-transfer interruption coverage

The exact S5-H candidate is integrated as test-only commit fddfa7374269338ab97cfc37843e52c4899f09ca,
cherry-picked to master 513c05388a82531e4d8fbcfb383e8897fad14ba2. It appends 203 lines
to test/simplex_precision_state_tests.jl and preserves the entire 10583-byte original
prefix. No production, environment, tolerance, arithmetic policy or CI change.
This adds regression coverage; it is not a solver fix or full-suite qualification.

## Evidence and validation

H's four missing-coverage structural RED predicates are reused. They are offline
source checks, not failing Julia tests or reproduction of a solver defect. The H
candidate SHA256 is 6b65d9194917ddde0e883fdb75c649a1d7eef229e57a210c11cc980fbc6d8616.
The new driver extracts only the appended marker from the ACTUAL target test file,
binds the whole file/prefix/suffix and actual module path, and never executes the
old testsets or includes the diagnostic candidate. Three reversible insertions
count setup entry, transfer entry and completed case, and save fixed work rows.
The inverse recovers the reviewed suffix byte-for-byte; callbacks and numerical
calls are unchanged. Two driver-only assertions check entry totals and case order.

Fresh independent prelaunch review found three Important gaps: complete root/target
source tree pinning, raw-log summary verification, and executable master/GREEN
source identity checking. A single offline RED3/GREEN4 correction resolved them;
original launcher/auditor/prelaunch texts and initial preparation evidence remain.
Initial preparation has eight checks and 792 read-time hashes, reconciled via three
preserved before files; its separate independent reconciliation has four checks.
No Julia or test-file edit occurred before final prelaunch acceptance.

| New run | Actual source | Assertions | Audit | Launch pins | Independent |
| --- | --- | --- | --- | --- | --- |
| green-1 | diagnostic checkout, exact H test | 300/300 | 24 PASS | 801 | 9 PASS |
| master-1 | actual master 513c053 | 300/300 | 25 PASS | 1322 | 9 PASS |

Each raw log and TOML agree, with zero failures/errors/broken assertions. There are
298 permanent assertions plus two driver-only assertions per run (subtraction from
aggregate summary, not a separately printed nested count). Each run has exactly
two setup/transfer/completion entries, ordered stop then throw: FOUR new lifecycles
total. There was no numerical RED, warmup, trial, success control or repeated run.
Master and GREEN match all 511 source/test file hashes and exact tree membership;
master launch inventory includes both root and actual-master trees. All seven raw
files per run have byte-identical portable copies and independent SHA256 bindings.
Each inventory was independently fully rehashed before and after its run. Review
coverage is stated separately in the original review records.

Each transfer observed one counted FTRAN, one BTRAN, one refactor kernel, zero other
kernel deltas, refactor_other event 1 and zero other event deltas, zero iteration
advance and one source refactor charge. Observer hits are one each; true stop calls
are one for stop and zero for throw. Existing finally-based counters are partial:
weight rebuilding also calls one direct untimed unit BTRAN and can call up to three
correction BTRANs even with solve_refinement=false. The permanent oracle retains
that allowance. Observed zero corrections is not a stronger general exact-work
contract or complete PREforward/native/import attempt count.

Both processes exited with reason exit0, returncode0 and unchanged pins. Fresh
full /proc scans confirmed absence of all members of new groups52772/52774 and
53479/53481, old groups49081/49084 and23249/23257, and Julia processes. Process
identity includes boot_id, command and start_ticks, not PID alone. Nine resource
samples per run met guard limits: minimum available RAM22452140/22377352KiB,
maximum swap0. Inclusive elapsed intervals9.014787/9.013972seconds include startup,
imports and compilation and are NOT performance measurements.

The unchanged guard uses its global lock, one Julia, Julia/BLAS/OMP/MKL threads1,
heap hint2GiB, VM limit8GiB, RAM>=6GiB, swap<=1GiB and120-second inclusive wall cap.
Actual cross-worktree and nested wrappers are pinned. compiled-modules=existing
prevents ordinary fresh compilecache workers; Pkg auto-precompile is disabled.
This is not cache confinement, continuous host census or complete import-work proof.

## Numerical, ownership and memory scope

The two existing one-row/two-structural-variable native-policy cases request128bits
and detach equal active cost/bound buffers. Callbacks arm only after setup and retain
fresh/count/stop or throw; they perform no numerical calls or snapshots. Direct Julia
assertions verify wrapper type and sentinel cause identity, avoiding type-name text
matching. Selected source array identities/values, journal owner, metadata and source
pre-detachment checkpoint phase keys are preserved while shared consumed work advances.
No _checkpoint_matches assertion is made for intentionally detached source buffers.
Fresh workspace has its own journal and expected active aliases, cleared history,
unchanged levels/cooldowns, empty cache/checkpoints, stored numerical128bits and
restored ambient precision/rounding; time_limit stays Float64. No lazy cache helper
is invoked on fresh state. This is selected-state coverage, not all private factor
internals, observer neutrality, whole-function rollback or certificate transfer.

No unnecessary production computational work or memory cost was introduced:
production is unchanged. These cold tests add two setup/transfer lifecycles to the
suite. Per case,31 source snapshot arrays contain76 entries; three intentional
working-buffer detachment copies contain9 entries, totaling34 explicit copies/85
entries,68/170 per pair, in addition to fixture/checkpoint/solver allocations.
Predicates perform bounded scans for distinct value/alias/precision contracts and
add no basis solves. Fixed metadata/test machinery allocates separately. There are
no growing ledgers, per-solve snapshots or callback snapshots. Source/fresh graphs
may remain GC roots; clearing a Ref does not prove collection or native retention.
The diagnostic driver adds fixed counters/two record slots and post-case kernel/
event rows, with serialization after cases. No hot-path benchmark or speedup claim.

## Preservation and continuation

Fresh numerical/work review accepted GREEN before test-only commit and promotion;
actual master is independently reviewed separately. See the linked review index
and original prelaunch, GREEN and master records in results/S5-I. Protected user
hashes remain unchanged in both checkouts. H/G/F frozen artifacts are untouched,
including G's original62/63 FALSE audit and separate seven-check PASS supplement.
H's STATUS/roadmap versions are preserved as *.before-I before continuation updates.

Next is ONE source/evidence-only S5-J dual auxiliary original-bound handoff ownership
reconciliation, under docs/superpowers/plans/2026-10-13-dual-auxiliary-handoff-ownership.md.
First reuse any matching existing composition coverage; do not infer a new defect.
No Julia, fixture, launch or test/production edit is authorized by that next step.
CI remains off and HH reuse disabled. S2-A/S6-J/whole-AF rejections, Q GC/outlier,
S4 bootstrap/cache/init/whole-controller caps/native retention, historical x64 and
full-suite failures and broader S3/S4/S5/S6 remain open and unchanged.
