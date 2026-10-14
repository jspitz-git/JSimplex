# MA-S fallback allocation source analysis

This bounded SOURCE/STORED-EVIDENCE analysis separates two different phenomena.
The scoped BigFloat fallback has an invariant extra128bytes/8events per four-call
window across all42measured pairs. Its added rounding lookup is the leading
source-supported explanation, but exact emitted allocation sites are not captured.
The Rational{BigInt} fallback has equal aggregate event counts in all42pairs and
byte differences of both signs; no fixed extra candidate allocation is established.
Native usable-size accounting is a compatible mechanism, not a proven runtime cause.
MA-S-2 remains rejected48/52. No numerical run, Julia query/parser/import/compile,
profiler, disassembly regeneration, candidate edit or old script rerun occurred.

## Evidence and provenance

Fresh entry13checks verifies published HEAD1d5117b69ff3313986a4d7c6cb7a79961c91cdee,
master6f68e24 unchanged, local/remote refs, source514/protected6 and preceding
result-review96/closure60/publication61bindings. Full166historical/new PGIDs
ANDsessions are absent and no Julia process exists; boot/start_ticks/command
identity handling remains explicit. New analysis.py was saved before its single
execution, reads immutable MA-S-2 raw data and source, and writes analysis.json.
It passes21checks, records24readtime hashes (12also MA-S-2 launch pins), and retains
all336measured control pairs with original side order, GC, bytes/events and outputs.
This is Python parsing/arithmetic on stored data, not a replay of Julia operations.
No old validator, aggregate or collector is imported or rerun.

The12launch-pinned files include candidate/reference/tests/fixtures/corrected driver,
installed mpfr/scopedvalues/dict/hamt/gmp/timing and libjulia-internal. Other readtime
records are explicitly not retroactive launch pins. Three saved S4-O instruction
excerpts are checked against S4-O/source-attribution.json; its internal-library hash
also exactly matches MA-S-2's launch pin and the actual file. Thus the existing
native counter interpretation can be reused without another objdump/load/hook.
This does not capture GMP callback pointers or allocator requests in MA-S-2.
The exploratory lowercase enums.jl path was absent; pinned Enums.jl was identified.
No analysis depends on that failed selector.

## Full paired pattern

All pairs below are the seven measured pairs in each of three processes, both
forward and transpose, four backend calls per window. No warm result is relabeled
as steady state, no GC or outlier is excluded, and the admitted gates are unchanged.
All336control pairs preserve outputs/inputs and have zero measured compile/recompile.

| Class | Pairs | Positive/negative/zero candidate-minus-reference bytes | Byte difference range | Event difference |
| --- | ---: | --- | --- | --- |
| scoped BigFloat n32 | 42 | 42/0/0 | +128 throughout | +8 throughout |
| Rational{BigInt} n32 | 42 | 21/19/2 | -24608 to +26880 | 0 throughout |
| Float64 n32 | 42 | 0/0/42 | 0 throughout | 0 throughout |
| small BigFloat n0/1/2/8/15 | 210 | 0/0/210 | 0 throughout | 0 throughout |

BigFloat has21reference-first and21candidate-first pairs; its constant delta holds
in both orders, both directions, all processes, and the one pair containing GC.
Rational has the same21/21order split and two GC-containing pairs. GC cannot be the
sole explanation:40pairs without recorded in-window GC still range-352 to+18256.
That subset is a descriptive check of the GC-only hypothesis, not a filtered
acceptance calculation. All original samples and rejecting decisions remain.

The earlier +0–32byte rational summary is a difference of side medians, NOT a fixed
per-pair delta. For process2 transpose, median(candidate bytes)-median(reference
bytes)=+16, while median(paired byte difference)=-16. Process1 forward gives+16
versus+32. These statistics differ legitimately. The frozen acceptance deliberately
uses side medians; changing to paired medians now would change the experiment.
There is no auditor arithmetic defect and no post-hoc reclassification as PASS.

## BigFloat: localized additional source path

MA-R/candidate.jl first checks exact BigFloat vector/backend storage, dimensions and
n>=16. Only then it calls Base.MPFR.rounding_raw(BigFloat) and compares against the
global ROUNDING_MODE[]. The scoped control sets global RoundNearest while the
nested scoped value is RoundUp, so eligibility is false and the original routine
runs. The product=BigFloat() statement and all MA multiplication helpers are AFTER
the early return. Product scratch is therefore not created on this source path;
frozen instrumented correctness also checks fallback scratch behavior.

The extra source work relative to direct reference is one eligibility call and
one scoped rounding lookup per backend call. The installed path is:

1. mpfr.jl: rounding_raw uses @something(ScopedValues.get(CURRENT_ROUNDING_MODE),
   ROUNDING_MODE[]); the scoped value has no default.
2. scopedvalues.jl: successful lookup goes through ScopeStorage, a
   PersistentDict{AbstractScopedValue,Any}, and Base.KeyValue.get. The result is
   unwrapped/type-checked and rewrapped as Some{MPFRRoundingMode}.
3. dict.jl: KeyValue.get is @noinline and returns the one-element tuple(leaf.val,)
   on success; the value storage type is Any. Missing keys return nothing.
4. hamt.jl: read lookup calls path with copy=false. This lookup does not construct
   a replacement tree or duplicate its vectors. HashState/tuple values and the
   Some wrapper are source-level values; their emitted allocation behavior depends
   on compilation and cannot be inferred by counting constructor expressions.

