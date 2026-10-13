# MA-A private scalar dot experiment

User explicitly requested this short measurement. One120second guarded Julia
process; VM8GiB, heap2GiB, RAMfloor6GiB, swapmax1GiB, Julia/BLAS1. No public
solver, JSimplex import, production/test/environment/CI changes, or long runs.
A separate diagnostic Project declares MutableArithmetics and TOML; copied
manifest uses existing packages without Pkg/instantiate/precompile operations.
Existing-only compiled modules, offline and automatic precompile disabled.

Exactly12 cases: BigFloat128/256/512bits and Rational{BigInt}, each n32dense,
n256dense and n256 with7/8 zero a entries. Same loops visit every element.
Exact fixture formula in driver.jl: a=((17i mod61-30)*2^80+(-1)^i)/17,
b=(13i mod47-23)/19, optional a=0 unless i divisible8. No random source.

Plain sequential s=s+a[i]*b[i] vs private acc+MA.buffer_for(add_mul,T,T,T),
MA.operate!(zero,acc) then MA.buffered_operate!(buffer,add_mul,acc,a[i],b[i]).
MA1.8.1 supports both types. No FMA/reassociation/zero omission. BigFloat scratch
created inside the selected precision scope; all values/buffer precision checked.
Rational private BigInt leaves, BigFloat private :d leaves are pairwise disjoint
and disjoint from input leaves. Input mutable copies verify no changes after
every window; private leaf identities checked throughout. No shared solver state.

Per case: one plain reference call,3 warm pairs then7 measured alternating pairs,
32 complete dots per window,20 windows/case =240total,168measured. Across cases
7692dot calls (7680window dots+12references),1394816multiply-add loop visits
(20*32+1)*(32+256+256)*4. Setup separately @timed including its compile costs;
no setup allocations charged to steady-state candidate. Reset and common Ref
output assignment are included in both windows. No GC calls or benchmark library.

Both exact Rational results and BigFloat sequential isequal required each window.
Independent exact rational dot of actual rounded inputs and gamma(2n)*sumabs
bound (u=2^-bits) checks floating error, Rational bound0. Scoped RoundNearest and
precision restored. All measured compile/recompile times must be zero. Preserve
all times/GC/bytes/allocation events; in-window GC reported, never silently discard.
Counters are Julia aggregate GC traffic (may include counted native allocations),
not a native free/retention ledger. BigInt limbs may still allocate as values grow.
Input/oracle/ownership scans, serialization, setup and graph queries outside
windows. One process/small synthetic fixtures, no solver/end-to-end speedup claim.

Fresh independent exact-manifest admission review BEFORE ONE launch. Freeze
actual source/MA/runtime/project/scripts/refs/authorization; full30priorgroups
ANDsessions absent. Postexit verify pins, process/resource/logs,240window schema,
all outputs/errors, independently recompute exact input dots/bounds and paired
medians/ranges. Fresh independent result/work/memory review, preserve evidence,
separate PASSclosure/exactstaging/failfastpush. No old script reruns. Automation
remains paused. No production optimization or new dependency addition is implied.
