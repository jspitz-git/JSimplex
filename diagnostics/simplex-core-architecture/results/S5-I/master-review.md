# Independent S5-I final master numerical and work review

Reviewer: independent agent `s5i_green_review`, continuing the accepted post-GREEN
review with new master evidence. Disposition: ACCEPTED for the exact test-only
integration and the completed bounded GREEN/master validation. Findings: Critical
0, Important 0, Minor 0. No additional numerical execution is required or accepted
by this review. Final diagnostic publication/closure and push-ref checks remain
separate work. The reviewer ran no Julia, imports, numerical calls, old scripts or
auditors and changed no source, test, environment or frozen evidence. Only this
new review file was written during this final review.

## Independent master verification

Actual master HEAD is `513c05388a82531e4d8fbcfb383e8897fad14ba2`, the test-only
cherry-pick of diagnostic `fddfa7374269338ab97cfc37843e52c4899f09ca`. Both commits
contain only 203 appended lines in test/simplex_precision_state_tests.jl. Against
master baseline `0eb75c3190096946b0e91e5360230ccd7166f298`, no production or CI file
changed. The actual main checkout retains its pre-existing .vscode/settings.json
modification and untracked environment files; all six protected user-file hashes
match the saved prelaunch values.

Independently streamed all 1322 master launch pins, totaling 3,580,791,375 bytes,
with zero hash or resolved-path mismatches. Exact membership holds for all four
pinned src/test trees, covering both diagnostic and actual main checkouts. The
511 relative source/test inventory entries on both checkouts exactly match the
saved accepted GREEN inventory in membership and content. Independently verified
master-source-comparison.json against those entries and its bound GREEN pins and
audit digests. This verifies actual source identity rather than relying solely on
commit ancestry or the master's recorded all_passed flag.

The actual master test equals the frozen H candidate and its original 10583-byte
baseline prefix plus the frozen append. Inverting the three unique driver-only
insertions in master's saved executed suffix recovers the exact append. The
actual module path is /home/jspitz/JSimplex.jl/src/JSimplex.jl and the selected
project/source root is /home/jspitz/JSimplex.jl. The driver executed only the
appended suffix. Original testsets, callbacks, fixture policy/options/tolerances
and 128-bit precision request remain unchanged.

All seven master original raw files equal their portable copies and the recorded
master audit SHA256 map. The raw Test summary reports 300/300 PASS, and report.toml
records passes=300, fails=errors=broken=0. With the two reviewed driver-only
completion assertions, 298 permanent assertion passes are inferred, not separately
printed. Entry counts are [2,2,2] in stop/throw order. Master report fields equal
GREEN except for module_path and source_root. In particular all recorded case
work, event and observer fields are identical. The recorded audit has 25 true
checks and the separate author independent checker has nine true checks; this
review independently read and verified the evidence without rerunning either.

The final process record is exit0/returncode 0/pins_unchanged true, with the exact
pin digest. Runner PID/PGID/start ticks are 53480/53479/2155185 and child values are
53481/53481/2155319. The reviewed command specifies actual main project, existing
compiled modules, threads=1, gcthreads=1,0 and heap hint 2G; reported Julia/BLAS
threads are 1. Nine resource samples show minimum available memory 22,377,352 KiB
and maximum used swap 0. Inclusive recorded wall interval is 9.013972 seconds,
within the reviewed 120-second guard; this includes startup/import/compilation
and is not a performance benchmark. Unchanged guard/wrappers apply the reviewed
lock, prelaunch Julia exclusion, 8 GiB address-space limit, thread environment,
RAM/swap thresholds and child-group cleanup, with the same sampled-observation
limitations documented in green-review.md.

Fresh /proc inspection found no Julia and no member of groups
23249/23257/49081/49084/52772/52774/53479/53481 on the same boot
`dade7243-9103-4398-bb45-fa28fbc0be72`. This independently agrees with after-master.json.

## Numerical correctness and computational work/memory

The accepted GREEN source review remains applicable because every relevant source
and test byte is identical on master. Direct assertions cover the selected source
array identities/values/metadata and checkpoint keys, budget synchronization,
restored ambient precision/rounding, distinct stop and wrapped-throw outcomes with
identical sentinel cause, fresh ownership and active aliases, cleared histories,
cache/checkpoints, preserved levels/cooldowns/options/policy, and stored precision.
No safeguard, tolerance, arithmetic precision policy or production code changed.
This remains selected state coverage, not inspection of every private factor field,
original-model certification, observer neutrality or arbitrary-callback rollback.

In each master case, iterations advance by zero and charged refactorizations by
one. Existing finally counters record one FTRAN, one BTRAN and one refactorization;
all other counted kernels are zero. refactor_other advances by one and all other
events are zero. Observer hits are one each; true stop calls are one for stop and
zero for throw. Source inspection already confirmed one additional untimed unit
BTRAN in the one-row weight rebuild. Up to three correction BTRANs remain allowed
by the test and production refinement loop despite solve_refinement=false. The
observed zero corrections do not justify narrowing that contract. These are
partial finally counters and lifecycle entries, not complete PREforward, backend,
import or allocation accounting.

