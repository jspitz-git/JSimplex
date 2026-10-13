# S5-Z independent offline numerical/work/memory review

Verdict: REJECTED

Critical: none.
Important: I1 (missing top-level SingularException binding).
Minor: M1 (incorrect location of preserved historical assertions).
Unresolved findings: [I1, M1]

I1 — The appended probe is not self-contained in the scope where it is defined.
`candidate.jl:120` declares `sentinel::SingularException` and line139 constructs
`SingularException(42)`, but the prefix's only LinearAlgebra import is inside
`module CrashLoggerTests` at lines61–62; that module ends at line90. It does not
import SingularException into the surrounding module. JSimplex does not export
that name. X had an explicit top-level LinearAlgebra import, removed in this
conversion. Consequently an isolated inclusion with the candidate's declared
imports cannot define the new probe; a previous whole-suite include could mask
the dependency. This is a source-scope finding, not a Julia failure reproduction.
The report's lines23–25 and author `independent.py:13` substring predicate
`native_import_already_available` incorrectly treat a nested module's import as
available to the append. Preserve this candidate/check/report as rejected evidence;
prepare a separately identified correction that supplies the dependency in the
correct scope while retaining the full prefix, exact numerical core and50 predicates.
Do not consume a Julia attempt to diagnose or fix this offline issue. A future
focused launcher importing LinearAlgebra would mask rather than repair the
permanent candidate's undeclared dependency unless that dependency is explicitly
part of the reviewed permanent test contract.

M1 — Report lines6–8 say the4774-byte preserved start-state file includes the old
six final-stop, ten pivot-stop and six observer-cause assertions. Only the six
final-stop assertions are there. The ten pivot-stop evaluations (five assertions
across two algorithms) and six observer-cause evaluations (two assertions across
three events) are in `test/simplex_start_guard_tests.jl:19` and `:44`. Both actual
files remain unchanged; this is an evidence-description error, not lost coverage.
The corrected report must distinguish the byte-exact candidate prefix from the
separately preserved guard tests. Do not rewrite frozen historical artifacts.

## Actual independent verification

Read the Z preparation plan/report, next integration plan, current STATUS/roadmap,
Z candidate/append/original/inverse/predicates/three construction sources and both
failure records, entry/inventory/author source and results, Y acceptance reviews,
audit and raw result, and actual factory, crash, reconstruction, diagnostic,
exception-class, numerical-policy and option source. Historical scripts were read
as text only: none was run, imported or rewritten. Newly supplied continuation,
closure and publication scripts were also read as text only; their future PASS
and publication outcomes are not established by this review.

New standalone read-only Python checks independently streamed and matched:

- All1398 Z read-time hashes and all8 author bindings; literal entry24/source19/
  author10 result schemas. Passing Boolean artifacts do not cure I1's faulty scope
  assumption.
- Y1347 launch and1344 admission hashes and resolved paths, required338 membership
  and hashes, closure51 and post8 bindings, audit23/post11/closure17/publication6
  literal schemas, raw6 original/portable identities and invocation3 bindings.
  Parsed raw TOML equals the audit's raw object and contains50 literal true checks.
- All53 exact Y published paths:52 manifest entries plus the manifest itself;
  working bytes, committed blobs and commit path set match2850c7e.
- X213 evidence, author10 and closure23; Wclosure21; U master1512, GREEN1489 and
  T891. Y inventories alone map continuation to Y/before-Y; Xclosure uses that same
  before-Y mapping; Wclosure uses X/before-X. U/T use before-U continuation and
  only the matching old precision-test hash maps to U/original-test.jl. No historical
  pin changed. Six user-file hashes match.1692 distinct paths were streamed in the
  combined hash check.
- Candidate SHA256
  `97b91463d0b793cfe8650c26452a1dc736fbdf95d72966d5130163d19d366be9`;
  exact4774-byte actual-test prefix plus191-line append; complete helper/core inverse
  with only the three declared renames; ordered bijection of50 unique predicates
  and50 explicit assertions. X construction inverse equals W's original testset,
  still present in the actual test.

Independently reproduced only the Python text-selection counts:0 without MULTILINE,
52 with it across the unscoped core (returned/caught plus50 checks),50 when scoped
to the tuple. Both preserved failures precede candidate writes in their sources.
The inaccurate `original53_includes_nontuple` key is explicitly explained by the
report and authoritative52-name record; it was not silently rewritten. Four missing
coverage markers remain structural evidence, not a failing Julia/CI reproduction.

