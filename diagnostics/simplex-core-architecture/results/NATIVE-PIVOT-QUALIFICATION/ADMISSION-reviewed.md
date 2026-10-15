# Native pivot policy: offline Task2 driver and stage controls

Prepared only. NO Julia/query/parser/import/compile/numerics, no staged checkout,
no sealed manifest, no numerical admission, no reservation and no output exists.
The accepted Task1 candidate and original plan/spec are frozen. Production,
master, actual tests/environment/CI and direct prototypes remain unchanged.

## Exact future stages

| Stage | Project arm | Inclusive cap | Expected child exit | Predecessor |
| --- | --- | --- | --- | --- |
| red | unchanged reference73 files | 30s | 1, exactly4 named missing-interface failures | accepted offline preparation |
| green | exact Task1 candidate75 files | 60s | 0, all6858 assertions | exact RED audit and independent result acceptance |
| cost | separate copy of exact candidate75 files | 45s | 0, all88 windows and selected-policy residuals | exact GREEN audit and independent result acceptance |

`control_reviewed.config(phase)` fixes the literal wrapper, arguments, stage and output.
`seal-reviewed.py PHASE` creates one write-once stage and immutable manifest; it executes
no Julia. The future stage reviewer must inspect all exact files/stage/host and
create `runs/PHASE/admission.json` with accepted=true, findings=[], phase,
scope="exact-stage admission", pins_sha256=SHA256(sealed.json), and EXACT sha256
membership sealed.files plus sealed.json. No script fabricates this approval.
`launch-reviewed.py PHASE` consumes that review, checks hashes/refs/boot/full groups and
sessions/noJulia anew, reserves once, then supervises exactly one child. It does
not seal, approve, retry or advance to another stage. Failure preserves all data.

Offline review has scope="offline preparation", exact membership from
preparation-pins-reviewed.json plus that manifest, and its pins_sha256. Result review has
scope="stage result", phase, exact audit.sha256 membership plus audit.json and
pins_sha256=SHA256(audit.json). Thus a preparation review never grants a launch,
and an earlier numerical permission never bypasses a failed predecessor.
Standing short-run human permission remains valid; no repeated permission ask.

Guard/supervisor are new copies of the accepted accuracy preparation, never
imports/reruns of historical executables. Guard's only policy delta is explicit
expected-exit 0/1 (including terminal memory check); reason/child exit stay raw.
Guard budget is inclusive cap minus8s; supervisor sends TERM at cap minus6s,
KILL at cap minus2s and requires reaping by cap. The outer elapsed predicate
includes launch, import, output and termination. Actual pidfd ownership checks
use boot/start_ticks/command and both PGID/SID. RAM>=6GiB, swap<=1GiB,
RLIMIT_AS8GiB, heap hint2GiB, Julia/BLAS1, global lock and no extra Julia child.
One incomplete reservation/output is never reused. No large LP/full suite.

## Loading

Ordinary package overlay, not a nested module or global method overwrite.
The wrapper chain and exact Julia1.13.0 executable/libs/source are freshly
read-time pinned in runtime-pins.json. `--compiled-modules=existing` permits
ordinary source fallback, forbids creation of fresh compilecache workers; it
is NOT a cache-confinement, import-work or hidden-loader proof. Startup is off,
auto-precompile off, offline package mode. Source LocalPreferences disables
JSimplex precompile_workload. Both drivers check PrecompileTools.verbose before
loading JSimplex. Path checks require the exact stage src/JSimplex.jl and pinned
stdlib paths. Existing loaded dependency initialization/import work remains
inside the inclusive limit and outside component call counts.

## GREEN and RED instrumentation

All Task1 test bodies/loops/assertions and five unchanged neighbor testsets are
preserved through a byte-exact inverse. The neighbor manifest identifies exact
file/character slices, not presumed execution from file pins. Diagnostic wrappers
count PRE-forward attempts, including throws, and record selected factor/control
owner transitions. No JSimplex method is overwritten. Test-only observations
can affect cold compilation/cost; GREEN is not a benchmark. Test recording retains
counts and only failure strings; all raw data is written before final exit.
An early import/syntax failure can prevent raw output: the launcher/guard log,
reservation and process record then fail closed. No missing-output repair run.

RED selects only the four original missing markers; selected body contains zero
factor/native/solver calls. Import is additional work, not claimed zero native
initialization. Its expected exit1 is not a solver defect or historical CI replay.

## Cost

Four exact saved B4 fixtures and entering/DSE/unit RHS, unchanged bits from
NATIVE-ACCURACY-PREPARATION. Each fixture has3warm+8measured rounds, C/P order
alternates per round:88windows. Each window constructs one managed native
backend, fresh/no-spare refactor, then private-spare lu!, then16triplets.
88constructions+176refactors+2816F/DSE+1408B=4224solves. Source-derived native
entries:176fresh LU+88lu!, not a complete native-internal operation trace.
No public solve, extra calibration, factor copy, update or explicit GC.

Five timers: construction, fresh refactor, spare refactor,48solve region and
enclosing total. Total is a superset and includes timer/constant identity-check
bookkeeping; do not add nested timers. Controls, CSC handling, workspace and
private candidate allocation remain inside their production region. Diagnostic
output/Info buffers are allocated equally before all windows. Four native Info
scalar stores per solve plus pre-forward scalar counters occur inside solve
regions in both arms; no vector scan/copy or independent solve is added there.
All48outputs/window, all solve Info, all times/bytes/events/compile/recompile/GC
and actual control/strategy are retained;8last-round fill/graph snapshots are
outside timers. Every measured compile/recompile field must be zero; GC and
outliers are never discarded. No numerical retry or extra warmup.

Exact offline residual bound is unchanged:
128*n*2^-52*max(1,norm(M,Inf)*norm(x,Inf),norm(b,Inf)). Every P residual must pass;
C sparse96 false remains data. Every C output is compared with all11saved C
windows for its fixture. A mismatch remains visible and needs explanation in
result review; it never triggers retry. Eight paired time ratios and
median/MAD/range plus every byte/event sample are reported for all five regions.
This compares policies within one candidate, not overhead against an old binary.
AUTO may choose SYMMETRIC: threshold-one is not universal full partial pivoting.
Legitimate accuracy-induced fill is disclosed rather than rejected by a speedup
threshold. GC counters/graph/native Info/RSS are distinct, not a native free ledger.

Task3 public/recovery integration and the later direct adapter remain separate.
Old direct cost1 FAILED/CONSUMED, cost2 BLOCKED; CIoff, HHreuse disabled,
automation paused. No production promotion follows from this preparation.
