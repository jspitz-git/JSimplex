# S6-AI: scoped public dual recovery fixture

Status: accepted by fresh independent review and integrated. Test62e6535 -> master354bb1f.
Base7eeb318/master3c0af5c. Only test/dual_pivot_consistency_tests.jl changes.
No production/options/tolerance/precision/CI change; AF whole qualification remains
NOT ACCEPTED with its failed control oracle. No rejected S6-J direct retry.

## Change and preserved contracts

New fixed Float64 dyadic helper and DualRecoveryFactor scope two recovery groups.
Real setup precedes wrapping; only two genuine unit BTRAN outputs are declared as
rho-2^-22*e1 after checking exact AE rho. Prepared, ordinary and correction solves
forward and check real outputs. Copy/update count then fail unsupported. Native unit
metadata and inner prepared-cache behavior are forwarded, not replaced.

All108 original recovery predicates, direct public calls/@test_throws, callback
bodies, policies/options and manager loops remain. The original native helper and
both other groups (108 assertions) are byte-identical. Added7 runtime work/ownership/
event checks per subject give248 target assertions. Candidate factor is shared;
ordinary vector copies still exist. Original zero/exact-one refactor assertions remain.

Counters advance before forwarding, stay active after two hits and include throws.
Nonrefresh:2preparedFTRAN/2unitBTRAN+1correction/0refactor; refresh adds1ordinaryFTRAN,
1zero-costBTRAN,1refactor. Outer invalidations4/6,metadata2,hits2,copy/update0.
Separate whole timed iteration kernels assert2/3/0 or3/4/1 after subtracting setup.
An outer observer forwards the unchanged callbacks; only scalar counts/flags and one
factor Ref are retained. It checks factor sharing, correction-before-rejection and
refactor event at2F/3B/1ref/4invalidations before both recomputations. No global
observer-neutrality or general factor lifecycle claim.

## Evidence and resource scope

Structural RED is offline pre-solve analysis:3 expected false missing-helper/work
predicates against the actual old source, zero workspace/public/numerical calls.
Python analysis exited0 after confirming all three were false; this is not a failing
Julia test or a numerical reproduction. Original source/hash and conditions preserved.
Preflight compares AG pins:627unchanged, one intentional test change; old test matches
its628th pin. Thus source/runtime/environment unchanged; represented AE inputs pinned.
Options/policy preservation follows unchanged original callsites and matching helper
constructors/source, not a new per-case runtime metadata census.

GREEN-1:339/339,exit0,22audit gates,627pins,4raw/portable/driver/source supplements.
Actual changed-source target192+56, native direct-small-pivot neighbor60, structural3,
driver-only micro27,global1. Exactly30 public iterations (20target+10neighbor), no new
real controls, no full-file sweep, no postcall solves/certificates. Untouched native
safety48 remains static/reused evidence, not newly run. No accepted driver rerun.

Nine driver-only sentinel/failfast calls verify pre-forward counters and exception
identity, including unit BTRAN with hits already2;27checks. They use a nonnumerical
inner sentinel, zero real factors/workspaces/public calls. This proves scoped attempt
accounting, not backend recovery. No sentinel methods enter permanent test source.

Raw log assertions are the runtime oracle; permanent callback exceptions remain
surrounded by direct @test_throws. No vacuous initialized error field. Actual per-call
value snapshots/ledgers were deliberately not added; AF values remain prior evidence.
All627pins independently hashed; actual selectedsource/driver/test/rawportable and
mainuser hashes verified. Runner416424/child416425/group416415 absent, noJulia,
boot20de7dde-704e-41c8-bee7-b8511c0a86b0. Guard Julia/BLAS1,heap2GiB,VM8GiB enforced.

## Work and memory review scope

No production work/allocation/retained-memory change. Test-only cold4row setup adds
small dyadic matrix and scalar wrapper. RHS/output comparisons use fixed-size tuples,
refactor validates16entries once; one Ref plus scalar event state, no growing ledgers,
per-solve vector copies/rationalization or extra permanent public iterations. Existing
bounded SimplexDiagnostics event storage and candidate vector copies remain. No
benchmark/speedup inference warranted. New-source compilation time is not solve cost.

Fresh independent numerical/work/memory review precedes test-only commit/integration.
Then new actual-master target-only gate (20publiccalls, no micro/neighbor repeats).
All original predicates and added full work gates must pass. Historical CI cause,
fullsuite/x64/broaderS6 remain open; CI stays disabled.

## Actual-master closure

Fresh gpt-6-astra review no Critical/Important/Minor; no unnecessary production work
or memory. Test-only62e6535 integrated as master354bb1f. Actual-master252/252,exit0,
21audit gates627pins,4raw/portable/source/driver/integration supplement checks.
Only20target calls; no microcheck/neighbor repeat. All source/test/user hashes verified.
Runner417368/child417369/group417360 absent, noJulia, same boot. Production/CI unchanged.
Next S6-AJ source-only historical failure coverage reconciliation; no accepted reruns.
