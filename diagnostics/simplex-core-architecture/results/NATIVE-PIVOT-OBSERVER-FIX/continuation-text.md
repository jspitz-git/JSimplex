Native pivot observer correction prepared OFFLINE and independently reviewed;
see results/NATIVE-PIVOT-OBSERVER-FIX/REPORT.md, inverse.json, check.json and review.
Separate test-support-fixed.jl adds one denseString helper and replaces only four
potentially sparse output/RHS token broadcasts; whole inverse restores original.
Separate test-driver-fixed.jl changes only four includes and reuses frozen tests.
Remaining controls/nzval/cost-driver broadcasts have concrete dense storage.
No candidate production/test oracle edits;6858/792/324 expectations unchanged.

regression.jl has119prospective assertions,12dense/sparse/empty/specialvalue cases,
16helpercalls/1expectedoldbroadcastMethodError/0factor-solves. Inputvalues/scalar
owners/precision/rounding/TOMLroundtrip checked prospectively. Not wired into the
full frozen test driver and NOTexecuted. Source/inverse checks are NOTJuliaRED/GREEN.
All Julia in this correction remains UNEXECUTED. Dense token output needsO(n)
storage/conversions; generic sparse reads maycostO(nlog(1+nnz)) and mutablezero
allocations. No speedup/nativework/zeroallocation proof; no new production cost.

NEXT: prepare NEW concrete GREEN-2 driver/admission routing and exact stage/output
manifest, wire119regressions with their own budget while preserving original6858
assertions/792entries/324equations, independently review BEFORE any new Julia.
No replacement launcher/admission exists yet. Frozen old control/launch target
the consumedgreen path and MUSTNOT rerun/overwrite. AcceptedRED and failedGREEN
must remain distinct prerequisites. Existing short-run human permission remains;
no repeated permission ask, but fresh concrete review/host/refs/groups required.
No cost orTask3 advancement before new acceptedGREEN. Do not tune away failures.

OriginalGREEN remainsFALSE:5352passes1observererror1506unfulfilled,289/792calls,
34/324equations, consumedattempt. Captured solve succeeded before sparse RHS
textconversion failed; no fullcandidatecorrectness or solverdefect conclusion.
Alloldraw/scripts/reviews/pins unchanged. Current GREENclosure/publication
STATUS/roadmap hashes map ONLY to OBSERVER-FIX before-fix copies via mappings;
every older mapping remains. Before future pinned edits get fresh212groups AND
sessions/noJulia/boot+start_ticks+command; storedhost is not freshpreflight.
Master6f68e24 unchanged, actualsrc/test/env/CI/directprototypes unchanged.
CIoff/HHreuse disabled/automationpaused, olddirectcost1FAILED/CONSUMED/cost2BLOCKED.
Broaderplan OPEN. No equivalent old inventory or numerical reruns.
