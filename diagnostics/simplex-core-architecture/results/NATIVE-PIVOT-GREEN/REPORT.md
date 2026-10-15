# Native pivot policy GREEN: observer failure, qualification not accepted

ONE independently admitted candidate GREEN ran; the attempt is CONSUMED and
qualification is NOT ACCEPTED. Raw records5352passed,0failed,1error,0broken;
6858passes were required. The private_spare_copy_and_failure group completed62
of1568prospective assertions and then aborted, leaving1506unfulfilled. All eight
other groups passed their fixed assertions. The outer driver completed and
serialized raw with complete=true/fatal empty: that does not mean all tests passed.
The candidate is not qualified by the successful subset. No cost run followed.

## Source-supported cause

At tests-observed.jl:59 the existing updated helper builds a SparseVector RHS
column=matrix[:,1]+matrix[:,2]/4. NP.forward_solve calls the real solver, which
returned a dense Vector{Float64}. The eighth observed forward_solve event contains
after.kind=Vector{Float64} and two output tokens. It has no rhs field: the next
statement, test-support.jl:35, e["rhs"]=scalar.(args[2]), throws MethodError
zero(::String). scalar converts numbers to strings, while sparse broadcast calls
SparseArrays._map_zeropres!/_isnotzero on those strings. The raw stack identifies
this exact diagnostic conversion. It is the sparse RHS, not a sparse solve output.

The observer's catch covers both the production call and its diagnostic recording;
its exception/after_failure labels therefore do not prove that the backend threw.
This event proves a completed solver return followed by observer failure. It does
not establish complete factor correctness or observer neutrality. No source was
changed and no reproducer, Julia query or numerical retry was run. The original
support/driver/candidate, admission and every failed record remain frozen.

## Exit, audit and resources

Child exit1/reason exit1 and guard/supervisor return1 are preserved. The original
auditor records all_passed=false with RuntimeError('Inclusive limit/cleanup').
That combined predicate includes supervisor.accepted: here it is false because
returncode1, NOT because elapsed time exceeded its cap or cleanup timed out.
All timeout/kill flags are false, cleanup_error absent. Inclusive launcher time
28.980952097976115s<60; this includes compilation/import/output and is NOT a
performance measurement. Original vague error text remains unchanged.

28 resource samples: min available RAM21,871,576KiB, swap0; terminal available
RAM22,455,520KiB; child resident high-water783,296KiB. Selected call records289
versus792required; helper equations34 versus324required. These partial counts
are not a full work budget or a speedup. No unexecuted assertion is credited.
Fresh closure covers all212groups AND sessions/noJulia: runner238457/start14328901,
child238458/start14328949, boot284d2228-1d9a-4c5f-913c-b9f1098b5838. Identity uses
boot/start_ticks/command and full group/session scans, never PID alone.

Exact admission bound981sealed files plus manifest982; 75candidate-stage files
and source/runtime/environment/command/load paths remain identical. New postcheck
is a post-exit supplemental preservation check, never a retroactive launch pin or
a replacement GREEN PASS. The original audit is never rerun or rewritten.

## Work/memory and next gate

No production change was introduced. The faulty diagnostic broadcast allocates
text tokens/containers and can throw after numerical work, so it is avoidable
instrumentation work with incomplete sparse-input handling. A later isolated fix
should materialize token output into explicitly dense storage for sparse RHS and
outputs, preserving element order/values and leaving numerical inputs untouched.
That proposal is UNIMPLEMENTED/UNQUALIFIED; review all similar tokenization sites,
including equations, and account for O(n) diagnostic conversion/storage. It is
not a production kernel change and does not justify extra numerical warmups or
looser bounds. Cost-driver timers and candidate production sources stay frozen.

Next: separate OFFLINE observer/serialization correction and focused regression
coverage plus independent review, followed by a new, explicitly labelled admission
before any new GREEN attempt. Current reservation/stage/output cannot be reused.
Do not change the expected6858/792/324 budgets to the partial observed values.
Standing short-run permission remains, but no automatic retry is authorized by
this failed attempt. Cost<=45s and Task3 are blocked by the failed GREEN gate.
No actual src/test/env/CI/master/direct changes. Master6f68e24 unchanged, CIoff,
HHreuse disabled, automation paused; old direct cost1FAILED/CONSUMED/cost2BLOCKED.
Broader plan stays OPEN. All prior failures and continuation mappings remain.
