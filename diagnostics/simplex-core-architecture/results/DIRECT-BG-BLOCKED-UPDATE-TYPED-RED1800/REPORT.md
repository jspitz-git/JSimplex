# Blocked BG RED1800 — incomplete OOM/SIGSEGV result

The single independently admitted RED1800 attempt is **not accepted**. It ended in dense256/native (unit13) after a fatal OutOfMemoryError, then SIGSEGV in shutdown/finalizer handling. The child returned -11 after776.087964727s, supervisor returned1/accepted=false after776.724177337s, and outer returned2 after786.032045617s including integrity checks outside the numerical window. All timeout/termination flags are false. This is not a timeout-only failure and does not authorize an automatic longer rerun.

## What completed

Exactly27 payload files survived: units1..12 and their12 costs, plus three load records. No final raw.toml, unit13 or cost13 exists; units14..28 never started. The saved prefix has **55695 passes, two expected N026 failures, zero errors and zero broken tests**. The two failures are dense96/native and dense96/Markowitz blocked-route coverage, not mathematical failure. Both sparse256 cases completed. The target of six expected N026 failures across all28 units is NOT verified.

Panel11768 assertions passed, including P011 once and P095-P102 once each. These retain the zero-byte/event, return-value and input/owner predicates. This is assertion evidence, not a standalone raw numerical allocation probe. The frozen source-bound prefix checker validates all completed unit counts, API/event budgets, mathematical and ownership test results. An interrupted unit cannot establish its own mathematical correctness.

The admitted auditor remains all_passed=false, pure_timeout=false, error=RuntimeError('Exact payload membership'). Its original record is preserved. A new supplemental saved-prefix checker passed21 checks without rerunning that auditor or Julia. Diagnostic acceptance by the subsequent independent review cannot convert this result into accepted RED; no result-review acceptance is written inside the run directory.

## Memory and causal limits

There are775 resource samples, minimum available RAM14527116KiB, swap0 throughout, terminal availableRAM22493520KiB. The guard's OS wait record reports child maxRSS7709432KiB; sampled VmHWM/VmRSS maximum7710180KiB is a separate observation. Sampled VmPeak reaches8388608KiB, exactly8GiB. The unchanged guard sets RLIMIT_AS to8GiB. The log first reports OutOfMemoryError in GC page allocation/exception-stack handling, later another OutOfMemoryError during atexit, then signal11 in run_finalizer. The process hit its virtual-address-space ceiling despite substantial free host RAM. This supports memory exhaustion under the admitted cap; the log does not identify the initial application allocation, establish a leak, prove native heap ownership, or show a BG numerical defect.

The test source includes exact Rational{BigInt} original-basis and chronological history checks. Saved sparse256/native and Markowitz cold unit costs are172.390993109s and173.484848308s, with182030397056B/4404446035events and182030742480B/4404679783events respectively; GC56.142480310s and54.661405587s. These are diagnostic cumulative allocation traffic, not retained memory or a production kernel benchmark. The lifecycle unit cost149.426662247s contains5.985205238s compilation and71.708440007s GC. Loading records overlap other preparation; do not sum them into an independent execution budget. Unit13 has no saved timing/allocation record. There is no measured attribution of its first failing allocation to an exact-rational helper or to factor updates.

## Integrity and disposition

HEADcc9d35dc3e2c526bcae8b752ca2ea43dad9a5212 and master26e2291745999f485a74f643298ca997d65c7205 were bound. The sealed manifest has2352 subjects, admission2353 bindings, and launch2357 subjects. All recorded inventories remain unchanged. External phase red1800 selects the unchanged driver/raw semantic phase red300. Twenty-two exact copies and all numerical controls remain as prepared.

Independent exact-run admission passed3467 checks. The reviewer's initial login-shell PATH assertion failure is preserved with source/result; its separate v2 verifies the actual executing outer environment and passed. No target environment or source was altered. The original RED300 timeout and all81 lineage bindings remain frozen and unaccepted.

Outer214974/start14546623, guard215655/start14580804 and child215656/start14580862 share boot1ecae454-f1f5-4e2e-a95c-7b5474243126. External closure verified all292 historical/new PGIDs AND sessions absent, with no visible Julia. Inaccessible executable symlinks remain an explicit visibility limitation, not universal process-identity proof.

No production/test/environment/CI/master/global STATUS/roadmap change occurred. No unnecessary new production work or retained memory was introduced; only the already reviewed cold diagnostic work and longer permitted sampling ran. The one attempt is consumed. GREEN and Task3 remain blocked by incomplete RED qualification. The next useful work is source/log analysis of diagnostic allocation and retention before any new driver or memory-limit proposal; no such change or further numerical run is authorized by this result. Preserve every raw file, failed audit and reviewer correction.
