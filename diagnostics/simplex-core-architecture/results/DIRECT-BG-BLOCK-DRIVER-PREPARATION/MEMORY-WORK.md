# Prospective work and memory — correctness driver

No candidate source change is made. Every count here is derived from the frozen test/control sources, not measured. The seven existing fixtures (empty0,singleton1,diagonal8,coupled8,core4,scaled16,stored_zeros4), Float64/native-one and Float64/Markowitz-default are unchanged. Supplemental structural sizes0/1/31/32/33/64 and repeated-row-fill160 are fixed; no LP/MPS input or public simplex iteration.

## Call ledger

work-ledger.json enumerates each of seven adapter groups. Reference/candidate API attempts are constructor53/123, refactor62/153, copy13/77, FTRAN384/400, BTRAN144/160, replacement118/135. Three manually constructed RejectBackend sentinel factors are additional. Six candidate constructor rejections precede factorization. Thus backend construction attempts115reference+270candidate=385, including failures. They are factorization entry counts, not total inner triangular/native solves. Private export/orientation, normalization, cache preparation and history applications retain their actual implementation work; no complete machine-operation/import budget is asserted.

Candidate constructor failures:6 prebackend,58 setup storage seam,2 malformed export. Refactor failures:58 storage seam,14 singular,14 throwing export. Copy failures:58 storage seam. Replacement failures:1 reference,18 candidate (including unsupported/dimension/tolerance routes and3 deliberate partial block failures). Candidate solve rejections:16 per direction. Prospective successful paired behavior is otherwise unchanged; no retry or solve on partially failed U before an explicit tested refactor.

Helpers:108 replace_pair!,512 solve_pair (377F/135B,each manager),673 pair_state. Each solve_pair performs two exact Rational{BigInt} residual checks:1024 total. Additional direct solve calls compare output bits and exception types. Test invariant @assert loops are separate from15093 Test outcomes. They scan blocks/rows/backrefs, allocate seen/owners/sets, materialize dense matrices and compare full arrays. These are correctness costs, not production overhead or timed benchmark work.

## Allocation injection, fully expanded

Task1 insertion:3*(1calibration+14failure attempts)=45operations; build1+90=91; copy1+69=70. Total206,201throws. Request arithmetic:3*(14+14*15/2)+(90+90*91/2)+(69+69*70/2)=7026.

Task2 diagonal3 storage:2arms*3operations*(1calibration+29failures)=180operations,174throws;6*(29+29*30/2)=2784requests. Two partial-update failures add2operations/2throws/3requests. Combined388operations/377throws/9813requests,9436 completed before the injected throw. Successful controls and every fresh backend setup preceding a failing build are included in the call ledger. Ordinary factories outside the custom allocator, Test storage, tuples, exports, rows, scratch, native allocations and GC are additional; these request counts are not aggregate allocation measurements.

## Memory and scaling

Reuse the accepted Task1/Task2 MEMORY-WORK.md budgets, pinned in entry.json. U payload16*C+4*R+28*K+32*n+656 plus outer reference slots8*n+24*D; vector containers n+3*S+23. Include per-container headers/backing reserve,27-field object and eight-field factor, lower factor/policy, updates/recycled/shared histories, work/spike, row cache and up to two prepared RHS entries/externally rooted outputs. Slabs/free blocks/gaps/descriptors retain high-water capacities until refactor, and copy duplicates retained capacities. Transactional refactor temporarily coexists with old U/lower factor/cache and held snapshots. Explicit reserve allocations precede publication but a failed update may already have removed a column. Capacity preservation is not factor rollback or native cleanup.

Correctness tests additionally retain exact Rational matrices/vectors, input and state snapshots, saved factors, all pair token buffers, dense expected matrices, and error strings. Largest structural materializations are160x160 Float64 (204800 payload bytes each); full64x64/40x40 population/deletion checks repeat full scans thousands of times. They are intentional bounded test work. Test.Pass results are counted and discarded by the recorder (constant state per group), while failure strings accumulate only on failure;21 group records remain until serialization. No per-solve production ledger, mirrored numerical U or hot-path instrumentation is introduced. Python source manifests retain hashes, not numerical/native objects. VM8GiB/resource guard is a runtime safety bound, not a predicted peak measurement or proof of native freeing.

No avoidable new production work or retained production memory was introduced by driver preparation. Test-only costs are necessary to exercise accepted contracts and are explicitly excluded from speedup claims. Time, aggregate allocation events/bytes, graph checkpoints and compile-zero cost cells remain future Task3 cost-driver work; correctness elapsed/RSS cannot accept performance.
