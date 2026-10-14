# Per-pass Float64 exact coefficient cache: bounded experiment

Human request: test the second performance hypothesis (repeated exact conversions
in Float64 presolve). Standing short-run authorization applies. This is a new
experiment, not a rerun of any MA or HH qualification. No production integration.

## Candidate and ownership

Append one Float64 specialization of reduce_dependent_rows to an ordinary
separate source overlay. Preserve the generic method byte-for-byte. Exact inverse
has three changes: signature, local Dict{Float64,ExactValue} AFTER the existing
size/nnz gate, and get! at coefficient conversion. No new preliminary scan.
One hash lookup per reached nonzero; one exact conversion per distinct reached
value. Cache retained until return: O(u) table entries and rational owners, u <=
10000. A matrix-wide distinct count in diagnostics is only an upper bound when
elimination stops early. No complete backend work or measured conversion-count
claim. All elimination, work cap, bound conversion, certificate tests, tolerances,
exceptions from arithmetic and iteration order stay intact. Tiny/unique-value
cases may regress; measure and report, no adaptive tuning in this experiment.

Cached Rational{BigInt} values are internal to this call and may share leaves.
_subtract_scaled!, normalization and implied intervals use nonmutating arithmetic
and dictionary replacement/deletion. No local exact pivot/proof/cache is returned.
Float64 inputs have no mutable scalar leaves. Other scalar types use the original
method. This is narrower than the stopped Rational primal ownership optimization.
Cache creation, growth and retention are inside the measured call. Allocation
counters are Julia aggregate GC traffic, possibly including native allocations;
not live/native retained-memory or free accounting.

## Fixed work and inputs

Four serial ordinary package processes, ABBA: reference, candidate, candidate,
reference. One sequence, no retries or tuning. At most 84 seconds each inclusive
of guard setup, 90 with cleanup; at most 360 cumulative seconds. Single Julia /
BLAS thread, 2 GiB heap hint, 8 GiB VM, >=6 GiB available RAM, <=1 GiB swap.
Use copied accepted guard and supervisor, compiled-modules=existing, offline Pkg,
auto-precompile disabled, unchanged LocalPreferences (workload false). No cache
confinement or complete import-work claim. Stop on first process/check failure.

Each process: 12 independent-oracle cases (four scalar types x removable,
necessary, inconsistent), four signed-zero/extreme/cutoff cases, two nonfinite
mutated-input behavior comparisons. Each normal case calls reference, candidate
and selected public pass (48 calls); exceptional cases call both (4 calls).
Value snapshots and mutable input owners must remain unchanged.

Eight component cost cases: the four existing small LPs in cases.toml plus
sparse24/dense16 with repeated/unique dyadic coefficients as fixed in driver.
Each has one reference baseline plus 10 alternating pairs (3 warm, 7 measured),
4 complete pass calls per window: 648 calls/process. Both algorithms live in a
private module through exact renamed function copies; imported helpers unchanged.
The 4-result tuple is identical diagnostic overhead inside both timed windows.
No callback instrumentation; full result tokens/owner checks outside windows.

Four whole public solves: afiro, adlittle, sc50a, primal-chain130. Existing options
except fixed algorithm / 10-second call limit / 2000 iterations, no tolerance,
precision, safeguard or presolve changes. Each has 1 cold + 3 warm + 7 measured
calls = 44 solves/process. Expected objectives from existing fixtures. Exact
status/objective/primal/iteration/refactor/message signatures must agree within
and between processes. Timing statistics excluded from equality. No extra solve
for validation. Total maximum: 2800 component calls + 176 public solves across
four processes. Setup/parser/import outside warm measurements, separately shown.

## Gates and interpretation fixed before running

66 named driver checks/process, 8 component files x20 windows, 4 solve files x10
windows plus cold entries. All measured compilation/recompilation zero; all GC
samples retained. Exact outputs and input preservation mandatory. Hash all actual
sources, overlays, runtime dependencies, driver, launcher, auditors and controls;
verify actual loaded package/method route and module source membership. Fresh
host boot/start_ticks/command/full176groups OR sessions/noJulia and refs before
launch, full new groups after each process. Independently review concrete inputs
and cost/ownership before launch; review results afterward. Preserve all failures.

Exploratory candidate merits further integration work only if both ABBA blocks
(C2/R1 and C3/R4) show >=5% whole-solve median improvement on at least two of the
four LPs, no LP >5% slower in either block, and lower median bytes and events on
those improved LPs in both blocks. Component no-regression guard: no case median
paired-time ratio >1.10 in any process, and no case median bytes/events >10% above
reference in any process. Report ratios, dispersion/range, all cases, and cold
load cost. These are screening gates, not statistical or universal speedup proof.
Failure closes this exact candidate; do not tune or open another variant here.
No CI, full-suite run, master/production/test/env edit, or old evidence rerun.