No unnecessary production computational work or memory cost was found: there is
no production change. Permanent cold-test overhead is two setup/transfer
lifecycles. Each case intentionally copies 31 source arrays/76 entries for
preservation checks and three detached arrays/nine entries: 34 explicit copies/
85 entries per case, 68/170 per two-case run. Across the one GREEN and one master
run, four new setup/transfer lifecycles were recorded, with 136 explicit test
copies/340 entries, beyond unchanged fixture/checkpoint/solver allocations.
The bounded source-after/fresh scans test distinct ownership/value/precision
properties; no extra production basis solve, per-iteration scan or growing ledger
was added. Driver accounting adds three integer counters, two fixed records and
28+64 post-case dictionary lookups per row. Offline hashing and source/report
processing are setup/cleanup costs.

These explicit copy counts are not total allocations or native retained memory.
Source/fresh graphs may remain GC roots, and clearing a Ref does not establish
collection. No material avoidable diagnostic overhead was found. Since no
production hot path changed, sparse/dense performance benchmarks would add no
needed evidence here; elapsed times and equal counters do not support a speedup.

## Final scope and limits

Accept the exact test-only integration and this single master validation. The two
permitted S5-I guarded runs are now used; no rerun, warmup, old-file/full-suite run
or expanded success-control matrix is part of this acceptance. Final report,
STATUS/roadmap and independently checked closure may now document these results,
while publication/push identities still require their own checks.

Preserve original G false audit62/63 and separate seven-check supplement, the
prelaunch offline RED3/GREEN4 amendment history, all prior rejection gates,
CI-off/HH-disabled status, Q GC/outlier limits, bootstrap/cache/init limitations,
whole-controller/native-retention limits, and historical/x64/full-suite failures.
No solver fix, performance result, broader precision/backend qualification,
certificate transfer or broader S3/S4/S5/S6 success is established. The proposed
S5-J plan remains accepted only as the bounded future source/evidence reconciliation
specified in green-review.md; no additional numerical or handoff qualification
was performed here.

## SHA256 bindings

- actual master test / H candidate: 6b65d9194917ddde0e883fdb75c649a1d7eef229e57a210c11cc980fbc6d8616
- original prefix: 37fe8c270e8cc8c66155cccd23491df171eba34647a442c4a809fab705ddb24c
- H append: 697ed577c5dba0210eeaf6b1f17b90a0c007a24fba948f87162122d51c0cd273
- executed suffix: 29e39d8ad93f3c268d3f68b152d28100592988591979392ad87711754dd5303b
- master pins: 51b3328731ee9bb77b8721b3c411600ad132ec659395392a93e836352ffdbbc3
- master process: c6b5fa2c6e3dcf0071adfec53b676605448c4bc2b54e36002b6409543afc2375
- master report: beb2e46b169be1d837a8985a454e4fb6201d86232b7262cc0579dc6157aa8b6c
- master audit: b35fc2db044094b5cd6e1c04361dac0e10236d60128e7802436917f1aef854ab
- master independent: 541c28c7d7a7311dcbc170ff1540bf9c7aee32e91604b7aa75bbadfb2628683f
- master source comparison: ae410cc2c22184c34988b0edf81051096676076cebfa59c60a3ea92030094907
- after-master: df150cf4cd49b4ec0f7db784ff41ecc66927523d21de90b362a7d6b1486ecb66
- accepted GREEN review: 8c8dd7a38d41eeae81d728ed6250a941b9872d787a2f517f04457121f70b91e9

## Final publication text and continuation review

Subsequently read the new S5-PRECISION-JOURNAL-INTERRUPTION-TEST-INTEGRATION.md,
updated STATUS current-state/continuation text, appended roadmap entry, and the
unchanged S5-J plan. The numerical outcomes, commit/source identities, inferred
298+2 assertion split, four lifecycle total, partial work limits and explicit copy
costs agree with the checked evidence. Documentation preserves the distinction
between H structural checks, I runtime validation and wider unqualified claims.
The S5-J continuation requires reuse of existing exact-composition evidence before
identifying any gap and authorizes no new numerical fixture, launch, source/test
edit or HH/DSE/controller-budget audit. This is accurate bounded continuation,
not qualification of the dual auxiliary handoff itself. No further finding arose.

Independently verified both *.before-I STATUS/roadmap snapshots against the old
S5-H closure hashes. The live continuation files are not in the master launch pin
inventory, so their authorized updates do not alter the independently verified
launch inputs. Frozen H and I evidence remains distinct from new publication.
The review index and final PASS closure are still to be created and checked by
the publication workflow; this review does not claim they already exist or that
push refs have been verified.

Publication identities reviewed:

- integration report: 427f454fea59ad1c7e67b3d3a802c38cf1205c4b3bb5f5e82c96bfe7b544a488
- STATUS.md: f08604ffd5ac30b4a047578092400ae50abcf34bad946828c01b11d608e4cd06
- roadmap: c2232dc8bb5cce8795c854c83c0c6b3a6880b6dc9091cd46f164fc9c2f0c5da5
- S5-J plan: 4b1c7a2bc7673a5b6a1820856fb378948e0bb22b78f2d0a96e916b85a6868ab2

Read the new closure.py source without executing it. Its exclusive final-output
gate checks the two inventories/raw copies, accepted review digest, source/main
identity, protected users, preserved historical closure, G false/supplement and
process absence, and binds the final publication files. No blocking issue found
for this bounded closure role. The script is not a new numerical validation and
its PASS remains pending execution. Reviewed closure.py SHA256: 707b1f718d0eb690bb3e8fb3d07394e18c3f85a9eff1445190282a26754f1e7e
