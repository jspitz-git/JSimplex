# Independent review: BG blocked U RED2 preparation

Accepted for OFFLINE preparation only. Findings: none. Launch admission, runtime acceptance, numerical acceptance and performance acceptance are all false. This review authorizes no outer, seal, reservation, release, Julia execution or retry.

Reviewed diagnostic HEAD `ee7d652cd4939d2fbce32f10c56073fbc62b640c` and master `26e2291745999f485a74f643298ca997d65c7205`, the current plan/spec and progress ledger, all changed control/launch/outer/audit files, the complete immutable preparation input set, the accepted stage-repair review/publication and unchanged numerical controls. The reviewer used the requesting-code-review template. Only fresh reviewer artifacts were written; no source, candidate, stage, original checker/evidence, index or Git ref was changed.

## Strengths and evidence

The independent checker `independent-review-2.py` passed 2,293 checks, recorded in `independent-evidence.json`. It rehashed all 347 preparation inputs, reconstructed the exact required set independently from the historical preparation/review and repair publication closures plus the explicit new-package roster, and checked the prospective 348-input review membership including preparation-pins.json. There are no missing or extra required paths. It checked both tracked source baselines and clean tracked/index state. Every one of the 609 runtime inventory entries matches both resolved path and SHA256; their logical file sizes total 1,255,423,127 bytes. These are read-time bindings, not a loader trace or runtime dependency completeness proof.

All 75 repaired-stage files match the accepted repair. All 71 committed master entries match Git objects directly after removing the two documented root adapter includes; stage membership is exact and has no symlinks. The 14 candidate files retain accepted hashes. The driver, recorder, three test clones, oracle, guard, supervisor, schedule and other declared copies are byte-identical to the frozen first harness. AST comparison confines control-function changes to config, validate_sources, validate_stage_binding, preparation and predecessor. launch.py, outer.py and audit.py differ only by the new exact-admission scope. Author receipts contain the reported 25 routing, 31 full-auditor synthetic and 44 source checks; no author or historical exclusive checker was rerun.

Fresh checker development history is preserved in `independent-checker-history.json` and `independent-review-1.py`. The first invocation correctly encountered environment rejection because a login shell expanded PATH; the non-login environment exactly matches the pinned environment. A later reviewer fixture expected the warning predicate to match the artificial bare text `method foo overwritten`; this does not contain a warning marker or the regex spelling `overwrite`. The corrected fixture uses the actual WARNING-form diagnostic. This is a reviewer fixture correction, not a harness change or numerical result. Actual warning, world-age and method-overwrite diagnostic forms are rejected. Runtime log behavior remains unexecuted.

## Admission and isolation review

- `control.py:19-30,60-73`: only red300 is accepted; GREEN, red600, malformed and unknown phase inputs fail. The new absolute run/output/outer roots and driver path resolve inside this package. The repaired stage and its accepted source-only review/publication are checked. Preparation requires strict boolean acceptance, no findings, the exact new preparation scope, exact input membership/hash and launch_admitted=false. Old scopes, missing/extra bindings, altered pins and nonboolean acceptance were independently rejected.
- `control.py:79-112` and launch.py/outer.py/audit.py: the failed original RED is historical evidence, not a successful predecessor. Its files and old stage remain frozen. Future exact seals include preparation/reviewer evidence, runtime/source/stage bindings and new host/config/outer identity files. Exact membership, trees and inventory are revalidated. All three admission consumers require `BG blocked U RED2 exact-stage admission`; a preparation or old exact-run receipt cannot substitute. Positive/refusal routing was exercised with an in-memory synthetic receipt, without writing any admission or seal.
- `control.py:45-59,86-102,117-125`, guard.py, supervisor.py and post-return.py: all 271 historical identities are retained; process matching checks both PGID and SID and comm/argv0/readable executable, with inaccessible executable links explicitly reported. Boot/start_ticks/command and outer identity linkage remain required. Fresh local/remote refs, host state, source/runtime/environment and clean tracked/index checks remain in the future seal/launch path. Post-return closure includes the outer and all runner/child group/session identities. No fresh launch-time host claim is made by this review.
- The configured inclusive budget remains 300 seconds and the inner guard receives 292 seconds plus an absolute deadline from the original launcher start. Supervisor cleanup is bounded by the inclusive deadline. One Julia/BLAS thread, gcthreads=1,0, heap hint 2GiB, VM8GiB, availableRAM>=6GiB and swap<=1GiB remain unchanged. The outer's 1200-second admission wait is outside the numerical budget. No run/outer/seal/reservation artifact exists.

## Numerical controls retained

The 160 assertion-site universe, 28 ordered units, 13 fixtures/26 backend cells and 512 stream replacements/begin/finish events remain unchanged. Exactly six N026 failures are allowed, for dense96, dense256 and dense96-long32 on native and Markowitz; every other mathematical, ownership, history, policy and API-attempt check must pass. Counts remain event-conditioned and reconciled rather than invented fixed totals. The driver loads modules at top level and checks actual staged JSimplex path before units; the auditor checks all loaded paths, complete unit/raw schemas, ordered logs, exact failure sites, resource/identity evidence and warning rejection. Expected exit 1 alone cannot qualify RED.

