# Direct LU backend diagnostic preparation

OFFLINE preparation for the accepted 2026-10-15 reference-backend diagnostic plan.
No Julia query, parsing, import, compilation, native execution, stage seal,
reservation or numerical run has occurred. Production/test/environment/CI/master
are unchanged. Task 3 cost1 remains failed and cost2 remains blocked.

## Concrete experiment and interpretation

The UNEXECUTED driver uses the qualified ordinary overlay and the exact existing
sparse96 B0..B4 and step1..5 tokens. Fresh B4 backend: 1 construction, 2 FTRAN,
1 BTRAN. Original FT/native prefix: 1 construction, four entering/DSE/replacement/
BTRAN steps, one refactor to B4, entering and DSE, immediate output snapshots,
then one direct-backend DSE into a distinct destination. Total explicit entries:
3 factorizations, 13 FTRAN, 5 BTRAN, 4 replacements, 1 refactor. These are not
transitive native/import-work counters. There is no fifth replacement, warmup,
performance comparison, quality/refinement/certificate call or factor copy.

Two post-solve snapshots each make one installed umf_lunz and one combined
umfpack_dl_get_numeric call. L stays CSR and U CSC: no conversion or helper
orientation solve. Capture raw p/q/Rs, controls, all90 Info fields, native CSC
values/ownership, and the scaling flag. Info tokens may be nonfinite and are
preserved as metadata; factors/outputs used for exact arithmetic must be finite.

The separate `results/DIRECT-LU-BACKEND-PREPARATION/scaling-contract.md` explicitly
clarifies the plan's quoted raw-Rs multiplication formula. Installed ABI accepts
an Int64 do_recip pointer; retained versioned upstream API documentation defines
1=multiply and0=divide. Capturing that flag in the SAME export call determines
s=Rs or exact1/Rs before inspecting residuals. No orientation fit, floating
reciprocal, changed control, tolerance, source method or extra native solve.
Upstream header is semantic documentation, not installed-build/runtime evidence.
Unknown flag or nonpositive/nonfinite scaling fails closed. The original accepted
plan remains frozen; this concrete ruling needs independent preparation approval.

The offline auditor checks all18 output vectors under the original exact bound
128*n*2^-52*max(1,||B||inf*||x||inf,||b||inf), with transpose for BTRAN. FALSE
residuals remain in the result; reproduction and nonreproduction are both valid
outcomes. Integrity requires exact entry counts, unchanged inputs, fixed controls,
all16 reset predicates, output preservation across the final direct-base call,
native input equality/ownership, valid factor shapes and fixed output membership.

For each captured factor, exact P=L*U and M=(s.*B)[p,q] give E=P-M. For each DSE
solution y=x[q], t=(s.*rhs)[p], the saved record reports E*y, P*y-t and M*y-t,
checking the identity M*y-t=(P*y-t)-E*y. Fresh, ordinary and direct-base DSE are
reported separately. This is combined LU application consistency, NOT captured
intermediate triangular solves or identification of the original native operation.
Token comparisons with the original failed step5 and between new contexts are
observations, not acceptance conditions. No numerical repair or cost acceptance.

## Work, allocations and retention

All new work is cold diagnostic work; no new production execution cost. Parsing
the existing TOML visits all four frozen fixtures; only sparse96 is selected, but
its full nine matrices/eight steps token record remains reachable during main.
Only five matrices and fifteen step vectors are decoded. Each CSC has three
arrays. Eighteen separate length96 output vectors have1728 Float64 slots. The
immediate two ordinary snapshots add192 token entries; serialized output records
add another1728 tokens. Token strings, dictionaries, TOML formatting and input
preservation scans allocate additional diagnostic storage and consume wall time.
The final unchanged check scans the five inputs and fifteen RHS vectors and
creates comparison token arrays; it is not inside any benchmark window.

Each factor extraction allocates nine arrays: L CSR ptr/indices/values, U CSC
ptr/indices/values, p, q, Rs, plus a scaling Ref and umf_lunz's five scalar Refs.
Each triangular nnz is <=4656; dimensions are96. Numeric values and Rs become
owned token arrays (three numeric temporaries may remain until GC); index arrays
are retained directly. Each snapshot additionally retains control20, Info90,
and three native CSC arrays/tokens, for14 array containers plus nested records.
Six index arrays are shifted in place once. Native ownership checks inspect three
array pairs; native equality scans CSC pointers and entries once. Five independent
control captures (2fresh,3prefix) each retain20 tokens, in addition to two snapshot
control copies. Reset predicates scan identity upper/maps/order once; they do not
add numerical solves. Diagnostic observer neutrality is not established.

Fresh B4 is retained through both contexts; prefix active B4 and original B0 spare
make THREE live native factors. FT ordinary scratch, upper/history pools and
prepared-spike storage remain additional. Detached outputs do not alias those
buffers. No GC, factor copy or cleanup is inserted, no graph/native-byte bound or
native deallocation claim. Offline exact Python factor products are bounded at
96x96 per context and separate from the Julia wall budget; their memory/time is
not a solver or native-allocation measurement.

## Admission controls and offline verification

`probe` is the only allowed phase. A future one-attempt reservation binds exact
command, launch pins, review and45second inclusive limit. The inner guard deadline
is39seconds; the independent supervisor terminates the complete group/session
within the45second admission. Julia/BLAS1,2GiBheap,8GiBVM,min6GiBavailableRAM,
max1GiBswap are unchanged. Fresh refs/boot/process start ticks/commands/all204
prior groups AND sessions/noJulia are required at seal and again at launch.
Prepared guard and supervisor are byte-identical to the accepted Task3 versions.
The later exact stage review binds the sealed manifest and every required file.
An accepted preparation review alone cannot launch. All outputs are exclusive;
failed/partial/raw-before-assert records survive and cannot be retried.

52 synthetic Python checks PASS: exact nontrivial permutation/scaling examples,
factor-error decomposition, preserved FALSE residual and nonreproduction, schema/
finite/permutation/CSR/ownership/control/count refusals, exact review membership,
one phase, timing/guard/reservation/ref/process-closure failures. No guard, seal,
launcher or old auditor was invoked. Canonical source-check-2 has17 PASS and
verifies514 unchanged production/test/CI files and the four ordinary overlay
sources. Original source-check.py failed on the nonexistent prepared_spikes.jl
selector before creating a result; original source/error preserved. Separate
source-check-2 changes only that filename to triangular_spikes.jl.

## Continuation and preservation

Evidence: results/DIRECT-LU-BACKEND-PREPARATION. Before changing continuation,
preserve prior exact STATUS and roadmap bytes. Prior diagnosis closure/publication
current STATUS/roadmap bindings map only to this directory's before-backend copies;
all earlier mappings remain. Original plan/report/reviews/scripts/raw remain frozen.
After independent acceptance, the next step is fresh stage sealing, exact stage
review, then at most ONE45second diagnostic. No cost2, retry, promotion, master
merge or benchmark expansion follows automatically. CI remains off, HH reuse
remains disabled, automation stays paused and the broader plan remains open.
