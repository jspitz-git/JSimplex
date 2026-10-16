# Direct BG block U — Task1 source preparation

Task1 of the accepted 2026-10-16 plan is prepared and independently accepted within the offline boundary. No Julia query, parser, import, compilation, structural test, numerical test or measurement was executed. Task2 adapters and Task3 drivers/admission remain separate work. Runtime correctness, allocations, memory gates and speed are not accepted by this record.

## Exact deliverables

The separate candidate is in diagnostics/direct-bg-block-upper/reproduce:

- block-upper.jl: private Float64 column-block U storage, 424 lines; SHA-256 94529e9b8ed5fb647b210e609708bf8d73db5b260c2a873f6610e0227ac7314c.
- block-oracles.jl: structural/materialization test oracles, 128 lines; SHA-256 87911ed1b6ef01f47c65fed56711f750697ab03599c6fcea6c2564e739dfce3f.
- block-upper-tests.jl: 14 named testsets, 193 lines; SHA-256 2f88495aaf8be75ce92665925b2da155dad5336fad61a0ef60ae0da0b2012a43.

The 83 static assertion sites include the oracles; they are not an executed assertion count. Coverage includes nonidentity q, handles and reciprocal row references, direct cursors and malformed imports, gap relocation/growth, 32-to-33 splits including interior insertion, swaps/rotation, retained-right merge, allocation refusal, real/synthetic checked limits, explicit/signed zeros, repeated fills, fragmentation and independent copies. No actual production or test file was changed.

The canonical ordinary overlay is task1-stage-reviewed under the ignored task workspace. Its 78 files comprise the 75 accepted baseline files and these three additions. Seventy-four baseline files are byte-identical; the root module differs only by the explicit candidate include, with a verified inverse. source-bindings-reviewed.json and overlay-reviewed.json bind it. The original overlay and preparation scripts remain frozen.

## Memory and computational work

MEMORY-WORK.md supplies the complete requested-storage ledger: all 23 vector fields and four scalar fields, nested owners, retained capacities, spare directory cells, headers, growth coexistence, full copy/refactor overlap and per-operation work. For its defined capacities C/R/K/D/S and dimension n, element payload is 16C+4R+28K+32n+656 bytes; outer directory payload is 8n+24D. Container count is n+3S+23 and the recorded 64-bit object-field contribution is 216 bytes. The historical 40-byte vector graph model is not a physical heap or native-memory bound; allocator overreservation, owner sharing and process peaks remain explicit unknowns.

Bulk import is O(n+m), with fixed validation/count/fill passes. Split stages and writes 33 tuples and clears 31 suffix slots. Delete plus one merge can move up to 63 old tuples, with separately budgeted clearing. Generic insertion scans the selected row and column; Task2 must consume the direct predecessor/cursor path. Capped additive row growth can accumulate Theta(f*d+f^2) copying. Copy scales with all retained capacities. No basis solves or update-chain work are introduced in Task1.

The conditional initial dense96 whole-factor graph estimate is 189560 bytes against a 190467.2-byte gate, leaving only 907.2 bytes. This is neither measured memory nor a gate pass: fragmentation, gaps, additional slabs and future manager state can erase the margin. All eight initial cells and 88 historical checkpoint lower-bound calculations are accounted for. No benchmark was authorized or run.

Independent review identified redundant import initialization, repeated free-bin search and excess row-gap initialization/repair; the canonical source removes those costs. Bounded clearing of unused numeric cells remains deliberate and explicitly charged. The review found no unexplained retained owner, full-U mirror, full-arena copy per fill or full invariant check in the candidate hot paths. Source counts do not establish allocation-free execution.

## Evidence, corrections and acceptance

- source-check.json: 33 offline source/hash checks passed, 27 bindings.
- budget-final.json: 15 offline arithmetic checks passed. The initial budget.json remains FALSE: it incorrectly carried pre-refactor capacity into fresh export segments. The correction resets m/K at refactor; no measured result or gate changed.
- independent-check-v1.json: 21 independent text/hash/arithmetic checks passed, including all 78 overlay files, all 75 baseline hashes and 88 checkpoint calculations.
- independent-review-v1.md: fresh gpt-6-astra semantic review accepted Task1 source preparation with no unresolved blocking findings. Its exact final bindings and ledger-count clarification are separate records.

Earlier source/test/ledger versions, initial overlay, failed arithmetic and review clarification are preserved. closure.py explicitly maps the old budget source to block-upper.jl.before-reserve-fix, old budget tests to block-upper-tests.jl.before-capacity-fix, final budget tests to block-upper-tests.jl.before-cursor-addition, and initial source/independent ledger bindings to MEMORY-WORK.md.before-count-fix. The before-cursor test copy was reconstructed by the recorded exact inverse, not represented as a contemporaneous capture. No old script was rerun.

The foreign user Julia process identified in host.json was not touched; the host record is not a no-Julia or future numerical admission. Only new diagnostic candidate/evidence and ignored staging paths were written. STATUS, roadmap, actual src/test, environment, CI and master remain unchanged. Historical raw results and user untracked files remain intact. Separate closure and exact publication records bind this report before any diagnostic commit/push.
