# MA-S: bounded DenseLU BigFloat admission preparation

Status: corrected preparation independently accepted; no unresolved findings. No Julia executed.
This step prepares the next numerical attempt; it does not qualify a speedup.

The immutable MA-R candidate/reference/tests/fixtures feed the new driver and
private environment. The driver preserves a two-failure route RED before candidate
loading,160correctness cases and52fixed cost cases. Source-derived budgets are
488correctness/smoke entries plus12480cost entries in three serial processes,
318explicit setup factorizations and2PFI copies. No extra calibration or first-call
solves: first warm windows carry first-call compilation. Product preparation is
inside every measured whole FTRAN/BTRAN call; resets and exact output/input checks
are outside. Diagnostic snapshots and preservation scans remain O(n²) outside
windows and can perturb GC/cache state; no observer-neutrality claim.

- [Canonical admission and work ledger](results/MA-S/admission-reviewed.md)
- [Unexecuted driver](results/MA-S/driver.jl)
- [Canonical launcher](results/MA-S/launcher-reviewed.py) and [auditor](results/MA-S/audit_reviewed.py)
- [Canonical manifest](results/MA-S/pins-reviewed.json)
- [Reviewed offline Python tests](results/MA-S/offline-tests-reviewed.json)

36synthetic Python checks passed, including wrong/missing RED/case/window data,
exception expectations, allocation/time thresholds,15/21faster-pair boundary,
resource guards and stale source pins. These are not Julia tests or live guard
qualification. Six preparation gates passed;4247fresh source/runtime bindings.
The old MA-P manifest supplied paths only; no old hash or execution was reused.
The guard is a new byte-identical copy of the reviewed guard; pure helpers alone
were exercised. Existing-loader mode is not cache confinement or import-work proof.

A future launch requires a fresh full host check and launch-context referencing the
then-published commit, plus independent numerical-review bound to the exact context,
manifest and preparation review. Launcher fails before reservation if that seal is
missing. Standing human permission for short numerics is already recorded; no new
permission question is needed. Maximum3processes,120s each including termination,
360s total process occupancy; first unexpected failure stops the sequence with no
retry. Every52case must satisfy unchanged per-case correctness/cost criteria for
promotion. Failed performance must remain a rejected outcome, not trigger tuning.

Production/test/user environments/master are unchanged. No launch-context,
numerical-review, sequence reservation or numerical output exists in preparation.
CI off, HH reuse disabled, automation paused; broader plan remains open. Current
MA-R continuation bindings map only to preserved MA-S beforecopies; all previous
maps remain. Next concrete work is fresh launch sealing and independent numerical
admission, then the one bounded sequence under existing permission if accepted.

The initial independent review rejected two P2 raw/stage-schema gaps: Boolean or
float values could pass integer index/exit equality, and invalid memory evidence
could pass one-sided limits. One separate offline correction preserved all original
sources/review/manifests and produced canonical reviewed variants. Seven source
predicate RED counterexamples and65new passing Python checks (including original
coverage and29new checks) bind strict indices, exit/resource/identity/limit schemas.
All original4247pins and16initial-review bindings remain unchanged; final manifest
has4262entries. Fresh final gpt-6-astra review independently accepted the correction
with no unresolved findings and no unnecessary candidate work or retained memory.
See [final review](results/MA-S/admission-review-final.md). This is preparation
acceptance only; the numerical schedule remains unconsumed. No numerical seal or
reservation is created here. Use canonical reviewed files for later admission.
