# Direct LU / Markowitz — separate offline test repair

2026-10-15. This is a test-harness amendment to the frozen 2026-10-14 plan,
Tasks 1–2. No Julia query, parser, import, compilation or numerical execution.
The original RED remains accepted and the original GREEN remains failed:
89 PASS, 1 ERROR, exit 2, incomplete audit FALSE. Neither attempt is repeated.
Candidate production sources, fixtures, actual src/test/Project/environment/CI
and master 6f68e24e8ddac42b948da8fcc2d636c010751194 remain unchanged.

## Repair and retained oracles

New `results/DIRECT-LU-TEST-REPAIR/correctness.jl` replaces exactly the native
source-backend mutation expression `lu!(...,sparse(2.0*B))`. It privately copies
B, scales only nzval, then uses that same-pattern CSC in the existing lu! call.
Stored zeros survive; colptr and rowval are unchanged. No reuse_symbolic=false
workaround, new fixture, relaxed residual or tolerance change is introduced.
All other test bytes, including final input owner/value and export snapshot/
identity assertions, are unchanged and checked by exact whole-file inversion.
The source-derived 16-to-4 pattern loss explains the preserved exception; no
new runtime observation is claimed by this repair.

Five new assertions run for each of six nonempty native export fixtures:
column pointers equal, row indices equal, all three copied buffers have distinct
owners from B, every stored value equals its original times 2 (isequal, including
stored zeros), and the real refactored factor reports issuccess. The existing
post-refactor export assertions still require the saved export to remain unchanged
and to represent the original B. Markowitz and empty-fixture behavior is unchanged.
Expected exports assertions become 100 + 6*5 = 130; complete GREEN becomes
19,527 + 30 = 19,557. These are prospective counts, not test results.

The separate driver changes only that count and two invokelatest call sites:
binding lookup and invocation now both occur inside a latest-world closure.
This addresses the observed binding-access warning without replacing methods,
changing test scheduling or adding numerical calls. Runtime compatibility is
unqualified. The retained RED branch has the same cleanup but is NOT permission
to repeat RED. All logging, stop-on-mismatch and raw-before-exit logic is unchanged.
Its @__DIR__/focused dependency must be populated and pinned in fresh admission;
this repair directory is not a runnable launch package.

## Computational work and ownership

No production change or added production work, allocation or retained memory.
On the successful test path there are still exactly six native source-backend
lu! mutations, with no new factorization/solve/update API entry. The previous
explicit work ledger (670 factor attempts plus those six lu!, 5,368 FTRAN,
3,139 BTRAN, 1,147 updates and 106 factor copies, plus listed implicit/additional
work) is unchanged. It remains a partial source ledger, not a native work cap.

Each of the six cold mutations now explicitly copies one CSC: three buffers
with n+1 column pointers, s row indices and s values, then scales s values.
Added checks traverse up to n+1 pointers, s indices, three owner identities and
s values (including the reference multiplication), plus scalar factor status.
This is O(n+s) work per tested source refactor, not per solver iteration.
The former sparse broadcast/copy also did work; no allocation reduction is
measured or asserted. Up to six CSC copies are created over the group, with
ordinary local lifetimes; no immediate collection or native-free claim.
Latest-world closures add bounded driver bookkeeping, outside any cost window.
These checks are justified by the failed pattern contract and ownership oracle;
no production performance claim or benchmark is needed for this offline repair.

## Verification and next gate

`source-check.json` checks exact test/driver inverses, frozen original hashes,
all 514 baseline src/test/Project/CI files, pattern-sensitive fixture source,
prospective counts and continuation mappings. Text checks are not Julia RED or
GREEN and do not prove runtime dispatch. Independent offline review is recorded
in this repair's review.md/json; only its explicit accepted decision closes this
preparation. Fresh host preflight checked all 200 prior groups AND sessions and
found no matching process or Julia; old host records were not substituted.

Next: prepare a NEW candidate overlay/control/config/output namespace for one
GREEN-only attempt <=90 seconds inclusive, copying these exact corrected files
and unchanged focused slices/fixtures/production candidate. Reuse accepted RED
records after checking their exact immutable bindings; do not reseal or rerun RED.
The original failed GREEN/raw/audit/reservations remain immutable evidence.
Update every count gate to 130 exports / 19,557 total and use new paths throughout;
old preparation reviews cannot admit the changed files. Bind this repair review,
full new source/runtime/command inventory and predecessor records. Require fresh
host refs/boot/start_ticks/command/full groups AND sessions/noJulia, then independent
exact admission before a new exclusive reservation. Preserve the existing single
Julia/BLAS thread, heap 2 GiB, VM 8 GiB, RAM floor 6 GiB and swap ceiling 1 GiB
with fail-closed termination/audit. Standing human permission covers short runs.
Any unexpected failure stops; no automatic retry, tuning, or longer limit.
No launcher or numerical reservation is prepared here. Tasks 3–4 remain gated
on accepted full correctness; no production promotion. CI off, HH reuse disabled,
automation paused. All old frozen artifacts and their mappings remain unchanged.
