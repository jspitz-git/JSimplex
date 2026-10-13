# S5-M independent final numerical and work review

Verdict: ACCEPTED for the narrow, single-attempt S5-M qualification described
below. Critical: none. Important: none unresolved. Minor: none. The original
prelaunch Important finding was resolved in two preserved offline amendments
before this attempt; that rejected review remains authoritative for its revision.
This is result-review acceptance, not a claim that publication closure has passed.
At review time results/S5-M/closure.json is absent. No permanent test promotion or
new numerical execution is authorized by this review.

## Independent scope and identity checks

I read the M qualification report and plan, relevant STATUS/roadmap continuation,
prospective N plan, exact L candidate/source provenance, canonical launcher-final,
audit-final, schema and command, original rejected/final accepted prelaunch reviews,
both correction records and correction source, acceptance, all six raw files,
18-gate audit, eight-check postcheck, host admission/after records and relevant
production publication/observer/initialization/pricing source. closure.py was read
as text only. No preserved launcher, auditor, closure, correction or historical
script was executed. No Julia, import/parser probe, package operation or numerical
attempt was performed by this reviewer.

I independently streamed all 756 final inventory files in 1 MiB chunks, reading
3,576,745,539 bytes. Every SHA-256 and resolved-path identity matched. Complete
src/test tree memberships matched. All 141 L evidence hashes and 18 L closure
bindings matched; only the current STATUS and roadmap paths were reconciled to
results/S5-M/STATUS.md.before-M and
2026-10-11-simplex-core-architecture.md.before-M where prior closure requires them.
Those two current documents differ from their preserved originals, as intended;
this does not excuse changes to any other pinned file. The final launch inventory
itself has no differing current pinned identities.

All six original raw files match their audit hashes and portable copies byte for
byte. The empty run.log is preserved. The seven prelaunch acceptance bindings,
5+6 correction bindings and six postcheck bindings independently match. All six
protected user-file hashes match. Source/test/.github have no diff from master,
and their working-tree status is clean. HEAD is
f478c417df4cda482f64c13fbafbedf2846f9bae; master remains
513c05388a82531e4d8fbcfb383e8897fad14ba2.

| Evidence | Independently verified SHA-256 |
| --- | --- |
| Exact L candidate | b553d449a0db620bfae1970861806a778bbf45d36465026e8b4a540e4b4f4288 |
| Final 756 manifest | f9e8ce912c596c58e93d528f81a574344facc2b46a66499966b843cac0fb2df2 |
| launcher-final.py | fb1b251b7b5e8b4fa3a203fec5509f94870d045cceb9985845d656785810bfca |
| audit-final.py | d927da7a461360f83c6673a0387d56ff76c1de257ae67e6e3c980a72acc8b41f |
| Raw report.toml | 0641daa8a1d59d70b667f78c29f6d9323fecbf4ce1bac8ab8ba54a0b5c7abbfe |
| audit.json | 0ee1d5072e1b64a92b5e7be3e5e6236ef86a54bc22e1e8e91e6805f22225a366 |
| postcheck.json | bc379ae5767b0aedb476aab1747c9b14720f75e2d265421752e9975e0a77b1a5 |
| closure.py, text review only | 2769389b3bd0c9af5fde8837d2973984d59867b8bc3bec4ccafd3ecd767044f7 |

Original744 manifest remains
7e216b4963f1856b5059771c4d8246bde70d083c2441e2d154a76b643076abe6;
intermediate750 remains
a97ada99806b68cb1f29030fe0c19f31305d31e4df628a81cb40e071d2fcdcb5.
The preserved before-M STATUS hash is
528abeba2f0b2fb732a0fc5b77497707f47a95f7f92fa061726abb12d027cbfe;
before-M roadmap is
02f9371a38a7a92512037485f3b186472fb2c498372aefe267a7a7002120ab2b.

## Numerical result and source-supported boundary

Independent TOML inspection finds exactly the frozen 40 predicate keys, each
literal true, and 15 correctly typed observations equal to audit.json. The three
helper bodies match their current-test source blocks and hashes and each occurs
once in the candidate; both setup blocks have the exact four-space indentation
inverse. This is one original Float64 one-row/one-column fixture initialization
and one public make_dual_feasible! call, with no extra success control, resume,
weight check or numerical call. Initialization source copies objective/zero slack
costs and concatenates column/row bounds consistently with the six entry-model
comparisons and selected scope predicates.

There is exactly one root-StageObserver trial latch and one selected throw. The
latch requires a non-LIVE candidate whose StageObserver.live is LIVE; auxiliary
nested candidates are excluded by root identity. _candidate_workspace clears the
pending-factor/post-iteration flags, refactor_other forwards the candidate, and
pricing_phase_reset is buffered by _StageObserver. The throw requires LIVE, its
adopted trial factor, and a factor different from entry. dual_simplex.jl:2148-2153
invalidates checkpoints, copies pivot state, clears history and adopts that factor
before pending replay. The discriminator therefore selects the intended published
handoff on this actual execution, without relying on the event symbol alone.

