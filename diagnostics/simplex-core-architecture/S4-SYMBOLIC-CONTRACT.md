# S4-E: native HH symbolic construction contract

Source/evidence-only decision, 2026-10-12. Base74731c1, master0eb75c3.
User explicitly resumed after S6-AO. New host boot is
`dade7243-9103-4398-bb45-fa28fbc0be72`; prior runner433429/child433431/group433420
are absent and no Julia/guarded numerical runner was found. Remote refs matched.
No Julia, factor, solver, test, old driver/auditor, corpus or benchmark executed.
Production/test/environment/CI are unchanged; CI remains disabled.

## Decision

A component qualification of conditional symbolic reuse is justified by the
installed `lu!` API. Production HH reuse is NOT qualified or enabled. The first
candidate is restricted to native Float64/Int64, exclusively owned UMFPACK
construction state with a valid existing symbolic object, canonical CSC input,
exact dimension/colptr/rowval equality (with the existing zero/one-index offset),
unchanged original control vector and q=nothing. Otherwise rebuild symbolic state
or use the existing fresh/empty HH route. Never use a shallow UmfpackLU copy as a
private candidate. No raw pointer cache, new retained matrix, or production patch
is authorized here. Controls/order must remain unchanged across the reuse window;
comparing against the already-mutated current control vector would prove nothing.

Numeric values may differ. API permission to reuse for identical stored pattern
is not an assertion that values are irrelevant to symbolic analysis: the wrapper
passes nzval and controls to native symbolic construction. Changing values may
change ordering, pivot decisions, scaling, fill and downstream arithmetic relative
to fresh analysis. Neither bitwise identity nor trajectory identity is promised.
First qualify the native boundary under a separate small plan, then evaluate HH
extraction/publication, saved factors, prepared state and borrowed assembly before
any production proposal. Exact pattern is a necessary gate, not complete proof.

## Provenance and accepted evidence

`results/S4-E/source-contract.json` contains25 evaluated checks,542 current hashes,
24 explicit comparisons, current refs/status/boot and no-run scope. All25 pass.
The exclusive source_contract.py must not be rerun on this accepted output.
No historical raw file or parser was rewritten or invoked.

The installed Julia1.13.0 AArch64 executable, Manifest and LocalPreferences match
S4-B/S4-C/S6-R launch pins. Current umfpack.jl sha256
`6d40eb41958765d47b9ef60fb08fd6b61c0ee850979e3601343ce67fbe6ac84d`
matches S6-R's explicit launch pin. S4-B/C did NOT pin that wrapper; its current
hash is not retroactive proof of their loaded implementation. Current
libumfpack.so.6.3.5, LibSuiteSparse.jl and SuiteSparse_jll.jl are newly hashed;
these are not historical loaded-library observations. No C implementation or
native allocation formula is established by the installed Julia wrapper alone.

S4-C-focused current HH source and huangfu_hall_tests.jl match exactly, with actual
Starting/test-summary lines in its saved log and explicit include in the pinned
hh_scratch_focused_tests.jl driver. This reuses the accepted4366-assertion run;
no new execution is claimed. S4-B whole HH source differs (later S4-C Markowitz
extraction change); its old attribution stays tied to its recorded source, not
relabelled current-master cost. Its accepted audit, raw report and pin-manifest
hashes were checked. All src/test/.github are identical to current master.

| Obligation | Existing source and actual evidence | Remaining gap |
| --- | --- | --- |
| Same pattern/new values | HH tests42–46,90–110, accepted C-focused matching test/source | All use current reuse_symbolic=false; true path untested in HH |
| Pattern/dimension changes | B saved lifecycle changed_pattern/shrink/regrow; C-focused scratch/dimension tests | Guard selection and fresh-symbolic fallback under proposed candidate |
| Empty/singular refactor | C-focused HH tests67,100,106–110,212; B singular lifecycle | Same-pattern numeric singular failure with reused symbolic and subsequent HH discard |
| Saved copies and history | C-focused HH tests42–45,94–105,170–216, shared suffix assertions | Candidate extraction/failure must preserve base, history and prepared values |
| Borrowed CSC | src/simplex.jl266–318 borrows assembly; native constructor/lu! copy input arrays | Assembly test loops omit HH; direct HH/candidate borrowed-buffer test missing |
| Nonfinite input | HH tests63/181 reject NaN update direction | Not proof of nonfinite basis/refactor behavior or symbolic eligibility |
| PFI native reuse | factorization.jl294–341 + umfpack_reuse_allocation_tests.jl | SOURCE ONLY in this map; no inferred HH execution from pins or other managers |
| Other scalars/backends | S4-D40cases/360samples and10lifecycles, accepted review | Native non-Float64 uses dense LU; Markowitz separate, neither qualifies UMFPACK |

