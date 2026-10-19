# Blocked BG U — separate ordinary-stage repair

Offline preparation only. The new stage uses all source files and Project.toml
from verified local and remote master26e2291745999f485a74f643298ca997d65c7205.
No Julia parser, package load, compilation, numerical test or measurement ran.
The original failed RED, original stage, all candidate/test bytes and original
harness remain frozen. This repair does not accept RED or admit a new run.

## Cause and scope

RED300 at diagnostic e7726ed23d26d5cc0739eb5978f3cb1347824ce9 failed at ordinary
module loading because its diagnostic-source baseline lacked _NativePivotPolicy.
The adapter required that API. It executed zero assertions, not the six expected
N026 failures. See DIRECT-BG-BLOCKED-UPDATE-RED/REPORT.md and result-review.md.

The new ignored ordinary overlay is
`.superpowers/sdd/2026-10-19-direct-bg-blocked-update/task2-master-stage`.
`build.py` reads committed Git blobs at the exact master SHA, not mutable source
files or a moving branch. It requires a fresh destination, current matching
master/remote refs and a byte-identical dependency Project. No enum shim, partial
source patch, private package clone, new dependency or production method
replacement is added. This is a standalone staging artifact; the old control.py
still points at the failed stage and must not be used to run this repair.

The 75 files occupy 1,010,881 source bytes on disk. All 70 master source files
plus Project.toml are copied; two original ordinary export/direct adapter files
are added. Manifest.toml and LocalPreferences.toml are copied byte-identically
from the old stage. JSimplex.jl has exactly the same final two include insertions
as before; deleting them recovers the committed master root byte-for-byte.
Environment/version/package resolution is unchanged, not newly executed/proven.
The old stage remains a separate preserved directory.

## Complete seven-file reconciliation

| Master change relative to diagnostic source | Purpose and relevance |
| --- | --- |
| factorization.jl | Enum, native policy-aware three-argument factory and controls; explicit Markowitz rejection; retain policy on copy and refactor; option dispatch. Supplies the adapter's missing API. |
| triangular_factorization.jl | Three manager constructors accept/forward policy. Struct layouts and the entire update/solve/copy tail are byte-identical outside that constructor region. |
| options.jl | Native policy field, validation, old positional compatibility and precision conversion propagation. Whole master file preserved. |
| lp_refinement_driver.jl | Propagate policy into auxiliary options. Whole master file preserved; no new auxiliary solve is requested. |
| simplex_phase_one.jl | Propagate policy into phase options. |
| simplex_precision.jl | Preserve policy through precision-option copying. |
| solver.jl | Preserve policy in remaining-budget options. |

All seven verbatim unified diffs are saved under `diffs/`; their whitespace-only
context lines are source-fidelity artifacts. No other staged file differs from
the failed stage. This restores the already accepted native threshold_one /
Markowitz default policy contract; it does not introduce a new pivot policy.
No tolerance, precision, fixture, fallback, arithmetic or numerical oracle was
changed. No historical result is reinterpreted as a run on the new baseline.

## Source interface and preservation evidence

`stage.json` records exact committed Git blobs, source SHA256 values, full new
stage membership, ordinary adapter hashes, unchanged environment and old/new
file mapping. `dependency-map.json` traverses all72 source includes in order,
including seven nested mps/moi sources, and lists declaration candidates for66
required symbols from candidate/tests and the ordinary adapters.

Review must inspect the real definitions and signatures, not infer compatible
method dispatch from token presence. The enum/native and Markowitz factories,
UMFPACK ownership/policy lifecycle, direct lower backend, export helpers,
manager constructors, prepared-RHS, refactor/copy and numerical-test consumers
are part of this boundary. Unchanged Markowitz/HH extraction, triangular index,
row/spike/incidence and update source bodies are hash-compared. The exact
original scalar suffix remains present in master and the unchanged candidate.
The full candidate directory (14 files) and six original harness driver/recorder/
oracle/test files retain their accepted bindings. All assertions,13 fixtures,
28 units and six expected N026 cells remain unchanged prospective requirements.

The source contract was tested first against the old stage: six missing API
conditions were observed. This is an offline source test, NOT the six numerical
RED failures. The new stage passes all8 contract conditions. Final reconciliation
passes176 checks. These results do not establish Julia syntax, loading, world
age, method ambiguity, numerical behavior or full runtime dependency closure.

Two failed new verification scripts remain preserved. `verify.py` incorrectly
compared72 include paths with65 top-level filenames; `verify-2.py` corrected
recursive membership but its declaration selector missed `<:` in UpperRowIndices.
`contract_complete.py` and `verify-3.py` correct the selectors without changing
any stage/candidate/test bytes. The successful artifact is verification.json.
Old exclusive scripts/auditors were not rerun. Recorded source checks never
constitute retrospective launch pins.

## Computational work and memory

No production code change or new run-time wrapper/check was introduced. No new
full-vector/matrix scan, basis solve, numeric conversion, factor copy or update
history is added relative to the accepted master plus original ordinary adapter.
The policy-aware setup/copy/refactor behavior is existing master behavior; native
threshold_one prepares its existing UMFPACK control vector per fresh native LU.
Direct refactor still creates one ordinary factor/export; fallback/ownership are
unchanged. These are source facts, not measured allocation counts. Differences
from the old unloadable stage cannot yield a meaningful measured cost comparison.

The new preparation adds75 disk files (~0.96MiB logical contents); it does not
load both old and new modules into one process. Offline copying/hashing scales
with source bytes and static checks with source/symbol count. Diagnostic exact
rational correctness work (potential O(n^3) and BigInt bit growth), cold compiler
work, candidate scratch72n+16*cld(9n,64)+256+4096 and existing packed/native/history
memory remain governed by the original plan; no new cost claim follows here.
No unnecessary new production computation/allocation/retained-memory cost is
expected from this staging-only repair. Independent review must verify that
statement explicitly. All runtime/performance acceptance remains false.

## Next separately reviewed boundary

Prepare a NEW harness/control/admission package referring to this stage and its
master baseline. Do not edit or reuse the frozen red300 reservation/output or
mutate old stages.json, loaded-paths.json, baseline.json, source maps or pins.
Preserve original source-map hashes as historical diagnostic baselines; use this
reconciliation to bind the new baseline. The unchanged driver/test/oracle text
may be copied with explicit exact path substitutions if needed; validate its
stage path, dependency loaded paths, expected counts and complete inventory.

Keep top-level loading before main, native threshold_one and Markowitz default,
all28 units, exact six expected N026 failures, original-B/factor-relation checks,
raw-prefix failures, work/memory guards and world-age warning rejection. A fresh
host preflight must cover271 prior groups AND sessions plus any newer identities.
Future numerical admission must pin fresh source/runtime/command, independent
exact-run acceptance and a fresh one-attempt output path. Initial300-second
limit, Julia/BLAS1, heap2GiB, VM8GiB, availableRAM6GiB and swap1GiB remain the
existing prospective constraints. No outer/seal/reservation/driver launch is
created here. GREEN remains conditional on independently accepted new RED.

Original master/src/test/environment/CI/global STATUS/roadmap are unchanged;
HH reuse disabled, automation paused, broader plan open. Preserve the plan's
workspace and all original failure evidence (overrides generic skill cleanup).
