Independent Task1 ownership RED admission: ACCEPTED

Pins SHA256: da7da6bbbc64ac802d7d68a4a44ca454d017a84c8b53b90829471c2d8077e343

Admits only the exact one-assertion regression through run-ownership.py ownership-red. This is source admission, not an observedRED result or correctedGREEN acceptance. The prior rejectedGREEN review remains preserved.

pin_inventory: 140 unique explicit files equal inventory; trees empty; every SHA256 and resolved path matches

prior_binding: all136 prior GREEN inventory entries unchanged; candidate5sourcefiles and original4testfiles unchanged

runner_delta: run-ownership.py differs only in stage whitelist ownership-red and ordinary expected failure pattern1instead16; AST valid

ordinary_test: single ordinary @test source basic_mask preservation after all-true sentinel and one private import; expected0passed1failed0errored0broken exit1

source_failure: basis_matrix(source) calls _validate_basis which resets source basic_mask to actual basis, so sentinel differs at3nonbasicindices

numerical_budget: one3x3fixture initialization plus one privateimport/nativefactorbuild; no explicitFTRAN,no publicLPsolve,no measurement

command: exact pinned Julia1.13 command/project master path; startup/history disabled, existing compiled modules/pkgimages only, heap2GiB, Julia1/GC1,0; test asserts packagepath/Julia1/BLAS1

guards: unchanged approved guardchain, nonblocking numericallock, pre/post noJulia, fresh boot/start_ticks/command and historical782plusRED groups/sessions; RAM>=6GiB swap<=1GiB hardVM8GiB; owned cleanup

deadline_outputs: new exclusive ownership-red-run absent;1800s shared accepted-run deadline covers preflight, execution, terminalhost and finalhash; preserves abnormalpartiallogs

review_activity: read-only source/AST/hash; noJulia,oldlauncher,repoedits

Work/memory assessment: no new production work or memory retention. The regression deliberately pays one tiny existing workspace setup and one tiny private phase reconstruction plus one6-bit mask snapshot; this is appropriate cold evidence for the reported ownership defect. No unnecessary new computational work/allocation/retention found in this focused test or the two-line runner amendment. Existing pin hashing is cold guard overhead, not solver work. No performance measurement is justified or claimed.

Limits: admission retains existing accepted-run deadline semantics; an arbitrarily blocked filesystem call is not guaranteed interruptible. Guard freshness checks must still pass at launch. No dual iterations, commits, recovery or certificates are exercised.
