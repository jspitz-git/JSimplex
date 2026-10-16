# Initial independent review — changes required

This is a planning/source review only. No Julia, candidate implementation, old driver, numerical parser, compilation or measurement ran. All 15 supplied source/evidence hashes matched. The exact pre-amendment plan/spec and evidence bindings are in review-initial.json.

## Important I1: exported column permutation breaks the stated append construction

The spec lines 17/25 require basis-stable column identity order but construct row lists by appending in CSC column order. The packed reference uses IDs equal to original basis positions: `q[j]` for logical column `j` (`direct-factor.jl:118-120,147-150`; `bartels_golub_rows.jl:67-80`). With q=[3,1,2], a row present in all columns is appended as [3,1,2], violating the sorted-row invariant. Labeling columns [1,2,3] instead changes the promised reference visitation order and the column-map semantics. This affects every row merge and adjacent swap, even if the resulting individual coefficient operations sometimes commute.

Specify the q-aware construction/interface and add a nonidentity-q fixture. Iterating stable IDs ascending and reading CSC column inverseq[cid] gives the required lists in O(n+nnzU), with no per-row sorting or extra persistent map.

## Important I2: closure draft reruns excluded full historical inventory verification

`close.py` calls old `control.validate_sources()`. Reading that function shows complete old source/stage/runtime inventory hashing, beyond the 15 relevant pins explicitly sufficient for this task. Replace it with new bounded closure checks, and describe their actual coverage. Preserve historical evidence unchanged.

## Numerical, work and memory assessment

Subject to I1, the shared-slot architecture is feasible: adjacent logical rows have adjacent shared column nodes; a one-row occurrence needs no relink when maps swap; pure rotation moves only the selected physical row's nodes while map rotation carries all other rows. Adjacent-target fill can insert immediately after the pivot source node, provided its absence is established by the ordered merge. Exact-zero stores, explicit signed-zero import, saved-next cursor handling and allocation-before-link rules address the main deletion/reuse hazards.

No unnecessary NEW production-wide scan, coefficient mirror, per-coefficient heap object or retained backend is mandated by this plan. New intended costs are seven buffers (56C bytes) and eight map/head vectors (64n bytes), row-merge traversal per elimination, row-list searches during whole-column replacement, interval traversal during rotation, pointer chasing on every solve, O(C) growth/copy and full-manager refactor construction. Growth coexistence and saved copies add peak memory beyond the formula; scratch, history and both prepared-spike slots are separately retained. The q fix must not add sorting to each solve/update. I2 is avoidable verification work, not a production kernel cost.

The separate factor type avoids packed-layout generic dispatch. Source-bound helper adaptation, two-slot provenance, fresh copied caches, shared-prefix history, separate lower scratch, refactor publish-after-construction and partial-update failure semantics are adequately planned. The row-cache coordinate map can differ from the upper map after copying, and the plan already requires adapting composed replay. Future tests must prove that contract; no runtime qualification is claimed here.

Primary cost arithmetic is consistent: 8 cells x 10 pairs x 2 sides =160 windows/process; two processes=320 constructors,640 refactors,2560 updates,5120 FTRAN and2560 BTRAN. Independently budgeted controls remain deferred. Per-process time/allocation gates, every-pair memory gate and ordinary comparisons are kept separate. There is no speedup claim; solve locality, high-water capacity and extra links can defeat the intended update benefit.

Recommendation: amend I1 and I2, refresh self-review and obtain a hash-bound final review before closure/publication. No candidate code or benchmark is needed to resolve these findings.
