# S5-M independent prelaunch numerical, work and admission review

Admission verdict: NOT ACCEPTED in this revision. Critical: none. Important: one
(failure-evidence handling below). Minor: none. No numerical attempt is authorized
by this review. The candidate remains unexecuted. A preserved offline correction
and separate acceptance of the resulting artifact/pin identities are required.

## Important: auditor can fail before preserving its failed-gate result

`results/S5-M/audit.py:30` unconditionally reads `p['child']['pgid']`. The actual
`reproduce/guarded_run.py` sets `child = None` and writes `process.json` with
`reason = 'launch_error'` when Popen fails, without adding a `child` key. This
legitimate early failure reaches the auditor's missing-raw handling, but then
raises KeyError before exclusive `audit.json` creation. A failure opening its log
or resources file can similarly leave resources absent, which line 10 reads
unconditionally. Raw process/log evidence survives, but the promised failed audit
with the original failure reason is not produced.

The same boundary is incomplete for parseable malformed TOML: lines 14 and 18-23
assume checks/observations are tables. A raw `checks = 1` or string/array in place
of either table can raise TypeError or AttributeError rather than become a false
schema gate. Missing/deleted pinned files can likewise raise inside line 16's
hash generator. These paths fail closed; they do not create a false PASS. They
still violate this stage's explicit requirement to preserve early/malformed
failure evidence as failed gates without a post-attempt auditor repair.

Before launch, make these expected unavailable/malformed-evidence paths produce
an exclusive failed audit recording their original errors. An absent child must
remain failed process evidence, not a fabricated successful child identity; inspect
all known prior/runner groups and any actual recorded child group. Preserve the
original auditor and 744-entry manifest, bind the corrected auditor with a new
reviewed manifest, and verify the correction using bounded offline mock evidence.
Do not execute the candidate, old scripts or Julia to validate this correction.

## Independently verified identities and scope

I streamed every one of the 744 pinned files in 1 MiB chunks, reading
3,576,705,197 bytes. Every SHA-256 and resolved-path identity matched. Both complete
pinned src/test tree memberships matched, comprising 70 source and 441 test files.
There are 132 selected runtime paths and 101 other pinned paths. Manifest SHA-256:
`7e216b4963f1856b5059771c4d8246bde70d083c2441e2d154a76b643076abe6`.
All six protected user-file hashes independently match. Source/test/.github diff
against master is empty. HEAD is `f478c417df4cda482f64c13fbafbedf2846f9bae`;
master is `513c05388a82531e4d8fbcfb383e8897fad14ba2`.

The exact 181-line L candidate is
`b553d449a0db620bfae1970861806a778bbf45d36465026e8b4a540e4b4f4288`.
Independent text extraction finds exactly 40 unique predicate keys and 15 unique
observation keys, equal to schema.json. All three copied helpers match their
recorded current-test line blocks and hashes, and each occurs once in the candidate.
Both setup blocks exactly invert the recorded four-space indentation change.
No Julia parser was involved in these textual checks.

I read STATUS and the M plan, L candidate/provenance/evidence/closure and independent
review, K oracle review and preserved failed-first/separate successful closure
records, J ownership review, concrete M launcher/auditor/schema/command/prelaunch/
preparation/host records, and relevant current source. Historical 237 assertions
per failed CI run and 78/19 scoped coverage remain reused evidence; I did not
reconstruct or rerun their historical test executions. L and K closure predicates
remain recorded PASS, without replacing this admission review.

Fresh host inspection found no Julia and no member of prior groups
23249/23257/49081/49084/52772/52774/53479/53481. Boot identity is
`dade7243-9103-4398-bb45-fa28fbc0be72`; qualification-1 is absent. These are review-time
observations only. The separate fresh whole-group check immediately before any
accepted launch is still required; host-before alone is insufficient.

## Concrete launcher and loader boundary

The command invokes the actual cross-worktree outer wrapper, with existing
compiled modules, one Julia thread, GC 1,0, a 2G heap hint, explicit project and
exact frozen candidate/output. The outer wrapper resolves basis-update-chain-bench
as its root, reads the nested wrapper's depot export with sed, prepends memory-probe
and precompiled-full depots, then execs the installed aarch64 Julia 1.13.0 binary
with startup disabled. The nested wrapper is data, not an additional Julia launch.
Both wrapper layers, binary, selected installed native libraries, loading.jl,
CLI documentation and project environment identities are pinned.