Fresh host reads found HEAD2850c7e92973fbb36001a28ca78cbde895118ac3 and
master2b546e946ddb7fdb6c0092df9cc19f566e301aa2, no src/test/.github/Project difference
against master, all22 historical process groups/sessions absent, and no Julia
process in the process listing or /proc comm scan. Boot remains
dade7243-9103-4398-bb45-fa28fbc0be72. No network/remote query was made by this offline
review; the stored remote observation was read as historical evidence only.

## Numerical semantics and limits

Apart from I1's missing surrounding binding, the selected numerical code is unchanged.
Storage precedes INITIAL setup; arming follows entry capture. One prospective
Float64 PFI/native initialization and one crash call preserve the original done Ref,
stop callback, default options/tolerances, Inf, interval20 and offsets. Native
refinement/recovery and kernel_timing remain false; refactor_timing defaults true.
No additional fixture, matrix arithmetic, warmup, loop, solve or certificate is added.

Actual source charges INITIAL before constructing TRIAL. The selected refactor
records work and its event before ordinary primal/dual reconstruction. The first
armed callback retains TRIAL and work scalars and latches done. Disabled native
refinement returns without invoking the stop callback; the subsequent guard
reaches fallback. Fallback applies maxima to INITIAL before recording the event
and invoking the observer on INITIAL. The sentinel becomes the identical cause in
DiagnosticObserverFailure, which is outside the numerical catch classes and escapes
without another numerical fallback or return. Missing/duplicate/wrong-state gates,
50 predicates, owner/value/work/event/clock/policy checks and no-return behavior
remain textually intact. Their permanent-candidate execution is UNQUALIFIED.

TRIAL remains mutable through reconstruction until unwind. Endpoint equalities and
identities are selected observations, not callback-time snapshots, complete event
history, full-state rollback, real expiry or certificate transfer. Only the separate
historical X execution was qualified in Y; its consumed allowance is not renewed.

## Computational work, allocation and retained memory

No unnecessary NEW production work, allocations or retained memory were found.
Production is unchanged by Git comparison and fresh hashes: there is no new setup,
iteration, candidate, refactorization, recovery or certification kernel cost.
No before/after benchmark is justified or authorized for this source-only change.

No unnecessary NEW cold diagnostic/test cost was found in the proposed oracle.
The11-field probe contains an armed Bool, five Int counters, two Any state references,
NTuple2 and NTuple7 scalar records and sentinel. The original done Ref is additional.
Three17-role owner tuples (TRIAL conditional), a seven-field entry-values tuple,
clock3/work2/refactor2/fallback7/after7 records and50-Bool result tuple are bounded
bookkeeping. Seven owned vector copies contain26 entries: basic2 plus six vectors
of4. Endpoint comparison inspects at most26 element pairs plus two explicit slack
indices; ownership comparisons cover11 distinct,17 preserved and six shared/value
roles. Copies and comparisons scale with m and n+m if generalized. Fifty Test
assertions and result bookkeeping are additional nonzero cold work. Removed CLI,
TOML, twelve observations and eight output dictionaries do not establish a speedup.

Callbacks add bounded counters, retained references and fixed scalar records, with
four event-count lookups per record capture. They add no array/matrix scan, copy,
conversion, basis solve or growing ledger. Existing diagnostics retain their own
bounded64-entry event history and dictionaries. Existing factory/backend/scratch,
validation, reconstruction, candidate scans, updates and refactorizations remain
additional work depending on dimensions, nonzeros and update-chain length. Local
work counts are not complete PREforward, kernel, native or import budgets.

Probe, tuples, closure, exception and ordinary aliases may retain transitive mutable
problem/progress/workspace/factor graphs; a fixed reference count is not a byte cap
or native-free/GC proof. No new cache invalidation mechanism is introduced. No
allocation-byte/retained-byte measurement or coverage of all supported precisions
is established by this Float64 fixture. Streamed inventory hashing and O(file-count)
metadata are justified cold integrity work, separate from solver work. There is no
observer-neutrality, hidden-trajectory, CI-cause, full-suite or performance claim.

This review wrote only this review.md. No Julia query/parser/import/compiler/native
operation, numerical case, launcher, package/environment/cache/CI change or actual
test edit occurred. I1 and M1 must be resolved with preserved rejected artifacts
before acceptance, separate PASS closure or publication. S5-AA runtime admission
remains a separate gate; CIoff/HHdisabled and all broader restrictions stay open.
