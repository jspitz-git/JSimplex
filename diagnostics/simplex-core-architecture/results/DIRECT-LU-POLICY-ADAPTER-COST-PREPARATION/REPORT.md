# Direct LU adapters — Task3 matched-policy cost preparation

OFFLINE preparation only. No Julia/query/parser/import/compile, seal, reservation,
launcher/guard, measurement, public solver or production edit. Task2 GREEN30455
and RED7 remain frozen. Actual master26e2291 and candidate source unchanged.

The new cost.jl uses accepted GREEN's75-file ordinary candidate overlay. Both
ordinary and direct factories receive the same explicit policy: native threshold_one
or Markowitz default. Four immutable sparse/dense32/96 fixtures, nine basis matrices
and eight incoming/DSE/unit steps are copied byte-for-byte from the old input JSON
and TOML. The old cost executable, failedcost1 and blockedcost2 are never rerun.
All new driver functions are defined at top level before main; there is no runtime
include/global binding lookup, avoiding the pattern behind Task2's warnings.
This is source preparation, not a runtime compatibility claim.

## Schedule and measured boundary

24cells=4fixtures*3managers*2backends. Each of two separately admitted processes
has3 warm and7 measured alternating pairs/cell. Process2 reverses starting side.
Per process480whole windows(144warm/336measured); both processes960. Each window
includes construction/export/validation/normalization/packed-U/scratch, eight
updates with16FTRAN+8BTRAN, and refactors after4/8. Nested construction/FTRAN/BTRAN/
update/refactor1/refactor2 times are subsets, never added to whole time. GC remains
in the whole total. Bytes/events are aggregate Julia GC counters and can include
native allocator traffic; not pure Julia objects or native live/peak memory.

Final Base.summarysize(factor) is outside timing and includes reachable pools,
capacity and spare fields. It is neither peak nor native-memory accounting. Only
the current factor survives to this graph check; no earlier factor or all-window
row list is retained. Each detached row is written immediately and dropped.
24output vectors are allocated once per decoded fixture outside timing and reused;
solves overwrite them. One input scan/window replaces the old duplicate scan.
Scalar timers and a six-element clock vector remain inside both sides equally.
Input scans, Float64 residual probes, graph scans, token conversion and TOML I/O
remain real outside-window process costs. Explicit GC is not added; releasing
roots does not establish native free or observer neutrality.

The actual candidate mode after construction/B4/B8 is recorded as normalized,
direct or fallback. A legitimate fallback is retained and labelled rather than
converted into a correctness failure. Modes are included in each result and must
accompany interpretation of any promising cell.

## Bounded untimed policy preflight and source ledger

Before each cell, two constructions and four refactors exercise B0/B4/B8 on both
sides. The candidate exporter inspects its actual backend before real extraction;
only detached control/strategy tokens survive. Native intent, all20 actual controls
against the installed default vector with pivot tolerance1 and IRSTEP0, and finite
actual strategy are checked. No unsymmetric strategy is assumed. Markowitz actual
type/default policy are checked. Zero additional explicit preflight solves; native
orientation inside export is additional. No control snapshots occur in timed windows.

Per process:480constructions960refactors3840updates7680FTRAN3840BTRAN timed API
entries. Separately48preflight constructions96refactors,72candidate exports,
72native and72Markowitz observations. Combined1584backend setup/refactor entries,
792candidate exports,396native candidate exports with up to396orientation solves.
These are source-derived entries/bounds, not complete observed PREforward/native
instruction budgets. Backend/internal refinements and helper primitive work remain
additional. Both processes' timed totals match the accepted960/1920/7680/15360/7680.

Per process11520 recorded solution vectors737280Float64 entries, checked by11520
exact offline residuals. The24output containers/fixture total6144Float64 slots over
all four fixtures; maximum simultaneous2304slots. Preflight144detached records,
2880native actual+expected control tokens plus72strategy tokens. Tests/scratch,
installed module loading, exact Python arithmetic and serialization are additional
bounded diagnostic work. No new production work, cache or retained structure.

## Audits, selection and launch gates

Exactly558output files on success: guard5+raw1+24*(started/preflight/cell)+480windows.
Raw counts/paths/threads/phase, every window's side/order/policy/mode/schema, integer
allocation/memory counters, finite times and timing subsets are checked. Every
recorded entering/DSE/BTRAN output is checked against the unchanged exact binary64
scaled128*n*eps residual bound. Every measured compile/recompile must be zero.
Nonzero compilation invalidates cost acceptance and never grants automatic retry.

Each cell reports process-separated median/MAD/range and raw paired series for time,
bytes/events, GC and retained memory. Nested times are also reported separately;
zero nested timings never cause division by zero. Engineering selection: median
whole-time ratio<=0.95 in each process, at least10/14 faster pairs across both,
median bytes AND events nonincreasing in each process, and no measured memory pair
exceeding+10%. Zero reference memory allows only zero candidate memory. All four
fixtures must qualify for a manager/backend to be called promising. A cost miss
remains a valid negative result; it is not a numerical failure or tuning permission.
No pooling across managers, universal speedup or production promotion.

Canonical phases cost1-300,cost2-300,cost1-600,cost2-600. Initial inclusive300s/
inner292s; only an independently accepted pure timeout allows matching600s/592s.
No automatic seals/launches/retries. Process2 requires exactly one accepted complete
first-process result with exact full-file review and unchanged inputs. Every phase
needs fresh host/source/runtime/stage checks, immutable seal and fresh independent
exact-stage admission. All old226groups ANDsessions are checked; new groups are
added after attempts. Julia/BLAS1,heap2GiB,VM8GiB,RAM>=6GiB,swap<=1GiB; existing
compiled-module mode, no package resolution. Runtime inventory609 is checked; this
is not complete loader/cache-confinement/native-retention proof.

A pure timeout must retain valid guard/process/resource/invocation identities,
unchanged pins, a driver checkpoint and a fully validated prefix of completed
windows/preflights/cells. Holes, malformed files, raw completion/error, observed
numerical failures, measured compilation, resource or cleanup errors prohibit
retry. Import-only timeout is unknown. Results are written before each correctness
or compile gate so failures survive. Raw is written in finally when possible;
kill/import failures can lack raw and require logs. Partial results never pass.

## Offline evidence

New Python checks91PASS cover fixed input bits/equations, factories, raw schemas,
exact residual rejection, mode recording, metric/statistic/zero-memory boundaries,
review membership and timeout exclusions. Separate17prefix tests use explicitly
synthetic2x2identity outputs (not solver evidence) to test all558files/480windows,
partial prefixes, missing preflight/hole/extra outputs, wrong policy/count/residual
and measured compilation. Original synthetic refusal wrapper failure (omitted
RuntimeError) is preserved; the corrected test is a separate file. Its memory
negative also selects candidate by side rather than assuming a row index.

Next is fresh first-process admission only after this offline preparation's
independent review and closure/publication. This step authorizes no Julia run.
Task4 public routing remains separate. CIoff,HHdisabled,automationpaused.
