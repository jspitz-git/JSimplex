# Independent RED result review

ACCEPTED, no actionable findings, scope **stage result**, phase **red**. This
review qualifies the single expected missing-interface RED result only. It does
not accept candidate numerical correctness, ordinary backend plumbing, recovery,
performance, GREEN or cost execution, or production integration.

The frozen Task2 plan, ADMISSION-reviewed.md, exact-stage admission, selected
source, wrapper/guard/supervisor source, raw TOML, all process/invocation/resource
and host records, both logs, audit, author REPORT.md and 14-check/9-binding
postcheck were independently inspected. No Julia query, Julia parser, import,
compilation or numerical execution was performed; no historical script, stage
auditor or existing checker was rerun. The new reviewer-result-check.py uses only
Python standard-library saved-data/hash and read-only Git/proc checks.

All **22 independent checks passed**. Every one of the 951 sealed and 954 launch
inventory entries was rehashed with resolved-path and exact-tree verification;
exact 952-member admission binding and manifest digest match. All 679 runtime
bindings, 872 preparation bindings, 873 final offline-review bindings and all 98
audit bindings match. The stage contains exactly 73 unchanged reference files,
each equal to its recorded source/hash, without symlinks or multiply linked files.
HEAD is 0798705ae92aa2f908b7468439b984deccde4c68 and master is
6f68e24e8ddac42b948da8fcc2d636c010751194; tracked/index diffs are empty.

Raw complete=true and fatal=""; the sole child testset retains exactly four
failure strings, in order: SolverOptions.native_pivot_policy,
JSimplex._NativePivotPolicy, UMFPACKBackend.pivot_policy and JSimplex._native_lu.
Pass/error/broken counts are zero at both root and child. Child returncode=1 and
reason=exit1 are preserved; guard/supervisor returncode=0 means the expected exit
was observed. Audit all_passed=true does not convert these four false assertions
into passing assertions. Raw is written before final exit. The empty run.log is
consistent with Capture retaining failures in raw; launcher.log exactly matches
the process record. Earlier rejected preparation/Test API evidence remains hash
bound and unchanged. No retry, replacement raw data or repaired attempt exists.

The command, reservation, config and guard command agree exactly, including the
reference project, reviewed test driver, phase red, existing compiled modules,
Julia/BLAS one thread, GC threads1,0 and 2-GiB heap hint. The pinned wrapper selects
Julia1.13.0 with startup disabled, offline package mode and automatic precompile
disabled. Source and actual loaded package/stdlib paths agree. RLIMIT_AS8GiB,
RAM>=6GiB, swap<=1GiB, global lock, pidfd ownership and one-shot exclusive records
are enforced in the inspected source. Existing-module mode is not proof of cache
confinement or zero import/initialization work.

Inclusive launcher elapsed **5.989787794009317s <=30s**; guard elapsed
5.4733938930148724s <=22s. All timeout/kill flags are false, cleanup has no error,
and accepted reaping is recorded. Five raw resource samples match the audit:
minimum available RAM **22,180,688KiB**, swap **0**, terminal available RAM
22,327,068KiB and child resident high-water **427,876KiB**. These are process and
resource-guard observations, not component timings or a native allocation ledger.

Current/process/supervisor identity records agree: runner229464/start13681290,
child229465/start13681339, each with PID=PGID=SID, boot
284d2228-1d9a-4c5f-913c-b9f1098b5838. Pre/post host records cover the historical
identifiers and both new identities. A newly written independent /proc scan
checked **all210 identifiers as both groups AND sessions**, process names and
readable executable paths: no matches or Julia processes. Unreadable system
executable links remain the documented visibility limit. This snapshot is not a
substitute for future preflight.

Computational work and memory review under AGENTS.md: **no unnecessary new
production work, allocations or retained memory found**. The exact unchanged
reference is used. The selected RED body comprises four metadata assertions and
has zero constructor/factor/refactor/copy/solve/update/native entries; the empty
pre-forward counts, event and equation records agree. There are no added
full-vector/matrix scans, basis solves, conversions, control copies, update-chain
traversals or repeated numerical invariant checks in setup, each iteration,
each candidate, recovery or certification. No production precision, tolerance,
coefficient or safeguard is changed. Shared diagnostic support allocates 2048
event reference slots and400 equation reference slots once during loading; RED
leaves them unused. Capture retains four failure strings and one child testset.
This bounded cold storage does not scale with dimensions, nonzeros, update-chain
length or factor lifetime. Import and compilation are additional work inside the
inclusive cap; empty component records do not prove zero native initialization.
Offline hashing/process scans are verification work. No before/after benchmark
is warranted for unchanged production, and no speedup or zero-overhead claim is
made from this single process duration or memory high-water.

Supplementary evidence is in NATIVE-PIVOT-RED/reviewer-result-check.json and
reviewer-result-host.json. Separate reviewer-result-supplement.json binds the
author report/postcheck and prepared continuation/finalize/publication sources;
those sources were read only and were not executed by this reviewer. The exact
stage result JSON has only accepted/findings/scope/phase/pins_sha256/sha256; its
membership is precisely audit.sha256 plus audit.json (99 entries). Supplemental
bindings deliberately stay outside that admission contract.

Only RED exists and its sole attempt is consumed. GREEN requires its own fresh
seal and independent exact-stage admission; cost and public/recovery integration
remain later gates. No GREEN was run or authorized by this result review itself.
