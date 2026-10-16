# Concrete observer, work and admission contract

## Fixed selected tests

Use the exact accepted Task3 tests from NATIVE-PIVOT-INTEGRATION-PREPARATION.
PFI/FT/SS/BG x default/threshold_one gives8 public solves of the same tiny LP,
with original options/tolerances/certificate checks and optimum[2,2],objective-10.
Case9 uses the original1x1 PFI workspace/checkpoint/private recovery trial once.
It checks private factor/control ownership, live/checkpoint preservation and
consumed refactor work. Five17field option comparisons use six copy calls including
the Float64/BigFloat/Float64 roundtrip; no BigFloat solve. Successful162 assertions
are mandatory, with exact test tree and case order in oracle.py.

## Diagnostic counters and controls

ProbeFailure is separate from production numerical exception types. Every selected
backend entry increments its attempt counter BEFORE checking its cap and BEFORE
calling the operation. failed is sticky even if Test captures the exception.
Successful construction/refactor validates enum, then all20 actual control bits.
Empty factors are counted separately. The probe retains no backend/factor/native
owner. Expected control vectors are obtained once per case, changing only pivot
and IRSTEP for threshold_one; oracle.py compares them to20 fixed defaults saved in
the accepted component result (controls-baseline.json), not to a new runtime query.
Other slots and all numerical safeguards stay unchanged. Result capture is after
public solve, with two point scalars/objective/status, not a trajectory snapshot.

Per public case caps are64 managed constructions,64 refactors,4096 forward and4096
transpose entries. Recovery caps are2/0/2/6; required successful recovery work is
2 constructions,0 refactors,2 F and3..6 B (the extra up to3 weight-refinement entries
are source-derived possibilities). Aggregate caps514/512/32770/32774. These guard
selected managed Float64 UMFPACK backend calls, NOT all manager, extracted-factor,
raw auxiliary LU, native-internal or controller work. Public counts depend on
trajectory; zero exercised public refactors is reported rather than forcing work.
No identical trajectories are required across policies. Source-local tests and
counter gates do not prove observer neutrality or a complete PREforward budget.

## Work and memory cost

The production candidate is unchanged: zero NEW production scans, solves, copies,
conversions, caches or retained owners in this preparation. The diagnostic overlay
adds constant scalar entry checks per selected attempt and one20slot scan per
successful nonempty construct/refactor. At the caps, at most20520 control entries
are checked, in addition to9 expected-control preparations (180entries).
Fixed numeric storage is72 Int counters +360 UInt64 controls +24 Float64 result
values =3648 payload bytes on64-bit, plus BitArrays for25 logical flags,8 string
slots, fixed ID tuples,3Refs and container/object overhead. Each of9 expected
control vectors has20 Float64 entries (1440 cumulative payload bytes plus headers),
not a retained native owner or native-memory bound. Capture status strings and
Test result storage allocate; this integration is not a cost measurement.

After cases, snapshot builds nine dictionaries and fixed token arrays. The
collect(array[:,i]) expressions create a slice and a second collection for each of
three counter records per case:27 temporary slices plus27 retained serialization
vectors,72 entries in each set (576 payload bytes each on64-bit), all outside solver
calls. Token formatting/dictionaries/TOML and raw failure text add bounded output
work; an arbitrary error message is not a strict total-memory bound. No growing
per-solve event ledger or callback vector snapshot. Existing public input snapshots
are6 objects/8 buffers/23 entries per case; recovery14 vector copies/44 entries plus
checkpoint5 containers/9 entries. Solver/factor/Test allocations are additional.
No diagnostic storage count is an allocation measurement, native graph cap or GC
proof. No timing result or speedup is claimed.

## Future launch, not executed here

Only phase integration is accepted. One fresh stage76files, one process, one
reservation, inclusive supervisor60seconds/inner guard52seconds. Julia/BLAS1,
heap2GiB, VM8GiB, availableRAM>=6GiB, swap<=1GiB; no large LP/full suite, retry,
extra warmup or increased limit. --compiled-modules=existing and ordinary loader
are inherited; this is not proof of cache confinement or complete import work.
seal.py requires preparation review, exact required membership, unchanged inputs,
environment, master, boot and fresh full216groups ANDsessions/noJulia. It creates
a fresh stage and immutable seal only. A separate independent exact-stage review
must bind every sealed file plus seal before launch.py can reserve one attempt.
The launcher additionally binds admission/prehost/reservation/command, supervises
termination, records posthost and audits. Stage/seal/launch were NOT invoked here.
A real boot/environment/ref change needs an explicitly reviewed new admission
arrangement; never overwrite old host/pins or silently bypass a gate.

The driver defines its probe before package loading, then loads the scoped Test
recorder and includes the observed tests once. Raw is written before final exit
when main reaches finally; loader failures before main can lack raw. The auditor
requires exact process/output membership, command identities with boot/start_ticks,
all file hashes, resources and terminal cleanup, exact tests/cases/controls/results.
Missing/malformed raw, any assertion/error/sticky probe failure, cap violation,
nonzero child exit, deadline/guard failure or surviving groups/sessions rejects.
Preserve all evidence and stop, no automatic numerical retry.