The five requested numerical review focuses are preserved:

1. Stale pivots/pure swap: numerical N001-N004 retain current shadow/pivot-policy checks; P027-P028 retain zero-diagonal and cross-boundary pure-lookahead rejection tests. The unmodified candidate/scalar suffix and repaired master bindings remain authoritative.
2. Zeros/presence/nonfinite: P015, P029-P032 and P092-P094 retain stored signed-zero/nonfinite rejection, cancellation, tiny coefficients, absent-source preservation and canonical-zero checks. L025-L032 retain overflow/nonfinite sticky-invalidity and scalar failure controls.
3. Logical/physical IDs and history: P034-P044/P051-P059 retain nonidentity order, support/outside-band and stable incidence tests; N005-N011 retain the post-spike H relation, independent chronological history, base preservation and incidence checks. Original-B residuals remain independently formed from requested entering columns.
4. Failure/alias/prepared RHS: N017-N023 and L001-L019 retain both prepared destinations, unchanged inputs, saved-factor divergence and scratch copy/refactor rules. L033-L040 retain gather/reserve/writeback failures, partial progress without false rollback, and reentrant-access rejection.
5. Sparse/work/scratch: P001-P015 and P049-P080 retain cheap rejection, separate eligibility/gather counts, preallocation commit cap, one stable-ID scan, prefix/suffix copy and coexistence accounting. Scratch reuse/shrink/copy/failure controls remain. This preparation adds no numerical work.

Fresh synthetic tests exercise real oracle and auditor validation while explicitly mocking host/ref/hash/admission boundaries and using JSON transport in place of TOML decoding. They reject incomplete/malformed units, missing raw, wrong failure sites, unknown events, missing API/assertion counts, bad loaded paths, invalid thread types, nonfinite observations, warnings, bad resource/identity evidence, deadline overflow and cleanup failure. Pure timeout remains failed; malformed prefix data cannot qualify as pure timeout. The full audit wrapper saves a failed receipt for invalid data. These tests do not execute a process or establish numerical correctness or TOML runtime emission.

## Issues and recommendations

Critical: none. Important: none. Minor: none requiring correction within this preparation boundary.

Proceed only to a separately authorized exact-run boundary. Preserve this preparation and historical failures. Recheck the pinned loading environment, fresh host/refs, exact seal membership and independent exact-run admission before any future release; use the new paths exclusively. No runtime acceptance should be inferred from the source/hash or synthetic checks.

## Computational work and memory verdict

No unnecessary new production computational work, allocation or retained memory was found. Evidence is the exact source-baseline comparison, unchanged 14 candidate files, unchanged Julia driver/recorder/test/oracle controls, and five-function Python-only delta. There are zero new production full-vector/matrix scans, basis solves, factor copies, conversions or invariant checks at setup, refactorization, iteration, candidate, recovery or certification frequency. The accepted master-stage setup-policy cost remains existing behavior; it is not a new optimization or free operation.

New cost is cold Python preparation/admission hashing and JSON metadata for the repair bindings. These validations repeat at integrity boundaries and scale with immutable file bytes/counts; they do not scale with n, nnz or update-chain length. validate_stage_binding reparses its small review metadata and can rehash overlapping repair inputs; this is bounded cold integrity redundancy, not a material production or hot-path regression. The existing 1.255GB runtime inventory hashing is substantial cold IO and remains charged where performed, including guard work inside the inclusive process budget. No timing/allocation improvement is inferred.

The unchanged numerical diagnostic remains expensive: exact-rational relation checks can cost O(n^3) and grow BigInt operands; original-B conversions, Trace matrices/checkpoints, compilation/native allocations and 1536 FTRAN/512 BTRAN stream calls are additional. Candidate scratch remains `72n + 16*cld(9n,64) + 256 + 4096`, with packed-column coexistence, incidence/history/native memory separate. Recorder state is bounded to one unit, with 200 failure records maximum. No benchmark was run or required for this source-only routing change; sparse/dense performance, allocations, retained/native/RSS memory and completion within 300 seconds remain unproved.

## Declined to judge

- Julia parsing/loading, dispatch, world age, package ABI and complete loaded dependency closure: Julia execution is prohibited; exact source/read-time inventories cannot prove these.
- Actual numerical RED/GREEN outcomes or successful completion within 300 seconds: no new run exists; only preparation is authorized.
- Actual elapsed time, allocation events/bytes, native memory, RSS and sparse/dense speedups: no measurements are authorized; unchanged future performance gates remain open.
- Live process signalling/reaping and launch-time host/ref/resource freshness: guard/supervisor are unchanged and inspected, but executing them or a future outer/launch is outside this review. Synthetic process fields are not live process evidence.
- Production adoption, whole-solver original-model certification, HH reuse and other-precision behavior: outside this Float64/Int DIRECT BG diagnostic preparation boundary.

## Assessment

Ready to accept this OFFLINE preparation: yes. The new package binds the accepted repaired stage, isolates all future output/admission paths and preserves the existing numerical and process safeguards. Exact-run admission and all runtime/numerical/performance qualification remain false.