## Ownership, compatibility and failure boundary

Line references below bind to the hashed source, not newest online API docs.

| Object/boundary | Current ownership and compatibility | Mutation/publication and work |
| --- | --- | --- |
| Basis assembly | simplex.jl260–318: public allocates; internal scratch CSC borrowed until next assembly | Validate basis, count stored column lengths, then copy O(n+nnz) entries; never retain borrowed arrays |
| New native LU | HH289–310; umfpack.jl241–252 | Copies/decrements CSC indices and copies values/control, allocates solve scratch and native symbolic/numeric objects |
| Reused native LU wrapper | umfpack.jl445–482 | Mutates dimensions, resizes workspace/CSC and copies indices/values BEFORE numeric success; reuse=false clears symbolic, numeric always rebuilt |
| Compatibility guard | factorization.jl294–308 | O(n+nnz) index comparison at each prospective refactor, not per iteration; early mismatch possible, no pattern hash collision shortcut |
| Symbolic and q | umfpack.jl585–599 | Existing nonnull symbolic short-circuits; q/control changes cannot be assumed to rebuild symbolic when reuse=true |
| Native numeric | umfpack.jl615–628 | New numeric object on each lu!; singular warning stores numeric/status then outer check throws; other native errors may leave partially changed candidate |
| Shallow native copy | umfpack.jl278–296 | Shares symbolic/numeric/colptr/rowval/nzval, copies workspace/control/info/lock. Unsafe isolation shortcut for mutating lu! |
| Extracted HH base | HH80–113,259–289 | Fresh owned U/p/q/scaling and L CSC; bounded CSR scratch stays private. O(n+nnz(L)+nnz(U)) extraction/index/adjacency passes |
| Scaling convention | HH167–197 | Unit scaling fast path; otherwise existing native solve, two new vectors and L/U multiply/absolute-multiply scans; keep these safeguards |
| Saved HH factor | HH591–595 | Shares immutable base/update records; copies update container and allocates private scratch/pools; native refactor_workspace=nothing |
| Failed HH candidate | HH549–570 | Catch discards private backend. Old base/history/prepared arrays not published; disposable work/auxiliary/extraction scratch may change |
| Successful publication | HH571–588 | Retire only private updates; publish new base/backend/vectors; adjust unit workspace; clear updates and prepared_valid. Later allocation failures are not globally transactional |
| Empty/dimension route | HH541–545,580 | Empty returns nothing; dimension mismatch constructs fresh native backend. Four owned scratch vectors follow accepted S4-A sizing rule |

Do not generalize private backend discard to rollback of the backend itself.
The old active HH base is independently extracted; this is why its old solves can
survive a failed private lu!. Recovery must preserve this distinction. No saved
native pointer or input-value alias may be introduced by a future optimization.

## Computational work and retained memory

No production work/allocation/retention changes in S4-E. Audit hashing and source
reads occur offline only. A prospective guard adds an O(n+nnz) pattern scan once
per refactorization, including recovery, while current lu! still copies all CSC
indices and values. Controls are small fixed arrays; proving unchanged controls
requires an immutable origin contract or an owned snapshot, not pointer equality.
Skipping symbolic construction does not skip numeric construction, extraction,
scaling validation, HH adjacency construction, scratch or history retirement.
The latter scales with packed update entries; base extraction scales with fill.

S4-B native backend region medians show allocation traffic exceeding extraction
for its four64/256 fixtures; e.g. dense256 backend84,613,968 bytes/16calls versus
extraction21,417,088. Independent scopes must not be added, and the backend scope
combines symbolic/numeric/copy/native work. It does not isolate avoidable symbolic
cost or demonstrate a candidate speedup. No current-master or cross-boot timing
comparison is made. S4-C's mostly-zero2561.0258 side median is not a speedup.
S4-D's BigFloat failed Serialization hashes and corrective probe remain intact.

Retaining one symbolic object rather than replacing it may retain native state
chosen under older values. Julia field lengths/summarysize do not bound its native
allocation, hidden vector capacity, allocator retention or process RSS. Future
qualification records separate reachable graphs/native metadata/resources; no
constant or bounded total-memory theorem follows from this table.

## Next gate

Separate plan2026-10-12-native-hh-symbolic-boundary.md defines six paired native
component cases,12fresh LU setups,12lu! attempts and20solves, with no HH/public
solver calls. This deliberately does not qualify HH publication/copy/prepared
integration; that remains a later separately bounded obligation. No old suite,
component/cost/corpus/reference is repeated. Fresh independent review must accept
this source contract and bounded plan before launch. Broader S4/S6, historical CI
cause, original-model certification and S2-A/S6-J/wholeAF rejection stay unchanged.