The cost harness installs the scope OUTSIDE each timed window. Direct reference
BigFloat arithmetic itself also performs rounding lookups; candidate fallback adds
one lookup before executing the same arithmetic. Small BigFloat controls return
before rounding lookup and have zero deltas in210pairs. Float64 likewise returns
at the first type check and has zero deltas. The successful scoped lookup's Any
boundary, noinline return tuple and typed wrapper are plausible allocation sites,
and the invariant32bytes/2events per call is consistent with this added path.

This is a strong localization, not an exact heap-object attribution. The saved
records contain no lowered/typed/native code, escape analysis, allocation stack,
per-category counters or isolated rounding-lookup observation. They cannot prove
which two objects allocate, their individual sizes, or whether another compiled
boundary contributes. The normal precision scope is also active, so the relevant
difference is a PRESENT rounding key versus an absent rounding key, not an empty
scope versus a nonempty scope. No claim that scoped rounding itself is incorrect
or that every lookup universally allocates is made.

## Rational: different mechanism remains unresolved

Rational vectors fail the FIRST BigFloat type check. They do not read scoped
rounding, inspect factor dimensions, construct product scratch, or enter MA loops.
The original reference ldiv! is invoked with unchanged arguments. No source-level
extra rational multiply, subtraction, division, vector scan, conversion or copy
appears on this fallback path. This does not prove the compiler eliminates every
wrapper operation or that equal total events imply equal event categories.

Both measured sides use separately deepcopied bundles with equal numeric inputs,
not equal object addresses or native allocation histories. Each window resets
destination references equally, then executes four calls; factor/RHS token/owner
checks and serialization are outside windows and can affect later allocator/GC
history. @timed wraps the entire batch, including its common timing bookkeeping;
there are no saved per-operation allocations or category splits.

Installed timing.jl defines bytes as the delta of allocd+deferred_alloc+total_allocd,
and events as malloc+realloc+poolalloc+bigalloc. They are different aggregates.
Installed gmp.jl __init__ installs jl_gc_counted_malloc,
jl_gc_counted_realloc_with_old_size and jl_gc_counted_free_with_size; initialization
exceptions are caught, so source alone is not a capture of actual callback state.
Its Rational{BigInt} arithmetic constructs new BigInt numerator/denominator owners
and invokes GMP, on both reference and delegated candidate paths.

The already preserved, exact-binary-matched native instructions show successful
counted malloc charging allocator usable size, and counted realloc charging
nonnegative new usable size minus the supplied old size, with a separate event
increment. memory_block_usable_size branches to malloc_usable_size in this binary.
Thus identical aggregate event counts need not entail identical byte totals.
Different block usable sizes, request/reallocation histories or category mixtures
can produce byte variation without a change in total events. This is a concrete
accounting mechanism compatible with the observed two-sided rational fluctuations;
it is not evidence that a particular MA-S-2 pointer followed that mechanism.

Neither exact native requests/pointers nor old/new usable sizes nor callback
selection was saved. We cannot assign the observed16/32byte median differences
or larger outliers to allocator size classes, GC, wrapper compilation, arithmetic
or another specific source. In particular, the +18256pair without recorded GC
rules out an assertion that all large byte variation is caused by in-window GC.
Equal final exact outputs do not reveal all internal allocation trajectories.
The original no-increase gate still fails, irrespective of whether its statistical
strictness might merit a separately designed future experiment.

## Decision, work/memory and remaining evidence

Do not modify arithmetic or remove the rounding guard based on these results.
The guard is required because MA multiplication and original scoped rounding must
agree; caching it across arbitrary calls, substituting global mode alone, or changing
scope placement in timing would require a new equivalence and ownership contract.
Do not reinterpret native usable bytes as exact requested payload or live memory.
No candidate, driver, numerical plan, new measurement or production fix is created.

The useful next investigation target is the extra PRESENT scoped rounding lookup
and its call boundary. Exact heap attribution would need a separately admitted
bounded runtime observation or suitable already-captured compiled/allocation
provenance; none exists in the preserved MA-S-2 schema. Rational attribution needs
category/request/usable-size provenance, not another guess from unchanged events.
No such observation is performed or automatically authorized by this record.
The current source analysis is complete within the requested no-measurement scope.

No new production computation, allocation or retained memory was introduced.
Offline processing is linear in336stored pairs plus24read files; it adds no solver
scan, solve, conversion, cache or update-chain retention. There is one added rounding lookup per eligible-size check; its trie traversal
can depend on active scoped-value storage, not on matrix dimensions/nonzeros or
update-chain length. Its possible boxing cost is not measured separately. Rational
arithmetic/native allocation already scales with solve dimensions and precision
on both sides.
Source constructors are not allocation counts. The previously deferred duplicate
cold Python memory validation remains unchanged, with no new production cost.
No public/large/sparse-storage/solver-wide speedup, native-free or retention proof.

Current MA-S-2 result-review/execution-closure/execution-publication STATUS/roadmap
hashes map ONLY to MA-S-FALLBACK beforecopies via continuation-map.json (sixpairs).
Earlier numerical/preparation and LOAD/S mappings remain unchanged. All old raw,
false gates, scripts, candidates and reviews remain frozen. Master/source/test/user
environment/CI unchanged; HH reuse disabled, automation paused, broader plan OPEN.