The observed type is JSimplex.DiagnosticObserverFailure{ErrorException}; candidate
code tests the wrapper directly and cause === sentinel. Diagnostics record the
event before wrapping the callback exception; public make_dual_feasible! rethrows
this nonnumerical exception. Type strings supplement these identity predicates.
All nine selected LIVE array owners persist, remain distinct from trial owners,
and have equal values at unwind. Factor and private refactor-policy publication
persist. Pricing retains its LIVE owner, differs from trial ownership, matches
all 19 fields and has the non-temporary phase transition. History/checkpoint/
phase-generation/journal predicates agree with the publication source. Retained
history has window_count=2; this is the selected history predicate, not a snapshot
of every old history field. The retained trial remains mutable until unwind.

Work observations are iterations 0 -> 1 and refactorizations 0 -> 1. Final counts
equal both trial and throw-time counts. Seven callbacks were delivered; the throw
is callback seven. The shared phase-event count is two at throw and unwind, and
the last recorded event is pricing_phase_reset. These are two shared diagnostics
events, not two selected target hits. No later selected callback, iteration,
refactorization or phase event is observed. There is no serialized full event
trajectory, vector snapshot or complete backend/PREforward accounting.

This qualifies selected postpublication exception behavior. It is not whole-
function rollback: earlier LIVE restoration/recompute/flips, auxiliary work,
private reconstruction and shared counters remain consumed. Original-bound means
LIVE postrestoration bounds. This fixture's entry model/cost/bound predicates
passed once; cost preservation is not guaranteed for arbitrary auxiliary repairs.
No original-model certificate is transferred from auxiliary success, and no
optimality, hidden trajectory or observer-neutrality claim follows.

## Admission, failure preservation and resource evidence

The exact recorded command matches command.json and directly executes the frozen
candidate. Final acceptance predates the separate host admission and the attempt.
Launcher/guard provide one exclusive qualification-1 reservation with no retry,
global lock, no concurrent Julia, one Julia/BLAS/OMP/MKL thread, 2 GiB heap hint,
8 GiB virtual-memory cap and sampled 120-second child wall guard. Both pinned
wrapper layers were read: the nested wrapper supplies depot text; the outer execs
the installed aarch64 Julia with startup disabled. Existing compiled modules and
disabled Pkg automatic precompilation support the reviewed ordinary-loader path.
They do not establish complete import/init work, cache confinement or actual
transitive module/cache selection.

The first audit correction guards wrong table shapes and absent children; the
second emits a failed-input audit for ordinary unreadable/missing inputs. I
independently compared the final try body with audit-reviewed.py: it is byte-exact
after removing the added leading indentation. Acceptance requirements were not
weakened. The preserved 3+5 synthetic failed audits are offline error-handling
evidence, not extra candidate attempts. No result predicate was retuned after
execution.

Final process.json records exit0 and unchanged pins. current.json is the guard's
provisional launch snapshot: its launch_error/null fields are written before the
running/final transition, not evidence of a second or failed attempt. Sixteen
samples have minimum available RAM 22,006,660 KiB and maximum swap zero; maximum
sample elapsed is 15.012573642001371 seconds. Inclusive guard time is
16.029080629348755 seconds, including imports/compilation and sampling overhead,
not a benchmark or instantaneous resource guarantee.

Runner60707/start_ticks2525108/PGID60706 and child60708/start_ticks2525229/PGID60708
share boot dade7243-9103-4398-bb45-fa28fbc0be72. Their identities agree across raw
and host-after records. A fresh independent /proc scan on that boot found no Julia
and no member of either group or prior groups23249/23257/49081/49084/52772/52774/
53479/53481. Child command capture is at wrapper launch, not a post-exec command
sample. Audit18 and postcheck8 PASS records are supported within these limits.

## Computational work, memory and continuation

No unnecessary NEW production computation, allocation or retained memory was
found: production/tests/environment/CI are unchanged. No hot-path change warrants
a sparse/dense before/after benchmark. Diagnostic callbacks add fixed identity/
scalar metadata per notification, with no vector scan/copy, solve or growing
ledger. Entry setup adds three vector copies totaling 3(m+n) entries, six here.
Post-unwind publication comparisons cover at most m+8(m+n) element pairs, 17 here,
plus 3(m+n) entry pairs, six here, and 19 pricing fields with fixed ownership checks.
Source can construct up to 18 small temporary nine-owner tuples in that cold path;
this is not a measured allocation count. Fixed 40/15 result maps and serialization
occur after unwind. Offline hashing is streamed identity work, not solver work.

Twenty selected reference roles exclude additional aliases/containers and do not
bound retained bytes. LIVE/trial/entry-factor/history roots can retain workspace
scratch, sparse metadata and factor/update-chain graphs. Dimension/nonzero/update-
chain and wider-precision memory scaling remain unmeasured. Existing production
factor copies, solves and recovery safeguards remain unchanged and are not fully
counted by iteration/refactor observations. No kernel saving, speedup, native-free,
GC-neutrality or complete import/backend-work conclusion is supported.

N is correctly limited to one OFFLINE, unexecuted separate test candidate with
source inverse and independent review; permanent test edits, execution and
automatic promotion remain outside that plan. closure.py separately checks audit,
postcheck, reconciled identities, review acceptance, current host groups and raw
copies before exclusive publication. I found no blocking defect in its reviewed
text, but it has not run and no closure PASS is asserted here. Historical 237
assertions per failed CI run and 78/19 scoped coverage remain reused evidence.
Full-suite/x64 and broader S5/S6, bootstrap/cache/init/work/retention gates remain
open; CI stays off and HH native symbolic reuse stays disabled.

Only this new review file was written by this reviewer.