The installed CLI documentation explicitly disallows new precompile files in
existing mode. `loading.jl:2752` guards ordinary automatic precompilation and
compilecache with `use_compiled_modules == 1`. Pkg automatic precompilation is
also disabled. This supports the scoped ordinary-loader admission. It does not
prove complete import/init work, actual module/cache selection or cache confinement.
In particular, the manifest names external packages such as OrderedCollections,
PrecompileTools and MathOptInterface, whose entire depot source/cache dependency
closure is not part of the 744-file inventory. The reviewed claims must remain
limited to the actual selected runtime/library and environment pins. No additional
pin is required to establish the unchanged project's selected numerical source
contract under this expressly limited admission; no complete dependency closure
claim is accepted.

The unchanged guard holds the global ownership lock, checks live Julia and full
pins/RAM before reserving an exclusive output directory, sets Julia/BLAS/OMP/MKL
thread controls, caps virtual memory at 8 GiB and uses the 2G heap hint. RAM/swap/
wall checks use the existing one-second sampling and 120-second child interval,
including imports/compilation. These are sampled resource enforcement, not a hard
instantaneous RAM/elapsed-time proof. It retains boot/start-ticks/command and
process outcome plus combined stdout/stderr and performs child-group cleanup.
No numerical input is passed; big/largo/AnyMOD hashes are exclusion metadata.

The launcher has no retry or second candidate call. Existing qualification-1
blocks reuse, and the guard creates it exclusively before spawning. Acceptance
must bind both the full pin-manifest digest and the actual review/artifacts;
the presently unresolved finding prevents that acceptance. No pins may change
while a run is active. The launcher and guard are reviewed as text, not executed.

## Numerical and observer semantics

Initialization copies the objective, appends zero slack costs, and concatenates
column/row bounds. The original one-by-one Float64 fixture and native policy
support the six entry-model checks and scope predicates; adaptive pricing/stalling
are enabled while phase_one/recovery/solve_refinement remain false. Recording
these prerequisites as acceptance predicates is sufficient for this exact pinned
fixture and source; it is not a general validator of arbitrary caller state.

The first latch requires a non-live candidate with `_StageObserver.live === LIVE`.
Auxiliary/nested candidates have a different root. `_candidate_workspace` resets
pending-factor/post-iteration flags; staged pricing_phase_reset is buffered while
refactor_other is forwarded. Only the first matched trial is retained, and duplicate
latches fail the oracle. The later throw requires the LIVE object and its adopted
trial factor, different from the saved entry factor. Source publication at
`dual_simplex.jl:2148-2153` invalidates checkpoints, copies state, clears history,
and adopts the factor before pending replay. This supports one selected
post-publication target conditionally, without proving future runtime reachability.

Ordinary diagnostics record the event before wrapping the sentinel once in
DiagnosticObserverFailure. Public make_dual_feasible! rethrows this nonnumerical
wrapper. Candidate checks use actual `isa` and direct `cause === sentinel`, with
schema strings providing additional outcome tokens rather than substituting for
identity. No syntax/import/type-string probe was made; a future mismatch fails.
The exact 40 predicates and 15 typed observations separately require one latch/hit,
work monotonicity and equality to throw time, the callback/event prefix, and the
selected publication/ownership contract. Exit0 alone cannot pass.

Nine live array owners are preserved by in-place copy, trial arrays remain distinct,
factor/refactor policy are adopted, and pricing is copied into its existing owner.
The 19 pricing fields, history clearing, checkpoint clearing and phase advancement
are consistent with source. Entry cost equality remains prospective: auxiliary
numerical repair may shift costs. Any false predicate or early failure must stop
qualification with original evidence, without tuning, retries or solver-defect
inference. No rollback, auxiliary certificate transfer or observer neutrality follows.

## Computational work and memory

No unnecessary NEW production work, allocation or retained memory was found:
production and tests are unchanged. No hot-path change warrants a before/after
benchmark. The callback adds constant identity/scalar metadata per notification,
without vector scans/copies, additional solves or a growing ledger. Setup adds
three copies of 3(m+n) total entries, six here. Post-unwind checks compare at most
m+8(m+n) publication pairs, 17 here, plus 3(m+n) entry pairs, six here, and 19
pricing fields. Owner checks may form up to 18 small nine-reference temporary
tuples in this cold path; this is not a measured allocation count.

The 20 selected reference roles do not bound retained graph memory: live/trial,
entry factor and history can retain scratch, sparse metadata and update-chain
storage. Scaling in dimensions, nonzeros, update history and wider scalar storage
remains unmeasured. Fixed 40/15 result maps and serialization are cold bounded
metadata work. Full pin hashing is separate offline/guard identity work, streamed
with bounded hash buffers; it is not solver kernel work or complete PREforward/
backend/import accounting. No speedup, full-suite, x64 or broader precision claim
is justified. Numerical safeguards, coefficients, tolerances and precision remain
unchanged.

Only this new review file was written. No Julia, candidate, launcher, auditor,
old script, syntax/import probe, package operation or numerical test was executed.
