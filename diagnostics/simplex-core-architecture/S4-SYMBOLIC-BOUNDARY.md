# S4-F: native symbolic boundary qualification

Status: new component run independently accepted; no production promotion. Sourceea5e0cc,
production/test identical to master0eb75c3. Protocol is the separate reviewed
2026-10-12-native-hh-symbolic-boundary.md plan. No production/test/CI change.

Exactly six new reference/candidate pairs, native Float64/Int64: changed values,
value-sensitive pivot, explicitly stored zero becoming nonzero, changed pattern,
changed dimension and same-pattern singular target. Each side owns separate CSC
inputs and a fresh LU; no shallow native copy. Candidate uses the production PFI
exact-pattern helper before lu!, reference always reuse_symbolic=false. Controls
remain default and q=nothing; IRSTEP0 is asserted. This is not an HH refactor or
public solve. No accepted driver/measurement was repeated.

## Results and provenance

boundary-1 completed179/179 runtime checks, exit0. The exclusive new auditor
passed24 gates, independently rehashed649 pins and recomputed exact factor and
forward/transpose residuals from saved binary64 representations. Six inputs and
all12side records present. The20planned solves meet their fixed diagnostic bounds;
exact factor identities generally have small NONZERO residuals, preserved. No
claim of exact factor arithmetic follows from a passing bound.

Entry accounting:12freshLU setups,12lu! attempts (including2expected singular
throws),20solves,10combined L/U/p/q/Rs extractions,10reachable-graph inspections.
Metadata access uses the already-existing numeric object; it does not create a
new decomposition on this successful path. No HH constructor/extraction/workspace,
observer, update, certificate or solver call. Singular factors are never solved.
The two same-pattern singular calls throw SingularException/status1 after mutation;
failed candidates are dropped. This is NOT native rollback or HH publication proof.

Candidates reuse the SAME symbolic wrapper on cases1/2/3/6; changed-pattern and
changed-dimension cases rebuild it. All12numeric wrapper identities change while
old owners are held, preventing pointer-recycling ambiguity. All five successful
pairs have equal saved L/U CSC, p/q/scaling and forward/transpose solution bits.
This small observed equality is not a requirement or general changed-value promise.

Input lifetime: native colptr/rowval/nzval are checked owned and equal to the
intended target. After both sides receive distinct inputs, each input's values and
row indices are overwritten with sentinels after its refactor. Planned solves and
metadata checks use a separate owned original matrix. All pass with unchanged
native copies. This is a direct native borrowed-array probe; actual workspace
basis assembly, HH extracted base/history/prepared state remain untested here.

The loaded native path is the pinned Julia1.13.0 AArch64 libumfpack.so.6.3.5 with
prelaunch hash match;13library files were pinned from host loader dependencies
and OpenBLAS candidates. Only loaded UMFPACK path/hash is observed in Julia;
pinning other dependency files does not independently capture all loader choices.
Actual package source, driver, source/test, Project/Manifest/LocalPreferences,
launchers and six user hashes are bound separately. No retroactive old native pin.

Raw reports/pins/process/resources and frozen driver/launcher/preflight source are
under results/S4-F. The Julia driver and exclusive auditor must NOT be rerun or
overwritten against this accepted evidence. No oracle failure/retry occurred.
Host runner3792(start101094), child3793(start101178), launchgroup3788 are absent;
boot dade7243-9103-4398-bb45-fa28fbc0be72. Four resource samples: minimumavailable
23,014,076KiB, maxswap0. This does not attribute peak native memory to a call.

## Work and allocation interpretation

All44 measured call records report compile0, but compilation outside @timed
expressions is not measured. No explicit warmup was performed. Setup, refactor,
forward and transpose metrics remain distinct; snapshots/metadata/graphs and
serialization are outside these measured scopes. Identity references keep the
old symbolic/numeric objects alive through mutation checks, affecting lifetimes.
They are released before the current-factor graph query; this is not immediate
native free/RSS proof or a production allocation benchmark.

| Case | Reference refactor bytes/events | Candidate bytes/events |
| --- | ---: | ---: |
| changed values |14912/60|13584/32|
| value-sensitive pivot |14912/60|13840/32|
| stored zero |14928/60|13632/32|
| pattern fallback |3040/60|2752/60|
| dimension fallback |3680/63|3680/63|
| singular |14912/60|13424/32|

Each is ONE cold call per side. Even the same no-reuse pattern-fallback paths
show different bytes, so these cannot establish universal savings/overhead or
isolate symbolic allocation. No speedup claim. Graph sizes1480B for2x2 and1624B
for3x3 are reachable Julia objects only; native bytes explicitly unavailable.
No retained symbolic memory bound or asymptotic-performance result is claimed.

Source review finds no new production work or memory: no production change.
Diagnostic cost includes exact-rational matrix/residual arithmetic, one owned
input snapshot per side, metadata copies/graph inspection and serialization.
These are bounded2x2/3x3 checks outside measured kernels, without growing native
factor collections. New runtime entry counters record attempts; only singular
refactor throws are exercised, not general throwing solve/accounting behavior.

## Next gate

A separate two-lifecycle HH publication/history/prepared-state qualification is
proposed in2026-10-12-hh-symbolic-publication.md. It requires a diagnostic exact
source clone whose only numerical branch change is conditional symbolic reuse;
production remains disabled. This first HH gate does not cover actual workspace
assembly, dimension/empty/nonfinite eligibility or native memory cost; these are
still required before production acceptance. No whole-solver/certification claim.
S2-A/S6-J/wholeAF stay rejected; CI stays disabled, broader S4/S6 remain open.

## Independent acceptance

Fresh gpt-6-astra accepts this component evidence; no unnecessary production work/
memory. Next-plan prepared-cache invalidation gap fixed offlineRED4/GREEN4 with
unchanged24HHsolve budget. One Minor leader-PID/group-label issue is deferred in
the preserved supplement; a separate fresh closure scan found both PGIDs empty.
See S4-SYMBOLIC-BOUNDARY-REVIEW.md. No old/exclusive audit or Julia rerun.
