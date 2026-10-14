# MA-V initial independent review — pre-final rejection

The initial admission draft was rejected for four Important findings below. This is a preserved record of review progress, not acceptance of the corrected admission, a launch authorization, or a numerical result. Reviewed by the independent mav_admission_review agent, configured by the parent with the requested gpt-6-astra model. No Julia/parser/import/compile/numerical execution, old script rerun, launcher/guard main, production edit, or Git mutation was performed.

## I1 — Preserve completed samples when later work fails

costs, micros and generated_code returned local arrays only on success. Later checksum/owner/exception failures discarded prior samples; qualification discarded partial records. In-memory retention alone also loses evidence on watchdog termination. Evidence: `driver.jl.before-review`.

## I2 — Bound guard housekeeping by the inclusive deadline

Unbounded subprocess.run waited for guard cleanup and full pin hashing beyond the inner 84-second child timer. The observed 90-second rejection was not an external execution bound. Evidence: `launcher.py.before-review`.

## I3 — Apply per-process cost gates before the second launch

Stage validation checked raw schema but deferred required per-process allocation and timing budgets until aggregate after process2, allowing an already-disqualified first process to continue the sequence. Evidence: `audit.py.before-review`.

## I4 — Capture predicate code growth separately

Only the 256-call batch IR was captured. No probe-body IR/size evidence supported the planned bounded predicate-local code-growth review. Evidence: `driver.jl.before-review`.

## Follow-up review and correction status

The first supervisor correction relied on a concurrently reaped child leader while signaling numeric groups. The revised implementation snapshots each member, uses pidfd plus repeated identity reads and checks current owner identity.

A follow-up required fresh PGID OR session membership after the second member read; same_identity deliberately excludes membership. Final mock coverage includes member_left_session.

The optional no-scope predicate bypassed normal record! journaling. The diagnostic copy now journals its already-computed record; reconciliation orders it between the first20 and last5 transitions.

Raw sample retention now includes an append-only flushed journal outside timers. It is not an fsync/power-loss guarantee, and incomplete tails remain rejected evidence.

The current corrected source has been read substantively, but final immutable pins and their complete verification remain pending. Parent-recorded source-check26PASS, synthetic audit106PASS and supervisor10PASS are preparation evidence only, not runtime results. They will be freshly rebound/reviewed in the final admission review; no historical test output is retroactively assigned to changed source.

Independent byte/arithmetic checks already verified the MA-U candidate inverse to MA-R, five frozen copies, 840 correctness cases/844 calls per arm, 2080 cost calls, 61440 micro calls and 256 explicit static micro calls. Both diagnostic modules load before main, so source order avoids the former late-include world-age boundary. No invokelatest is required in this arrangement.

No unnecessary new production work or retained memory was found: production files and frozen MA-U candidate remain unchanged. The new diagnostic snapshots, progress references, IR capture and journal add cold setup/recording work and bounded retained evidence; they may affect later GC and must be counted explicitly. Source does not prove allocation elimination, speedup, runtime anti-hoisting, native memory bounds, or complete DenseLU/Rational acceptance.
