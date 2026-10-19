from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER'
def put(n,s):
 with (D/n).open('x') as f:f.write(s)
put('prepare-docs.py',Path(__file__).read_text())
put('ADMISSION.md','''# BG specialization Task2 — preparation only

No Julia query/parser/import/compile/numerics, seal, reservation or runtime output
is produced here. Candidate Task1 and every historical artifact stay frozen.
No production/test/env/CI/master/STATUS/roadmap changes. This package is not a
numerical admission. Its copied protocols are new files, not reruns of old mains.

## Sources, phases and exact results

Both phases use the same accepted83-file Task1 ordinary stage containing packed
DIRECT BG, old workspace `_bgx_` and specialized `_bgxs_`. The reference dispatch
is unchanged. RED loads red-kernel.jl; GREEN loads green-kernel.jl and four accepted
Task1 test modules in their manifest order. All includes occur at top level before
main; no eval/invokelatest/method overwrite. Phase changes only the kernel's one
candidate factory namespace and whether the complete structural suite executes.
No Julia syntax or runtime acceptance is claimed by source checks.

RED has exactly3 allocation-nonincrease assertions, one each for native sparse32,
dense32,sparse96. Expected3 failures/exit1; correctness, inputs, modes, measured
compile/recompile zero, loaded paths and every exact residual must pass. There are
no manufactured missing-symbol/math failures. GREEN requires8640 passes/exit0:
8637 structural leaves (14 groups) plus3 allocation predicates. Per-group counts
are source-derived in assertion-inventory.md and exact JSON/TOML. No post-output
count adjustment is allowed. The auditor independently recomputes the allocation
predicates, exact binary64 residuals and paired output/mode equality from all60
raw windows, not just the Julia boolean or exit code.

## Measurement and RED expectation

Three unchanged fixtures from the full old cost input files; native threshold_one,
Float64/Int; no Markowitz cost cell here (both backends remain in correctness tests).
Each cell:3warm+7observed alternating pairs, candidate-first even pairs;20windows.
Each whole lifecycle constructs1factor, performs8updates,16FTRAN/8BTRAN and refactors
after4/8. Six clocks are construct/FTRAN/BTRAN/update/refactor1/refactor2; nested
subsets are not added to the total. No hidden warmup, preflight factorization,
profiler/IR query or probe clone. All setup inside lifecycle remains timed.

The exact old lifecycle and window bodies are retained (only an unused save helper
rename and the GREEN factory symbol differ). Both sides allocate output destinations
outside the window, return the complete factor/clocks/modes, inspect the complete
factor graph and all24numeric outputs, then serialize detached tokens outside timing.
The new paired dictionary holds both serialized result records identically, never
factor owners. No side-specific return holder, artificial factor escape or annotation
is introduced. Arrays for medians/sorting, Test results, graphs, residual checks and
serialization are outside measured windows and remain process overhead.

Symmetric SOURCE/capture does not prove symmetric compiled materialization.
Historical profile found2reference-only inner return tuples and14reference-only
outer timer-result allocations, the latter OUTSIDE the lifecycle's GC delta.
Neither is asserted eliminated. Every reported number remains a whole-lifecycle
measurement with its inner harness; it is not a standalone export/import allocation
count, native allocation/free ledger or proof that a particular boxed site vanished.
No scalar replacement success is inferred from source specialization.

Prior native event medians1274->1279,1282->1291,2513->2514 support three expected
failures as a regression hypothesis under the preserved lifecycle, not a guarantee
for the new83-file load/compiler context. Fresh preparation review MUST explicitly
judge this concrete expectation support. control.preparation refuses launch unless
review.json has red_expectation_supported=true. If the reviewer cannot support it,
stop before numerical admission and publish that decision; do not tune fixture/gate
or force allocations to manufacture RED. Unexpected RED outcomes remain failure.

Each predicate is median(events_candidate)<=median(events_reference) AND the same
for bytes, using7observed samples. Preserve all warm/measured time/bytes/events/GC/
compile/recompile/nested times/graph/modes/outputs. Time and graph are descriptive
here, not waived Task3 gates. GREEN predicate failure stops this fixed candidate:
no full cost qualification, annotation tuning, or automatic promotion.

## Future launch and immutable admission

Use separately selected red300, then green300 only after exact accepted RED result.
The seal binds actual head/master/boot, stage, source/runtime, tests, expected counts,
wrapper/guard chain, inputs, reviewed preparation and predecessor evidence. Review
scope is `BG specialization exact-stage admission`, exact phase, accepted=true,
findings=[], pins_sha256 of sealed.json and sha256 map of all sealed files + seal.
No preparation review is a substitute for that future fresh independent review.

Fresh full256 prior groups AND sessions plus every later runner/child/supervisor
PGID and SID; identity boot/start_ticks/command, comm/argv0/readable executable.
Inaccessible executable links remain disclosed visibility limits; unreadable
stat/comm/argv0 identities fail closed. Recheck local/remote master, diagnostic
ancestor/clean tracked tree, exact runtime/environment/actual wrapper chain and
no recognizable Julia before sealing and again launching. All membership/hashes
are checked; no baseline regeneration, retroactive launch pins or old-host reuse.

Initial300outer/292inner seconds; Julia/BLAS1, heap hint2GiB, VM8GiB,
availableRAM>=6GiB/swap<=1GiB; compiled-modules=existing, auto-precompile off.
No multi-hour run. Exclusive reservation prevents repeats. Preserve raw/logs on
all failures. Only verified pure timeout permits new600/592 admission with identical
source/options; never automatic retry or retry for warning/error/resource failure.
Partial windows must form a contiguous prefix and independently pass their exact
schema/residual/bit gates; truncated TOML is not classified as pure timeout.
Warning/world-age anywhere in Julia or launcher logs rejects both success and retry.

Independent result review and separate closure/publication are mandatory after
any run. No output or reservation exists at this preparation boundary.
''')
put('WORK-MEMORY.md','''# Task2 full scope of work and memory

## Measured part per process (RED and GREEN identical)

3fixtures, each decoded once;9CSC matrices+8step triples per fixture from unchanged
input tokens. No generated LP.60 lifecycle windows:18warm42observed.60constructors,
120refactors,480updates,960explicitFTRAN480explicitBTRAN =1440solve entries.
180factorization/export build routes; at most180native orientation solves from
reached nonunit exports, not an instrumented total. Original update/base/triangular
work remains additional; counts are API entries, not complete PREforward backend
operations. No factor copy, separate policy setup, probe, Profile.Allocs or IR call.

Each lifecycle retains its returned finalfactor through full Base.summarysize and
24outside-window residual checks. Peak includes old+new factor during refactor,
backend/rawCSC/extraction/import, old workspace/new workspace, histories/prepared
outputs and garbage; released references do not prove native freeing. Reference
and candidate retain factor/clocks/modes through identical source boundaries.
Return tuple/compiler escape differences remain included where in-window.

24 output vectors per fixture (30720bytes cumulative scalar payload for32+32+96),
reused across all20windows/cell.60 new six-UInt64 clock arrays,2880bytes cumulative
payload, inside windows. Each serialized window24vectors;76800Float64 tokens total
across60windows (614400bytes before hex/string/dict/TOML overhead). At most two
result dictionaries retained per pair, with detached tokens rather than factor
owners. Four seven-element observed-metric lists per cell and sorting copies are
outside windows. Every warm and observed output is checked;1440 exact residuals
are recomputed by Python auditor and1440 preliminary residuals by Julia outside
timing. Exact arithmetic matrix/vector work is diagnostic overhead.

## Additional GREEN structural work — not hidden in windows

The original three suites execute once with exact namespace inverse and corrected
GREEN2 import source. Fourteen original genuine export fixtures (7*2backends),
28candidate/reference exports,6native source lu! ownership-witness attempts and
6Markowitz source mutations. Synthetic validation/import/normalization/orientation
and every allocation failure prefix stay in their existing cold tests. Original
ASSERTION-INVENTORY and WORK-MEMORY, composition-ledger and work-memory-ledger are
bound as full supporting inventories, including source-site loops; no suite rerun
is concealed as warmup. Per-group work follows these bounded schedules:

- repeated:28pairs/56managers,24nonempty*8=192steps,384updates,96refactors,
  2984valid explicit solve entries; rejected alias/dimension/dispatch calls additional.
- private failure:2active n8 setups/update/copy; six cold seam failures each, one
  wrong-type inner each, one cold successful allocator census each; native25 and
  Markowitz21 individual prefix failures.5synthetic scratch failures, one recursive
  refactor/copy rejection and one successful publication each. Two warm64 witnesses
  add4manager setups,4refactor attempts,4updates,2copies,34explicit solves, in addition
  to4active-pair FTRAN. Prefixes stop at their injected failure; they do not all do
  full import/inner build. Recursion fails before a second factorization.
- copy divergence:2active setups/update/copy plus4reference constructors,4refactors,
  4active-pair FTRAN+36paired solves. Synthetic cache attachment/poison is cold.
- dimensions:4initial empty setups,24reference shape constructors/24refactors;
  each arm/mode additionally3candidate refactors,2reference constructors and one
  reference fallback refactor,one copy;9paired_solutions calls per combination,
  216explicit solves. One separate synthetic-export setup/refactor+reference import.
- Workspace/import synthetic helpers and exact-rational export identity checks
  are bounded by the preserved source loops and original assertion inventory;
  their allocator-request counts are not GC allocation-event measurements.

New boundary tests:12checked_orientation cases,20successful importer comparisons
plus134allocation-failure imports,24hook cases,24build_pair calls plus8rejection
imports. Total92real factorize API entries,24refactor attempts,246importer entries,
96explicit factor solves (48F48B),8synthetic orientation solves. At most44genuine
native orientation solves, not an observed count. No newupdates orfactorcopies.
The hook cases are24initial setups+20reached refactor factorizations;40exports,
36imports,32inner initializers. build_pair adds48builds/imports. Rejected factory
prefixes/requests and incomplete paths are preserved rather than treated as fullwork.

New test-only218Requests objects each with256(T,n)slots;24five-slotHookLogs. These
are cumulative source counts, not simultaneous peak or measured allocations. Graph
snapshots/retained owner tuples/input copies/exact-rational oracle storage scale
with n+nnz+updatechain+cache, plus Julia headers/capacities/IdDict/backtraces. Existing
scratch64 matrices, two factor graphs and saved copies can coexist. No callback
snapshot or extra instrumentation enters implementation or timed lifecycle. Test
recorder retains14structural+3allocation child summaries and failure text, not8640
Pass objects. No claim of a physical native-memory cap from these source counts.

## Candidate work reviewed

Task1 source inverse proves no additional algorithmic scan/solve/copy/conversion/
array request/retained field, only parametric call boundaries and selected inline
facades/import core. Unchanged scratchcharge512+8cld(n,64)+optional32n is bounded
by min(1MiB,(16(l+u)+8(n+1))div16); charge is not graphbytes. Full original factor
capacity/history/old+new/GC/native coexistence remains. Specialization can add cold
compilation/code-size cost; process duration and warm compile samples expose it,
while observed windows require compile/recompile zero. No performance acceptance
until execution, no production code change or integration here.
''')
# Explicit RED expectation review binding, mandatory before seal.
p=D/'control.py';s=p.read_text().replace("v=D/'review.json';verify_review", "v=D/'review.json';require(rd(v).get('red_expectation_supported') is True,'Three RED expectations not independently supported');verify_review");p.write_text(s)
put('task-ledger.md','''# Task2 preparation ledger

Plan: docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md.
Base:b504ea4fbf3bc40a9fa87cfc0b9a7dd69cc821cd. Task1 frozen/complete.
Inline executing-plans workflow; user explicitly requires no Julia. New Python
synthetic tests are permitted; Julia RED/GREEN remain future admitted execution.
No worktree cleanup, old checker rerun, source/test/env/master/CI changes.
Ruling: use exact original timed lifecycle/window, with symmetric source capture,
and retain explicit compiler/harness attribution limits; do not force artificial
escape to manufacture a RED failure. Independent reviewer must accept this concrete
hypothesis or block launch. Wrong expectation costs one bounded failed regression,
never permission to retune after output.
''')
print('Task2 admission and full work/memory scope written; no launch.')
