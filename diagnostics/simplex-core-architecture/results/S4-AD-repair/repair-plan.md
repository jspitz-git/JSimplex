# S4-AD collector correction and separate admission

The first RED attempt consumed its reservation and failed before Base.include:
Test.push_testset is undefined in installed Julia 1.13.0. No test was executed;
exit1 and the false audit are preserved in S4-AD/red. This is NOT expected RED.
The original three-process plan and all accepted review/pins remain frozen.

Standing human permission for additional short attempts applies. This amendment
admits no launch by itself. After fresh independent correction/admission review,
allow one replacement RED, then the original GREEN and master sequence, each
with a distinct manifest, reservation, output and 120-second guard. No retries
within these stages. Original failed attempt remains part of the full budget:
at most four processes overall, of which the first ended after 2.00535 seconds.

Replace only the diagnostic collector's unavailable push/pop context with the
installed Test.@with_testset macro around Base.include. The macro scopes
CURRENT_TESTSET and TESTSET_DEPTH and restores both on normal/exception exit.
Nested @testset inherits RecordedTests and finish records children after their
scope exits. Do not add finish for the outer file collector. All test code,
result schema, 20pass4fail RED oracle, 722 GREEN and 324 master counts remain.
No production/test change until valid replacement RED; exact AC candidates only.
Full group/session sets start at36 and grow38/40/42. Pin all original failed
attempt artifacts and original reviews. Never rerun or rewrite their auditor.

The existing integration plan's remaining work/review/commit/push gates apply.
No new benchmark, changed numeric arithmetic, dependency, CI or HH reuse.
