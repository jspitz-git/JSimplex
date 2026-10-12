# S6-AC: deterministic reconstruction success test

Status: independently accepted and integrated. Test610c4bd -> master3c0af5c
(pushed and remote verified). Basefcf7870/master74f7835. Test-only edit native_phase_transfer_tests.jl prefix/helper and only
`Artificial exchanges certify native reconstruction before export` target.

Qualified S6-AB identity6 construction and real-forward phase boundary retained.
Seven original assertions, two scalars/four managers, options and max_refinements3
unchanged. Native roundoff helper and all other testsets byte-identical. The reliable
identity helper from AA is reused byte-identically. Same structural singleton as old
fixture, different equations/row activity/cancellation. No solver/tolerance/precision/
safeguard/workflow change. Historical native arithmetic cause remains unknown.

Compact phase-only factor owns three length6 vectors and scalar counters/flags.
Ordinary/prepared/BTRAN/update/refactor/invalidation counters increment before real
forwarding, RHS classification continues after one-shot consumption. Successful
update6 and first identity refactor arm sole real primal-FTRAN output perturbation
2^-10coordinate3. Failed update/refactor disarm; unsupported copy fails explicitly.
Original/export factors real. Four observer Refs track enable/order/real-export only,
no numerical mutation, solve, certificate or snapshot. Complete phase work and whole
remove6FTRAN/4BTRAN/2refactor kernels enforced; fresh export initialization separate.
Kernel baselines are read before initial legacy certificate (which performs no such
kernels); assertions immediately after remove exclude all post-call checks. No
observer neutrality/hidden trajectory/general lifecycle claim.

## Verification

- red-1:2expected structural failures,exit1,zero old exchanges/workspaces/solves;
  all15audit gates623pins. Old numerical failure is not replayed.
- green-1:339/339 =2structural+192target+108native cancellation/policy neighbor+
  16reliable neighbor+20pre-forward microchecks+1globals;28newsource exchanges.
  Exit0,20audit gates623pins;allneighbor/nativehelper/originaloracle/source/userhashes.
- Six driver-only throwing-inner operation checks verify exact exception identity,
  pre-forward counter1,unarmed/hit0; seventh unsupported-copy check changes no count.
  Zero numerical kernel/extra exchange. This is wrapper accounting, not backend
  failure recovery. Static extra-primal-attempt count violates actual work assertions
  with unchanged hit; no extra numerical call and no mutated-loop proof.
- Eight supplementary raw/portable/driver/negative checks. Guard Julia/BLAS1,heap2GiB,
  VM8GiB,minRAM6GiB,maxswap1GiB. Host406189/406193/406181 separately absent,noJulia,
  boot20de7dde-704e-41c8-bee7-b8511c0a86b0. No accepted AB/corpus/cost reruns.

## Cost and scope

Production untouched. Eight permanent target exchanges remain eight. Tiny test setup
adds three owned length6 vectors,wrapper, four scalar Refs/observer and existing
bounded SimplexDiagnostics dictionaries; one6x6identity allocation per phase refactor.
Per-call extra exact comparisons are O(6),identity check O(36). No retained call
ledgers or per-solve vector copies. Kernel timing/counting adds small test-only work;
one corrective FTRAN is intentional coverage, not a performance claim. No benchmark
required for cold bounded test setup. Extra17assertions per targetcase enforce scope.
Actual-master gate passed215/215,20audit gates623pins and7supplementary raw/portable/
source/driver/user checks. Master source byte-identical to accepted GREEN. Separate
host runner407128/child407129/launchgroup407116 absent,noJulia,same boot.
Fresh gpt-6-astra review found no Critical/Important/Minor or unnecessary work/memory.
BroaderS6/x64/fullsuite/privateCI
cause remain open. Next separate dual recovery contract step must respect S6-J
rejection; do not promote explicit retry or weaken work/publication safeguards.
